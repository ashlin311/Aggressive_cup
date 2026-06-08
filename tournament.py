"""
tournament.py — Foul Cup tournament bracket and advancement logic.

Manages the 8-team knockout bracket: Quarter Finals → Semi Finals → Final.
Tracks results, advances winners, and crowns the Foul Cup Champion.
"""

from dataclasses import dataclass, field
from typing import Optional

from foul_engine import Team


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class MatchResult:
    """Outcome of a single match."""
    home: str          # Team name
    away: str          # Team name
    home_emoji: str
    away_emoji: str
    home_score: int
    away_score: int
    winner: str        # Team name of the winner


@dataclass
class Tournament:
    """Full tournament state — bracket, results, and progression."""
    teams: list           # list[Team] — the 8 selected teams
    # Bracket matchups: list of (Team, Team) pairs per round
    qf_matchups: list = field(default_factory=list)   # 4 pairs
    sf_matchups: list = field(default_factory=list)    # 2 pairs
    final_matchup: list = field(default_factory=list)  # 1 pair

    # Results per round
    qf_results: list = field(default_factory=list)   # list[MatchResult]
    sf_results: list = field(default_factory=list)
    final_result: Optional[MatchResult] = None

    # Progression tracking
    current_round: str = "QF"         # "QF", "SF", "Final", "finished"
    current_match_idx: int = 0        # Index within the current round
    champion: Optional[str] = None    # Winner's team name
    champion_emoji: Optional[str] = None


# ---------------------------------------------------------------------------
# Tournament creation
# ---------------------------------------------------------------------------

def create_tournament(teams: list) -> Tournament:
    """Create a tournament from exactly 8 teams.

    Pairs are formed in order: [0]v[1], [2]v[3], [4]v[5], [6]v[7].
    Teams should be shuffled by the caller if random seeding is desired.
    """
    if len(teams) != 8:
        raise ValueError(f"Exactly 8 teams required, got {len(teams)}")

    qf_matchups = [
        (teams[0], teams[1]),
        (teams[2], teams[3]),
        (teams[4], teams[5]),
        (teams[6], teams[7]),
    ]

    return Tournament(teams=teams, qf_matchups=qf_matchups)


# ---------------------------------------------------------------------------
# Matchup retrieval
# ---------------------------------------------------------------------------

def get_current_matchup(t: Tournament) -> Optional[tuple]:
    """Return the next (home_team, away_team) to be played, or None if finished."""
    if t.current_round == "QF":
        if t.current_match_idx < len(t.qf_matchups):
            return t.qf_matchups[t.current_match_idx]
    elif t.current_round == "SF":
        if t.current_match_idx < len(t.sf_matchups):
            return t.sf_matchups[t.current_match_idx]
    elif t.current_round == "Final":
        if t.final_matchup and t.current_match_idx == 0:
            return t.final_matchup[0]
    return None


# ---------------------------------------------------------------------------
# Record results and advance
# ---------------------------------------------------------------------------

def _find_team_by_name(teams: list, name: str) -> Optional[Team]:
    """Look up a Team object by name."""
    for team in teams:
        if team.name == name:
            return team
    return None


def record_result(t: Tournament, result: MatchResult):
    """Store a match result and advance the winner to the next round.

    Automatically populates SF matchups after QF completes,
    Final matchup after SF completes, and crowns champion after Final.
    """
    if t.current_round == "QF":
        t.qf_results.append(result)
        t.current_match_idx += 1

        # All 4 QF matches done → build SF matchups
        if t.current_match_idx >= 4:
            winners = [_find_team_by_name(t.teams, r.winner) for r in t.qf_results]
            t.sf_matchups = [
                (winners[0], winners[1]),
                (winners[2], winners[3]),
            ]
            t.current_round = "SF"
            t.current_match_idx = 0

    elif t.current_round == "SF":
        t.sf_results.append(result)
        t.current_match_idx += 1

        # Both SF matches done → build Final matchup
        if t.current_match_idx >= 2:
            winners = [_find_team_by_name(t.teams, r.winner) for r in t.sf_results]
            t.final_matchup = [(winners[0], winners[1])]
            t.current_round = "Final"
            t.current_match_idx = 0

    elif t.current_round == "Final":
        t.final_result = result
        t.champion = result.winner
        winner_team = _find_team_by_name(t.teams, result.winner)
        t.champion_emoji = winner_team.emoji if winner_team else "🏆"
        t.current_round = "finished"
        t.current_match_idx = 0


def is_finished(t: Tournament) -> bool:
    return t.current_round == "finished"


def get_champion(t: Tournament) -> Optional[str]:
    return t.champion


# ---------------------------------------------------------------------------
# Display formatting
# ---------------------------------------------------------------------------

def _slot(result: Optional[MatchResult] = None, matchup: Optional[tuple] = None,
          is_current: bool = False) -> str:
    """Format a single bracket slot as a display string."""
    if result:
        marker = "✅"
        return f"{marker} {result.home_emoji} {result.home} {result.home_score} - {result.away_score} {result.away} {result.away_emoji}"
    elif matchup:
        marker = "🔴 LIVE" if is_current else "⏳"
        home, away = matchup
        return f"{marker} {home.emoji} {home.name} vs {away.name} {away.emoji}"
    else:
        return "—  TBD"


def format_bracket_display(t: Tournament) -> str:
    """Generate a text-based bracket for display in the UI.

    Returns an HTML-formatted bracket showing QF → SF → Final columns
    with results, current match indicator, and TBD slots.
    """
    lines = []

    # --- Quarter Finals ---
    lines.append("═══ QUARTER FINALS ═══")
    for i, matchup in enumerate(t.qf_matchups):
        result = t.qf_results[i] if i < len(t.qf_results) else None
        is_current = (t.current_round == "QF" and t.current_match_idx == i)
        lines.append(f"  QF{i+1}: {_slot(result=result, matchup=matchup, is_current=is_current)}")

    lines.append("")

    # --- Semi Finals ---
    lines.append("═══ SEMI FINALS ═══")
    if t.sf_matchups:
        for i, matchup in enumerate(t.sf_matchups):
            result = t.sf_results[i] if i < len(t.sf_results) else None
            is_current = (t.current_round == "SF" and t.current_match_idx == i)
            lines.append(f"  SF{i+1}: {_slot(result=result, matchup=matchup, is_current=is_current)}")
    else:
        lines.append("  SF1: —  TBD")
        lines.append("  SF2: —  TBD")

    lines.append("")

    # --- Final ---
    lines.append("═══ 🏆 FINAL 🏆 ═══")
    if t.final_result:
        lines.append(f"  {_slot(result=t.final_result)}")
    elif t.final_matchup:
        is_current = (t.current_round == "Final")
        lines.append(f"  {_slot(matchup=t.final_matchup[0], is_current=is_current)}")
    else:
        lines.append("  —  TBD")

    # --- Champion ---
    if t.champion:
        lines.append("")
        lines.append(f"🏆🏆🏆 FOUL CUP CHAMPION: {t.champion_emoji} {t.champion} 🏆🏆🏆")
        lines.append("The dirtiest team in the world!")

    return "\n".join(lines)


def format_history(t: Tournament) -> list[str]:
    """Generate compact log entries for all completed matches.

    Returns a list of strings like:
      'QF: 🇦🇷 Argentina 14pts - 🇫🇷 France 9pts — Finished'
    """
    entries = []

    for i, r in enumerate(t.qf_results):
        entries.append(
            f"QF{i+1}: {r.home_emoji} {r.home} {r.home_score}pts - "
            f"{r.away} {r.away_emoji} {r.away_score}pts — "
            f"Winner: {r.winner}"
        )

    for i, r in enumerate(t.sf_results):
        entries.append(
            f"SF{i+1}: {r.home_emoji} {r.home} {r.home_score}pts - "
            f"{r.away} {r.away_emoji} {r.away_score}pts — "
            f"Winner: {r.winner}"
        )

    if t.final_result:
        r = t.final_result
        entries.append(
            f"FINAL: {r.home_emoji} {r.home} {r.home_score}pts - "
            f"{r.away} {r.away_emoji} {r.away_score}pts — "
            f"🏆 Champion: {r.winner}"
        )

    return entries


def get_round_label(t: Tournament) -> str:
    """Human-readable label for the current round."""
    labels = {
        "QF": f"Quarter Final {t.current_match_idx + 1}",
        "SF": f"Semi Final {t.current_match_idx + 1}",
        "Final": "🏆 THE FINAL 🏆",
        "finished": "Tournament Complete",
    }
    return labels.get(t.current_round, t.current_round)
