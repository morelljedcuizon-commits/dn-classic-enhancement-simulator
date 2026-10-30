# Dragon Nest Unique Enhancement Simulator

A small Python desktop application for simulating dragon Unique equipment, including Sea Dragon gear. Uses only the Python standard library (Tkinter); no pip packages required.

## Run

Install Python 3.10 or newer with Tkinter (included in the standard Windows installer), then double-click **run_simulator.bat**, or run `python main.py` from this folder. No extra packages are needed. On Linux, your distribution may package Tkinter separately as `python3-tk`; launch with `python3 main.py`.

The Windows launcher checks the usual per-user Python 3.14 installation first, then uses `python` from PATH. Restart your IDE/terminal after installing Python so it picks up the new PATH.

Choose a starting level and click **New item / reset**. Use **Enhance once**, or choose a target and click **Auto to target**. Automatic runs stop at the target, destruction, the attempt limit, or **Stop**. A destroyed item must be replaced explicitly with **New item / reset**. Reset clears the session history and counters.

Protection Magic Jelly is enabled by default. It blocks destruction while allowing downgrades. Protected attempts count attempts with jelly at target +7 or above, not individual jellies consumed. Material and gold costs are not simulated.

## Sources and limitations

Sources checked on October 29, 2026:

- [Official Classic SEA launch notes, March 20, 2025](https://seaclassic.dragonnest.com/news/notice/all/16): guaranteed enhancement through +6, maximum +15, a +9 floor, destruction risk afterward, and jelly protection. These notes do not disclose exact success, destruction or downgrade probabilities for Unique equipment.
- [Rewind of Dragon enhancement guide](https://www.rewindth.com/guides/enchant-rates): the numeric reference preset for dragon Unique gear below. **Rewind is a separate server. Its probabilities are not verified official Classic SEA rates**, and should not be assumed to apply to every Unique set.

Rows use the **target level**: the +10 row means attempting +9 to +10. Drop amounts are subtracted from the current level after a surviving failure.

| Target | Success per attempt | Destruction after failure, without jelly | Drop on surviving failure |
| --- | ---: | ---: | --- |
| +1–6 | 100% | 0% | 0 |
| +7 | 65% | 20% | 0 |
| +8 | 50% | 20% | 0–1 |
| +9 | 45% | 20% | 0–1 |
| +10 | 40% | 25% | 0 |
| +11 | 30% | 25% | 1 |
| +12 | 20% | 25% | 1 |
| +13 | 15% | 25% | 1 |
| +14 | 5% | 25% | 1–2 |
| +15 | 1% | 25% | 1–2 |

The guide supplies drop ranges, **not the probability of each value within a range**. The simulator assumes a 50% chance of 1 versus 0 at targets +8/+9 and a 50% chance of 2 versus 1 at targets +14/+15. Both assumptions can be adjusted from 0% to 100% in the app. Fixed drops need no extra probability roll.

Each attempt rolls success, then destruction if it failed and has no jelly, then the drop if it survives. For example, +6 to +7 has a 35% failure chance and a 20% conditional destruction chance: 7% destruction per unprotected attempt. The displayed next-attempt odds are unconditional probabilities under the current settings.

The floor applies when the item is **already +9 or higher**. An unsuccessful +8 to +9 attempt may still drop to +7 under this preset. Reaching +9 does not protect an unjellied item from destruction.

## Development

- `main.py`: desktop interface, bounded automatic runs, and session history.
- `enhancement.py`: rates, probability calculations, and simulation rules.
- `test_enhancement.py`: deterministic checks for probability boundaries and enhancement behavior.
- `test_gui.py`: hidden-window checks for session controls and automatic stopping.

Run all 21 checks with `python -m unittest -v` (requires a desktop environment for Tkinter). For just the probability engine, use `python -m unittest -v test_enhancement`.
