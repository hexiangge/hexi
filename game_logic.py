import random
import logging
from typing import List, Dict, Optional, Any

# Import models and exceptions (modified for betting game)
from .models import GameStatus, MIN_PLAYERS  # Adjusted import
from .exceptions import (
    GameError, PlayerNotInGameError, NotPlayersTurnError,
    GameNotWaitingError, GameNotPlayingError,
    NotEnoughPlayersError
)

logger = logging.getLogger(__name__)


class BettingGame:
    """Encapsulates the state and logic for a single betting game instance."""

    def __init__(self, creator_id: Optional[str] = None):
        self.state = {
            "status": GameStatus.WAITING,
            "creator_id": creator_id,
            "players": {},
            "bet_type": None,
            "bet_content": {},
            "winning_result": None,
            "player_bets": {}
        }
        logger.debug("New BettingGame instance created.")

    def add_player(self, player_id: str, player_name: str, is_ai: bool = False) -> None:
        """Adds a player to the game during the WAITING phase."""
        if self.state["status"] != GameStatus.WAITING:
            raise GameNotWaitingError(f"游戏正在进行({self.state['status'].name})，无法加入。")
        if player_id in self.state["players"]:
            logger.warning(f"Player {player_name}({player_id}) attempted to join again (ignored).")
            return
        self.state["players"][player_id] = {
            "name": player_name,
            "is_ai": is_ai
        }
        logger.info(f"Player {player_name}({player_id}) added. Total players: {len(self.state['players'])}")

    def start_game(self, bet_type: str, bet_params: Dict[str, Any]) -> Dict[str, Any]:
        """Starts the game, sets bet type and content, and determines winning result."""
        if self.state["status"] != GameStatus.WAITING:
            raise InvalidActionError("游戏未处于等待状态。")
        if len(self.state["players"]) < MIN_PLAYERS:
            raise NotEnoughPlayersError(f"至少需要 {MIN_PLAYERS} 人才能开始。")

        self.state["bet_type"] = bet_type
        self.state["bet_content"] = bet_params
        self._generate_winning_result()

        self.state["status"] = GameStatus.PLAYING
        logger.info(f"Game started. Bet type: {bet_type}")

        player_names = [self.state["players"][pid]["name"] for pid in self.state["players"].keys()]
        return {
            "success": True,
            "bet_type": bet_type,
            "bet_params": bet_params,
            "player_names": player_names
        }

    def process_bet(self, player_id: str, bet: Any) -> Dict[str, Any]:
        """Processes a player's bet action with validation."""
        self._check_is_playing()
        if player_id not in self.state["players"]:
            raise PlayerNotInGameError(f"玩家 {player_id} 不在本局。")
        if player_id in self.state["player_bets"]:
            raise InvalidActionError("你已经下注了。")

        self.state["player_bets"][player_id] = bet
        logger.info(f"{self.state['players'][player_id]['name']} bet: {bet}")

        if len(self.state["player_bets"]) == len(self.state["players"]):
            results = self._end_game()
            return {
                "success": True,
                "action": "bet",
                "player_id": player_id,
                "player_name": self.state["players"][player_id]["name"],
                "bet": bet,
                "game_ended": True,
                "results": results
            }

        return {
            "success": True,
            "action": "bet",
            "player_id": player_id,
            "player_name": self.state["players"][player_id]["name"],
            "bet": bet,
            "game_ended": False
        }

    def _generate_winning_result(self):
        if self.state["bet_type"] == "猜数字":
            self.state["winning_result"] = random.randint(
                self.state["bet_content"]["min"],
                self.state["bet_content"]["max"]
            )
        elif self.state["bet_type"] == "猜单双":
            self.state["winning_result"] = "单" if random.randint(0, 1) == 0 else "双"

    def _end_game(self):
        results = {}
        for player_id, bet in self.state["player_bets"].items():
            is_win = False
            if self.state["bet_type"] == "猜数字":
                is_win = bet == self.state["winning_result"]
            elif self.state["bet_type"] == "猜单双":
                is_win = bet == self.state["winning_result"]
            results[player_id] = {
                "name": self.state["players"][player_id]["name"],
                "is_ai": self.state["players"][player_id]["is_ai"],
                "is_win": is_win
            }
        self.state["status"] = GameStatus.ENDED
        return results

    # --- Internal Helper Methods ---
    def _check_is_playing(self):
        if self.state["status"] != GameStatus.PLAYING:
            raise GameNotPlayingError(f"游戏需要为 PLAYING 状态 (当前: {self.state['status'].name})。")

