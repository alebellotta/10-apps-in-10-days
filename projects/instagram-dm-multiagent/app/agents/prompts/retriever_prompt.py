def build_retrieval_prompt(text: str, intent: str, history: list[dict[str, str]], kb_entries: list[dict[str, str]]) -> str:
    return f"""
You are the Context Retrieval Agent.
Return JSON only with keys:
conversation_summary, relevant_faq_entries, known_customer_data, missing_information.

Intent: {intent}
Conversation history: {history}
Latest user message: {text}
Candidate FAQ entries: {kb_entries}
""".strip()
