"""Terminal-only presentation: clocks and input never enter the rule engine."""

from __future__ import annotations

import math
import os
import shutil
import sys
import time
from collections import deque
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Optional

from .model import Action, ActionKind, EventKind, MahjongError, Phase, ReplayFrame, SimulationResult, Tile
from .simulation import iter_replay


def _tiles(tiles: tuple[Tile, ...]) -> str:
    return " ".join(tile.code for tile in tiles) or "-"


def _result_lines(result: SimulationResult, *, chinese: bool = False) -> list[str]:
    state = result.final_state
    if state.phase is not Phase.ENDED:
        return ["紀錄結束（牌局尚未結束）。" if chinese else "End of recorded prefix (game unfinished)."]
    if chinese:
        reasons = {"SELF_DRAW": "自摸", "DISCARD_WIN": "放槍胡", "ROB_KONG": "搶槓胡", "WALL_EXHAUSTED": "流局"}
        lines = [f"結果: {reasons[state.end_reason.value]} | 贏家={state.winner} 來源={state.win_source}"]
    else:
        lines = [f"Result: {state.end_reason.value} | winner={state.winner} source={state.win_source}"]
    if getattr(state, "rules_version", 1) == 1:
        return lines + ["計分資訊未包含（v1 紀錄）。" if chinese else "Scoring: unavailable (v1 record)."]
    from .scoring import settle_hand

    settlement = settle_hand(state, result.settlement_config)
    from .board import SCORE_NAMES

    lines.append(f"牌型台數: {settlement.score.tai}" if chinese else f"Hand tai: {settlement.score.tai}")
    lines.extend(f"  {SCORE_NAMES[item.code] if chinese else item.code}: +{item.tai}" for item in settlement.score.items)
    for payment in settlement.payments:
        lines.append(f"  P{payment.payer} -> P{payment.payee}: {payment.amount} 分（含莊家加台共 {payment.tai} 台）" if chinese else f"  P{payment.payer} -> P{payment.payee}: {payment.amount} points ({payment.tai} tai incl. dealer)")
    lines.append(f"分數增減: {settlement.deltas}" if chinese else f"Score deltas: {settlement.deltas}")
    return lines


def main_action(frame: ReplayFrame, detail: bool = False) -> Optional[Action]:
    if not detail:
        for kind in (EventKind.WON, EventKind.KONG_COMPLETED, EventKind.CLAIMED):
            for event in frame.events:
                if event.kind is kind and event.action is not None:
                    return event.action
    if frame.action is not None and (detail or frame.action.kind is not ActionKind.PASS):
        return frame.action
    return None


@dataclass(frozen=True)
class _PlaybackFrame:
    frame: ReplayFrame
    recent: tuple[str, ...]
    draws: int
    discards: int


def _visible_frames(result: SimulationResult, detail: bool = False) -> tuple[_PlaybackFrame, ...]:
    """Filter presentation only; every original action is still replayed."""
    meaningful = {EventKind.CLAIMED, EventKind.KONG_COMPLETED, EventKind.DRAWN,
                  EventKind.FLOWER, EventKind.WON, EventKind.EXHAUSTED}
    recent: deque[str] = deque(maxlen=5)
    draws = discards = 0
    visible = []
    for frame in iter_replay(result.initial_state, result.actions):
        action = frame.action
        if action is not None:
            draws += int(action.kind is ActionKind.DRAW)
            discards += int(action.kind is ActionKind.DISCARD)
        primary = main_action(frame, detail)
        if primary is not None:
            ids = " ".join(Tile(i).code for i in primary.tiles)
            request = not detail and frame.events and all(event.kind is EventKind.RESPONSE for event in frame.events)
            name = ("REQUEST_" if request else "") + primary.kind.value
            recent.append(f"P{primary.player} {name}{' ' + ids if ids else ''}")
        for event in frame.events:
            if not detail and event.kind is EventKind.RESPONSE:
                continue
            tile = "" if event.tile is None else f" {Tile(event.tile).code}"
            actor = "" if event.player is None else f" P{event.player}"
            recent.append(f"{event.kind.value}{actor}{tile}")
        show = (
            detail or frame.index in (0, len(result.actions))
            or action is not None and action.kind is not ActionKind.PASS
            or any(event.kind in meaningful for event in frame.events)
        )
        if show:
            visible.append(_PlaybackFrame(frame, tuple(recent), draws, discards))
    return tuple(visible)


def render_frame(frame: ReplayFrame, result: SimulationResult, recent: tuple[str, ...], *, speed: float, paused: bool,
                 visible_index: Optional[int] = None, visible_total: Optional[int] = None,
                 draws: int = 0, discards: int = 0, detail: bool = False,
                 plain: bool = True, ascii_tiles: bool = False, color: bool = False,
                 columns: int = 100) -> str:
    state = frame.state
    status = "FINISHED" if frame.index == len(result.actions) else ("PAUSED" if paused else "PLAYING")
    index = frame.index if visible_index is None else visible_index
    total = len(result.actions) if visible_total is None else visible_total
    if not plain:
        from .board import render_board

        return render_board(frame, result, recent, primary=main_action(frame, detail), speed=speed,
                            paused=paused, visible_index=index, visible_total=total, draws=draws,
                            discards=discards, columns=columns, ascii_tiles=ascii_tiles, color=color,
                            result_lines=tuple(_result_lines(result, chinese=not ascii_tiles)) if frame.index == len(result.actions) else ())
    lines = [
        f"Taiwanese mahjong | display {index}/{total} | operation {frame.index}/{len(result.actions)} | draws {draws} discards {discards}",
        f"{state.phase.value} | turn P{state.turn} | wall {len(state.wall.tiles)} | {status} | {speed:g} steps/s",
        "space pause | n/Enter step | +/- speed | q quit",
    ]
    primary = main_action(frame, detail)
    if primary is not None:
        lines.append(f"Action: P{primary.player} {primary.kind.value} {primary.tiles}")
    for player, own in enumerate(state.players):
        wind = (player - state.dealer) % 4 if getattr(state, "rules_version", 1) == 2 else player
        lines.append(f"P{player} {'ESWN'[wind]}{' [dealer]' if player == state.dealer else ''} | hand: {_tiles(own.hand)}")
        melds = " / ".join(f"{meld.kind.value}[{_tiles(meld.tiles)}]" for meld in own.melds) or "-"
        lines.append(f"  melds: {melds} | flowers: {_tiles(own.flowers)}")
        lines.append(f"  river: {_tiles(state.discards[player])}")
    lines.append("Recent events:")
    lines.extend(f"  {line}" for line in recent)
    if frame.index == len(result.actions):
        lines.extend(_result_lines(result))
    return "\n".join(lines)


class _Terminal(AbstractContextManager):
    """Restore console mode and cursor on both normal and exceptional exits."""

    def __init__(self) -> None:
        self.saved = None
        self.handle = None

    def __enter__(self) -> "_Terminal":
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.GetStdHandle.argtypes = [wintypes.DWORD]
            kernel.GetStdHandle.restype = wintypes.HANDLE
            kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            handle = kernel.GetStdHandle(-11 & 0xFFFFFFFF)
            mode = wintypes.DWORD()
            if not kernel.GetConsoleMode(handle, ctypes.byref(mode)):
                raise OSError(ctypes.get_last_error(), "Cannot read terminal output mode; use --plain")
            if not kernel.SetConsoleMode(handle, mode.value | 0x0004):
                raise OSError(ctypes.get_last_error(), "Cannot enable terminal rendering; use --plain")
            self.handle = (kernel, handle)
            self.saved = mode.value
        else:
            import termios
            import tty

            self.saved = termios.tcgetattr(sys.stdin.fileno())
            try:
                tty.setcbreak(sys.stdin.fileno())
            except BaseException:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.saved)
                raise
        try:
            sys.stdout.write("\x1b[?25l\x1b[2J\x1b[H")
            sys.stdout.flush()
        except BaseException:
            self.__exit__(*sys.exc_info())
            raise
        return self

    def __exit__(self, *args: object) -> None:
        try:
            sys.stdout.write("\x1b[?25h\n")
            sys.stdout.flush()
        finally:
            if os.name == "nt" and self.handle is not None:
                kernel, handle = self.handle
                kernel.SetConsoleMode(handle, self.saved)
            elif os.name != "nt" and self.saved is not None:
                import termios

                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.saved)

    def key(self) -> Optional[str]:
        if os.name == "nt":
            import msvcrt

            if not msvcrt.kbhit():
                return None
            key = msvcrt.getwch()
            if key in ("\x00", "\xe0"):
                msvcrt.getwch()
                return None
        else:
            import select

            if not select.select([sys.stdin], [], [], 0)[0]:
                return None
            key = os.read(sys.stdin.fileno(), 1).decode("ascii", errors="ignore")
            if not key:
                return "q"
        if key == "\x03":
            raise KeyboardInterrupt
        return key


def watch(result: SimulationResult, *, speed: float = 2, step: bool = False, plain: bool = False,
          detail: bool = False, ascii_tiles: bool = False, no_color: bool = False) -> None:
    if isinstance(speed, bool) or not isinstance(speed, (int, float)) or not math.isfinite(speed) or not 0.25 <= speed <= 64:
        raise MahjongError("INVALID_PLAYBACK", "Speed must be finite and between 0.25 and 64")
    interactive = sys.stdin.isatty() and sys.stdout.isatty() and not plain
    if step and not interactive:
        raise MahjongError("INVALID_PLAYBACK", "--step requires an interactive terminal without --plain")
    frames = _visible_frames(result, detail)

    def render(index: int, paused: bool) -> str:
        item = frames[index]
        options = dict(speed=speed, paused=paused, visible_index=index, visible_total=len(frames) - 1,
                       draws=item.draws, discards=item.discards, detail=detail, plain=not interactive,
                       ascii_tiles=ascii_tiles, color=interactive and not no_color,
                       columns=shutil.get_terminal_size((100, 40)).columns)
        text = render_frame(item.frame, result, item.recent, **options)
        try:
            text.encode(sys.stdout.encoding or "utf-8")
        except UnicodeEncodeError:
            options["ascii_tiles"] = True
            text = render_frame(item.frame, result, item.recent, **options)
        return text

    if not interactive:
        for index in range(len(frames)):
            print(render(index, False))
            print()
        return
    index = 0
    paused = step
    deadline = time.monotonic() + 1 / speed
    with _Terminal() as terminal:
        dirty = True
        last_columns = shutil.get_terminal_size((100, 40)).columns
        while True:
            columns = shutil.get_terminal_size((100, 40)).columns
            if columns != last_columns:
                last_columns = columns
                dirty = True
            if dirty:
                sys.stdout.write("\x1b[H\x1b[J" + render(index, paused))
                sys.stdout.flush()
                dirty = False
            if index == len(frames) - 1:
                break
            key = terminal.key()
            advance = False
            if key in ("q", "Q"):
                break
            if key == " ":
                paused = not paused
                deadline = time.monotonic() + 1 / speed
                dirty = True
            elif key in ("n", "N", "\r", "\n"):
                paused = True
                advance = True
            elif key in ("+", "=", "-"):
                speed = min(64, speed * 2) if key != "-" else max(0.25, speed / 2)
                deadline = time.monotonic() + 1 / speed
                dirty = True
            if advance or (not paused and time.monotonic() >= deadline):
                index += 1
                deadline = time.monotonic() + 1 / speed
                dirty = True
            else:
                delay = 0.02 if paused else min(0.02, max(0.0, deadline - time.monotonic()))
                time.sleep(delay)
