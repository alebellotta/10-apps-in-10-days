from app.agents.prompts.utils import load_brand_voice


def build_classifier_prompt(text: str, history: list[dict[str, str]], user_metadata: dict[str, str]) -> str:
    voice = load_brand_voice().get("brand_voice", {})
    return f"""
You are the Intent Classifier Agent for an Instagram DM workflow.
Return JSON only with keys:
intent, language, sentiment, priority, requires_human, confidence, reasoning_summary.

Brand default language: {voice.get("language_default", "it")}
User metadata: {user_metadata}
Conversation history: {history}
Last message: {text}
""".strip()
