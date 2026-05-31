# Spec: `retrieve()`

**File:** `retriever.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Given a user's natural language query, find the most relevant chunks from the vector store using semantic similarity search. Return them ranked by relevance so that `generate_response()` can use them as context.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | `str` | The user's natural language question |
| `n_results` | `int` | Maximum number of chunks to return (default: `N_RESULTS` from `config.py`) |

**Output:** `list[dict]`

Each dict in the returned list must contain exactly these keys:

| Key | Type | Description |
|-----|------|-------------|
| `"text"` | `str` | The chunk text |
| `"game"` | `str` | The game name this chunk came from |
| `"distance"` | `float` | Cosine distance score — lower means more similar to the query |

Results should be ordered from most to least relevant (lowest to highest distance). Returns an empty list `[]` if the collection contains no documents.

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Query approach

*Describe how you will use `_collection.query()` to find relevant chunks. What arguments will you pass, and why?*

```
Call _collection.query() with query_texts=[query], a list holding the single user query. The collection's embedding function (all-MiniLM-L6-v2) embeds this query into the same vector space as the stored chunks, so I never embed anything manually. I pass n_results=n_results to cap how many nearest neighbors come back (default 3), and include=["documents", "metadatas", "distances"] because I need the chunk text, the per-chunk metadata (to recover the game name), and the distance scores (to rank and inspect relevance). ChromaDB runs the nearest-neighbor search by cosine distance and returns the closest chunks, already sorted closest-first.
```

---

### Return structure

*Sketch out what one item in your return list looks like as a concrete example. Where does each field come from in the query results?*

```
One item looks like: {"text": "When a 7 is rolled, no one collects resources. The player who rolled moves the robber...", "game": "Catan", "distance": 0.142}. The "text" field comes from results["documents"][0][i], "game" comes from results["metadatas"][0][i]["game"], and "distance" comes from results["distances"][0][i]. I zip the three parallel lists together so each dict is assembled index-for-index. The final return type is list[dict], ordered lowest distance (most similar) first.
```

---

### Handling the nested result structure

*`_collection.query()` returns nested lists. Describe what index you need to access to get the actual list of results for a single query, and why the nesting exists.*

```
query() returns lists-of-lists, one inner list per query string passed in, because the API is built for batched queries. Since I only pass one query, all my results live at index [0]: results["documents"][0] is the list of chunk texts, results["metadatas"][0] is the list of metadata dicts, and results["distances"][0] is the list of distance floats. Forgetting the [0] is the classic bug: results["documents"] is a single-element list whose only element is itself a list, so iterating gives one nested list instead of strings, and m["game"] fails with "list indices must be integers, not str" because m is a list, not a dict.
```

---

### Relevance threshold

*Will you filter out results above a certain distance score, or return all `n_results` regardless of how relevant they are? What are the tradeoffs of each approach?*

```
No distance threshold in retrieve() — I return all n_results ranked closest-first and let generate_response() decide what to do with weak matches. The no-threshold approach is simplest and never accidentally returns an empty list, but on an off-topic query it still returns the three least-bad chunks, which the grounding instruction in Milestone 3 has to be trusted to reject. A threshold (e.g. drop anything above 0.6) gives cleaner "no relevant rules found" behavior and can skip the LLM call, but the right cutoff is corpus-dependent and brittle — too tight and good answers get filtered out. Keeping retrieval dumb and pushing the "is this good enough?" judgment to the generation prompt keeps the two stages cleanly separated.
```

---

### Edge cases

*How does your implementation behave when: (a) the collection is empty, (b) the query matches no chunks well, (c) the query matches chunks from multiple games?*

```
(a) Empty collection: the pre-built guard if _collection.count() == 0: return [] fires before any query, so there's no crash, and generate_response() then hits its empty-chunks fallback message. (b) Poor match: query() still returns its n_results closest chunks, just with high distance scores (~0.7-0.9); retrieve() returns them as-is and grounding in M3 is responsible for refusing if nothing is actually relevant. (c) Multiple games: expected and correct — "how do you win?" is semantically close to victory-condition chunks across several rulebooks, so the top-3 can legitimately span games. That's semantic search matching meaning, not a bug.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 3.*

**Test query and top result returned:**

```
Query: What happens when you run out of disease cubes in Pandemic?
Top result game: Pandemic
Distance score: ~0.37
Does it make sense? Yes — top chunks are all Pandemic, specifically about cube depletion and outbreaks, with low distances. Any wrong-game chunks sit lower with noticeably higher distance.
```

**One thing about the query results that surprised you:**

```
How tight the distance spread is for a well-targeted query — the relevant Pandemic chunks cluster around 0.1-0.2 while anything off-topic jumps to 0.6+. The gap makes it visually obvious which results are real matches, which is why printing distances is such a useful debugging move.
```
