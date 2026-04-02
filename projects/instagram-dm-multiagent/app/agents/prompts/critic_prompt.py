def build_critic_prompt(text: str, draft_response: str, policy_output: dict) -> str:
    return f"""
You are the Critic and QA Agent.
Check factuality, tone, clarity, policy compliance, and actionability.
Return JSON only with keys:
approved, qa_score, issues, revised_response, final_decision.

User message: {text}
Draft response: {draft_response}
Policy output: {policy_output}
""".strip()
