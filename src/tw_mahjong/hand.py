"""Exhaustive, canonical five-meld-and-pair decomposition (SPEC HAND)."""

from functools import lru_cache

from .model import Decomposition, HandAnalysis, MahjongError, Meld, Tile


def _validate_hand(hand: tuple[Tile, ...], melds: tuple[Meld, ...], total: int) -> list[int]:
    """Validate a physical hand and return its concealed tile-kind counts."""
    if not isinstance(melds, tuple) or len(melds) > 5:
        raise MahjongError("INVALID_MELD", "Expected at most five melds")

    for meld in melds:
        if not isinstance(meld, Meld):
            raise MahjongError("INVALID_MELD", "Expected Meld values")
        meld.__post_init__()

    if not isinstance(hand, tuple) or not all(
        isinstance(t, Tile) and not t.is_flower for t in hand
    ):
        raise MahjongError("INVALID_HAND", "Hand requires ordinary physical tiles")
    if len(hand) != total - 3 * len(melds):
        raise MahjongError("INVALID_HAND", "Wrong concealed tile count for meld count")

    # Include melds when checking ownership; a physical tile cannot appear twice.
    tiles = hand + tuple(t for meld in melds for t in meld.tiles)
    if len({t.id for t in tiles}) != len(tiles):
        raise MahjongError("INVALID_HAND", "Duplicate physical tile across hand and melds")

    counts = [0] * 34
    for tile in hand:
        counts[tile.kind] += 1
    return counts


def find_waits(hand: tuple[Tile, ...], melds: tuple[Meld, ...] = ()) -> tuple[int, ...]:
    """List winning tile kinds without estimating opponents' holdings."""
    _validate_hand(hand, melds, 16)

    used = {tile.id for tile in hand}
    used.update(tile.id for meld in melds for tile in meld.tiles)

    # Pick any unused physical copy of each kind to avoid inventing a fifth copy.
    waits = []
    for kind in range(34):
        candidate = next(
            (Tile(i) for i in range(kind * 4, kind * 4 + 4) if i not in used),
            None,
        )
        if candidate is not None and analyze_hand(hand + (candidate,), melds).winning:
            waits.append(kind)

    return tuple(waits)


def analyze_hand(hand: tuple[Tile, ...], melds: tuple[Meld, ...] = ()) -> HandAnalysis:
    """Enumerate every unique five-meld-and-pair decomposition."""
    counts = _validate_hand(hand, melds, 17)

    @lru_cache(maxsize=None)
    def split(remaining: tuple[int, ...]) -> tuple[tuple[tuple[int, int, int], ...], ...]:
        first = next((i for i, count in enumerate(remaining) if count), None)
        if first is None:
            return ((),)

        # Explore both triplet and sequence choices for the smallest tile kind.
        possibilities = []
        if remaining[first] >= 3:
            possibilities.append((first, first, first))
        if (
            first < 27
            and first % 9 <= 6
            and remaining[first + 1]
            and remaining[first + 2]
        ):
            possibilities.append((first, first + 1, first + 2))

        results = set()
        for group in possibilities:
            reduced = list(remaining)
            for kind in group:
                reduced[kind] -= 1
            for tail in split(tuple(reduced)):
                results.add(tuple(sorted((group,) + tail)))

        return tuple(sorted(results))

    # Reserve the pair first, then split all remaining concealed tiles.
    decompositions = set()
    for pair, count in enumerate(counts):
        if count >= 2:
            reduced = counts.copy()
            reduced[pair] -= 2
            for groups in split(tuple(reduced)):
                decompositions.add(Decomposition(pair, groups))

    ordered = tuple(sorted(decompositions))
    return HandAnalysis(bool(ordered), ordered)
