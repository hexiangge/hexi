class GameError(Exception):
    """游戏逻辑错误基类"""
    pass


class GameNotFoundError(GameError):
    """未找到游戏实例"""
    pass


class PlayerNotInGameError(GameError):
    """玩家不在游戏中"""
    pass


class PlayerAlreadyJoinedError(GameError):
    """玩家已加入"""
    pass


class GameNotWaitingError(GameError):
    """操作要求游戏状态为 WAITING"""
    pass


class GameNotPlayingError(GameError):
    """操作要求游戏状态为 PLAYING"""
    pass


class NotEnoughPlayersError(GameError):
    """玩家人数不足以开始游戏"""
    pass


class NotPlayersTurnError(GameError):
    """在非玩家回合尝试操作"""
    def __init__(self, message="在非玩家回合尝试操作", current_player_name=None):
        super().__init__(message)
        self.current_player_name = current_player_name  # 可以携带当前轮到谁的名字


class InvalidActionError(GameError):
    """在当前上下文中不允许的操作"""
    pass


class InvalidBetError(GameError):
    """提供的赌注无效"""
    def __init__(self, message="提供的赌注无效", invalid_bet=None):
        super().__init__(message)
        self.invalid_bet = invalid_bet


