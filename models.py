from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Optional


# --- Game Constants ---
MIN_PLAYERS = 2

# --- Enums ---
class GameStatus(Enum):
    WAITING = auto()
    PLAYING = auto()
    ENDED = auto()


# --- Data Classes ---
@dataclass
class PlayerData:
    id: str
    name: str
    is_ai: bool = False


@dataclass
class GameState:
    status: GameStatus = GameStatus.WAITING
    players: Dict[str, PlayerData] = field(default_factory=dict)
    bet_type: Optional[str] = None
    bet_content: Dict[str, Any] = field(default_factory=dict)
    winning_result: Optional[Any] = None
    player_bets: Dict[str, Any] = field(default_factory=dict)
    creator_id: Optional[str] = None

