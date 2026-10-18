"""Pure terminal board layout with explicit display-cell widths."""

from __future__ import annotations

import re
import unicodedata
from itertools import zip_longest
from typing import Optional

from .model import Action, ActionKind, EventKind, ReplayFrame, SimulationResult, Tile

_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_NUMBERS = "一二三四五六七八九"
_HONORS = "東南西北中發白"
_FLOWERS = "春夏秋冬梅蘭竹菊"
_ACTIONS = {
    "DRAW": "摸牌",
    "DISCARD": "出牌",
    "CHI": "吃",
    "PENG": "碰",
    "HU": "胡牌",
    "PASS": "過",
    "KONG_EXPOSED": "明槓",
    "KONG_CONCEALED": "暗槓",
    "KONG_ADDED": "加槓",
}
_PHASES = {
    "DRAW": "摸牌",
    "DISCARD": "出牌",
    "RESPONSE": "等待吃碰槓胡",
    "ROB_KONG": "等待搶槓",
    "ENDED": "已結束",
}
_EVENTS = {
    "DRAWN": "摸入",
    "FLOWER": "補花",
    "DISCARDED": "打出",
    "RESPONSE": "登記回應",
    "CLAIMED": "副露成立",
    "TURN": "輪到",
    "WON": "胡牌",
    "EXHAUSTED": "牌牆耗盡",
    "KONG_DECLARED": "宣告加槓",
    "KONG_COMPLETED": "槓成立",
}
SCORE_NAMES = {
    "CONCEALED": "門清",
    "SELF_DRAW": "自摸",
    "CONCEALED_SELF_DRAW": "門清自摸",
    "DRAGON_R": "紅中",
    "DRAGON_G": "青發",
    "DRAGON_B": "白板",
    "SEAT_WIND": "門風",
    "ROUND_WIND": "圈風",
    "SEAT_FLOWER": "門花",
    "FLOWER_SET": "花槓",
    "ALL_TRIPLETS": "碰碰胡",
    "MIXED_SUIT": "混一色",
    "PURE_SUIT": "清一色",
    "ALL_HONORS": "字一色",
    "SMALL_DRAGONS": "小三元",
    "BIG_DRAGONS": "大三元",
    "SMALL_WINDS": "小四喜",
    "BIG_WINDS": "大四喜",
    "THREE_CONCEALED": "三暗刻",
    "FOUR_CONCEALED": "四暗刻",
    "FIVE_CONCEALED": "五暗刻",
    "SUPPLEMENT_WIN": "槓上開花",
    "ROB_KONG": "搶槓",
    "LAST_DRAW": "海底撈月",
    "LAST_DISCARD": "河底撈魚",
    "SINGLE_WAIT": "獨聽",
}


def display_width(text: str) -> int:
    """Count terminal cells, ignoring color codes and combining marks."""
    return sum(
        0 if unicodedata.combining(char)
        else 2 if unicodedata.east_asian_width(char) in ("W", "F")
        else 1
        for char in _ANSI.sub("", text)
    )


def _pad(text: str, width: int) -> str:
    return text + " " * max(0, width - display_width(text))


def _wrap_tokens(tokens: tuple[str, ...], width: int) -> list[str]:
    """Wrap between tokens so a tile block is never split across rows."""
    rows = []
    row = ""

    for token in tokens:
        candidate = f"{row} {token}" if row else token
        if row and display_width(candidate) > width:
            rows.append(row)
            row = token
        else:
            row = candidate

    rows.append(row)
    return rows


def _wrap_text(text: str, width: int) -> list[str]:
    rows = []
    row = ""

    for char in text:
        if row and display_width(row + char) > width:
            rows.append(row)
            row = ""
        row += char

    rows.append(row)
    return rows


def tile_block(
    tile: Tile,
    *,
    ascii_tiles: bool,
    color: bool,
    marked: bool = False,
) -> str:
    if ascii_tiles:
        label = tile.code
    elif tile.kind < 27:
        label = _NUMBERS[tile.kind % 9] + "萬筒索"[tile.kind // 9]
    elif tile.kind < 34:
        label = _HONORS[tile.kind - 27]
    else:
        label = _FLOWERS[tile.kind - 34] + "花"

    block = "[" + _pad(label, 4) + "]"
    if color:
        palette = (31, 34, 32, 33, 35)
        group = tile.kind // 9 if tile.kind < 27 else 3 if tile.kind < 34 else 4
        block = f"\x1b[{'1;' if marked else ''}{palette[group]}m{block}\x1b[0m"

    return ("*" if marked else " ") + block


def _action_text(
    frame: ReplayFrame,
    primary: Optional[Action],
    *,
    ascii_tiles: bool,
    color: bool,
) -> tuple[str, ...]:
    if primary is None:
        return (
            ("Initial board" if frame.index == 0 else "Response recorded",)
            if ascii_tiles
            else ("起手盤面" if frame.index == 0 else "回應已登記",)
        )

    name = primary.kind.value if ascii_tiles else _ACTIONS[primary.kind.value]
    request = (
        frame.events
        and all(event.kind is EventKind.RESPONSE for event in frame.events)
        and primary.kind is not ActionKind.PASS
    )
    if request:
        name = "request " + name if ascii_tiles else "申請" + name
    if primary.kind is ActionKind.KONG_ADDED:
        declared = any(event.kind is EventKind.KONG_DECLARED for event in frame.events)
        suffix = " declared" if declared else " completed"
        name = name + suffix if ascii_tiles else ("宣告加槓" if declared else "加槓成立")

    # Include the external tile for claims and the actual tile for draw events.
    ids = set(primary.tiles)
    pending = frame.state.pending or frame.state.pending_kong
    if request and pending is not None:
        ids.add(pending.tile.id)
    for event in frame.events:
        if event.action == primary and event.tile is not None and event.kind in (
            EventKind.DRAWN,
            EventKind.DISCARDED,
            EventKind.CLAIMED,
            EventKind.KONG_COMPLETED,
            EventKind.WON,
        ):
            ids.add(event.tile)

    return (f"P{primary.player}", name) + tuple(
        tile_block(Tile(i), ascii_tiles=ascii_tiles, color=color) for i in sorted(ids)
    )


def _panel(
    frame: ReplayFrame,
    player: int,
    width: int,
    *,
    ascii_tiles: bool,
    color: bool,
) -> list[str]:
    state = frame.state
    own = state.players[player]
    inner = width - 4

    wind = (player - state.dealer) % 4 if state.rules_version == 2 else player
    wind_name = "ESWN"[wind] if ascii_tiles else _HONORS[wind] + "風"
    title = f"P{player} {wind_name}"
    if player == state.dealer:
        title += " [dealer]" if ascii_tiles else " [莊家]"
    if player == state.turn:
        title += " <<current>>" if ascii_tiles else " <<目前玩家>>"
    rows = _wrap_text(title, inner)

    drawn = next((event.tile for event in frame.events if event.kind is EventKind.DRAWN), None)
    discarded = next((event.tile for event in frame.events if event.kind is EventKind.DISCARDED), None)
    if frame.index == 0:
        drawn = state.last_drawn

    def blocks(tiles: tuple[Tile, ...]) -> tuple[str, ...]:
        return tuple(
            tile_block(
                tile,
                ascii_tiles=ascii_tiles,
                color=color,
                marked=tile.id in (drawn, discarded),
            )
            for tile in tiles
        )

    rows.extend(_wrap_tokens(
        (f"Hand({len(own.hand)}):" if ascii_tiles else f"手牌({len(own.hand)}):",)
        + (blocks(own.hand) or ("-",)),
        inner,
    ))

    meld_tokens = []
    for meld in own.melds:
        name = meld.kind.value if ascii_tiles else _ACTIONS[meld.kind.value]
        meld_tokens.extend((name + "{",) + blocks(meld.tiles) + ("}",))
    rows.extend(_wrap_tokens(
        ("Melds:" if ascii_tiles else "副露:",) + tuple(meld_tokens or ("-",)),
        inner,
    ))
    rows.extend(_wrap_tokens(
        ("Flowers:" if ascii_tiles else "花牌:",) + (blocks(own.flowers) or ("-",)),
        inner,
    ))

    # Keep the live panel compact; plain transcripts retain the whole river.
    river = state.discards[player]
    omitted = max(0, len(river) - 12)
    label = (
        f"River({len(river)},hidden={omitted}):"
        if ascii_tiles else f"河牌(共{len(river)},省略{omitted}):"
    )
    rows.extend(_wrap_text(label, inner))
    rows.extend(_wrap_tokens(blocks(river[-12:]) or ("-",), inner))

    border = "+" + "-" * (width - 2) + "+"
    return [border] + ["| " + _pad(row, inner) + " |" for row in rows] + [border]


def render_board(
    frame: ReplayFrame,
    result: SimulationResult,
    recent: tuple[str, ...],
    *,
    primary: Optional[Action],
    speed: float,
    paused: bool,
    visible_index: int,
    visible_total: int,
    draws: int,
    discards: int,
    columns: int,
    ascii_tiles: bool,
    color: bool,
    result_lines: tuple[str, ...],
) -> str:
    """Arrange four player panels and the playback summary within the width."""
    columns = max(20, columns)
    state = frame.state
    finished = frame.index == len(result.actions)

    if ascii_tiles:
        headers = [
            f"Display {visible_index}/{visible_total} "
            f"| operation {frame.index}/{len(result.actions)} "
            f"| draws {draws} | discards {discards}",
            f"{state.phase.value} | P{state.turn} | wall {len(state.wall.tiles)} "
            f"| {'FINISHED' if finished else 'PAUSED' if paused else 'PLAYING'} "
            f"| {speed:g} steps/s",
            "space pause | n/Enter step | +/- speed | q quit | * drawn/discarded",
        ]
    else:
        headers = [
            f"播放 {visible_index}/{visible_total} "
            f"| 原始操作 {frame.index}/{len(result.actions)} | 摸牌 {draws} | 出牌 {discards}",
            f"{_PHASES[state.phase.value]} | P{state.turn} | 剩餘牌 {len(state.wall.tiles)} "
            f"| {'播放結束' if finished else '暫停' if paused else '播放中'} | 每秒 {speed:g} 步",
            "空白:暫停/繼續  n/Enter:單步  +/-:調速  q:離開  *:剛摸入/打出",
        ]
    lines = [row for header in headers for row in _wrap_text(header, columns)]
    lines.append("")

    # Wide terminals use two columns; narrow terminals stack player panels.
    if columns >= 120:
        left_width = (columns - 2) // 2
        right_width = columns - 2 - left_width
        for first, second in ((0, 1), (2, 3)):
            left = _panel(frame, first, left_width, ascii_tiles=ascii_tiles, color=color)
            right = _panel(frame, second, right_width, ascii_tiles=ascii_tiles, color=color)
            for a, b in zip_longest(left, right):
                lines.append(
                    (a if a is not None else " " * left_width)
                    + "  "
                    + (b if b is not None else " " * right_width)
                )
            lines.append("")
    else:
        for player in range(4):
            lines.extend(_panel(frame, player, columns, ascii_tiles=ascii_tiles, color=color))

    label = "Action:" if ascii_tiles else "主要動作:"
    lines.extend(_wrap_tokens(
        (label,) + _action_text(frame, primary, ascii_tiles=ascii_tiles, color=color),
        columns,
    ))
    lines.append("Recent events:" if ascii_tiles else "近期事件:")
    translations = {
        **_ACTIONS,
        **_EVENTS,
        **{"REQUEST_" + key: "申請" + value for key, value in _ACTIONS.items()},
    }
    for event in recent:
        if not ascii_tiles:
            event = re.sub(r"\b[A-Z_]+\b", lambda match: translations.get(match[0], match[0]), event)
        lines.extend(_wrap_text("  " + event, columns))
    for line in result_lines:
        lines.extend(_wrap_text(line, columns))

    return "\n".join(lines)
