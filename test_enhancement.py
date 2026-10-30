"""Deterministic checks of enhancement rules and displayed probabilities."""

import random
import unittest

from enhancement import RATES, Settings, enhance, outcome_chances


class ScriptedRandom(random.Random):
    """Supply precise rolls; an unexpected extra roll fails the test."""

    def __init__(self, *rolls: float):
        self.rolls = iter(rolls)

    def random(self) -> float:
        return next(self.rolls)


class EnhancementTests(unittest.TestCase):
    def test_safe_levels_always_succeed_without_protection(self):
        for level in range(6):
            for jelly in (False, True):
                with self.subTest(level=level, jelly=jelly):
                    attempt = enhance(level, Settings(jelly=jelly), ScriptedRandom(0.999999))
                    self.assertEqual(attempt.after, level + 1)
                    self.assertEqual(attempt.outcome, "success")
                    self.assertFalse(attempt.protected)
                    self.assertEqual(outcome_chances(level, Settings(jelly=jelly))["success"], 1)

    def test_target_level_selects_the_rate(self):
        # 0.60 succeeds at +6 -> +7 (65%) but fails at +7 -> +8 (50%).
        success = enhance(6, Settings(), ScriptedRandom(0.60))
        failure = enhance(7, Settings(drop_one_chance=0), ScriptedRandom(0.60, 0.4))
        self.assertEqual((success.target, success.after), (7, 7))
        self.assertEqual((failure.target, failure.after), (8, 7))
        self.assertEqual(failure.outcome, "unchanged")

    def test_success_threshold_is_exclusive(self):
        self.assertEqual(enhance(6, Settings(), ScriptedRandom(0.649999)).outcome, "success")
        self.assertEqual(enhance(6, Settings(), ScriptedRandom(0.65)).outcome, "unchanged")

    def test_break_is_conditional_on_failure(self):
        settings = Settings(jelly=False)
        # A successful roll never consumes a destruction roll.
        self.assertEqual(enhance(6, settings, ScriptedRandom(0.1)).outcome, "success")
        broken = enhance(6, settings, ScriptedRandom(0.9, 0.199999))
        survived = enhance(6, settings, ScriptedRandom(0.9, 0.20))
        self.assertEqual(broken.outcome, "destroyed")
        self.assertIsNone(broken.after)
        self.assertFalse(broken.protected)
        self.assertEqual(survived.outcome, "unchanged")
        self.assertAlmostEqual(outcome_chances(6, settings)["destroyed"], 0.07)

    def test_jelly_prevents_break_but_not_downgrade(self):
        attempt = enhance(10, Settings(), ScriptedRandom(0.99))
        self.assertEqual((attempt.outcome, attempt.after), ("downgrade", 9))
        self.assertTrue(attempt.protected)
        for level in range(15):
            self.assertEqual(outcome_chances(level, Settings())["destroyed"], 0)

    def test_floor_applies_to_current_level(self):
        below_floor = enhance(8, Settings(drop_one_chance=1), ScriptedRandom(0.99, 0.99))
        at_floor = enhance(9, Settings(), ScriptedRandom(0.99))
        above_floor = enhance(10, Settings(), ScriptedRandom(0.99))
        self.assertEqual((below_floor.target, below_floor.after), (9, 7))
        self.assertEqual((at_floor.outcome, at_floor.after), ("unchanged", 9))
        self.assertEqual(above_floor.after, 9)
        self.assertAlmostEqual(outcome_chances(9, Settings())["unchanged"], 0.6)
        self.assertEqual(outcome_chances(9, Settings())["downgrade"], 0)

    def test_zero_or_one_drop_weights_can_be_zero_or_one(self):
        for level in (7, 8):
            no_drop = enhance(level, Settings(drop_one_chance=0), ScriptedRandom(0.99, 0.0))
            one_drop = enhance(level, Settings(drop_one_chance=1), ScriptedRandom(0.99, 0.999999))
            self.assertEqual(no_drop.after, level)
            self.assertEqual(one_drop.after, level - 1)
            self.assertEqual(outcome_chances(level, Settings(drop_one_chance=0))["downgrade"], 0)
            self.assertEqual(outcome_chances(level, Settings(drop_one_chance=1))["unchanged"], 0)

    def test_one_or_two_drop_weights_can_be_zero_or_one(self):
        for level in (13, 14):
            one_drop = enhance(level, Settings(drop_two_chance=0), ScriptedRandom(0.99, 0.0))
            two_drop = enhance(level, Settings(drop_two_chance=1), ScriptedRandom(0.99, 0.999999))
            self.assertEqual(one_drop.after, level - 1)
            self.assertEqual(two_drop.after, level - 2)

    def test_configured_distribution_threshold(self):
        settings = Settings(drop_one_chance=0.2, drop_two_chance=0.8)
        self.assertEqual(enhance(7, settings, ScriptedRandom(0.99, 0.199999)).after, 6)
        self.assertEqual(enhance(7, settings, ScriptedRandom(0.99, 0.2)).after, 7)
        self.assertEqual(enhance(13, settings, ScriptedRandom(0.99, 0.799999)).after, 11)
        self.assertEqual(enhance(13, settings, ScriptedRandom(0.99, 0.8)).after, 12)

    def test_unconditional_probabilities_at_plus_seven(self):
        chances = outcome_chances(7, Settings(jelly=False, drop_one_chance=0.25))
        expected = {"success": 0.50, "destroyed": 0.10, "unchanged": 0.30, "downgrade": 0.10}
        for outcome, probability in expected.items():
            self.assertAlmostEqual(chances[outcome], probability)

    def test_probabilities_sum_to_one_for_all_levels_and_settings(self):
        for level in range(15):
            for jelly in (False, True):
                for weight in (0, 0.37, 1):
                    chances = outcome_chances(level, Settings(jelly, weight, 1 - weight))
                    self.assertEqual(set(chances), {"success", "unchanged", "downgrade", "destroyed"})
                    self.assertAlmostEqual(sum(chances.values()), 1)
                    self.assertTrue(all(0 <= chance <= 1 for chance in chances.values()))

    def test_surviving_failures_stay_within_the_documented_range(self):
        for level in range(6, 15):
            rate = RATES[level + 1]
            for weight in (0, 1):
                attempt = enhance(level, Settings(True, weight, weight), ScriptedRandom(0.999999, 0.5))
                expected_drop = rate.min_drop if weight == 0 else rate.max_drop
                self.assertEqual(attempt.after, max(9 if level >= 9 else 0, level - expected_drop))

    def test_invalid_current_levels_are_rejected(self):
        for level in (-1, 15, 100, 7.0, "7", None, True):
            with self.subTest(level=level):
                with self.assertRaises(ValueError):
                    enhance(level, Settings(), ScriptedRandom())
                with self.assertRaises(ValueError):
                    outcome_chances(level, Settings())

    def test_invalid_settings_are_rejected(self):
        for name in ("drop_one_chance", "drop_two_chance"):
            for value in (-0.01, 1.01, float("nan"), float("inf"), float("-inf"), "0.5", None, True):
                with self.subTest(name=name, value=value):
                    with self.assertRaises(ValueError):
                        Settings(**{name: value})
        with self.assertRaises(ValueError):
            Settings(jelly="yes")


if __name__ == "__main__":
    unittest.main()
