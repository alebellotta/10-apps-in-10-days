def build_escalation_prompt(text: str, classifier_output: dict, policy_output: dict, draft_output: dict | None) -> str:
    return f"""
You are the Escalation Agent.
Summarize why a human should review this message.
Return JSON only with keys:
escalation_reason, operator_summary, suggested_reply, priority.

User message: {text}
Classifier output: {classifier_output}
Policy output: {policy_output}
Draft output: {draft_output}
""".strip()
