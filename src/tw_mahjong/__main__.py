"""Small simulation and verified replay CLI (SPEC CLI)."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import Optional

from .engine import create_game
from .model import MahjongError, SimulationResult
from .records import record_from_json, record_to_json
from .simulation import SimplePolicy, simulate
from .playback import watch


def _summary(result: SimulationResult) -> dict[str, object]:
    state = result.final_state
    return {
        "phase": state.phase.value,
        "end_reason": None if state.end_reason is None else state.end_reason.value,
        "winner": state.winner, "win_source": state.win_source,
        "winning_tile": state.winning_tile,
        "actions": len(result.actions), "remaining_tiles": len(state.wall.tiles),
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Simplified Taiwanese 16-tile mahjong")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("simulate", help="Run four simple policies")
    run.add_argument("--seed", type=int, required=True)
    run.add_argument("--dealer", type=int, choices=range(4), default=0)
    run.add_argument("--output", type=Path)
    load = commands.add_parser("replay", help="Validate and replay a JSON record")
    load.add_argument("path", type=Path)
    viewer = commands.add_parser("watch", help="Watch a verified record in the terminal")
    viewer.add_argument("path", type=Path)
    viewer.add_argument("--speed", type=float, default=2)
    viewer.add_argument("--step", action="store_true")
    viewer.add_argument("--plain", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "watch":
        if not math.isfinite(args.speed) or not 0.25 <= args.speed <= 64:
            parser.error("--speed must be finite and between 0.25 and 64")
        if args.step and (args.plain or not sys.stdin.isatty() or not sys.stdout.isatty()):
            parser.error("--step requires an interactive terminal without --plain")
    try:
        if args.command == "simulate":
            initial = create_game(dealer=args.dealer, rng=random.Random(args.seed))
            policies = tuple(SimplePolicy(random.Random(args.seed * 4 + player + 1)) for player in range(4))
            result = simulate(initial, policies)
            if args.output is not None:
                text = record_to_json(result)
                with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                    stream.write(text + "\n")
        else:
            result = record_from_json(args.path.read_text(encoding="utf-8"))
        if args.command == "watch":
            watch(result, speed=args.speed, step=args.step, plain=args.plain)
            return 0
        print(json.dumps(_summary(result), ensure_ascii=False, sort_keys=True))
        return 0
    except (MahjongError, OSError, UnicodeError) as exc:
        code = exc.code if isinstance(exc, MahjongError) else "IO_ERROR"
        print(f"{code}: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
