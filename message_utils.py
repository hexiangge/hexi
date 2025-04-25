import logging
from typing import List, Dict, Any, Optional

# Import framework components and models
import astrbot.api.message_components as Comp
from .exceptions import GameError

logger = logging.getLogger(__name__)


# --- Helper to create At or Plain based on ID ---
def _get_player_mention(player_id: str, player_name: str, is_ai: bool) -> List[Any]:
    """根据玩家 ID 和是否 AI 返回 Comp.At 或 Comp.Plain"""
    if not is_ai and player_id.isdigit():
        # 如果不是 AI 且 ID 是数字，尝试 @
        try:
            return [Comp.At(qq=int(player_id)), Comp.Plain(f"({player_name})")]
        except ValueError:
            # 如果 ID 是数字但转换失败（理论上不应发生），回退到 Plain
            logger.warning(f"玩家 ID '{player_id}' 是数字但无法转换为 int 用于 At。")
            return [Comp.Plain(f"{player_name}")]
    elif is_ai:
        # 如果是 AI，使用 Plain
        return [Comp.Plain(f"🤖 {player_name}")]
    else:
        # 其他情况（非 AI 但 ID 不是纯数字），使用 Plain
        return [Comp.Plain(f"{player_name}")]


# --- Formatting Helpers ---
def format_player_list(players: Dict[str, Any], turn_order: List[str]) -> str:
    """格式化玩家列表，包含状态和 AI 标识"""
    if not turn_order: return "无玩家"
    display_list = []
    for pid in turn_order:
        pdata = players.get(pid)
        if pdata:
            status = " (淘汰)" if pdata.get('is_eliminated', False) else ""
            ai_tag = " [AI]" if pdata.get('is_ai', False) else ""
            display_list.append(f"{pdata['name']}{ai_tag}{status}")
        else:
            display_list.append(f"[未知:{pid}]")
    return ", ".join(display_list)


# --- Result to Message Conversion ---

def build_join_message(player_id: str, player_name: str, player_count: int, is_ai: bool = False) -> List[Any]:
    """构建玩家加入/添加 AI 的消息"""
    action_text = "添加 AI" if is_ai else "加入"
    mention_comps = _get_player_mention(player_id, player_name, is_ai)  # 获取提及组件
    prefix_comp = Comp.Plain(text="🤖 " if is_ai else "✅ ")
    suffix_comp = Comp.Plain(text=f" 已{action_text}！当前 {player_count} 人。")
    # 组合消息，注意 mention_comps 返回的是列表
    return [prefix_comp] + mention_comps[:-1] + [Comp.Plain(mention_comps[-1].text.replace('(', '').replace(')', ''))] + [suffix_comp]  # 移除括号并组合


def build_start_game_message(bet_type: str, bet_params: Dict[str, Any]) -> List[Any]:
    """构建游戏开始的消息"""
    components = [
        Comp.Plain(text=f"🎉 竞猜游戏开始！\n竞猜类型: {bet_type}")
    ]
    if bet_type == "猜数字":
        components.append(Comp.Plain(text=f"请猜 {bet_params['min']} 到 {bet_params['max']} 之间的数字"))
    elif bet_type == "猜单双":
        components.append(Comp.Plain(text="请猜单或双"))
    return components


def build_bet_result_messages(results: Dict[str, bool]) -> List[List[Any]]:
    """构建下注结果的多条群公告"""
    messages = []
    for player_id, is_win in results.items():
        player_name = results.get(player_id, {}).get('name', '未知玩家')
        is_ai = results.get(player_id, {}).get('is_ai', False)
        mention_comps = _get_player_mention(player_id, player_name, is_ai)
        result_text = "猜对" if is_win else "猜错"
        messages.append([Comp.Plain("👉 ")] + mention_comps + [Comp.Plain(f" {result_text}！")])
    return messages


def build_game_status_message(game: Dict[str, Any], requesting_player_id: Optional[str]) -> List[Any]:
    """构建游戏状态查询的回复消息"""
    status_text = f"🎲 竞猜游戏状态\n状态: {'等待下注' if game.get('status') == 'waiting' else '游戏已结束'}\n"
    if game.get('status') == 'waiting':
        player_list = [f"- {pdata['name']}{' [AI]' if pdata.get('is_ai', False) else ''}" for pdata in game.get('players', {}).values()]
        status_text += f"玩家 ({len(player_list)}人):\n" + ('\n'.join(player_list) if player_list else "暂无")
        status_text += f"\n\n➡️ 等待所有人下注"
        return [Comp.Plain(status_text)]

    bet_type = game.get('bet_type', '未知')
    status_text += f"竞猜类型: {bet_type}\n"
    if bet_type == "猜数字":
        status_text += f"数字范围: {game.get('bet_content', {}).get('min', '未知')} 到 {game.get('bet_content', {}).get('max', '未知')}\n"
    elif bet_type == "猜单双":
        status_text += "猜单或双\n"

    status_components = [Comp.Plain(status_text)]

    requesting_pdata = game.get('players', {}).get(requesting_player_id) if requesting_player_id else None
    if requesting_pdata:
        player_name = requesting_pdata.get('name', '未知玩家')
        is_ai = requesting_pdata.get('is_ai', False)
        mention_comps = _get_player_mention(requesting_player_id, player_name, is_ai)
        status_components.append(Comp.Plain("你已参与游戏\n"))
        status_components.extend(mention_comps)

    return status_components


def build_game_end_message(winner_ids: List[str], winner_names: List[str]) -> List[Any]:
    """构建游戏结束的消息"""
    announcement = f"🎉 游戏结束！胜者是: "
    for i, (winner_id, winner_name) in enumerate(zip(winner_ids, winner_names)):
        is_ai = False
        if i > 0:
            announcement += ", "
        mention_comps = _get_player_mention(winner_id, winner_name, is_ai)
        announcement += ''.join([comp.text for comp in mention_comps])
    return [Comp.Plain(announcement)]


def build_error_message(error: Exception) -> str:
    """生成用户友好的错误消息字符串"""
    error_prefix = "⚠️ 操作失败: "
    error_details = ""
    if isinstance(error, GameError):
        error_details = str(error)
    else:
        error_prefix = "❌ 内部错误: "
        error_details = f"处理时遇到意外问题。请联系管理员。错误类型: {type(error).__name__}"
        logger.error(f"Unexpected error: {error}", exc_info=True)
    return error_prefix + error_details

