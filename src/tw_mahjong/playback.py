"""Terminal-only presentation: clocks and input never enter the rule engine."""

from __future__ import annotations

import math
import os
import sys
import time
from collections import deque
from contextlib import AbstractContextManager
from typing import Optional

from .model import MahjongError, Phase, ReplayFrame, SimulationResult, Tile
from .simulation import iter_replay


def _tiles(tiles: tuple[Tile, ...]) -> str:
    return " ".join(tile.code for tile in tiles) or "-"


def _result_lines(result: SimulationResult) -> list[str]:
    state = result.final_state
    if state.phase is not Phase.ENDED:
        return ["End of recorded prefix (game unfinished)."]
    lines = [f"Result: {state.end_reason.value} | winner={state.winner} source={state.win_source}"]
    if getattr(state, "rules_version", 1) == 1:
        return lines + ["Scoring: unavailable (v1 record)."]
    from .scoring import settle_hand

    settlement = settle_hand(state, result.settlement_config)
    lines.append(f"Hand tai: {settlement.score.tai}")
    lines.extend(f"  {item.code}: +{item.tai}" for item in settlement.score.items)
    for payment in settlement.payments:
        lines.append(f"  P{payment.payer} -> P{payment.payee}: {payment.amount} points ({payment.tai} tai incl. dealer)")
    lines.append(f"Score deltas: {settlement.deltas}")
    return lines


def render_frame(frame: ReplayFrame, result: SimulationResult, recent: tuple[str, ...], *, speed: float, paused: bool) -> str:
    state = frame.state
    lines = [
        f"Taiwanese mahjong | step {frame.index}/{len(result.actions)} | {state.phase.value} | turn P{state.turn} | wall {len(state.wall.tiles)}",
        f"{'PAUSED' if paused else 'PLAYING'} | {speed:g} actions/s | space pause | n/Enter step | +/- speed | q quit",
    ]
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


def watch(result: SimulationResult, *, speed: float = 2, step: bool = False, plain: bool = False) -> None:
    if isinstance(speed, bool) or not isinstance(speed, (int, float)) or not math.isfinite(speed) or not 0.25 <= speed <= 64:
        raise MahjongError("INVALID_PLAYBACK", "Speed must be finite and between 0.25 and 64")
    interactive = sys.stdin.isatty() and sys.stdout.isatty() and not plain
    if step and not interactive:
        raise MahjongError("INVALID_PLAYBACK", "--step requires an interactive terminal without --plain")
    frames = iter_replay(result.initial_state, result.actions)
    recent: deque[str] = deque(maxlen=5)

    def remember(frame: ReplayFrame) -> None:
        if frame.action is not None:
            recent.append(f"#{frame.index} P{frame.action.player} {frame.action.kind.value} {frame.action.tiles}")
        for event in frame.events:
            tile = "" if event.tile is None else f" {Tile(event.tile).code}"
            recent.append(f"{event.kind.value} P{event.player}{tile}")

    if not interactive:
        for frame in frames:
            remember(frame)
            print(render_frame(frame, result, tuple(recent), speed=speed, paused=False))
            print()
        return
    frame = next(frames)
    paused = step
    deadline = time.monotonic() + 1 / speed
    with _Terminal() as terminal:
        dirty = True
        while True:
            if dirty:
                sys.stdout.write("\x1b[H\x1b[J" + render_frame(frame, result, tuple(recent), speed=speed, paused=paused))
                sys.stdout.flush()
                dirty = False
            if frame.index == len(result.actions):
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
                frame = next(frames)
                remember(frame)
                deadline = time.monotonic() + 1 / speed
                dirty = True
            else:
                time.sleep(0.02)
