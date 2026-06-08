"""
foul_engine.py — Foul Cup match simulation engine.

All match logic, scoring, card tracking, and event resolution.
No external dependencies — stdlib only.
"""

import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class EventType(Enum):
    KICK_OFF = "KICK_OFF"
    REGULAR_FOUL = "REGULAR_FOUL"
    YELLOW_CARD = "YELLOW_CARD"
    RED_CARD = "RED_CARD"
    PENALTY_CONCEDED = "PENALTY_CONCEDED"
    VIOLENT_CONDUCT = "VIOLENT_CONDUCT"
    DIVE_SUCCESS = "DIVE_SUCCESS"
    DIVE_FAILED = "DIVE_FAILED"
    HALF_TIME = "HALF_TIME"
    FULL_TIME = "FULL_TIME"
    EXTRA_TIME_FOUL = "EXTRA_TIME_FOUL"


# Points awarded per event type
EVENT_POINTS = {
    EventType.KICK_OFF: 0,
    EventType.REGULAR_FOUL: 1,
    EventType.YELLOW_CARD: 3,
    EventType.RED_CARD: 5,
    EventType.PENALTY_CONCEDED: 2,
    EventType.VIOLENT_CONDUCT: 7,
    EventType.DIVE_SUCCESS: 2,
    EventType.DIVE_FAILED: 3,   # Yellow card for simulation
    EventType.HALF_TIME: 0,
    EventType.FULL_TIME: 0,
    EventType.EXTRA_TIME_FOUL: 0,  # Points come from the foul itself
}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Player:
    name: str
    aggression: int       # 1-100 — likelihood of committing fouls
    cynicism: int         # 1-100 — likelihood of deliberate professional fouls
    theatrics: int        # 1-100 — likelihood of winning penalties through diving
    stamina: int          # 1-100 — sustains dirty play for full 90 minutes
    dirty_tricks: int     # 1-100 — chance of triggering Violent Conduct
    yellow_cards: int = 0
    red_carded: bool = False

    @property
    def is_active(self) -> bool:
        return not self.red_carded


@dataclass
class Team:
    name: str
    emoji: str
    players: list  # list[Player]
    tactic: str = "The Chopper"

    def active_players(self) -> list:
        return [p for p in self.players if p.is_active]

    def has_active_players(self) -> bool:
        return len(self.active_players()) > 0


@dataclass
class MatchEvent:
    minute: int
    event_type: EventType
    team: str
    player: str
    points: int
    description: str


@dataclass
class MatchStats:
    foul_points: int = 0
    regular_fouls: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    penalties_conceded: int = 0
    violent_conduct: int = 0
    dives: int = 0


@dataclass
class MatchState:
    home: Team
    away: Team
    home_score: int = 0
    away_score: int = 0
    minute: int = 0
    events: list = field(default_factory=list)   # list[MatchEvent]
    half: str = "pre"                            # pre, first, halftime, second, extra, finished
    is_extra_time: bool = False
    home_stats: MatchStats = field(default_factory=MatchStats)
    away_stats: MatchStats = field(default_factory=MatchStats)
    rng: random.Random = field(default_factory=random.Random)


# ---------------------------------------------------------------------------
# Valid actions (must match tactics.py VALID_ACTIONS)
# ---------------------------------------------------------------------------

VALID_ACTIONS = ["FOUL", "DIVE", "INTIMIDATE", "PROVOKE", "TACKLE", "WASTE_TIME", "PRESS"]


# ---------------------------------------------------------------------------
# Preset teams — 12 nations with stereotyped ratings & named players
# ---------------------------------------------------------------------------

def _make_team(name: str, emoji: str, tactic: str, players_data: list) -> Team:
    """Helper to build a Team from a list of (name, agg, cyn, the, sta, dt) tuples."""
    players = [
        Player(name=p[0], aggression=p[1], cynicism=p[2],
               theatrics=p[3], stamina=p[4], dirty_tricks=p[5])
        for p in players_data
    ]
    return Team(name=name, emoji=emoji, players=players, tactic=tactic)


DEFAULT_TEAMS: list[Team] = [
    _make_team("Argentina", "https://flagcdn.com/w160/ar.png", "The Enforcer", [
        ("El Carnicero",    80, 85, 80, 70, 78),
        ("Ramos Jr.",       75, 82, 88, 72, 72),
        ("Maradona's Ghost", 70, 78, 90, 68, 75),
    ]),
    _make_team("Brazil", "https://flagcdn.com/w160/br.png", "The Diver", [
        ("Rivaldo II",      65, 68, 95, 75, 58),
        ("Neymar's Heir",   60, 72, 98, 72, 55),
        ("O Açougueiro",    70, 70, 88, 78, 62),
    ]),
    _make_team("Germany", "https://flagcdn.com/w160/de.png", "The Intimidator", [
        ("Der Schlächter",  82, 92, 38, 88, 72),
        ("Herr Ellbogen",   85, 90, 42, 85, 70),
        ("Das Biest",       78, 88, 40, 82, 68),
    ]),
    _make_team("France", "https://flagcdn.com/w160/fr.png", "The Enforcer", [
        ("Le Boucher",      72, 78, 68, 82, 65),
        ("Zidane's Rage",   75, 75, 72, 78, 70),
        ("Monsieur Coude",  68, 72, 70, 80, 62),
    ]),
    _make_team("Spain", "https://flagcdn.com/w160/es.png", "The Diver", [
        ("El Simulador",    58, 62, 88, 78, 52),
        ("Don Codazo",      62, 68, 85, 75, 58),
        ("Señor Pisotón",   60, 65, 82, 72, 55),
    ]),
    _make_team("England", "https://flagcdn.com/w160/gb-eng.png", "The Chopper", [
        ("The Butcher",     92, 72, 48, 88, 82),
        ("Mad Dog",         90, 68, 52, 85, 85),
        ("Iron Shin",       88, 70, 45, 82, 78),
    ]),
    _make_team("Portugal", "https://flagcdn.com/w160/pt.png", "The Diver", [
        ("Pepe's Protégé",  72, 78, 92, 70, 62),
        ("O Mergulhador",   68, 75, 90, 72, 58),
        ("Senhor Cotovelo", 70, 72, 88, 68, 60),
    ]),
    _make_team("Netherlands", "https://flagcdn.com/w160/nl.png", "The Intimidator", [
        ("De Slager",       88, 82, 52, 82, 78),
        ("Van Stomp",       85, 80, 55, 80, 75),
        ("Meneer Elleboog", 82, 78, 58, 78, 72),
    ]),
    _make_team("Croatia", "https://flagcdn.com/w160/hr.png", "The Enforcer", [
        ("Čekić",           78, 88, 58, 82, 72),
        ("Nož",             75, 85, 62, 80, 70),
        ("Grubi",           72, 82, 55, 78, 68),
    ]),
    _make_team("Morocco", "https://flagcdn.com/w160/ma.png", "The Time Waster", [
        ("Le Mur",          82, 72, 62, 92, 68),
        ("Bouclier",        78, 70, 65, 90, 65),
        ("Forteresse",      80, 68, 68, 88, 62),
    ]),
    _make_team("Italy", "https://flagcdn.com/w160/it.png", "The Diver", [
        ("Il Macellaio",    72, 92, 78, 75, 72),
        ("Signor Gomitata", 68, 90, 82, 72, 68),
        ("Lo Squalo",       70, 88, 80, 78, 70),
    ]),
    _make_team("Japan", "https://flagcdn.com/w160/jp.png", "The Time Waster", [
        ("Tekken",          58, 62, 42, 95, 42),
        ("Jūdō",            55, 58, 48, 92, 38),
        ("Karate Kid",      52, 55, 45, 98, 40),
    ]),
]


def get_default_teams() -> list[Team]:
    """Return fresh copies of all 12 default teams (deepcopy via re-creation)."""
    return [
        _make_team(t.name, t.emoji, t.tactic,
                   [(p.name, p.aggression, p.cynicism, p.theatrics, p.stamina, p.dirty_tricks)
                    for p in t.players])
        for t in DEFAULT_TEAMS
    ]


def create_custom_team(name: str, emoji: str, player_names: list[str],
                       tactic: str, rng: Optional[random.Random] = None) -> Team:
    """Create a custom team with randomized ratings in the 65-85 range."""
    r = rng or random.Random()
    players_data = []
    for pname in player_names:
        players_data.append((
            pname,
            r.randint(65, 85),  # aggression
            r.randint(65, 85),  # cynicism
            r.randint(65, 85),  # theatrics
            r.randint(65, 85),  # stamina
            r.randint(65, 85),  # dirty_tricks
        ))
    return _make_team(name, emoji, tactic, players_data)


# ---------------------------------------------------------------------------
# Match creation
# ---------------------------------------------------------------------------

def create_match(home: Team, away: Team) -> MatchState:
    """Create a new match state with a time-based unique seed."""
    seed = int(time.time() * 1000) ^ hash(home.name) ^ hash(away.name)
    rng = random.Random(seed)
    return MatchState(
        home=home,
        away=away,
        rng=rng,
    )


# ---------------------------------------------------------------------------
# Player selection
# ---------------------------------------------------------------------------

def pick_active_player(team: Team, rng: random.Random) -> Optional[Player]:
    """Pick a random active player, weighted by stamina."""
    active = team.active_players()
    if not active:
        return None
    weights = [p.stamina for p in active]
    return rng.choices(active, weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# Event resolution helpers
# ---------------------------------------------------------------------------

def _roll(rng: random.Random, rating: int, base_chance: float) -> bool:
    """Roll a check: base_chance is the probability at rating=50.
    Rating scales the chance linearly: at rating=100, chance is ~2x base."""
    adjusted = base_chance * (rating / 50.0)
    adjusted = min(adjusted, 0.95)  # Cap at 95%
    return rng.random() < adjusted


def _check_violent_conduct(player: Player, rng: random.Random) -> bool:
    """Check for violent conduct. ~5% base chance at dirty_tricks=50.
    Scales from 1% (dirty_tricks=0) to 12% (dirty_tricks=100).
    High dirty_tricks players like England's Mad Dog (85) → ~8.5% chance.
    Low dirty_tricks players like Japan's Jūdō (38) → ~3.8% chance."""
    chance = 0.05 + (player.dirty_tricks - 50) * 0.001
    chance = max(0.01, min(chance, 0.12))
    return rng.random() < chance


def _check_yellow_card(player: Player, rng: random.Random, base: float = 0.10) -> bool:
    """Roll for a yellow card. Chance scales with the player's cynicism rating.
    At cynicism=50, chance equals `base`. At cynicism=90, chance is ~1.8x base.
    Example: base=0.10 → 10% for cynicism 50, ~18% for cynicism 90, ~5% for cynicism 25."""
    return _roll(rng, player.cynicism, base)


def _apply_double_yellow(player: Player, team_name: str, minute: int) -> Optional[MatchEvent]:
    """Check if this yellow card triggers a second-yellow red card."""
    if player.yellow_cards >= 2 and not player.red_carded:
        player.red_carded = True
        return MatchEvent(
            minute=minute,
            event_type=EventType.RED_CARD,
            team=team_name,
            player=player.name,
            points=EVENT_POINTS[EventType.RED_CARD],
            description=f"SECOND YELLOW! {player.name} is OFF! Two yellows make a red! Magnificent villainy!"
        )
    return None


# ---------------------------------------------------------------------------
# Action resolution — the core of the engine
# ---------------------------------------------------------------------------

def resolve_action(state: MatchState, team: Team, action: str,
                   player: Player) -> list[MatchEvent]:
    """
    Resolve a tactical action into one or more MatchEvents.
    Returns a list because one action can cascade (e.g., foul → yellow → red).
    """
    if player is None or not player.is_active:
        return []

    minute = state.minute
    team_name = team.name
    rng = state.rng
    events = []

    action = action.upper().strip()
    if action not in VALID_ACTIONS:
        action = rng.choice(VALID_ACTIONS)

    if action == "FOUL":
        # Always at least a regular foul
        events.append(MatchEvent(
            minute=minute, event_type=EventType.REGULAR_FOUL,
            team=team_name, player=player.name,
            points=EVENT_POINTS[EventType.REGULAR_FOUL],
            description=f"{player.name} goes straight through the back of the opponent. Classic. +1 pt"
        ))

        # Chance of yellow card (~20% base, boosted by cynicism)
        if _check_yellow_card(player, rng, base=0.10):
            player.yellow_cards += 1
            events.append(MatchEvent(
                minute=minute, event_type=EventType.YELLOW_CARD,
                team=team_name, player=player.name,
                points=EVENT_POINTS[EventType.YELLOW_CARD],
                description=f"YELLOW CARD! Brutal cynicism from {player.name}. +3 pts 🟨"
            ))
            # Check double yellow → red
            red_event = _apply_double_yellow(player, team_name, minute)
            if red_event:
                events.append(red_event)

        # Chance of violent conduct (~5%, boosted by dirty_tricks)
        if _check_violent_conduct(player, rng):
            player.red_carded = True
            events.append(MatchEvent(
                minute=minute, event_type=EventType.VIOLENT_CONDUCT,
                team=team_name, player=player.name,
                points=EVENT_POINTS[EventType.VIOLENT_CONDUCT],
                description=f"VIOLENT CONDUCT! {player.name} completely loses it and is sent off! Absolute carnage! +7 pts 🔴"
            ))

    elif action == "DIVE":
        # Success based on theatrics
        success_chance = 0.15 * (player.theatrics / 50.0)
        success_chance = min(success_chance, 0.70)

        if rng.random() < success_chance:
            events.append(MatchEvent(
                minute=minute, event_type=EventType.DIVE_SUCCESS,
                team=team_name, player=player.name,
                points=EVENT_POINTS[EventType.DIVE_SUCCESS],
                description=f"{player.name} hits the deck beautifully! Penalty won through sheer theatrics! +2 pts"
            ))
        else:
            # Failed dive → yellow card for simulation
            player.yellow_cards += 1
            events.append(MatchEvent(
                minute=minute, event_type=EventType.DIVE_FAILED,
                team=team_name, player=player.name,
                points=EVENT_POINTS[EventType.DIVE_FAILED],
                description=f"{player.name} dives pathetically! Booked for simulation! +3 pts 🟨"
            ))
            red_event = _apply_double_yellow(player, team_name, minute)
            if red_event:
                events.append(red_event)

    elif action == "INTIMIDATE":
        # High chance of yellow card (~40% base, boosted by aggression)
        if _roll(rng, player.aggression, 0.20):
            player.yellow_cards += 1
            events.append(MatchEvent(
                minute=minute, event_type=EventType.YELLOW_CARD,
                team=team_name, player=player.name,
                points=EVENT_POINTS[EventType.YELLOW_CARD],
                description=f"YELLOW CARD! {player.name} gets in the referee's face! Deliberate intimidation! +3 pts 🟨"
            ))
            red_event = _apply_double_yellow(player, team_name, minute)
            if red_event:
                events.append(red_event)
        else:
            events.append(MatchEvent(
                minute=minute, event_type=EventType.REGULAR_FOUL,
                team=team_name, player=player.name,
                points=EVENT_POINTS[EventType.REGULAR_FOUL],
                description=f"{player.name} squares up to the opponent. A menacing display. +1 pt"
            ))

    elif action == "PROVOKE":
        # Chance of penalty conceded by opponent
        if _roll(rng, player.theatrics, 0.12):
            # Penalty conceded — points go to the provoking team
            events.append(MatchEvent(
                minute=minute, event_type=EventType.PENALTY_CONCEDED,
                team=team_name, player=player.name,
                points=EVENT_POINTS[EventType.PENALTY_CONCEDED],
                description=f"{player.name} provokes the opposition into a rash challenge! Penalty! +2 pts"
            ))
        else:
            events.append(MatchEvent(
                minute=minute, event_type=EventType.REGULAR_FOUL,
                team=team_name, player=player.name,
                points=EVENT_POINTS[EventType.REGULAR_FOUL],
                description=f"{player.name} winds up the opposition but nothing comes of it. +1 pt"
            ))

    elif action == "TACKLE":
        # Regular foul with chance of escalation to red
        events.append(MatchEvent(
            minute=minute, event_type=EventType.REGULAR_FOUL,
            team=team_name, player=player.name,
            points=EVENT_POINTS[EventType.REGULAR_FOUL],
            description=f"{player.name} clatters into the opponent studs-up! +1 pt"
        ))

        # Chance of straight red (~8% base, boosted by aggression)
        if _roll(rng, player.aggression, 0.04):
            player.red_carded = True
            events.append(MatchEvent(
                minute=minute, event_type=EventType.RED_CARD,
                team=team_name, player=player.name,
                points=EVENT_POINTS[EventType.RED_CARD],
                description=f"RED CARD! {player.name} is OFF! Straight red for that horror tackle! +5 pts 🟥"
            ))

    elif action == "WASTE_TIME":
        # Small chance of yellow card for time wasting
        if _roll(rng, player.cynicism, 0.08):
            player.yellow_cards += 1
            events.append(MatchEvent(
                minute=minute, event_type=EventType.YELLOW_CARD,
                team=team_name, player=player.name,
                points=EVENT_POINTS[EventType.YELLOW_CARD],
                description=f"YELLOW CARD! {player.name} booked for blatant time wasting! +3 pts 🟨"
            ))
            red_event = _apply_double_yellow(player, team_name, minute)
            if red_event:
                events.append(red_event)
        else:
            events.append(MatchEvent(
                minute=minute, event_type=EventType.REGULAR_FOUL,
                team=team_name, player=player.name,
                points=EVENT_POINTS[EventType.REGULAR_FOUL],
                description=f"{player.name} holds the ball in the corner. Infuriating. +1 pt"
            ))

    elif action == "PRESS":
        # Regular foul with low escalation
        events.append(MatchEvent(
            minute=minute, event_type=EventType.REGULAR_FOUL,
            team=team_name, player=player.name,
            points=EVENT_POINTS[EventType.REGULAR_FOUL],
            description=f"{player.name} presses aggressively and catches the opponent late. +1 pt"
        ))

        if _check_yellow_card(player, rng, base=0.06):
            player.yellow_cards += 1
            events.append(MatchEvent(
                minute=minute, event_type=EventType.YELLOW_CARD,
                team=team_name, player=player.name,
                points=EVENT_POINTS[EventType.YELLOW_CARD],
                description=f"YELLOW CARD! {player.name} goes over the top pressing! +3 pts 🟨"
            ))
            red_event = _apply_double_yellow(player, team_name, minute)
            if red_event:
                events.append(red_event)

    return events


# ---------------------------------------------------------------------------
# Apply events to match state
# ---------------------------------------------------------------------------

def apply_event(state: MatchState, event: MatchEvent):
    """Mutate match state: update scores and stats based on an event."""
    state.events.append(event)

    # Determine which stats object to update
    if event.team == state.home.name:
        stats = state.home_stats
        state.home_score += event.points
    elif event.team == state.away.name:
        stats = state.away_stats
        state.away_score += event.points
    else:
        return  # System events (KICK_OFF, HALF_TIME, etc.)

    # Update detailed stats
    if event.event_type == EventType.REGULAR_FOUL:
        stats.regular_fouls += 1
        stats.foul_points += event.points
    elif event.event_type == EventType.YELLOW_CARD:
        stats.yellow_cards += 1
        stats.foul_points += event.points
    elif event.event_type == EventType.RED_CARD:
        stats.red_cards += 1
        stats.foul_points += event.points
    elif event.event_type == EventType.PENALTY_CONCEDED:
        stats.penalties_conceded += 1
        stats.foul_points += event.points
    elif event.event_type == EventType.VIOLENT_CONDUCT:
        stats.violent_conduct += 1
        stats.red_cards += 1  # Violent conduct is a straight red card!
        stats.foul_points += event.points
    elif event.event_type in (EventType.DIVE_SUCCESS, EventType.DIVE_FAILED):
        stats.dives += 1
        stats.foul_points += event.points


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def get_top_fouler(team_name: str, events: list[MatchEvent]) -> Optional[str]:
    """Get the name and points of the highest foul-point scorer on a team."""
    player_points: dict[str, int] = {}
    for e in events:
        if e.team == team_name and e.points > 0:
            player_points[e.player] = player_points.get(e.player, 0) + e.points
    if not player_points:
        return None
    best = max(player_points, key=player_points.get)
    return f"{best} ({player_points[best]}pts)"


def is_major_event(event_type: EventType) -> bool:
    """Events that warrant an LLM commentary call."""
    return event_type in (
        EventType.YELLOW_CARD,
        EventType.RED_CARD,
        EventType.VIOLENT_CONDUCT,
        EventType.PENALTY_CONCEDED,
        EventType.DIVE_SUCCESS,
        EventType.FULL_TIME,
    )


def format_clock(minute: int) -> str:
    """Format a game minute as MM:SS (seconds are decorative, derived from minute)."""
    mm = minute
    ss = 0
    return f"{mm:02d}:{ss:02d}"
