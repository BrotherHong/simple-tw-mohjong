"""Fixed v2 tai rules and zero-sum settlement (SPEC SCORE/PAY)."""

from __future__ import annotations

from .engine import validate_state
from .hand import analyze_hand, find_waits
from .model import (
    Decomposition,
    DrawSource,
    EndReason,
    GameState,
    MahjongError,
    MeldKind,
    Payment,
    Phase,
    ScoreItem,
    ScoreResult,
    Settlement,
    SettlementConfig,
    Tile,
)


def score_hand(state: GameState) -> ScoreResult:
    """Choose the best legal decomposition and winning-tile placement."""
    validate_state(state)

    if state.rules_version != 2 or state.phase is not Phase.ENDED:
        raise MahjongError("INVALID_SCORE", "Scoring requires a finished v2 game")

    if state.end_reason is EndReason.WALL_EXHAUSTED:
        return ScoreResult(0, (), None, None)

    # Rebuild the winning hand without moving the physical winning tile.
    own = state.players[state.winner]
    self_draw = state.end_reason is EndReason.SELF_DRAW
    win = Tile(state.winning_tile)
    hand = own.hand if self_draw else own.hand + (win,)
    before = tuple(tile for tile in own.hand if tile != win) if self_draw else own.hand
    single_wait = len(find_waits(before, own.melds)) == 1
    closed = all(meld.kind is MeldKind.KONG_CONCEALED for meld in own.melds)

    # Suit patterns include both concealed tiles and declared melds.
    all_tiles = hand + tuple(tile for meld in own.melds for tile in meld.tiles)
    suits = {tile.kind // 9 for tile in all_tiles if tile.kind < 27}
    honors = any(tile.kind >= 27 for tile in all_tiles)

    candidates = []
    for decomposition in analyze_hand(hand, own.melds).decompositions:
        # The same tile kind may complete a pair, sequence, or triplet.
        placements = {group for group in decomposition.groups if win.kind in group}
        if decomposition.pair == win.kind:
            placements.add(None)

        for placement in placements:
            items: dict[str, int] = {}

            def add(code: str, tai: int) -> None:
                if tai:
                    items[code] = tai

            # Combined concealed self-draw replaces its two separate items.
            if closed and self_draw:
                add("CONCEALED_SELF_DRAW", 3)
            else:
                add("CONCEALED", int(closed))
                add("SELF_DRAW", int(self_draw))

            concealed_triplets = tuple(
                group for group in decomposition.groups if len(set(group)) == 1
            )
            triplets = {group[0] for group in concealed_triplets}
            triplets.update(
                meld.tiles[0].kind for meld in own.melds if meld.kind is not MeldKind.CHI
            )

            # Dragon sets suppress the individual dragon-tile awards.
            dragons = triplets.intersection((31, 32, 33))
            if len(dragons) == 3:
                add("BIG_DRAGONS", 8)
            elif len(dragons) == 2 and decomposition.pair in {31, 32, 33} - dragons:
                add("SMALL_DRAGONS", 4)
            else:
                for kind, code in ((31, "DRAGON_R"), (32, "DRAGON_G"), (33, "DRAGON_B")):
                    add(code, int(kind in dragons))

            # Wind patterns and seat/round awards can accumulate.
            winds = triplets.intersection((27, 28, 29, 30))
            if len(winds) == 4:
                add("BIG_WINDS", 16)
            elif len(winds) == 3 and decomposition.pair in {27, 28, 29, 30} - winds:
                add("SMALL_WINDS", 8)
            seat = (state.winner - state.dealer) % 4
            add("SEAT_WIND", int(27 + seat in winds))
            add("ROUND_WIND", int(state.round_wind in winds))

            # A flower set may also contain the winner's seat flowers.
            flowers = {tile.id for tile in own.flowers}
            add("SEAT_FLOWER", len(flowers.intersection((136 + seat, 140 + seat))))
            add(
                "FLOWER_SET",
                int(set(range(136, 140)) <= flowers)
                + int(set(range(140, 144)) <= flowers),
            )

            # Suit patterns are exclusive; all honors suppresses all triplets.
            if not suits:
                add("ALL_HONORS", 16)
            elif len(suits) == 1:
                add("MIXED_SUIT" if honors else "PURE_SUIT", 4 if honors else 8)
            if (
                len(concealed_triplets)
                + sum(meld.kind is not MeldKind.CHI for meld in own.melds) == 5
                and suits
            ):
                add("ALL_TRIPLETS", 4)

            # A triplet completed by another player is not concealed.
            dark_count = len(concealed_triplets) + sum(
                meld.kind is MeldKind.KONG_CONCEALED for meld in own.melds
            )
            if not self_draw and placement is not None and len(set(placement)) == 1:
                dark_count -= 1
            if dark_count >= 3:
                code, tai = {
                    3: ("THREE_CONCEALED", 2),
                    4: ("FOUR_CONCEALED", 5),
                    5: ("FIVE_CONCEALED", 8),
                }[dark_count]
                add(code, tai)

            # These awards depend on how the final tile was obtained.
            add(
                "SUPPLEMENT_WIN",
                int(self_draw and state.draw_source in (DrawSource.FLOWER, DrawSource.KONG)),
            )
            add("ROB_KONG", int(state.end_reason is EndReason.ROB_KONG))
            add("LAST_DRAW", int(self_draw and not state.wall.tiles))
            add(
                "LAST_DISCARD",
                int(state.end_reason is EndReason.DISCARD_WIN and state.last_discard_last),
            )
            add("SINGLE_WAIT", int(single_wait))

            ordered = tuple(ScoreItem(code, tai) for code, tai in sorted(items.items()))
            candidates.append(
                ScoreResult(sum(item.tai for item in ordered), ordered, decomposition, placement)
            )

    return min(candidates, key=_candidate_key)


def _candidate_key(score: ScoreResult) -> tuple:
    """Break equal-score ties with a stable structural order."""
    decomposition: Decomposition = score.decomposition
    return (
        -score.tai,
        decomposition.pair,
        decomposition.groups,
        score.winning_group or (-1, -1, -1),
    )


def settle_hand(
    state: GameState,
    config: SettlementConfig = SettlementConfig(),
) -> Settlement:
    """Calculate each payment separately and return zero-sum score changes."""
    if not isinstance(config, SettlementConfig):
        raise MahjongError("INVALID_SETTLEMENT", "Expected SettlementConfig")
    config.__post_init__()

    score = score_hand(state)
    if state.end_reason is EndReason.WALL_EXHAUSTED:
        return Settlement(score, (), (0, 0, 0, 0))

    # Only self-draw makes all three opponents pay.
    payers = (
        tuple(p for p in range(4) if p != state.winner)
        if state.end_reason is EndReason.SELF_DRAW
        else (state.win_source,)
    )
    payments = []
    deltas = [0, 0, 0, 0]

    for payer in payers:
        tai = score.tai + int(state.winner == state.dealer or payer == state.dealer)
        amount = config.base + config.tai_value * tai
        payments.append(Payment(payer, state.winner, tai, amount))
        deltas[payer] -= amount
        deltas[state.winner] += amount

    return Settlement(score, tuple(payments), tuple(deltas))
