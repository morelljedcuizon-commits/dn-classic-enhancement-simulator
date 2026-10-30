"""Hidden-window integration checks. Run explicitly with python -m unittest test_gui."""

import tkinter as tk
import unittest
from unittest.mock import patch

from main import SimulatorApp
from test_enhancement import ScriptedRandom


class GuiTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = SimulatorApp(self.root)

    def tearDown(self):
        self.app._close()

    def reset_at(self, level):
        self.app.start_var.set(str(level))
        self.app._reset()

    def run_auto_tick(self):
        self.root.after_cancel(self.app.after_id)
        self.app.after_id = None
        self.app._auto_tick()

    def test_manual_attempt_updates_session_and_reset_clears_it(self):
        self.app._enhance_once()
        self.assertEqual((self.app.level, self.app.attempts, self.app.successes), (1, 1, 1))
        self.assertEqual(len(self.app.history.get_children()), 1)
        self.reset_at(6)
        self.assertEqual((self.app.level, self.app.attempts, self.app.highest), (6, 0, 6))
        self.assertFalse(self.app.history.get_children())

    def test_auto_stops_when_target_is_reached(self):
        self.app.target_var.set("6")
        self.app._start_auto()
        self.run_auto_tick()
        self.assertFalse(self.app.running)
        self.assertEqual((self.app.level, self.app.attempts), (6, 6))
        self.assertIn("Reached +6", self.app.status_var.get())

    def test_auto_stops_at_limit(self):
        self.reset_at(9)
        self.app.rng = ScriptedRandom(0.99, 0.99, 0.99)
        self.app.target_var.set("15")
        self.app.limit_var.set("3")
        self.app._start_auto()
        self.run_auto_tick()
        self.assertFalse(self.app.running)
        self.assertEqual((self.app.level, self.app.attempts, self.app.protected), (9, 3, 3))
        self.assertIn("Attempt limit reached", self.app.status_var.get())

    def test_auto_stops_on_destruction(self):
        self.reset_at(6)
        self.app.jelly_var.set(False)
        self.app.rng = ScriptedRandom(0.99, 0.01)
        self.app._start_auto()
        self.run_auto_tick()
        self.assertIsNone(self.app.level)
        self.assertFalse(self.app.running)
        self.assertEqual(str(self.app.enhance_button.cget("state")), "disabled")
        self.assertEqual(self.app.attempts, 1)

    def test_stop_cancels_pending_attempts(self):
        self.app._start_auto()
        self.app._stop()
        self.root.update()
        self.assertFalse(self.app.running)
        self.assertIsNone(self.app.after_id)
        self.assertEqual(self.app.attempts, 0)

    def test_invalid_settings_and_max_level_disable_attempts(self):
        for value in ("", "nan", "101", "-1"):
            self.app.drop_one_var.set(value)
            self.assertEqual(str(self.app.enhance_button.cget("state")), "disabled")
        self.app.drop_one_var.set("50")
        self.reset_at(15)
        self.assertEqual(str(self.app.enhance_button.cget("state")), "disabled")

    def test_invalid_limit_does_not_start_an_auto_run(self):
        self.app.limit_var.set("abc")
        with patch("main.messagebox.showerror") as dialog:
            self.app._start_auto()
        dialog.assert_called_once()
        self.assertFalse(self.app.running)
        self.assertEqual(self.app.attempts, 0)


if __name__ == "__main__":
    unittest.main()
