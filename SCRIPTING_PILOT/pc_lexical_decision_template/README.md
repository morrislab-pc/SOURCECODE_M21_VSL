# m21 lexical decision: first PsychoPy translation

This is a specific, unprimed lexical decision paradigm, based on the active execution paths of the two supplied OpenSesame 3.3.11 files. It is a first translation for pilot testing, not a hardware-validated replacement for data collection.

## Files you edit

- `stimuli_ab.csv` / `stimuli_ba.csv`: the complete embedded 300-trial lists, extracted without changing targets, condition labels, correct responses, item codes, or ITIs.
- `config_ab.json` / `config_ba.json`: study settings, display, timing, keys, breaks and serial trigger settings.
- `lexical_decision.py`: the fixed trial sequence. Future studies normally change a CSV and configuration, rather than this file.
- `ab_ba_differences.csv`: all 100 target differences between versions. Response mapping is identical; AB/BA is not a response-key reversal in these files.

## Starting without learning Builder

Install PsychoPy Standalone on your pilot computer. Open `lexical_decision.py` in its Coder editor and run it: defaults are the AB list, participant `pilot`, a new random seed, windowed presentation, and mock triggers. This uses the code editor only; no Builder experiment is needed. Keep the complete folder together. Escape aborts and saves completed trials.

Alternatively, in a Python environment containing PsychoPy and its dependencies:

```bash
python lexical_decision.py --config config_ab.json --participant pilot --seed 12345 --limit 12
python lexical_decision.py --config config_ba.json --participant pilot --seed 12345 --limit 12
```

Do not assume a terminal's ordinary Python is the interpreter bundled with PsychoPy Standalone. For the simplest initial pilot use Coder. To select BA there, change the default configuration filename at the `--config` line, or run with arguments through your configured Python environment.

Validation does not require PsychoPy:

```bash
python lexical_decision.py --config config_ab.json --validate-only --seed 12345
python lexical_decision.py --config config_ba.json --validate-only --seed 12345
```

Mock mode sends no hardware signals, but retains the trigger pulse waits. For EEG piloting, set `triggers.mode` to `serial` and verify the port name. The source uses COM4, 115200 baud, 8 data bits, no parity, one stop bit, and raw single-byte codes. Serial mode requires pyserial. Serial failures raise an error rather than silently permitting a run without markers. This reproduces the software protocol; the attached device's identity and actual EEG behavior cannot be established from these files.

## Source trial sequence

| OpenSesame item | Script behavior |
| --- | --- |
| inc_counter | Increment trial number |
| fixation_1 | White cross, half-length 21 pixels, 497 ms |
| blank_screen | Black display, 497 ms |
| target_present | White uppercase target on black, remains visible |
| cond_trigger | Condition byte, wait 10 ms, zero byte, wait 10 ms |
| word_trigger | Item byte, wait 10 ms, zero byte, wait 10 ms |
| new_keyboard_response_1 | Flush keys; collect first allowed key, timeout 1200 ms |
| response_trigger_trial | 220 correct; 221 incorrect OR timeout; same pulse/reset waits |
| responsescreen | Remove target; black display for 600 ms |
| blink_screen | Show (--) for 1500 ms every third trial |
| ITI | Black display, row-specific 200–400 ms |
| break1 / break2 / break3_1 | Self-paced breaks after 75, 150, 225 trials |
| logger | Save trial fields and timing |

The source has one globally shuffled 300-trial loop, with breaks every 75 trials. It does not shuffle separately within predefined blocks. The translated script likewise shuffles the whole list once.

## Conditions and responses

| Label | Condition byte | Trials per version | Source correct key |
| --- | --- | --- | --- |
| CW_S | 201 | 50 | / |
| CW_L | 202 | 50 | / |
| NW_S_COMP | 203 | 25 | z |
| NW_L_COMP | 204 | 25 | z |
| NW_S_SIMP | 205 | 25 | z |
| NW_L_SIMP | 206 | 25 | z |
| FILL_W | 207 | 50 | / |
| FILL_NW | 208 | 50 | z |

The CSV preserves OpenSesame's `/`; the default configuration maps this to PsychoPy's `slash` key name. Both versions use the same keys. Their instructions describe a joystick, but the active response item reads keyboard events. A joystick/response box must therefore provide compatible key events for this translation; test both physical buttons before piloting.

## Timing detail that needs your attention

The source `target_present` has duration zero, which returns immediately after drawing; it does not erase the target. The next display-changing item is `responsescreen`, after response collection AND the response trigger. Consequently target duration is variable, and includes trigger delays.

Both target trigger routines run sequentially after target onset. With successful writes the nominal waits total 40 ms before the keyboard item starts; responses during this interval are flushed. Its 1200 ms timeout and reported RT begin at response collection, rather than precisely at target onset. This translation deliberately retains that delayed response gate for the first comparison.

The translation saves both `rt_from_response_window_ms` and `rt_from_target_ms`, along with target onset, response-window onset, target offset, and every serial write timestamp. The latter RT is reconstructed from the key's response-window RT and the measured gate offset; very small clock-reset overhead remains. Onset timestamps are software screen-flip timestamps, not photodiode measurements. Serial write timestamps indicate host write calls, not the instant the EEG hardware registered a marker. Condition and item markers are intentionally distinct: the item marker comes after the condition pulse and reset gap.

For a future revised paradigm we can start response recording at target onset and synchronize the first marker using `callOnFlip`, but that should be an explicit timing revision with its own validation and Git version. It is not silently applied here.

Display waits are synchronized to subsequent screen flips and approximate the requested milliseconds within refresh-cycle constraints. 497 ms will often become about 500 ms at 60 Hz; it cannot be exactly represented on every monitor. The script measures refresh rate and stops if a stable estimate cannot be obtained. Target on/off and major trial onsets are logged so actual intervals can be checked. There is no claim of dropped-frame or physical display timing validation.

## Deliberate implementation differences

- Use raw `bytes([code])` for serial writes, with explicit error handling and cleanup.
- Save completed trials before breaks; source logger ran after breaks.
- Replace long HTML instruction strings with plain text carrying the same task rules; break wording is simplified. Any key continues, as in the source sketchpads, even though original break text requests space.
- Use Courier New at 18-pixel text height as an initial approximation to OpenSesame `mono`, size 18. Font metrics and actual retinal stimulus size must be compared on the lab monitor.
- New keyboard API rather than OpenSesame legacy keyboard. Input latency equivalence must be measured.
- Omit unexecuted items, including coroutines, old parallel-port code, and unused canvas/log scripts. The 1000 vs 1500 ms coroutine difference is inactive. AB opens serial in prepare; BA opens it in run; both active protocols are the same. The translation initializes once before instructions.
- Correctly close serial on exit. Source `close_port` merely appends a cleanup callback a second time.

A fixed-duration target is not a setting in this particular template because the source is response-terminated. A study that needs a fixed target duration deserves a deliberate change to its trial sequence.

## What every run saves

A unique folder under `data/` holds behavioral CSV, event CSV, shuffled trial-order CSV, exact configuration, full stimulus list, exact script, and run metadata. Metadata includes participant, seed, trial limit, PsychoPy/Python/OS versions, measured refresh rate, source hashes, Git commit and dirty-state flag when available, completion count, and completion/abort/error status. A source hash manifest accompanies the template. Keep participant data outside the experiment's Git repository; `.gitignore` excludes `data/`.

## Validation completed here and still needed

The extracted CSVs were compared field by field with their source setcycle tables. All 300 rows per file, eight condition counts, 100 AB/BA differences, keys, condition/item codes, and ITIs were verified. Both configuration/list combinations passed command-line validation, and the Python script passed compilation. A simulated execution checks the sequence, response scoring, timeout, and trigger order; it is not a display/hardware test.

Before collecting EEG: pilot on the actual Windows presentation computer; verify response-box key names; compare font size/position and full-screen resolution; inspect target duration and response-gate times; record every condition/item/response code in BrainVision; and measure marker-to-light timing with a photodiode. Decide whether preserving the original delayed response gate is appropriate for the study before accepting the replacement.

Official API references:
- https://psychopy.org/api/hardware/keyboard.html
- https://psychopy.org/api/visual/window.html
