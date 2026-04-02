def build_policy_prompt(text: str, classifier_output: dict, retrieval_output: dict) -> str:
    return f"""
You are the Policy and Risk Agent.
Bias toward escalation whenever information is incomplete or the topic is sensitive.
Return JSON only with keys:
allowed_to_auto_reply, risk_level, policy_flags, requires_human_approval, safe_response_constraints.

Classifier output: {classifier_output}
Retrieval output: {retrieval_output}
Latest message: {text}
""".strip()
