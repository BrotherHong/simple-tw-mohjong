"""Exhaustive, canonical five-meld-and-pair decomposition (SPEC HAND)."""

from functools import lru_cache

from .model import Decomposition, HandAnalysis, MahjongError, Meld, Tile


def analyze_hand(hand: tuple[Tile, ...], melds: tuple[Meld, ...] = ()) -> HandAnalysis:
    if not isinstance(melds, tuple) or len(melds) > 5:
        raise MahjongError("INVALID_MELD", "Expected at most five melds")
    for meld in melds:
        if not isinstance(meld, Meld):
            raise MahjongError("INVALID_MELD", "Expected Meld values")
        meld.__post_init__()
    if not isinstance(hand, tuple) or not all(isinstance(t, Tile) and not t.is_flower for t in hand):
        raise MahjongError("INVALID_HAND", "Hand requires ordinary physical tiles")
    if len(hand) != 17 - 3 * len(melds):
        raise MahjongError("INVALID_HAND", "Wrong concealed tile count for meld count")
    tiles = hand + tuple(t for meld in melds for t in meld.tiles)
    if len({t.id for t in tiles}) != len(tiles):
        raise MahjongError("INVALID_HAND", "Duplicate physical tile across hand and melds")
    counts = [0] * 34
    for tile in hand:
        counts[tile.kind] += 1

    @lru_cache(maxsize=None)
    def split(remaining: tuple[int, ...]) -> tuple[tuple[tuple[int, int, int], ...], ...]:
        first = next((i for i, count in enumerate(remaining) if count), None)
        if first is None:
            return ((),)
        possibilities = []
        if remaining[first] >= 3:
            possibilities.append((first, first, first))
        if first < 27 and first % 9 <= 6 and remaining[first + 1] and remaining[first + 2]:
            possibilities.append((first, first + 1, first + 2))
        results = set()
        for group in possibilities:
            reduced = list(remaining)
            for kind in group:
                reduced[kind] -= 1
            for tail in split(tuple(reduced)):
                results.add(tuple(sorted((group,) + tail)))
        return tuple(sorted(results))

    decompositions = set()
    for pair, count in enumerate(counts):
        if count >= 2:
            reduced = counts.copy()
            reduced[pair] -= 2
            for groups in split(tuple(reduced)):
                decompositions.add(Decomposition(pair, groups))
    ordered = tuple(sorted(decompositions))
    return HandAnalysis(bool(ordered), ordered)
