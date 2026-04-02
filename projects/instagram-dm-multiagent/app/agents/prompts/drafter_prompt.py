from app.agents.prompts.utils import load_brand_voice


def build_drafter_prompt(text: str, classifier_output: dict, retrieval_output: dict, constraints: list[str]) -> str:
    voice = load_brand_voice().get("brand_voice", {})
    return f"""
You are the Response Drafting Agent.
Write a concise Instagram DM reply in {voice.get("language_default", "it")}.
Maximum length: {voice.get("max_length_chars", 500)} characters.
Use a {voice.get("tone", "friendly_professional")} tone.
Do not invent prices, policies, or guarantees.
If data is missing, ask one short clarifying question.

Classifier output: {classifier_output}
Retrieval output: {retrieval_output}
Constraints: {constraints}
User message: {text}

Return JSON only with keys:
draft_response, response_style, used_sources, open_questions.
""".strip()
