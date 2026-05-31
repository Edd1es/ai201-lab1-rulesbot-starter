# Spec: `generate_response()`

**File:** `generator.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Given a user query and a list of retrieved rule chunks, generate a response that directly answers the question using only the retrieved text as context. The response must be grounded — it should not draw on the model's general knowledge of board games, only on what was retrieved.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | `str` | The user's original question |
| `retrieved_chunks` | `list[dict]` | Ranked list of chunks from `retrieve()`, each with `"text"`, `"game"`, and `"distance"` |

**Output:** `str`

A plain string containing the response to show the user. The response should:
- Answer the question using only the retrieved rule text
- Identify which game the answer comes from
- Acknowledge clearly when the answer is not found in the loaded rules

Returns a fallback string (not an error) when `retrieved_chunks` is empty.

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Context formatting

*How will you format the retrieved chunks before passing them to the LLM? Describe the structure — not the code. Consider: will you label chunks by game? Include distance scores? Separate chunks with delimiters?*

```
I join the retrieved chunks into a single context block, each one labeled with its source game on its own line, then the chunk text, with a blank line between chunks. So each entry reads "[Source: Catan]" followed by the chunk text. I label by game but do not include distance scores — the scores are useful for debugging but would just be noise to the model. The explicit source label matters because the top-3 can span multiple games: labeling each chunk lets the model attribute its answer to the right game and lets me cite the source. Clearly delimited, labeled sources help the model distinguish between them rather than blurring them together.
```

---

### System prompt — grounding instruction

*Write the exact system prompt instruction you will use to prevent the model from answering beyond the retrieved text. This is the most important design decision in this function.*

```
You are RulesBot, a board game rules assistant. Answer using only the rule text provided below. If the answer is not contained in the provided text, say so clearly — do not draw on outside knowledge or fill in gaps from what you know about board games.
```

---

### System prompt — citation instruction

*Write the exact instruction you will use to tell the model to identify which game its answer comes from.*

```
Always cite which game your answer comes from.
```

---

### Fallback behavior

*What should the response say when the answer isn't found in the loaded rule books? Write the exact fallback message.*

```
I couldn't find anything relevant in the loaded rule books. Try rephrasing your question — or check that your ingestion pipeline is working.
```

---

### Handling low-relevance chunks

*`retrieved_chunks` may include chunks with high distance scores (weak relevance). Will you filter these out before building context, pass them all in, or handle them another way? What are the tradeoffs?*

```
I pass all retrieved chunks in without filtering by distance, and rely on the grounding instruction to handle weak matches. Because the model is told to answer only from the provided text and to refuse when the answer isn't there, a set of loosely-related chunks should produce a refusal rather than a confident wrong answer. The tradeoff: filtering by a distance threshold before building context would keep obviously-irrelevant chunks out of the prompt entirely, but the right cutoff is corpus-dependent and brittle, and filtering risks dropping a good chunk that happens to score slightly high. Keeping retrieval unfiltered and pushing the "is this relevant enough?" judgment to the prompt keeps the two stages cleanly separated.
```

---

### Message structure

*Describe how you will structure the messages list for the API call — what goes in the system message vs. the user message?*

```
Two messages. A system message carries the grounding and citation instructions — the role and rules RulesBot must follow. A user message carries the actual task: the formatted context block followed by the question, structured as "Context:\n<context>\n\nQuestion: <query>". Keeping the grounding rules in the system role and the data in the user role is the standard chat-completions split and keeps the instruction from getting buried inside the context.
```

---

## Implementation Notes

*Fill this in after implementing and testing.*

**Test query and response:**

```
Query: How do you get out of Jail in Monopoly?
Response: Described the three Monopoly mechanics — pay $50, roll doubles, or use a Get Out of Jail Free card — and cited Monopoly as the source.
Correctly grounded? Yes
Cited the right game? Yes
```

**One thing you changed from your original spec after seeing the actual output:**

```
After seeing the output I kept the grounding instruction as one firm sentence rather than padding it with extra rules — the single "answer using only the rule text below, do not draw on outside knowledge" line did the work, and the refusal on the Chess castling test confirmed it held without further tuning.
```
