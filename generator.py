from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL

_client = Groq(api_key=GROQ_API_KEY)


def generate_response(query, retrieved_chunks):
    if not retrieved_chunks:
        return ("I couldn't find anything relevant in the loaded rule books. "
                "Try rephrasing your question — or check that your ingestion pipeline is working.")

    context = "\n\n".join(
        f"[Source: {c['game']}]\n{c['text']}" for c in retrieved_chunks
    )
    system_prompt = (
        "You are RulesBot, a board game rules assistant. "
        "Answer using only the rule text provided below. "
        "If the answer is not contained in the provided text, say so clearly — "
        "do not draw on outside knowledge or fill in gaps from what you know "
        "about board games. Always cite which game your answer comes from."
    )
    user_message = f"Context:\n{context}\n\nQuestion: {query}"
    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content
