"""Run the Dragon Nest Unique enhancement simulator with Python's built-in Tkinter."""

import random
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

from enhancement import RATES, Settings, enhance, outcome_chances


REFERENCE_URL = "https://www.rewindth.com/guides/enchant-rates"
OFFICIAL_URL = "https://seaclassic.dragonnest.com/news/notice/all/16"
BG = "#151923"
PANEL = "#202636"
TEXT = "#edf0f7"
MUTED = "#b6bfd2"
GOLD = "#e8c477"


class SimulatorApp:
    def __init__(self, root):
        self.root = root
        root.title("Dragon Nest | Unique Enhancement Simulator")
        root.geometry("1060x820")
        root.minsize(980, 760)
        root.configure(background=BG)
        self.rng = random.Random()
        self.level = 0
        self.attempts = self.successes = self.downgrades = self.protected = 0
        self.highest = 0
        self.running = False
        self.after_id = None
        self.start_var = tk.StringVar(value="0")
        self.target_var = tk.StringVar(value="12")
        self.limit_var = tk.StringVar(value="10000")
        self.jelly_var = tk.BooleanVar(value=True)
        self.drop_one_var = tk.StringVar(value="50")
        self.drop_two_var = tk.StringVar(value="50")
        self.level_var = tk.StringVar()
        self.odds_var = tk.StringVar()
        self.stats_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready. Enhance once or choose a target and start an auto run.")
        self._style()
        self._build()
        for variable in (self.jelly_var, self.drop_one_var, self.drop_two_var):
            variable.trace_add("write", lambda *_: self._refresh())
        root.protocol("WM_DELETE_WINDOW", self._close)
        self._refresh()

    def _style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), background=BG, foreground=TEXT)
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG)
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("Level.TLabel", font=("Segoe UI", 44, "bold"), foreground=GOLD)
        style.configure("TLabelframe", background=BG, bordercolor="#3c465c")
        style.configure("TLabelframe.Label", foreground=GOLD)
        style.configure("TButton", background=PANEL, padding=(14, 8), borderwidth=0)
        style.map("TButton", background=[("active", "#35415b")],
                  foreground=[("disabled", "#7f899f")])
        style.configure("Accent.TButton", background=GOLD, foreground=BG)
        style.map("Accent.TButton", background=[("active", "#f2d99d"), ("disabled", "#5c5649")])
        for kind in ("TEntry", "TCombobox", "TSpinbox"):
            style.configure(kind, fieldbackground=PANEL, foreground=TEXT, padding=5,
                            arrowcolor=TEXT, insertcolor=TEXT)
            style.map(kind, fieldbackground=[("readonly", PANEL), ("disabled", BG)],
                      foreground=[("readonly", TEXT), ("disabled", "#7f899f")])
        style.configure("TCheckbutton", background=BG, foreground=TEXT)
        style.map("TCheckbutton", background=[("active", BG)])
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, padding=(18, 9))
        style.map("TNotebook.Tab", background=[("selected", "#35415b")])
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                        foreground=TEXT, rowheight=27, borderwidth=0)
        style.configure("Treeview.Heading", background="#30394c", foreground=TEXT,
                        padding=6, font=("Segoe UI", 10, "bold"))
        self.root.option_add("*TCombobox*Listbox.background", PANEL)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)

    def _build(self):
        shell = ttk.Frame(self.root, padding=22)
        shell.pack(fill="both", expand=True)
        ttk.Label(shell, text="Unique Enhancement", style="Title.TLabel").pack(anchor="w")
        ttk.Label(shell, text="Dragon Nest • Dragon Unique / Sea Dragon reference preset",
                  style="Muted.TLabel").pack(anchor="w", pady=(3, 5))
        ttk.Label(shell, text="Rewind server rates. Exact official Classic SEA probabilities are unverified.",
                  foreground=GOLD).pack(anchor="w", pady=(0, 16))
        notebook = ttk.Notebook(shell)
        notebook.pack(fill="both", expand=True)
        simulation = ttk.Frame(notebook, padding=(0, 14))
        rules = ttk.Frame(notebook, padding=16)
        notebook.add(simulation, text="Simulator")
        notebook.add(rules, text="Rates & assumptions")
        self._build_simulator(simulation)
        self._build_rules(rules)

    def _build_simulator(self, frame):
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(4, weight=1)
        top = ttk.Frame(frame)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)
        item = ttk.Frame(top, padding=(10, 0, 30, 0))
        item.grid(row=0, column=0, sticky="nw")
        ttk.Label(item, text="CURRENT ITEM", style="Muted.TLabel").pack(anchor="w")
        ttk.Label(item, textvariable=self.level_var, style="Level.TLabel").pack(anchor="w")
        ttk.Label(item, text="+9 floor after reaching +9", style="Muted.TLabel").pack(anchor="w")

        controls = ttk.LabelFrame(top, text="Session", padding=12)
        controls.grid(row=0, column=1, sticky="nsew")
        ttk.Label(controls, text="Start level").grid(row=0, column=0, sticky="w")
        self.start_input = ttk.Combobox(controls, textvariable=self.start_var,
                                       values=list(range(16)), width=5, state="readonly")
        self.start_input.grid(row=0, column=1, padx=(8, 18))
        self.reset_button = ttk.Button(controls, text="New item / reset", command=self._reset)
        self.reset_button.grid(row=0, column=2, columnspan=2, sticky="ew")
        ttk.Label(controls, text="Auto target").grid(row=1, column=0, sticky="w", pady=12)
        self.target_input = ttk.Combobox(controls, textvariable=self.target_var,
                                        values=list(range(1, 16)), width=5, state="readonly")
        self.target_input.grid(row=1, column=1, padx=(8, 18))
        ttk.Label(controls, text="Attempt limit").grid(row=1, column=2, sticky="w")
        self.limit_input = ttk.Entry(controls, textvariable=self.limit_var, width=10)
        self.limit_input.grid(row=1, column=3, padx=(8, 0))
        self.jelly_input = ttk.Checkbutton(controls, text="Use Protection Magic Jelly (prevents destruction)",
                                           variable=self.jelly_var)
        self.jelly_input.grid(row=2, column=0, columnspan=4, sticky="w")

        assumptions = ttk.LabelFrame(frame, text="Unknown drop probabilities — adjustable assumptions", padding=12)
        assumptions.grid(row=1, column=0, sticky="ew", pady=(15, 10))
        ttk.Label(assumptions, text="Targets +8 / +9: chance of dropping 1 instead of 0").grid(row=0, column=0, sticky="w")
        self.drop_one_input = ttk.Spinbox(assumptions, from_=0, to=100, increment=5,
                                         textvariable=self.drop_one_var, width=6)
        self.drop_one_input.grid(row=0, column=1, padx=8)
        ttk.Label(assumptions, text="%").grid(row=0, column=2)
        ttk.Label(assumptions, text="Targets +14 / +15: chance of dropping 2 instead of 1").grid(row=1, column=0, sticky="w", pady=(7, 0))
        self.drop_two_input = ttk.Spinbox(assumptions, from_=0, to=100, increment=5,
                                         textvariable=self.drop_two_var, width=6)
        self.drop_two_input.grid(row=1, column=1, padx=8, pady=(7, 0))
        ttk.Label(assumptions, text="%").grid(row=1, column=2, pady=(7, 0))
        ttk.Label(assumptions, text="Applied only after failure when the item survives. Default 50% is an assumption.",
                  style="Muted.TLabel").grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))

        actions = ttk.Frame(frame)
        actions.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.enhance_button = ttk.Button(actions, text="Enhance once", style="Accent.TButton", command=self._enhance_once)
        self.enhance_button.pack(side="left")
        self.auto_button = ttk.Button(actions, text="Auto to target", command=self._start_auto)
        self.auto_button.pack(side="left", padx=10)
        self.stop_button = ttk.Button(actions, text="Stop", command=self._stop)
        self.stop_button.pack(side="left")
        summary = ttk.Frame(frame)
        summary.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(summary, textvariable=self.odds_var, foreground=GOLD).pack(anchor="w")
        ttk.Label(summary, textvariable=self.stats_var, style="Muted.TLabel").pack(anchor="w", pady=(7, 0))

        history_frame = ttk.Frame(frame)
        history_frame.grid(row=4, column=0, sticky="nsew")
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        columns = ("attempt", "before", "target", "outcome", "after", "jelly")
        self.history = ttk.Treeview(history_frame, columns=columns, show="headings", height=6)
        for column, title, width in zip(columns, ("Attempt", "From", "Target", "Outcome", "After", "Jelly"),
                                        (80, 80, 80, 260, 80, 100)):
            self.history.heading(column, text=title)
            self.history.column(column, width=width, anchor="center")
        self.history.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(history_frame, orient="vertical", command=self.history.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.history.configure(yscrollcommand=scroll.set)
        for name, color in (("success", "#9ee6b0"), ("downgrade", "#f0c278"), ("destroyed", "#ff9292")):
            self.history.tag_configure(name, foreground=color)
        ttk.Label(frame, text="History shows the latest 300 attempts. Counters include the whole session.",
                  style="Muted.TLabel").grid(row=5, column=0, sticky="w", pady=(6, 0))
        ttk.Label(frame, textvariable=self.status_var, wraplength=960).grid(row=6, column=0, sticky="w", pady=(10, 0))
        self.setting_widgets = (self.start_input, self.target_input, self.limit_input,
                                self.jelly_input, self.drop_one_input, self.drop_two_input)

    def _build_rules(self, frame):
        ttk.Label(frame, text="Dragon Unique reference rates", font=("Segoe UI", 15, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Rows name the target: +10 means attempting +9 → +10.",
                  style="Muted.TLabel").pack(anchor="w", pady=(5, 12))
        table = ttk.Treeview(frame, columns=("target", "success", "break", "drop"), show="headings", height=10)
        for column, heading in (("target", "Target"), ("success", "Success / attempt"),
                                ("break", "Break / failure, no jelly"), ("drop", "Drop if failure survives")):
            table.heading(column, text=heading)
            table.column(column, width=200, anchor="center")
        table.insert("", "end", values=("+1 to +6", "100%", "0%", "0"))
        for target in range(7, 16):
            rate = RATES[target]
            drop = str(rate.min_drop) if rate.min_drop == rate.max_drop else f"{rate.min_drop}–{rate.max_drop}"
            table.insert("", "end", values=(f"+{target}", f"{rate.success:.0%}",
                                           f"{rate.break_on_failure:.0%}", drop))
        table.pack(fill="x")
        notes = (
            "Each attempt checks success first. If it fails, an unprotected item may break. "
            "If it survives, the listed drop is applied to its current level.\n\n"
            "Break rates are conditional on failure. For example, +6 → +7 has a 35% failure rate "
            "and 20% break chance after failure: 7% destruction per unprotected attempt.\n\n"
            "A current level of +9 or higher never downgrades below +9. Jelly prevents destruction "
            "but still allows downgrades. At +15, enhancement stops.\n\n"
            "Rewind supplies the numeric rates and drop ranges for dragon Unique gear; these are "
            "not verified official Classic SEA rates. The chance of each value in a drop range is "
            "undisclosed. This app starts with a 50/50 split, which you can change.\n\n"
            "The official launch notes confirm guaranteed +1–6, a +15 maximum, the +9 floor and "
            "destruction protection. Jelly counts and material costs are not modeled."
        )
        ttk.Label(frame, text=notes, wraplength=900, justify="left").pack(anchor="w", pady=16)
        links = ttk.Frame(frame)
        links.pack(anchor="w")
        ttk.Button(links, text="Open Rewind reference", command=lambda: webbrowser.open(REFERENCE_URL)).pack(side="left")
        ttk.Button(links, text="Open official launch notes", command=lambda: webbrowser.open(OFFICIAL_URL)).pack(side="left", padx=10)

    def _settings(self):
        try:
            return Settings(jelly=self.jelly_var.get(),
                            drop_one_chance=float(self.drop_one_var.get()) / 100,
                            drop_two_chance=float(self.drop_two_var.get()) / 100)
        except (ValueError, tk.TclError) as error:
            raise ValueError("Enter a number from 0 to 100 for each assumed drop probability.") from error

    def _refresh(self):
        self.level_var.set("BROKEN" if self.level is None else f"+{self.level}")
        self.stats_var.set(f"Attempts {self.attempts:,}    Successes {self.successes:,}    "
                           f"Failures {self.attempts - self.successes:,}    Downgrades {self.downgrades:,}    "
                           f"Protected attempts {self.protected:,}    Best +{self.highest}")
        valid = True
        try:
            settings = self._settings()
        except ValueError as error:
            valid = False
            self.odds_var.set(str(error))
        if valid:
            if self.level is None:
                self.odds_var.set("Item destroyed. Start a new item to continue.")
            elif self.level == 15:
                self.odds_var.set("Maximum enhancement reached: +15.")
            else:
                odds = outcome_chances(self.level, settings)
                self.odds_var.set(f"Next +{self.level} → +{self.level + 1}   |   "
                                  f"Success {odds['success']:.1%}   Stay {odds['unchanged']:.1%}   "
                                  f"Downgrade {odds['downgrade']:.1%}   Break {odds['destroyed']:.1%}")
        ready = valid and self.level is not None and self.level < 15 and not self.running
        for button in (self.enhance_button, self.auto_button):
            button.configure(state="normal" if ready else "disabled")
        self.stop_button.configure(state="normal" if self.running else "disabled")
        self.reset_button.configure(state="disabled" if self.running else "normal")
        for widget in self.setting_widgets:
            state = "disabled" if self.running else ("readonly" if isinstance(widget, ttk.Combobox) else "normal")
            widget.configure(state=state)

    def _reset(self):
        self.level = int(self.start_var.get())
        self.attempts = self.successes = self.downgrades = self.protected = 0
        self.highest = self.level
        rows = self.history.get_children()
        if rows:
            self.history.delete(*rows)
        self.status_var.set(f"New item at +{self.level}. Session counters cleared.")
        self._refresh()

    def _attempt(self, settings):
        result = enhance(self.level, settings, self.rng)
        self.level = result.after
        self.attempts += 1
        self.successes += result.outcome == "success"
        self.downgrades += result.outcome == "downgrade"
        self.protected += result.protected
        if self.level is not None:
            self.highest = max(self.highest, self.level)
        labels = {"success": "Success", "unchanged": "Failed — level unchanged",
                  "downgrade": f"Failed — dropped {result.before - (result.after or 0)}",
                  "destroyed": "Destroyed"}
        after = "Broken" if result.after is None else f"+{result.after}"
        row = self.history.insert("", "end", values=(f"{self.attempts:,}", f"+{result.before}",
                                  f"+{result.target}", labels[result.outcome], after,
                                  "Protected" if result.protected else "—"), tags=(result.outcome,))
        rows = self.history.get_children()
        if len(rows) > 300:
            self.history.delete(*rows[:-300])
        self.history.see(row)
        return f"+{result.before} → +{result.target}: {labels[result.outcome]}. Item: {after}."

    def _enhance_once(self):
        try:
            self.status_var.set(self._attempt(self._settings()))
        except ValueError as error:
            messagebox.showerror("Check settings", str(error), parent=self.root)
        self._refresh()

    def _start_auto(self):
        try:
            self.auto_settings = self._settings()
            self.auto_target = int(self.target_var.get())
            self.auto_limit = int(self.limit_var.get())
            if not 1 <= self.auto_limit <= 1_000_000:
                raise ValueError("The auto attempt limit must be between 1 and 1,000,000.")
        except ValueError as error:
            messagebox.showerror("Check settings", str(error), parent=self.root)
            return
        if self.level is None or self.level >= self.auto_target:
            self.status_var.set("Choose a target above the current level, or start a new item.")
            return
        self.auto_count = 0
        self.running = True
        self._refresh()
        self.after_id = self.root.after(15, self._auto_tick)

    def _auto_tick(self):
        self.after_id = None
        if not self.running:
            return
        for _ in range(20):
            self._attempt(self.auto_settings)
            self.auto_count += 1
            if self.level is None:
                self._stop(f"Auto stopped: item destroyed after {self.auto_count:,} auto attempts.")
                return
            if self.level >= self.auto_target:
                self._stop(f"Reached +{self.auto_target} after {self.auto_count:,} auto attempts!")
                return
            if self.auto_count >= self.auto_limit:
                self._stop(f"Attempt limit reached ({self.auto_limit:,}). Item is at +{self.level}; target was +{self.auto_target}.")
                return
        self.status_var.set(f"Auto running: {self.auto_count:,} / {self.auto_limit:,} attempts, aiming for +{self.auto_target}.")
        self._refresh()
        self.after_id = self.root.after(15, self._auto_tick)

    def _stop(self, message=None):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.running = False
        self.status_var.set(message or "Auto run stopped. You can continue with this item.")
        self._refresh()

    def _close(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
        self.root.destroy()


def main():
    root = tk.Tk()
    SimulatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
