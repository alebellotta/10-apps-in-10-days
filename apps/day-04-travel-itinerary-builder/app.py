from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, timedelta
from textwrap import dedent
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class Activity:
    title: str
    category: str
    vibe: str
    duration_hours: float
    price_eur: int
    indoor: bool
    morning_fit: bool
    evening_fit: bool
    description: str


class AITripDay(BaseModel):
    day_number: int = Field(ge=1, le=7)
    title: str = Field(min_length=6, max_length=80)
    morning_plan: str = Field(min_length=30, max_length=320)
    afternoon_plan: str = Field(min_length=30, max_length=320)
    evening_plan: str = Field(min_length=30, max_length=320)
    dining_recommendation: str = Field(min_length=20, max_length=220)
    logistics_tip: str = Field(min_length=20, max_length=220)
    wow_moment: str = Field(min_length=20, max_length=220)
    booking_priority: str = Field(min_length=20, max_length=220)


class AITripBrief(BaseModel):
    trip_hook: str = Field(min_length=20, max_length=180)
    client_summary: str = Field(min_length=50, max_length=420)
    personalization_notes: list[str] = Field(min_length=3, max_length=5)
    booking_checklist: list[str] = Field(min_length=3, max_length=6)
    budget_notes: list[str] = Field(min_length=2, max_length=4)
    concierge_upgrade: str = Field(min_length=25, max_length=220)


class AITripResponse(BaseModel):
    overview: str = Field(min_length=60, max_length=500)
    destination_fit: str = Field(min_length=30, max_length=220)
    tone: str = Field(min_length=10, max_length=80)
    days: list[AITripDay] = Field(min_length=1, max_length=7)
    brief: AITripBrief


DESTINATIONS: dict[str, dict[str, object]] = {
    "Rome": {
        "country": "Italy",
        "airport": "FCO",
        "best_for": ["history", "food", "culture", "architecture"],
        "daily_budget": {"Budget": 110, "Comfort": 185, "Premium": 310},
        "packing": ["Comfortable walking shoes", "Light scarf for churches", "Power bank"],
        "activities": [
            Activity("Colosseum and Roman Forum loop", "history", "iconic", 3.0, 24, False, True, False, "Start early to beat queues and heat."),
            Activity("Trastevere food walk", "food", "social", 2.5, 38, False, False, True, "Best on the first night for an easy landing."),
            Activity("Vatican Museums focus visit", "culture", "immersive", 3.0, 30, True, True, False, "Book an early slot and move straight to the highlights."),
            Activity("Villa Borghese slow afternoon", "relaxation", "calm", 2.0, 12, False, False, False, "A lower-energy reset between bigger sightseeing blocks."),
            Activity("Campo de' Fiori and Pantheon stroll", "architecture", "wandering", 2.0, 0, False, True, True, "Great flexible block for day one orientation."),
            Activity("Tiber sunset walk", "relaxation", "romantic", 1.5, 0, False, False, True, "Easy add-on before dinner."),
        ],
    },
    "Paris": {
        "country": "France",
        "airport": "CDG",
        "best_for": ["culture", "romance", "food", "art"],
        "daily_budget": {"Budget": 135, "Comfort": 220, "Premium": 360},
        "packing": ["Compact umbrella", "Smart-casual dinner outfit", "Museum-ready tote"],
        "activities": [
            Activity("Louvre priority highlights", "art", "iconic", 3.0, 22, True, True, False, "Keep it selective so the museum stays energizing."),
            Activity("Montmartre cafe and stair circuit", "culture", "cinematic", 2.5, 18, False, True, True, "Ideal for photographers and slow wanderers."),
            Activity("Seine picnic and riverbank walk", "relaxation", "romantic", 2.0, 16, False, False, True, "Weather-dependent but easy to swap."),
            Activity("Le Marais tasting crawl", "food", "social", 2.5, 35, False, False, True, "Small plates, pastry stop, and late-afternoon browsing."),
            Activity("Musee d'Orsay visit", "art", "refined", 2.0, 16, True, True, False, "Works well when rain hits."),
            Activity("Eiffel and Trocadero blue-hour stop", "architecture", "romantic", 1.5, 0, False, False, True, "Short and memorable close to the day."),
        ],
    },
    "Barcelona": {
        "country": "Spain",
        "airport": "BCN",
        "best_for": ["architecture", "nightlife", "food", "beach"],
        "daily_budget": {"Budget": 105, "Comfort": 175, "Premium": 285},
        "packing": ["Sunscreen", "Light layers", "Swimwear in warm months"],
        "activities": [
            Activity("Sagrada Familia and Eixample walk", "architecture", "iconic", 2.5, 26, False, True, False, "Pair the basilica with a relaxed neighborhood lap."),
            Activity("Gothic Quarter tapas trail", "food", "social", 2.5, 32, False, False, True, "Best done without a rigid pace."),
            Activity("Barceloneta beach reset", "beach", "easygoing", 2.0, 12, False, False, True, "Useful low-effort buffer if the trip feels packed."),
            Activity("Park Guell morning slot", "architecture", "playful", 2.0, 18, False, True, False, "Morning light and smaller crowds help here."),
            Activity("El Born design and coffee circuit", "culture", "creative", 2.0, 14, False, True, True, "Flexible block with shops, coffee, and galleries."),
            Activity("Bunker viewpoint sunset", "relaxation", "scenic", 1.5, 0, False, False, True, "Great payoff for a lower-cost evening."),
        ],
    },
    "Amsterdam": {
        "country": "Netherlands",
        "airport": "AMS",
        "best_for": ["culture", "canals", "nightlife", "cycling"],
        "daily_budget": {"Budget": 120, "Comfort": 195, "Premium": 320},
        "packing": ["Waterproof jacket", "Crossbody bag", "Bike-friendly shoes"],
        "activities": [
            Activity("Canal cruise opener", "culture", "easygoing", 1.5, 22, False, False, True, "Low-friction first activity after arrival."),
            Activity("Jordaan cafe and gallery wander", "culture", "creative", 2.0, 18, False, True, True, "Balanced option for slower travelers."),
            Activity("Rijksmuseum essentials", "art", "immersive", 2.5, 22, True, True, False, "Focus on one wing plus a short museum stop."),
            Activity("Foodhallen casual tasting", "food", "social", 2.0, 28, True, False, True, "Ideal when weather turns wet."),
            Activity("Vondelpark decompress block", "relaxation", "calm", 1.5, 0, False, True, False, "Good counterweight to museum-heavy days."),
            Activity("De Pijp late dinner circuit", "nightlife", "lively", 2.5, 34, False, False, True, "A stronger evening for groups or couples."),
        ],
    },
}

PACE_TARGETS = {"Slow": 2, "Balanced": 3, "Fast": 4}
SEASON_PACKING = {
    "Spring": ["Light jacket", "Layering basics"],
    "Summer": ["Refillable water bottle", "Sunglasses"],
    "Autumn": ["Packable rain layer", "Closed-toe shoes"],
    "Winter": ["Warm coat", "Thermal layer"],
}

DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")
OLLAMA_MODE_PROFILES = {
    "Cheap": {
        "model": os.getenv("OLLAMA_CHEAP_MODEL", DEFAULT_OLLAMA_MODEL),
        "temperature": 0.1,
        "label": "Lowest local cost, fastest local draft",
    },
    "Balanced": {
        "model": os.getenv("OLLAMA_BALANCED_MODEL", DEFAULT_OLLAMA_MODEL),
        "temperature": 0.2,
        "label": "Best default for most local runs",
    },
    "Premium": {
        "model": os.getenv("OLLAMA_PREMIUM_MODEL", "qwen3:8b"),
        "temperature": 0.25,
        "label": "Richer local copy, heavier model",
    },
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Manrope:wght@400;500;600;700&display=swap');
        :root {
            --bg: #f5efe4;
            --sand: #efe2ce;
            --card: rgba(255, 252, 247, 0.9);
            --ink: #1f2a2f;
            --muted: #5e6a6e;
            --accent: #e36a3d;
            --accent-deep: #9e4321;
            --line: rgba(31, 42, 47, 0.1);
            --olive: #70825d;
            --sun: #f0b65a;
            --shadow: 0 22px 50px rgba(76, 52, 32, 0.12);
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(227, 106, 61, 0.16), transparent 23%),
                radial-gradient(circle at 92% 8%, rgba(112, 130, 93, 0.18), transparent 18%),
                linear-gradient(180deg, #f8f2e8 0%, var(--bg) 100%);
            color: var(--ink);
            font-family: "Manrope", sans-serif;
        }
        .block-container {
            max-width: 1200px;
            padding-top: 1.25rem;
            padding-bottom: 3rem;
        }
        h1, h2, h3 {
            font-family: "Fraunces", serif;
            color: var(--ink);
            letter-spacing: -0.03em;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f7f0e4 0%, #f1e5d3 100%);
            border-right: 1px solid var(--line);
        }
        [data-testid="stSidebar"] * {
            color: var(--ink);
        }
        .hero {
            background:
                linear-gradient(135deg, rgba(31, 42, 47, 0.95) 0%, rgba(66, 76, 63, 0.93) 45%, rgba(227, 106, 61, 0.88) 100%);
            border-radius: 30px;
            padding: 1.6rem;
            color: #fff8ef;
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
            margin-bottom: 1rem;
        }
        .hero::after {
            content: "";
            position: absolute;
            right: -30px;
            top: -30px;
            width: 220px;
            height: 220px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,0.18), transparent 65%);
        }
        .eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 0.72rem;
            opacity: 0.82;
            margin-bottom: 0.45rem;
        }
        .hero-title {
            font-size: 2.8rem;
            line-height: 0.95;
            margin-bottom: 0.55rem;
            max-width: 700px;
            position: relative;
            z-index: 1;
        }
        .hero-copy {
            max-width: 640px;
            color: rgba(255, 248, 239, 0.88);
            position: relative;
            z-index: 1;
        }
        .hero-strip {
            display: flex;
            gap: 0.7rem;
            flex-wrap: wrap;
            margin-top: 1rem;
            position: relative;
            z-index: 1;
        }
        .chip {
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 999px;
            padding: 0.45rem 0.75rem;
            font-size: 0.82rem;
        }
        .chip.ai-on {
            background: rgba(240, 182, 90, 0.22);
            border-color: rgba(240, 182, 90, 0.28);
        }
        .panel, .day-card, .hint-card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 24px;
            padding: 1rem;
            box-shadow: var(--shadow);
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.85rem;
            margin: 1rem 0 1.2rem;
        }
        .metric-card {
            background: rgba(255, 252, 247, 0.72);
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 1rem;
            box-shadow: var(--shadow);
        }
        .metric-label {
            color: var(--muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }
        .metric-value {
            font-family: "Fraunces", serif;
            font-size: 2rem;
            margin-top: 0.28rem;
        }
        .metric-note {
            color: var(--muted);
            font-size: 0.9rem;
            margin-top: 0.2rem;
        }
        .section-title {
            font-size: 1.2rem;
            margin: 0.2rem 0 0.9rem;
        }
        .day-card {
            padding: 1.1rem;
            margin-bottom: 0.9rem;
            background: linear-gradient(180deg, rgba(255,253,250,0.92), rgba(249,243,233,0.94));
        }
        .day-title {
            font-family: "Fraunces", serif;
            font-size: 1.35rem;
            margin-bottom: 0.2rem;
        }
        .day-date {
            color: var(--muted);
            font-size: 0.9rem;
            margin-bottom: 0.8rem;
        }
        .activity-row {
            display: grid;
            grid-template-columns: 96px 1fr 110px;
            gap: 0.8rem;
            align-items: start;
            padding: 0.7rem 0;
            border-top: 1px solid rgba(31, 42, 47, 0.08);
        }
        .activity-row:first-of-type {
            border-top: none;
            padding-top: 0;
        }
        .slot {
            color: var(--accent-deep);
            font-weight: 700;
            font-size: 0.86rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        .activity-title {
            font-weight: 700;
            margin-bottom: 0.15rem;
        }
        .activity-meta {
            color: var(--muted);
            font-size: 0.88rem;
        }
        .price-pill {
            justify-self: end;
            background: #fff4ea;
            color: var(--accent-deep);
            border: 1px solid rgba(227, 106, 61, 0.22);
            border-radius: 999px;
            padding: 0.35rem 0.65rem;
            font-size: 0.82rem;
            font-weight: 700;
        }
        .tag-row {
            display: flex;
            gap: 0.55rem;
            flex-wrap: wrap;
            margin-top: 0.65rem;
        }
        .tag {
            border-radius: 999px;
            padding: 0.32rem 0.58rem;
            background: rgba(112, 130, 93, 0.12);
            color: #45503d;
            font-size: 0.78rem;
            border: 1px solid rgba(112, 130, 93, 0.18);
        }
        .copy-block {
            background: linear-gradient(180deg, rgba(31, 42, 47, 0.96), rgba(42, 52, 50, 0.94));
            color: #fff8ef;
            border-radius: 24px;
            padding: 1.1rem;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: var(--shadow);
        }
        .copy-title {
            font-family: "Fraunces", serif;
            font-size: 1.2rem;
            margin-bottom: 0.45rem;
        }
        .copy-text {
            color: rgba(255, 248, 239, 0.88);
            line-height: 1.55;
        }
        .list-card {
            background: rgba(255, 252, 247, 0.75);
            border-radius: 20px;
            border: 1px solid var(--line);
            padding: 0.95rem;
            box-shadow: var(--shadow);
            height: 100%;
        }
        .list-card-title {
            font-weight: 800;
            margin-bottom: 0.45rem;
        }
        @media (max-width: 900px) {
            .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .activity-row { grid-template-columns: 1fr; }
            .price-pill { justify-self: start; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def trip_length(start_date: date, end_date: date) -> int:
    return (end_date - start_date).days + 1


def validate_trip_inputs(start_date: date, end_date: date, interests: list[str], trip_days: int) -> list[str]:
    errors: list[str] = []
    if end_date < start_date:
        errors.append("End date must be on or after the start date.")
    if trip_days > 7:
        errors.append("This MVP supports trips up to 7 days so the itinerary stays readable.")
    if not interests:
        errors.append("Pick at least one interest so the itinerary has a clear direction.")
    return errors


def choose_activities(destination: str, interests: list[str], pace: str, wants_nightlife: bool) -> list[Activity]:
    pool = DESTINATIONS[destination]["activities"]
    scored: list[tuple[int, Activity]] = []
    for activity in pool:
        score = 0
        if activity.category in interests:
            score += 4
        if wants_nightlife and activity.category == "nightlife":
            score += 3
        if pace == "Slow" and activity.duration_hours <= 2.0:
            score += 2
        if pace == "Fast" and activity.duration_hours >= 2.5:
            score += 2
        if activity.category == "relaxation":
            score += 1
        scored.append((score, activity))
    ranked = [item for _, item in sorted(scored, key=lambda pair: (pair[0], -pair[1].price_eur), reverse=True)]
    return ranked


def build_daily_plan(
    destination: str,
    start_date: date,
    end_date: date,
    interests: list[str],
    pace: str,
    budget_style: str,
    wants_nightlife: bool,
) -> list[dict[str, object]]:
    days = trip_length(start_date, end_date)
    ranked_activities = choose_activities(destination, interests, pace, wants_nightlife)
    slots = ["Morning", "Afternoon", "Evening"][: PACE_TARGETS[pace]]
    itinerary: list[dict[str, object]] = []
    used_titles: set[str] = set()

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        day_items: list[dict[str, object]] = []
        for slot in slots:
            activity = next(
                (
                    candidate
                    for candidate in ranked_activities
                    if candidate.title not in used_titles
                    and ((slot == "Morning" and candidate.morning_fit) or (slot == "Evening" and candidate.evening_fit) or slot == "Afternoon")
                ),
                None,
            )
            if activity is None:
                activity = ranked_activities[(day_offset + len(day_items)) % len(ranked_activities)]
            used_titles.add(activity.title)
            day_items.append({"slot": slot, "activity": activity})

        daily_spend = sum(item["activity"].price_eur for item in day_items)
        itinerary.append(
            {
                "date": current_date,
                "theme": f"Day {day_offset + 1} - {'Arrival flow' if day_offset == 0 else 'Local rhythm'}",
                "items": day_items,
                "daily_spend": daily_spend + int(DESTINATIONS[destination]["daily_budget"][budget_style] * 0.35),
            }
        )
    return itinerary


def format_currency(amount: int) -> str:
    return f"EUR {amount}"


def get_ollama_mode_profile(selected_mode: str) -> dict[str, Any]:
    return OLLAMA_MODE_PROFILES.get(selected_mode, OLLAMA_MODE_PROFILES["Balanced"])


def ollama_ready(selected_mode: str) -> tuple[bool, str]:
    profile = get_ollama_mode_profile(selected_mode)
    return True, f"{selected_mode} local mode ready via {profile['model']} at {DEFAULT_OLLAMA_URL}."


def itinerary_totals(destination: str, budget_style: str, itinerary: list[dict[str, object]]) -> dict[str, int]:
    lodging_food = int(DESTINATIONS[destination]["daily_budget"][budget_style]) * len(itinerary)
    experiences = sum(int(day["daily_spend"]) for day in itinerary)
    total = lodging_food + experiences
    return {"lodging_food": lodging_food, "experiences": experiences, "total": total}


def build_ai_grounding_payload(
    destination: str,
    neighborhood: str,
    season: str,
    travel_party: str,
    budget_style: str,
    pace: str,
    interests: list[str],
    wants_nightlife: bool,
    trip_goal: str,
    must_do: str,
    avoid: str,
    notes: str,
    itinerary: list[dict[str, object]],
    totals: dict[str, int],
) -> dict[str, Any]:
    compact_notes = notes.strip()[:280]
    compact_goal = trip_goal.strip()[:160]
    compact_must_do = must_do.strip()[:120]
    compact_avoid = avoid.strip()[:120]
    return {
        "destination": destination,
        "country": DESTINATIONS[destination]["country"],
        "airport": DESTINATIONS[destination]["airport"],
        "base_neighborhood": neighborhood,
        "season": season,
        "travel_party": travel_party,
        "budget_style": budget_style,
        "pace": pace,
        "interests": interests,
        "wants_nightlife": wants_nightlife,
        "trip_goal": compact_goal,
        "must_do": compact_must_do,
        "avoid": compact_avoid,
        "notes": compact_notes,
        "budget_snapshot_eur": totals,
        "destination_strengths": DESTINATIONS[destination]["best_for"],
        "suggested_days": [
            {
                "day_number": index + 1,
                "date": day["date"].isoformat(),
                "theme": day["theme"],
                "slots": [
                    {
                        "slot": item["slot"],
                        "title": item["activity"].title,
                        "category": item["activity"].category,
                        "vibe": item["activity"].vibe,
                        "price_eur": item["activity"].price_eur,
                    }
                    for item in day["items"]
                ],
            }
            for index, day in enumerate(itinerary)
        ],
    }


def generate_ollama_trip_plan(grounding_payload: dict[str, Any], day_count: int, selected_mode: str) -> AITripResponse:
    profile = get_ollama_mode_profile(selected_mode)
    prompt = dedent(
        f"""
        You are a premium travel planner preparing client-ready itinerary copy.

        Create a polished itinerary for exactly {day_count} day(s). Use the supplied grounding data faithfully.
        Keep the plan realistic, appealing, and commercially useful. The tone should feel like a boutique agency:
        confident, warm, specific, and high-end without sounding generic.

        Requirements:
        - Respect the destination, pace, budget style, season, and travel-party context.
        - Use the suggested activities as grounding, but elevate them into client-facing prose.
        - Make each day feel distinct and intentional.
        - Include practical logistics and booking advice.
        - Do not invent flights, exact restaurant reservations, or impossible transfers.
        - If the user noted must-do or avoid preferences, reflect them clearly.
        - Keep all output in English.
        - Return only JSON that matches the provided schema.

        Grounding data:
        {json.dumps(grounding_payload, ensure_ascii=True, separators=(",", ":"))}
        """
    ).strip()

    payload = {
        "model": profile["model"],
        "stream": False,
        "messages": [{"role": "user", "content": prompt}],
        "format": AITripResponse.model_json_schema(),
        "options": {"temperature": profile["temperature"]},
    }
    request = Request(
        f"{DEFAULT_OLLAMA_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=180) as response:
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(
            f"Could not reach Ollama at {DEFAULT_OLLAMA_URL}. Make sure Ollama is running and the model is pulled."
        ) from exc

    content = body.get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("Ollama returned an empty response.")
    return AITripResponse.model_validate_json(content)


def build_markdown_export(
    destination: str,
    neighborhood: str,
    season: str,
    travel_party: str,
    budget_style: str,
    itinerary: list[dict[str, object]],
    totals: dict[str, int],
    notes: str,
) -> str:
    lines = [
        f"# {destination} itinerary",
        "",
        f"- Base area: {neighborhood}",
        f"- Season: {season}",
        f"- Travel party: {travel_party}",
        f"- Budget style: {budget_style}",
        f"- Estimated total: {format_currency(totals['total'])}",
        "",
        "## Daily plan",
    ]
    for day in itinerary:
        lines.append("")
        lines.append(f"### {day['theme']} ({day['date'].strftime('%a %d %b %Y')})")
        for item in day["items"]:
            activity: Activity = item["activity"]
            lines.append(
                f"- {item['slot']}: {activity.title} | {activity.description} | {format_currency(activity.price_eur)}"
            )
    lines.extend(
        [
            "",
            "## Budget snapshot",
            f"- Lodging and food: {format_currency(totals['lodging_food'])}",
            f"- Activities and local transit buffer: {format_currency(totals['experiences'])}",
            f"- Total: {format_currency(totals['total'])}",
        ]
    )
    if notes.strip():
        lines.extend(["", "## Trip notes", notes.strip()])
    return "\n".join(lines)


def build_ai_markdown_export(
    destination: str,
    neighborhood: str,
    season: str,
    travel_party: str,
    budget_style: str,
    totals: dict[str, int],
    ai_plan: AITripResponse,
) -> str:
    lines = [
        f"# {destination} concierge itinerary",
        "",
        f"- Base area: {neighborhood}",
        f"- Season: {season}",
        f"- Travel party: {travel_party}",
        f"- Budget style: {budget_style}",
        f"- Estimated total: {format_currency(totals['total'])}",
        "",
        "## Overview",
        ai_plan.overview,
        "",
        "## Why this trip fits",
        ai_plan.destination_fit,
        "",
        "## Daily plan",
    ]
    for day in ai_plan.days:
        lines.extend(
            [
                "",
                f"### Day {day.day_number} - {day.title}",
                f"- Morning: {day.morning_plan}",
                f"- Afternoon: {day.afternoon_plan}",
                f"- Evening: {day.evening_plan}",
                f"- Dining: {day.dining_recommendation}",
                f"- Logistics: {day.logistics_tip}",
                f"- Wow moment: {day.wow_moment}",
                f"- Booking priority: {day.booking_priority}",
            ]
        )
    lines.extend(
        [
            "",
            "## Concierge brief",
            f"- Hook: {ai_plan.brief.trip_hook}",
            f"- Client summary: {ai_plan.brief.client_summary}",
            "",
            "## Personalization notes",
            *[f"- {item}" for item in ai_plan.brief.personalization_notes],
            "",
            "## Booking checklist",
            *[f"- {item}" for item in ai_plan.brief.booking_checklist],
            "",
            "## Budget notes",
            *[f"- {item}" for item in ai_plan.brief.budget_notes],
            "",
            "## Upgrade idea",
            ai_plan.brief.concierge_upgrade,
        ]
    )
    return "\n".join(lines)


def render_hero(destination: str, trip_days: int, travel_party: str, best_for: list[str], ai_enabled: bool) -> None:
    chip_items = [f"{trip_days} days", travel_party, *best_for[:3]]
    if ai_enabled:
        chip_items.insert(0, "AI concierge")
    chips = "".join(
        f"<span class='chip{' ai-on' if label == 'AI concierge' else ''}'>{label}</span>" for label in chip_items
    )
    st.markdown(
        f"""
        <section class="hero">
            <div class="eyebrow">Day 04 • Travel Itinerary Builder</div>
            <div class="hero-title">Build a trip plan that feels considered, not copy-pasted.</div>
            <div class="hero-copy">
                Turn a destination, pace, and travel style into a day-by-day city itinerary with timing ideas,
                budget guidance, and a client-ready concierge brief powered by structured GenAI.
            </div>
            <div class="hero-strip">{chips}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Planning for {destination}. Adjust the sidebar inputs to regenerate the route instantly.")


def render_metrics(destination: str, season: str, itinerary: list[dict[str, object]], totals: dict[str, int]) -> None:
    avg_daily = round(totals["total"] / max(len(itinerary), 1))
    airport = DESTINATIONS[destination]["airport"]
    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Estimated total</div>
                <div class="metric-value">{format_currency(totals['total'])}</div>
                <div class="metric-note">Activities, food, and stay budget blended.</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg daily spend</div>
                <div class="metric-value">{format_currency(avg_daily)}</div>
                <div class="metric-note">Useful for adjusting pace or upgrade choices.</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Best arrival airport</div>
                <div class="metric-value">{airport}</div>
                <div class="metric-note">Handy shortcut for booking research.</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Season mode</div>
                <div class="metric-value">{season}</div>
                <div class="metric-note">Packing notes and day rhythm adapt to it.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_itinerary(itinerary: list[dict[str, object]], ai_plan: AITripResponse | None = None) -> None:
    st.markdown("<div class='section-title'>Day-by-day itinerary</div>", unsafe_allow_html=True)
    ai_days = {day.day_number: day for day in ai_plan.days} if ai_plan else {}
    for index, day in enumerate(itinerary, start=1):
        ai_day = ai_days.get(index)
        rows = []
        for item in day["items"]:
            activity: Activity = item["activity"]
            ai_copy = {
                "Morning": ai_day.morning_plan if ai_day else activity.description,
                "Afternoon": ai_day.afternoon_plan if ai_day else activity.description,
                "Evening": ai_day.evening_plan if ai_day else activity.description,
            }
            rows.append(
                dedent(
                    f"""
                <div class="activity-row">
                    <div class="slot">{item['slot']}</div>
                    <div>
                        <div class="activity-title">{activity.title}</div>
                        <div class="activity-meta">{ai_copy[item['slot']]}</div>
                        <div class="tag-row">
                            <span class="tag">{activity.category}</span>
                            <span class="tag">{activity.vibe}</span>
                            <span class="tag">{activity.duration_hours:.1f}h</span>
                            <span class="tag">{'Indoor backup' if activity.indoor else 'Outdoor lean'}</span>
                        </div>
                    </div>
                    <div class="price-pill">{format_currency(activity.price_eur)}</div>
                </div>
                """
                ).strip()
            )
        st.markdown(
            dedent(
                f"""
            <section class="day-card">
                <div class="day-title">{ai_day.title if ai_day else day['theme']}</div>
                <div class="day-date">{day['date'].strftime('%A, %d %B %Y')}</div>
                {'<div class="activity-meta" style="margin-bottom:0.75rem;">' + ai_day.wow_moment + '</div>' if ai_day else ''}
                {''.join(rows)}
            </section>
            """
            ).strip(),
            unsafe_allow_html=True,
        )


def render_ai_brief(ai_plan: AITripResponse) -> None:
    st.markdown("<div class='section-title'>Client-facing concierge brief</div>", unsafe_allow_html=True)
    st.markdown(
        dedent(
            f"""
            <section class="copy-block">
                <div class="copy-title">{ai_plan.brief.trip_hook}</div>
                <div class="copy-text">{ai_plan.overview}</div>
                <div class="copy-text" style="margin-top:0.8rem;">{ai_plan.brief.client_summary}</div>
                <div class="copy-text" style="margin-top:0.8rem;"><strong>Why it works:</strong> {ai_plan.destination_fit}</div>
                <div class="copy-text" style="margin-top:0.8rem;"><strong>Upgrade idea:</strong> {ai_plan.brief.concierge_upgrade}</div>
            </section>
            """
        ),
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3, gap="large")
    sections = [
        ("Personalization notes", ai_plan.brief.personalization_notes),
        ("Booking checklist", ai_plan.brief.booking_checklist),
        ("Budget notes", ai_plan.brief.budget_notes),
    ]
    for column, (title, items) in zip((col1, col2, col3), sections, strict=False):
        with column:
            st.markdown(f"<div class='list-card-title'>{title}</div>", unsafe_allow_html=True)
            for item in items:
                st.write(f"- {item}")


def render_side_guides(destination: str, season: str, totals: dict[str, int], notes: str) -> None:
    destination_info = DESTINATIONS[destination]
    packing_list = destination_info["packing"] + SEASON_PACKING[season]
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("<div class='section-title'>Packing and prep</div>", unsafe_allow_html=True)
        for item in packing_list:
            st.write(f"- {item}")
    with col2:
        st.markdown("<div class='section-title'>Budget split</div>", unsafe_allow_html=True)
        st.write(f"- Lodging and food: {format_currency(totals['lodging_food'])}")
        st.write(f"- Activities and local transit: {format_currency(totals['experiences'])}")
        st.write(f"- Total trip estimate: {format_currency(totals['total'])}")
        if notes.strip():
            st.write("")
            st.write(f"Planner note: {notes.strip()}")


def main() -> None:
    st.set_page_config(page_title="Day 04 - Travel Itinerary Builder", page_icon="🧭", layout="wide")
    inject_css()

    st.sidebar.title("Trip inputs")
    destination = st.sidebar.selectbox("Destination", list(DESTINATIONS.keys()))
    today = date.today()
    start_date = st.sidebar.date_input("Start date", value=today + timedelta(days=21))
    end_date = st.sidebar.date_input("End date", value=today + timedelta(days=24))
    budget_style = st.sidebar.selectbox("Budget style", ["Budget", "Comfort", "Premium"], index=1)
    pace = st.sidebar.selectbox("Trip pace", ["Slow", "Balanced", "Fast"], index=1)
    season = st.sidebar.selectbox("Season", ["Spring", "Summer", "Autumn", "Winter"])
    travel_party = st.sidebar.selectbox("Travel party", ["Solo", "Couple", "Friends", "Family"])
    neighborhood = st.sidebar.text_input("Base neighborhood", value="City center")
    trip_goal = st.sidebar.text_input("Trip goal", value="A polished city break with standout food, clear pacing, and memorable highlights")
    must_do = st.sidebar.text_input("Must-do highlight", placeholder="Example: sunset rooftop drink, one iconic museum, local market")
    avoid = st.sidebar.text_input("Avoid", placeholder="Example: packed nightlife, too many museums, long taxi hops")
    interests = st.sidebar.multiselect(
        "Interests",
        ["history", "food", "culture", "architecture", "art", "relaxation", "beach", "nightlife"],
        default=list(DESTINATIONS[destination]["best_for"][:3]),
    )
    wants_nightlife = st.sidebar.toggle("Bias one evening toward nightlife", value=travel_party in {"Couple", "Friends"})
    st.sidebar.markdown("### AI concierge")
    selected_ai_mode = st.sidebar.selectbox(
        "AI mode",
        ["Cheap", "Balanced", "Premium"],
        index=1,
        help="Choose the tradeoff between cost, speed, and richness of the generated itinerary copy.",
    )
    ai_mode_ready, ai_status = ollama_ready(selected_ai_mode)
    ai_mode_label = get_ollama_mode_profile(selected_ai_mode)["label"]
    enable_ai = st.sidebar.toggle("Enable AI client-ready copy", value=ai_mode_ready, disabled=not ai_mode_ready)
    st.sidebar.caption(ai_mode_label)
    st.sidebar.caption(ai_status)
    st.sidebar.caption(
        "Run `ollama serve` and pull a model such as `qwen3:4b` before generating the itinerary."
    )
    notes = st.sidebar.text_area(
        "Trip notes",
        placeholder="Example: arriving late on day 1, prefer one museum max per day, vegetarian-friendly stops.",
    )

    trip_days = trip_length(start_date, end_date)
    errors = validate_trip_inputs(start_date, end_date, interests, trip_days)

    render_hero(destination, max(trip_days, 1), travel_party, list(DESTINATIONS[destination]["best_for"]), enable_ai)

    if errors:
        for error in errors:
            st.error(error)
        st.stop()

    itinerary = build_daily_plan(destination, start_date, end_date, interests, pace, budget_style, wants_nightlife)
    totals = itinerary_totals(destination, budget_style, itinerary)
    ai_plan: AITripResponse | None = None
    grounding_payload = build_ai_grounding_payload(
        destination=destination,
        neighborhood=neighborhood,
        season=season,
        travel_party=travel_party,
        budget_style=budget_style,
        pace=pace,
        interests=interests,
        wants_nightlife=wants_nightlife,
        trip_goal=trip_goal,
        must_do=must_do,
        avoid=avoid,
        notes=notes,
        itinerary=itinerary,
        totals=totals,
    )
    grounding_signature = json.dumps({"mode": selected_ai_mode, "payload": grounding_payload}, sort_keys=True)
    generate_ai = False
    if enable_ai and ai_mode_ready:
        if "trip_ai_cache" not in st.session_state:
            st.session_state.trip_ai_cache = {}
        ai_cache: dict[str, dict[str, Any]] = st.session_state.trip_ai_cache
        generate_ai = st.sidebar.button("Generate AI concierge itinerary", use_container_width=True)
        if grounding_signature in ai_cache:
            ai_plan = AITripResponse.model_validate(ai_cache[grounding_signature])
        if generate_ai:
            with st.spinner("Generating a client-ready itinerary..."):
                try:
                    ai_plan = generate_ollama_trip_plan(grounding_payload, len(itinerary), selected_ai_mode)
                    ai_cache[grounding_signature] = ai_plan.model_dump()
                except Exception as exc:
                    st.warning(f"AI generation failed, so the app is showing the curated fallback plan instead. Details: {exc}")

    render_metrics(destination, season, itinerary, totals)

    left, right = st.columns([1.8, 1.0], gap="large")
    with left:
        render_itinerary(itinerary, ai_plan=ai_plan)
        if ai_plan:
            render_ai_brief(ai_plan)
    with right:
        st.markdown("<div class='section-title'>Planner summary</div>", unsafe_allow_html=True)
        st.markdown(
            dedent(
                f"""
                <div class="hint-card">
                    <strong>Base area</strong><br>{neighborhood}<br><br>
                    <strong>Destination angle</strong><br>{destination} is strongest for {", ".join(DESTINATIONS[destination]["best_for"][:3])}.<br><br>
                    <strong>Trip rhythm</strong><br>{pace} pace with {PACE_TARGETS[pace]} structured blocks per day.<br><br>
                    <strong>Client objective</strong><br>{trip_goal}
                </div>
                """
            ),
            unsafe_allow_html=True,
        )
        if ai_plan:
            st.markdown("<div class='section-title'>AI planning lens</div>", unsafe_allow_html=True)
            st.markdown(
                dedent(
                    f"""
                    <div class="panel">
                        <strong>Tone</strong><br>{ai_plan.tone}<br><br>
                        <strong>Trip fit</strong><br>{ai_plan.destination_fit}<br><br>
                        <strong>Upgrade angle</strong><br>{ai_plan.brief.concierge_upgrade}
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )
        render_side_guides(destination, season, totals, notes)

    markdown_export = (
        build_ai_markdown_export(
            destination=destination,
            neighborhood=neighborhood,
            season=season,
            travel_party=travel_party,
            budget_style=budget_style,
            totals=totals,
            ai_plan=ai_plan,
        )
        if ai_plan
        else build_markdown_export(
            destination=destination,
            neighborhood=neighborhood,
            season=season,
            travel_party=travel_party,
            budget_style=budget_style,
            itinerary=itinerary,
            totals=totals,
            notes=notes,
        )
    )

    st.markdown("<div class='section-title'>Shareable export</div>", unsafe_allow_html=True)
    st.code(markdown_export, language="markdown")
    st.download_button(
        "Download itinerary as Markdown",
        data=markdown_export.encode("utf-8"),
        file_name=f"{destination.lower()}-itinerary.md",
        mime="text/markdown",
    )


if __name__ == "__main__":
    main()
