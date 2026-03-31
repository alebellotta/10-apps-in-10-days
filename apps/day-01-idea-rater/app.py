from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent

import pandas as pd
import streamlit as st


DIMENSIONS = {
    "market_pain": "Market pain",
    "willingness_to_pay": "Willingness to pay",
    "implementation_complexity": "Implementation complexity",
    "differentiation": "Differentiation",
    "speed_to_mvp": "Speed to MVP",
}

DEFAULT_WEIGHTS = {
    "market_pain": 30,
    "willingness_to_pay": 20,
    "implementation_complexity": 15,
    "differentiation": 20,
    "speed_to_mvp": 15,
}

EXAMPLE_PRESETS = {
    "AI meeting prep assistant": {
        "idea_description": (
            "A tool that turns a calendar event into a one-page meeting brief with company context, "
            "participant notes, likely objections, and a draft agenda."
        ),
        "target_user": "B2B account executives and customer success managers",
        "pain_point": (
            "Revenue teams walk into important meetings underprepared and spend too much time manually "
            "researching contacts, accounts, and past conversations."
        ),
        "monetization_hypothesis": (
            "Sell as a per-seat SaaS subscription to sales teams and RevOps leaders, with expansion into "
            "enterprise CRM workflows."
        ),
    },
    "Neighborhood meal planner": {
        "idea_description": (
            "A mobile app that matches households with nearby cooks for affordable prepared meals "
            "available within walking distance."
        ),
        "target_user": "Busy urban professionals and parents",
        "pain_point": (
            "People want convenient meals that feel more personal than takeout, but local options are fragmented."
        ),
        "monetization_hypothesis": (
            "Take a commission on each transaction and upsell premium placement for top local cooks."
        ),
    },
}


@dataclass
class DimensionResult:
    name: str
    score: int
    weight: int
    weighted_score: float
    rationale: str


def normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def validate_inputs(idea_description: str, target_user: str, pain_point: str, monetization_hypothesis: str) -> list[str]:
    errors: list[str] = []
    fields = {
        "Idea description": idea_description,
        "Target user": target_user,
        "Pain point": pain_point,
        "Monetization hypothesis": monetization_hypothesis,
    }
    for label, value in fields.items():
        if len(normalize_text(value)) < 15:
            errors.append(f"{label} must be at least 15 characters so the scoring is meaningful.")
    return errors


def count_matches(text: str, keywords: list[str]) -> int:
    lower_text = text.lower()
    return sum(1 for keyword in keywords if keyword in lower_text)


def score_market_pain(idea_text: str, pain_point: str) -> tuple[int, str]:
    urgent_keywords = [
        "manual",
        "expensive",
        "slow",
        "compliance",
        "risk",
        "revenue",
        "waste",
        "frustrating",
        "underprepared",
        "churn",
    ]
    pain_hits = count_matches(pain_point, urgent_keywords)
    score = min(10, 4 + pain_hits)
    if len(pain_point) > 180:
        score = min(10, score + 1)
    rationale = (
        "Scores higher when the pain sounds urgent, costly, or operationally persistent."
        f" Detected {pain_hits} urgency signals."
    )
    return score, rationale


def score_willingness_to_pay(target_user: str, monetization_hypothesis: str) -> tuple[int, str]:
    monetization_keywords = [
        "subscription",
        "enterprise",
        "b2b",
        "per-seat",
        "commission",
        "savings",
        "revenue",
        "team",
        "ops",
        "workflow",
    ]
    buyer_keywords = ["manager", "leader", "team", "business", "company", "professional", "operator"]
    score = 3 + count_matches(monetization_hypothesis, monetization_keywords) + count_matches(target_user, buyer_keywords)
    rationale = (
        "Scores higher when a clear buyer, budget owner, or ROI path is visible."
        " The engine looks for commercial language in the user and monetization fields."
    )
    return min(10, score), rationale


def score_implementation_complexity(idea_description: str, pain_point: str) -> tuple[int, str]:
    hard_keywords = ["marketplace", "real-time", "hardware", "computer vision", "multi-sided", "logistics", "payments"]
    simple_keywords = ["dashboard", "report", "workflow", "assistant", "summary", "template", "planner"]
    hard_hits = count_matches(idea_description + " " + pain_point, hard_keywords)
    simple_hits = count_matches(idea_description + " " + pain_point, simple_keywords)
    raw_score = 6 + simple_hits - hard_hits
    rationale = (
        "Higher is better: the score rises when the MVP can be delivered with straightforward workflows and drops "
        "when delivery depends on complex operations or infrastructure."
    )
    return max(1, min(10, raw_score)), rationale


def score_differentiation(idea_description: str, pain_point: str) -> tuple[int, str]:
    moat_keywords = ["proprietary", "workflow", "integration", "specialized", "vertical", "local", "context", "automation"]
    generic_keywords = ["app", "platform", "marketplace", "tool"]
    moat_hits = count_matches(idea_description + " " + pain_point, moat_keywords)
    generic_hits = count_matches(idea_description, generic_keywords)
    raw_score = 4 + moat_hits - max(0, generic_hits - 1)
    rationale = (
        "Scores higher when the idea is anchored in a specific workflow, audience, or data advantage instead of generic positioning."
    )
    return max(1, min(10, raw_score)), rationale


def score_speed_to_mvp(idea_description: str, monetization_hypothesis: str) -> tuple[int, str]:
    fast_keywords = ["template", "assistant", "internal", "pilot", "team", "subscription", "service"]
    slow_keywords = ["marketplace", "network", "consumer", "mobile app", "two-sided", "inventory"]
    raw_score = 5 + count_matches(idea_description, fast_keywords) + count_matches(monetization_hypothesis, ["pilot", "subscription"])
    raw_score -= count_matches(idea_description + " " + monetization_hypothesis, slow_keywords)
    rationale = (
        "Scores higher when a narrow MVP can launch quickly with a direct path to test users and lower dependency risk."
    )
    return max(1, min(10, raw_score)), rationale


def score_dimensions(inputs: dict[str, str], weights: dict[str, int]) -> list[DimensionResult]:
    scoring_functions = {
        "market_pain": lambda: score_market_pain(inputs["idea_description"], inputs["pain_point"]),
        "willingness_to_pay": lambda: score_willingness_to_pay(inputs["target_user"], inputs["monetization_hypothesis"]),
        "implementation_complexity": lambda: score_implementation_complexity(inputs["idea_description"], inputs["pain_point"]),
        "differentiation": lambda: score_differentiation(inputs["idea_description"], inputs["pain_point"]),
        "speed_to_mvp": lambda: score_speed_to_mvp(inputs["idea_description"], inputs["monetization_hypothesis"]),
    }

    results: list[DimensionResult] = []
    for key, label in DIMENSIONS.items():
        score, rationale = scoring_functions[key]()
        weight = weights[key]
        results.append(
            DimensionResult(
                name=label,
                score=score,
                weight=weight,
                weighted_score=(score / 10) * weight,
                rationale=rationale,
            )
        )
    return results


def total_score(results: list[DimensionResult]) -> int:
    return round(sum(item.weighted_score for item in results))


def score_label(score: int) -> str:
    if score >= 75:
        return "Strong candidate"
    if score >= 55:
        return "Promising but needs proof"
    return "High risk until validated"


def generate_swot(inputs: dict[str, str], results: list[DimensionResult]) -> dict[str, list[str]]:
    result_map = {item.name: item.score for item in results}
    strengths = [
        "The problem statement reads as concrete and easy to explain." if result_map["Market pain"] >= 7 else "The idea can still be framed more sharply around a painful problem.",
        "There is a plausible path to buyer value and monetization." if result_map["Willingness to pay"] >= 7 else "The monetization path needs stronger economic evidence.",
    ]
    weaknesses = [
        "Differentiation is currently thin and could be copied quickly." if result_map["Differentiation"] <= 5 else "Positioning is reasonably specific, but the moat is still early.",
        "MVP delivery may be slower than it first appears." if result_map["Speed to MVP"] <= 5 else "Execution looks manageable for a narrow first release.",
    ]
    opportunities = [
        f"Target a narrow wedge within {inputs['target_user']} to increase relevance and conversion.",
        "Use early customer interviews and manual service delivery to validate the workflow before expanding scope.",
    ]
    threats = [
        "Existing tools or incumbents may absorb the feature if demand becomes obvious.",
        "If users can workaround the pain manually, urgency may be overstated.",
    ]
    return {
        "Strengths": strengths,
        "Weaknesses": weaknesses,
        "Opportunities": opportunities,
        "Threats": threats,
    }


def generate_experiments(inputs: dict[str, str], results: list[DimensionResult]) -> list[str]:
    weakest = sorted(results, key=lambda item: item.score)[:2]
    experiments = [
        f"Run five customer interviews with {inputs['target_user']} using the current pain statement to test urgency and existing alternatives.",
        f"Prototype a manual concierge version of '{inputs['idea_description']}' and measure willingness to engage before building automation.",
    ]
    for item in weakest:
        if item.name == "Willingness to pay":
            experiments.append("Test pricing acceptance with a landing page or mock proposal that includes explicit packaging and price anchors.")
        elif item.name == "Differentiation":
            experiments.append("Map the top three substitutes and define one workflow-specific advantage you can own in the first release.")
        elif item.name == "Speed to MVP":
            experiments.append("Trim the first release to a one-week build by removing non-essential features and validating the smallest usable workflow.")
        elif item.name == "Implementation complexity":
            experiments.append("List technical dependencies and replace any risky integration with manual or CSV-based operations for the pilot.")
        elif item.name == "Market pain":
            experiments.append("Quantify the pain with a before/after metric such as hours saved, revenue protected, or error reduction.")
    deduped: list[str] = []
    for experiment in experiments:
        if experiment not in deduped:
            deduped.append(experiment)
    return deduped[:3]


def build_report(inputs: dict[str, str], results: list[DimensionResult], swot: dict[str, list[str]], experiments: list[str]) -> str:
    lines = [
        "# Idea Rater Report",
        "",
        f"**Idea:** {inputs['idea_description']}",
        f"**Target user:** {inputs['target_user']}",
        f"**Pain point:** {inputs['pain_point']}",
        f"**Monetization hypothesis:** {inputs['monetization_hypothesis']}",
        "",
        f"## Total Score: {total_score(results)} / 100",
        "",
        "## Score Breakdown",
    ]
    for item in results:
        lines.append(f"- **{item.name}:** {item.score}/10, weighted contribution {item.weighted_score:.1f}")
        lines.append(f"  - {item.rationale}")
    lines.append("")
    lines.append("## SWOT Analysis")
    for section, bullets in swot.items():
        lines.append(f"### {section}")
        for bullet in bullets:
            lines.append(f"- {bullet}")
    lines.append("")
    lines.append("## Recommended Next Experiments")
    for experiment in experiments:
        lines.append(f"- {experiment}")
    return "\n".join(lines)


def apply_example(preset_name: str) -> None:
    preset = EXAMPLE_PRESETS[preset_name]
    for key, value in preset.items():
        st.session_state[key] = value


def main() -> None:
    st.set_page_config(page_title="Idea Rater", page_icon="📈", layout="wide")
    st.title("Idea Rater")
    st.caption("Evaluate a startup or product idea with a rules-based score, SWOT analysis, and next-step experiments.")

    for key in ["idea_description", "target_user", "pain_point", "monetization_hypothesis"]:
        st.session_state.setdefault(key, "")

    with st.sidebar:
        st.header("Setup")
        example_choice = st.selectbox("Load an example", ["Custom"] + list(EXAMPLE_PRESETS.keys()))
        if example_choice != "Custom" and st.button("Apply example", use_container_width=True):
            apply_example(example_choice)
            st.success("Example loaded into the form.")

        st.subheader("Dimension weights")
        st.caption("Weights should total 100. Use them to reflect your strategy.")
        weights = {
            "market_pain": st.slider("Market pain", 5, 50, DEFAULT_WEIGHTS["market_pain"], 5),
            "willingness_to_pay": st.slider("Willingness to pay", 5, 40, DEFAULT_WEIGHTS["willingness_to_pay"], 5),
            "implementation_complexity": st.slider("Implementation complexity", 5, 30, DEFAULT_WEIGHTS["implementation_complexity"], 5),
            "differentiation": st.slider("Differentiation", 5, 40, DEFAULT_WEIGHTS["differentiation"], 5),
            "speed_to_mvp": st.slider("Speed to MVP", 5, 30, DEFAULT_WEIGHTS["speed_to_mvp"], 5),
        }
        weight_total = sum(weights.values())
        if weight_total != 100:
            st.warning(f"Weights currently total {weight_total}. Scores still work, but 100 keeps the report easier to compare.")

    section_one, section_two = st.columns([1.3, 1])
    with section_one:
        st.subheader("1. Describe the idea")
        idea_description = st.text_area(
            "Idea description",
            key="idea_description",
            height=120,
            placeholder="Describe the product or startup idea in plain language.",
        )
        pain_point = st.text_area(
            "Pain point",
            key="pain_point",
            height=120,
            placeholder="What painful problem does this solve?",
        )
    with section_two:
        st.subheader("2. Define the market")
        target_user = st.text_area(
            "Target user",
            key="target_user",
            height=120,
            placeholder="Who experiences the pain most acutely?",
        )
        monetization_hypothesis = st.text_area(
            "Monetization hypothesis",
            key="monetization_hypothesis",
            height=120,
            placeholder="How will this make money or justify a budget?",
        )

    normalized_inputs = {
        "idea_description": normalize_text(idea_description),
        "target_user": normalize_text(target_user),
        "pain_point": normalize_text(pain_point),
        "monetization_hypothesis": normalize_text(monetization_hypothesis),
    }
    errors = validate_inputs(**normalized_inputs)

    st.subheader("3. Evaluate")
    evaluate = st.button("Rate idea", type="primary", use_container_width=True)

    if evaluate:
        if errors:
            for error in errors:
                st.error(error)
            return

        results = score_dimensions(normalized_inputs, weights)
        report_score = total_score(results)
        swot = generate_swot(normalized_inputs, results)
        experiments = generate_experiments(normalized_inputs, results)
        report_markdown = build_report(normalized_inputs, results, swot, experiments)

        metric_one, metric_two = st.columns(2)
        metric_one.metric("Total score", f"{report_score}/100")
        metric_two.metric("Assessment", score_label(report_score))

        st.subheader("4. Score breakdown")
        breakdown_df = pd.DataFrame(
            [
                {
                    "Dimension": item.name,
                    "Score (10)": item.score,
                    "Weight": item.weight,
                    "Weighted contribution": round(item.weighted_score, 1),
                    "Rationale": item.rationale,
                }
                for item in results
            ]
        )
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

        st.subheader("5. SWOT and experiments")
        swot_columns = st.columns(2)
        sections = list(swot.items())
        for index, (section, bullets) in enumerate(sections):
            with swot_columns[index % 2]:
                with st.expander(section, expanded=True):
                    for bullet in bullets:
                        st.write(f"- {bullet}")

        st.markdown("**Recommended next experiments**")
        for idx, experiment in enumerate(experiments, start=1):
            st.write(f"{idx}. {experiment}")

        st.download_button(
            "Download markdown report",
            data=report_markdown,
            file_name="idea-rater-report.md",
            mime="text/markdown",
            use_container_width=True,
        )
    else:
        st.info(
            dedent(
                """
                Use the example preset or fill in the four fields, then click **Rate idea**.
                The app uses deterministic heuristics so it remains useful without external APIs.
                """
            ).strip()
        )


if __name__ == "__main__":
    main()
