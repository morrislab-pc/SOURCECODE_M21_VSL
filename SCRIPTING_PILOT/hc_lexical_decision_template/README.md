# Hampshire m21 lexical decision: PsychoPy template

A separate paradigm script translated from FIN__AB__M21__7_10_17.osexp and FIN__BA__M21__7_10_17.osexp. This template follows the HC configuration, rather than the sequential PC trial. It is ready for pilot testing; it has not been validated on a display, response box, or EEG system.

## Getting started

Unzip and keep the folder together. Install PsychoPy Standalone, open `lexical_decision.py` in Coder, and run. Defaults: AB stimuli, participant `pilot`, windowed display, mock triggers, and a new random seed. Escape aborts while preserving completed trials.

From an environment containing PsychoPy and its dependencies:

```bash
python lexical_decision.py --config config_ab.json --participant pilot --limit 12 --seed 12345
python lexical_decision.py --config config_ba.json --participant pilot --limit 12 --seed 12345
```

The ordinary terminal Python may differ from the interpreter in PsychoPy Standalone. Coder is the simplest initial route. To try BA in Coder, change the default filename in the script's `--config` definition to `config_ba.json`.

Configuration/list validation requires only Python's standard library:

```bash
python lexical_decision.py --config config_ab.json --validate-only
python lexical_decision.py --config config_ba.json --validate-only
```

## Files to edit for a study

- `stimuli_ab.csv` / `stimuli_ba.csv`: all 300 rows extracted exactly from each HC source.
- `config_ab.json` / `config_ba.json`: timing, display, response keys, and hardware settings.
- `lexical_decision.py`: fixed HC trial sequence, with comments explaining the source correspondence.
- `source_manifest.json`: SHA-256 hashes of the original HC files.

AB preserves **ADOPTISH**, the HC stimulus, rather than PC's ADOPTILP. Both lists use `/` for words and `z` for nonwords. The template maps `/` to PsychoPy `slash`. Original instructions described top/bottom joystick buttons; the actual source collected keyboard events. Check the physical response device generates the configured key names.

## HC sequence retained

| Stage | Behavior |
| --- | --- |
| Fixation | White cross, half-length 21 pixels, 497 ms requested |
| Pretarget blank | Black screen, 497 ms requested |
| Condition marker | Write row's 201–208 code before target presentation |
| Target onset | Show uppercase target and start response clock on the flip |
| Target offset | Replace target with blank at requested 395 ms, rounded to display frames |
| Remaining response window | Continue collecting first allowed response until requested 1000 ms from target onset |
| Scoring marker | At window end, write 220 correct or 221 incorrect/timeout |
| Duplicate correct write | Correct trials write 220 a second time, matching HC's two active routines |
| Blink prompt | (--) for 1500 ms every third trial |
| ITI | Black screen for the row's 200–400 ms |
| Item marker | Write row's 1–50 item code after ITI |
| Break | Self-paced after trials 75, 150, and 225 |
| End | Thank-you screen |

Early responses do not shorten target exposure or the trial. At a measured 60 Hz, 395 ms rounds to 24 frames (400 ms), and 1000 ms rounds to 60 frames. The nominal blank portion of the response window is then 600 ms. At other refresh rates frame counts and nominal durations differ and are recorded. A dropped frame can extend actual exposure/window duration; the script records onset/offset times, dropped-frame counts, and frame intervals.

The HC source puts `responsescreen` at 395 ms inside a 1000 ms coroutine. Its ordinary sketchpad duration of 600 ms is not an additional wait after that coroutine; it is therefore not added as another postresponse blank here. The coroutine's scheduled end governs the response interval. This is a translation of the supplied schedule, not a measurement of the historical run.

## Condition trigger and source-code issue

HC runs `def_chain` before the coroutine. Its `cond_trigger()` expression evaluates immediately there, before the target, rather than attaching a deferred callable. This template explicitly writes the condition code before target onset, preserving that order. It does not copy the broken function-wrapping expression. The elapsed marker-to-target interval in PsychoPy will not necessarily equal historical OpenSesame's interval. Hardware timing must be measured.

If you prefer a future target-onset marker, that is an intentional revision: place the condition write on the target flip and validate it separately. No such revision is silently included here.

## Parallel-port triggers

Default mode is `mock`: no hardware access. To test a compatible parallel-port system, change `triggers.mode` to `parallel` and check `parallel_address`. The HC address is `0x1FF0`; it is machine-specific, not a universal default. PsychoPy's ParallelPort class supports Windows/Linux with an appropriate installed driver and port. It is not a COM4 serial connection.

Within trials the template sends raw latched codes, with no zero resets and no 10 ms pulse waits, as in HC. Correct trials write 220 twice; whether the EEG interface records one or two events must be checked. For setup/cleanup it sets the port to zero; this is an explicit implementation difference from HC's routines.

The raw parallel write method is deliberately separate from the PC serial pulse protocol. To run this paradigm on PC's serial hardware, the transport must be adapted and tested; simply changing a port string is insufficient. A serial option is not supplied here because resetting/pulsing codes could change the historical marker behavior.

## Outputs and version control

Each run creates a unique `data/` directory containing behavioral data, event write timestamps, exact shuffled trial order, configuration, stimuli, script copy, frame intervals, and metadata. Metadata records participant, seed, software/OS versions, script/config/stimulus hashes, frame counts, measured refresh rate, Git commit/dirty state when available, and completion/abort/error status. The entire list is randomized once, as in HC. CSV condition and item codes remain unchanged.

Event write timestamps refer to software calls, not physical EEG marker arrival. Screen-flip timestamps are not photodiode measurements. The scoring marker is at the end of the fixed response window, not at the button press; use the RT columns for response timing. Log writes are buffered during the target interval and flushed at trial end. Completed trials save before breaks, improving on the source's post-break logger. Participant data are excluded by `.gitignore`.

## Differences from a literal rerun

- PsychoPy's keyboard API and frame loop replace the OpenSesame 3.1.4 coroutine.
- Broken function wrapping is replaced by an explicit pretarget condition write.
- Courier New at 18-pixel text height approximates HC `mono` size 18; compare actual glyph dimensions on the lab monitor.
- Instructions and break text are simplified; any key continues, as with the original sketchpads.
- Parallel hardware initializes/resets to zero outside trials, and errors stop the run rather than being swallowed.
- Metadata and completed trials are saved more explicitly.

## Checks completed

Both CSVs were checked field by field against all 300 source rows. Both configuration/list combinations passed validation, and the script passed Python compilation. A simulated four-trial execution checked the fixed 400 ms exposure at 60 Hz, full 1000 ms window despite an early response, timeout handling, condition-before-target order, response marker order, duplicate 220 writes on correct trials, item-after-ITI placement, and blink scheduling.

Still required before EEG collection: pilot both lists on the actual computer; check response buttons, font/display size, target exposure and full window duration; verify all marker codes and duplicate-write behavior in the EEG recording; and measure marker-to-light offsets with a photodiode. These files alone cannot establish historical HC hardware timing.

Official API references:
- https://psychopy.org/api/hardware/keyboard.html
- https://psychopy.org/api/visual/window.html
- https://psychopy.org/api/parallel.html
- https://osdoc.cogsci.nl/4.1/manual/structure/coroutines/
