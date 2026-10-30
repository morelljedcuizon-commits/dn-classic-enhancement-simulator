"""Dragon Unique enhancement using the Rewind reference preset.

Source: https://www.rewindth.com/guides/enchant-rates
These are not verified official Dragon Nest Classic SEA rates. Break rates
are conditional on failure. The source gives drop ranges, not their weights;
Settings exposes those unknown weights and defaults to an assumed 50/50 split.
"""

from dataclasses import dataclass
import math
from numbers import Real
import random


@dataclass(frozen=True)
class Rate:
    success: float
    break_on_failure: float
    min_drop: int
    max_drop: int


# Keys are TARGET levels: RATES[8] describes an attempt from +7 to +8.
RATES: dict[int, Rate] = {
    **{target: Rate(1.0, 0.0, 0, 0) for target in range(1, 7)},
    7: Rate(0.65, 0.20, 0, 0),
    8: Rate(0.50, 0.20, 0, 1),
    9: Rate(0.45, 0.20, 0, 1),
    10: Rate(0.40, 0.25, 0, 0),
    11: Rate(0.30, 0.25, 1, 1),
    12: Rate(0.20, 0.25, 1, 1),
    13: Rate(0.15, 0.25, 1, 1),
    14: Rate(0.05, 0.25, 1, 2),
    15: Rate(0.01, 0.25, 1, 2),
}


@dataclass(frozen=True)
class Settings:
    jelly: bool = True
    drop_one_chance: float = 0.5
    drop_two_chance: float = 0.5

    def __post_init__(self) -> None:
        if not isinstance(self.jelly, bool):
            raise ValueError("jelly must be True or False")
        for name in ("drop_one_chance", "drop_two_chance"):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, Real)
                or not math.isfinite(value)
                or not 0 <= value <= 1
            ):
                raise ValueError(f"{name} must be a finite probability from 0 to 1")


@dataclass(frozen=True)
class Attempt:
    before: int
    target: int
    after: int | None
    outcome: str
    protected: bool


def _rate_for(level: int) -> Rate:
    if isinstance(level, bool) or not isinstance(level, int) or not 0 <= level <= 14:
        raise ValueError("Current level must be an integer from 0 to 14")
    return RATES[level + 1]


def _max_drop_chance(rate: Rate, settings: Settings) -> float:
    """Probability of the larger drop in one of the preset's two ranges."""
    return settings.drop_one_chance if rate.min_drop == 0 else settings.drop_two_chance


def _level_after_drop(level: int, drop: int) -> int:
    # The +9 floor starts once the item is +9, not while attempting +9.
    return max(9 if level >= 9 else 0, level - drop)


def enhance(level: int, settings: Settings, rng: random.Random) -> Attempt:
    """Attempt one enhancement; destroyed equipment has after=None."""
    rate = _rate_for(level)
    target = level + 1
    protected = settings.jelly and target >= 7

    if rng.random() < rate.success:
        return Attempt(level, target, target, "success", protected)

    if not protected and rng.random() < rate.break_on_failure:
        return Attempt(level, target, None, "destroyed", protected)

    drop = rate.min_drop
    if rate.min_drop != rate.max_drop and rng.random() < _max_drop_chance(rate, settings):
        drop = rate.max_drop
    after = _level_after_drop(level, drop)
    outcome = "unchanged" if after == level else "downgrade"
    return Attempt(level, target, after, outcome, protected)


def outcome_chances(level: int, settings: Settings) -> dict[str, float]:
    """Return unconditional probabilities for the next attempt's outcomes."""
    rate = _rate_for(level)
    failure = 1.0 - rate.success
    break_chance = 0.0 if settings.jelly else rate.break_on_failure
    surviving_failure = failure * (1.0 - break_chance)
    chances = {
        "success": rate.success,
        "unchanged": 0.0,
        "downgrade": 0.0,
        "destroyed": failure * break_chance,
    }
    if rate.min_drop == rate.max_drop:
        drops = ((rate.min_drop, 1.0),)
    else:
        maximum_chance = _max_drop_chance(rate, settings)
        drops = ((rate.min_drop, 1.0 - maximum_chance), (rate.max_drop, maximum_chance))
    for drop, probability in drops:
        after = _level_after_drop(level, drop)
        outcome = "unchanged" if after == level else "downgrade"
        chances[outcome] += surviving_failure * probability
    return chances
