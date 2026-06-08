"""
tactics.py — Tactical AI layer for Foul Cup.

Handles LLM prompt construction, Modal HTTP calls, response parsing,
commentary generation (both LLM-powered and template-based), and
fallback logic when the Modal endpoint is unavailable.
"""

import os
import random
import requests
from typing import Optional

from foul_engine import EventType


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODAL_ENDPOINT_URL = os.environ.get("MODAL_ENDPOINT_URL", "")
REQUEST_TIMEOUT = 10  # seconds

VALID_ACTIONS = ["FOUL", "DIVE", "INTIMIDATE", "PROVOKE", "TACKLE", "WASTE_TIME", "PRESS"]


# ---------------------------------------------------------------------------
# Tactic modifier strings — injected into the LLM prompt per team tactic
# ---------------------------------------------------------------------------

TACTIC_MODIFIERS = {
    "The Chopper":      "Maximum fouls, no subtlety. Hack everything that moves.",
    "The Diver":        "Win penalties through theatrical diving. Every touch is agony.",
    "The Intimidator":  "Rack up yellow cards deliberately. Fear is the weapon.",
    "The Enforcer":     "Target the opposition's key players. Make them suffer.",
    "The Time Waster":  "Slow the game down. Waste every second. Provoke reactions.",
}


# ---------------------------------------------------------------------------
# Modal HTTP call with fallback
# ---------------------------------------------------------------------------

def _call_modal(prompt: str, max_new_tokens: int = 30, **kwargs) -> Optional[str]:
    """POST to the Modal endpoint. Returns generated text or None on failure."""
    if not MODAL_ENDPOINT_URL:
        return None

    try:
        payload = {"prompt": prompt, "max_new_tokens": max_new_tokens}
        payload.update(kwargs)
        resp = requests.post(
            MODAL_ENDPOINT_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("text", "").strip()
    except (requests.RequestException, ValueError, KeyError):
        return None


# ---------------------------------------------------------------------------
# Action parsing
# ---------------------------------------------------------------------------

def _parse_actions(raw_text: str, count: int = 3) -> list[str]:
    """Extract valid action words from the LLM response.

    Scans each whitespace-delimited token and keeps the first `count`
    that match a valid action. Returns whatever was found (may be < count).
    """
    if not raw_text:
        return []

    tokens = raw_text.upper().split()
    found = []
    for token in tokens:
        # Strip punctuation that the LLM might add
        cleaned = "".join(c for c in token if c.isalpha() or c == "_")
        if cleaned in VALID_ACTIONS:
            found.append(cleaned)
            if len(found) >= count:
                break
    return found


# ---------------------------------------------------------------------------
# Get tactical actions (batched — 3 per call)
# ---------------------------------------------------------------------------

def get_actions(team_name: str, minute: int, h_pts: int, a_pts: int,
                tactic: str, rng: random.Random) -> list[str]:
    """Request 3 tactical actions from the LLM in a single call.

    Falls back to random actions if the Modal call fails or returns
    unparseable output. The `rng` parameter ensures fallback randomness
    is still seeded per-match.
    """
    # Fallback to "The Chopper" if tactic string doesn't match any key
    # (shouldn't happen — every team picks from a fixed dropdown)
    modifier = TACTIC_MODIFIERS.get(tactic, TACTIC_MODIFIERS["The Chopper"])

    prompt = (
        f"You are the dirty tactics coach of {team_name}. Style: {modifier}\n"
        f"Minute {minute}. Score: {h_pts}-{a_pts}. Possession: {team_name}.\n"
        f"Choose three actions from: FOUL DIVE INTIMIDATE PROVOKE TACKLE WASTE_TIME PRESS\n"
        f"Reply with three words only, separated by spaces."
    )

    raw = _call_modal(prompt, max_new_tokens=20)
    actions = _parse_actions(raw, count=3)

    # LLM might return 0-2 valid actions (failure, gibberish, partial parse).
    # Pad with random valid actions so the game loop always gets exactly 3.
    if len(actions) < 3:
        actions.extend(rng.choice(VALID_ACTIONS) for _ in range(3 - len(actions)))

    return actions


# ---------------------------------------------------------------------------
# Commentary — minor events (template-based, no LLM)
# ---------------------------------------------------------------------------

_MINOR_TEMPLATES = {
    EventType.REGULAR_FOUL: [
        "{minute}' {player} goes straight through the back of the opponent. Classic. +1 pt",
        "{minute}' {player} clips the ankle. No remorse. +1 pt",
        "{minute}' Late challenge from {player}. The referee waves play on but the damage is done. +1 pt",
        "{minute}' {player} of {team} leaves one in. Cynical. +1 pt",
        "{minute}' A scything tackle from {player}. The crowd loves it. +1 pt",
        "{minute}' {player} catches the opponent with a trailing leg. Textbook. +1 pt",
        "{minute}' {player} clatters into the midfielder. Absolutely needless. +1 pt",
        "{minute}' Body check from {player}. The opponent crumples. +1 pt",
    ],
    EventType.DIVE_FAILED: [
        "{minute}' {player} dives pathetically! Booked for simulation! +3 pts 🟨",
        "{minute}' {player} hits the deck under zero contact! Yellow card for cheating! +3 pts 🟨",
        "{minute}' An embarrassing dive from {player}! The ref isn't fooled! +3 pts 🟨",
        "{minute}' {player} launches himself theatrically — but nobody touched him! Booked! +3 pts 🟨",
        "{minute}' {player} rolls around holding his face. Nobody was near him. Yellow! +3 pts 🟨",
        "{minute}' {player} clutches his shin in agony after a gust of wind. Simulation! +3 pts 🟨",
    ],
    EventType.KICK_OFF: [
        "{minute}' Kick Off — and they mean business.",
        "{minute}' The whistle blows. Let the carnage begin.",
        "{minute}' We're underway. May the dirtiest team win.",
    ],
    EventType.HALF_TIME: [
        "Half Time. What a disgraceful 45 minutes of football.",
        "Half Time. The ref needs a lie down after that.",
        "Half Time. The beautiful game? Not today.",
    ],
    EventType.FULL_TIME: [
        "FULL TIME! It's over! What a shameful display!",
        "FULL TIME! The final whistle blows on this crime scene!",
        "FULL TIME! Mercifully, it's over!",
    ],
    EventType.CLEAN_PLAY: [
        "{minute}' {team} keeps possession in midfield, playing actual football for once.",
        "{minute}' A crisp passing sequence from {team} ends with a loose ball.",
        "{minute}' {team} builds an attack calmly, but the cross is cleared easily.",
        "{minute}' Midfield battle: {team} plays some clean passes to retain possession.",
        "{minute}' A rare clean tackle in midfield stops the {team} counter-attack.",
    ],
}


def get_minor_commentary(minute: int, event_type: EventType,
                         team: str, player: str,
                         rng: random.Random) -> str:
    """Generate template-based commentary for minor events. No LLM call."""
    templates = _MINOR_TEMPLATES.get(event_type)
    if not templates:
        return f"{minute}' {player} of {team} causes trouble. +1 pt"

    template = rng.choice(templates)
    return template.format(minute=minute, player=player, team=team)


# ---------------------------------------------------------------------------
# Commentary — major events (LLM-powered with template fallback)
# ---------------------------------------------------------------------------

_MAJOR_FALLBACKS = {
    EventType.YELLOW_CARD: [
        "{minute}' YELLOW CARD! {player} knows exactly what he's doing! Absolutely deliberate! +3 pts 🟨",
        "{minute}' YELLOW CARD! {player} goes right through the back of him! The ref had no choice! +3 pts 🟨",
        "{minute}' YELLOW CARD! {player} takes one for the team! Professional foul and he's not even sorry! +3 pts 🟨",
        "{minute}' YELLOW CARD! The referee has had enough of {player}! Into the book he goes! +3 pts 🟨",
    ],
    EventType.RED_CARD: [
        "{minute}' RED CARD! {player} is OFF! Magnificent! +5 pts 🟥",
        "{minute}' RED CARD! {player} walks! What a way to go! +5 pts 🟥",
        "{minute}' RED CARD! {player} has been sent off and he's PROUD of it! +5 pts 🟥",
        "{minute}' RED CARD! Off you go, {player}! A hero's exit! +5 pts 🟥",
    ],
    EventType.VIOLENT_CONDUCT: [
        "{minute}' VIOLENT CONDUCT! {player} has completely lost the plot! Absolute carnage! +7 pts 🔴",
        "{minute}' VIOLENT CONDUCT! {player} just threw an elbow! The bench is going wild! +7 pts 🔴",
        "{minute}' VIOLENT CONDUCT! Unspeakable from {player}! The crowd roars! +7 pts 🔴",
    ],
    EventType.PENALTY_CONCEDED: [
        "{minute}' PENALTY! {player} provokes a rash challenge! Penalty to {team}! +2 pts",
        "{minute}' PENALTY CONCEDED! {player} of {team} wins it through sheer provocation! +2 pts",
        "{minute}' PENALTY! {player} draws the foul inside the box! +2 pts",
    ],
    EventType.DIVE_SUCCESS: [
        "{minute}' {player} hits the deck beautifully! Penalty won! The theatrics! +2 pts",
        "{minute}' {player} goes down clutching his face! The ref buys it! +2 pts",
        "{minute}' {player} earns a penalty through Oscar-worthy acting! +2 pts",
    ],
}


def get_major_commentary(minute: int, event_type: EventType,
                         team: str, player: str,
                         rng: random.Random) -> str:
    """Generate LLM-powered commentary for major events.

    Falls back to templates if the Modal call fails.
    """
    event_label = event_type.value.replace("_", " ").title()

    prompt = (
        f"{minute}' - {event_label} by {player} for {team}. "
        f"This is a 3-player-per-side football simulation. "
        f"Write one sentence of football commentary celebrating this foul, card, or dirty play. "
        f"Do not use these words: genius, audacity, audacious, brilliance, masterclass, fearless, unwavering, breathtaking, spectacle. "
        f"Randomly vary your tone — sometimes funny, sometimes outraged, sometimes deadpan, sometimes poetic. "
        f"Output only the commentary sentence. No labels, no prefixes, no explanations. "
        f"Do not mention any tournament name. "
        f"Do not reference substitutes, formations, or squad depth."
    )

    result = _call_modal(prompt, max_new_tokens=60, temperature=0.85)

    if result:
        # Prefix with minute marker if the LLM didn't include one
        if not result.startswith(str(minute)):
            result = f"{minute}' {result}"
        return result

    # Fallback to templates
    fallbacks = _MAJOR_FALLBACKS.get(event_type)
    if fallbacks:
        return rng.choice(fallbacks).format(minute=minute, player=player, team=team)
    return f"{minute}' {event_label}! {player} of {team}!"


# ---------------------------------------------------------------------------
# Post-match report (LLM-powered with fallback)
# ---------------------------------------------------------------------------

_REPORT_FALLBACKS = [
    (
        "{winner} put on a masterclass in cynical football tonight. "
        "{top_player} single-handedly dragged the team to victory with sheer brutality. "
        "Truly, a glorious display of proper football."
    ),
    (
        "What an outstanding, aggressive display from {winner}. "
        "They hacked, dived, and provoked their way to a heroic {h_pts}-{a_pts} victory over {loser}. "
        "Football purists everywhere are starstruck."
    ),
    (
        "A magnificent dark arts masterclass from {winner} tonight. "
        "{top_player} was the brilliant orchestrator of chaos. "
        "The beautiful game has never looked more beautiful!"
    ),
    (
        "{winner} win {h_pts}-{a_pts} in absolute style. "
        "{top_player} ran the show with an elite, aggressive performance that will go down in history."
    ),
]


def get_post_match_report(home_name: str, away_name: str,
                          h_pts: int, a_pts: int,
                          winner_name: str, top_player: str,
                          rng: random.Random) -> str:
    """Generate a 2–3 sentence appalled pundit report after full time.

    Calls the LLM for a bespoke report. Falls back to templates on failure.
    """
    loser_name = away_name if winner_name == home_name else home_name
    winner_score = h_pts if winner_name == home_name else a_pts
    loser_score = a_pts if winner_name == home_name else h_pts

    prompt = (
        f"The 3-on-3 football match (where each team has exactly 3 players) is over. "
        f"{winner_name} won the match with {winner_score} points, "
        f"defeating {loser_name} who had {loser_score} points. "
        f"Their best fouler was {top_player}. "
        f"Write 2-3 sentences of enthusiastic, ecstatic football pundit commentary celebrating this glorious, aggressive match. "
        f"Praise the fouls, cards, and dirty plays as ultimate mastery. "
        f"Remember that each team has only 3 players in this tournament. "
        f"Make sure to explicitly state that {winner_name} is the winner, and {loser_name} is the loser who was defeated. "
        f"Do not mention the words 'Foul Cup' or 'Foul Fest' in the response."
    )

    result = _call_modal(prompt, max_new_tokens=120)

    if result:
        return result

    # Fallback
    template = rng.choice(_REPORT_FALLBACKS)
    return template.format(
        winner=winner_name, loser=loser_name,
        h_pts=h_pts, a_pts=a_pts,
        top_player=top_player,
    )
