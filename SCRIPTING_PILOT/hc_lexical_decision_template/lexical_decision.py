"""HC lexical decision paradigm translated from FIN__AB/BA__M21__7_10_17.osexp.

Run --validate-only without PsychoPy. See README.md before collecting data.
"""
import argparse
import csv
import hashlib
import json
import math
import platform
import random
import secrets
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def load_study(config_path):
    config = json.loads(config_path.read_text())
    stimulus_path = config_path.parent / config['stimulus_file']
    with stimulus_path.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError('The stimulus list is empty.')
    required = {'trial_id', 'target', 'targ_type', 'cond_trig', 'cresp', 'word_trig', 'ITI'}
    if not required.issubset(rows[0]):
        raise ValueError(f'Required CSV columns: {sorted(required)}')
    if len({r['trial_id'] for r in rows}) != len(rows):
        raise ValueError('trial_id must be unique.')
    for row in rows:
        if not row['target'].strip() or not row['targ_type'].strip():
            raise ValueError(f'Missing target/condition: {row}')
        if row['cresp'] not in ('/', 'z'):
            raise ValueError('This template expects original cresp values / or z.')
        for name in ('cond_trig', 'word_trig'):
            row[name] = int(row[name])
            if not 1 <= row[name] <= 255:
                raise ValueError(f'{name} must be an integer from 1 to 255.')
        row['ITI'] = float(row['ITI'])
        if not math.isfinite(row['ITI']) or row['ITI'] < 0:
            raise ValueError('ITI must be finite and nonnegative.')
    for section, names in [('timing', ['fixation_ms', 'pretarget_blank_ms',
                                      'target_ms', 'response_window_ms', 'blink_ms'])]:
        for name in names:
            if not math.isfinite(config[section][name]) or config[section][name] <= 0:
                raise ValueError(f'{section}.{name} must be finite and positive.')
    for name in ('blink_every', 'break_every'):
        if not isinstance(config['schedule'][name], int) or config['schedule'][name] < 1:
            raise ValueError(f'{name} must be a positive integer.')
    if config['responses']['word'] == config['responses']['nonword']:
        raise ValueError('Word and nonword response keys must differ.')
    if 'escape' in config['responses'].values():
        raise ValueError('Escape is reserved for aborting.')
    if config['triggers']['mode'] not in ('mock', 'parallel'):
        raise ValueError('Trigger mode must be mock or parallel.')
    if config['timing']['target_ms'] >= config['timing']['response_window_ms']:
        raise ValueError('Target duration must be shorter than the response window.')
    int(config['triggers']['parallel_address'], 0)
    for name in ('correct', 'incorrect_or_timeout'):
        if not isinstance(config['triggers'][name], int) or not 1 <= config['triggers'][name] <= 255:
            raise ValueError(f'Trigger {name} must be an integer from 1 to 255.')
    return config, rows, stimulus_path


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TriggerPort:
    """HC raw latched codes: no intervening zero resets, no pulse waits."""
    def __init__(self, settings, clock, core, event_writer, event_stream):
        self.settings, self.clock = settings, clock
        self.writer, self.stream = event_writer, event_stream
        self.port = None
        if settings['mode'] == 'parallel':
            from psychopy import parallel
            self.port = parallel.ParallelPort(address=int(settings['parallel_address'], 0))
            # Known safe initial state; source did not explicitly initialize to zero.
            self.port.setData(0)

    def write(self, code, label, trial):
        before = self.clock.getTime()
        if self.port is not None:
            self.port.setData(code)
        after = self.clock.getTime()
        # Buffered until end of trial to avoid disk flushes at target onset.
        self.writer.writerow([trial, label, code, self.settings['mode'], before, after])
        return before

    def close(self):
        if self.port is not None:
            self.port.setData(0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).with_name('config_ab.json'))
    parser.add_argument('--participant', default='pilot')
    parser.add_argument('--seed', type=int)
    parser.add_argument('--limit', type=int, help='Pilot only: run the first N shuffled trials.')
    parser.add_argument('--validate-only', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'data')
    args = parser.parse_args()
    config_path = args.config.resolve()
    config, rows, stimulus_path = load_study(config_path)
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be positive.')
    seed = args.seed if args.seed is not None else secrets.randbits(32)
    random.Random(seed).shuffle(rows)
    if args.limit is not None:
        rows = rows[:args.limit]
    if args.validate_only:
        print(f'Valid: {len(rows)} trials; seed={seed}; trigger mode={config["triggers"]["mode"]}')
        return

    # Import only when presenting stimuli; validation uses the standard library.
    import psychopy
    from psychopy import visual, core
    from psychopy.hardware import keyboard

    run_dir = args.output.resolve() / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / 'config.json').write_text(json.dumps(config, indent=2))
    (run_dir / 'stimuli.csv').write_bytes(stimulus_path.read_bytes())
    (run_dir / 'lexical_decision.py').write_bytes(Path(__file__).read_bytes())
    with (run_dir / 'trial_order.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    try:
        git_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=Path(__file__).parent,
                                             stderr=subprocess.DEVNULL, text=True).strip()
        git_status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=Path(__file__).parent,
                                             stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        git_commit, git_status = None, None
    metadata = dict(participant=args.participant, seed=seed, trial_limit=args.limit,
                    python=platform.python_version(), platform=platform.platform(),
                    psychopy_version=psychopy.__version__, git_commit=git_commit,
                    git_dirty=None if git_status is None else bool(git_status),
                    script_sha256=sha256(Path(__file__)), stimulus_sha256=sha256(stimulus_path),
                    config_sha256=sha256(config_path), status='starting')
    def save_metadata():
        (run_dir / 'run_metadata.json').write_text(json.dumps(metadata, indent=2))
    save_metadata()
    win = port = None
    clock = core.Clock()
    timing, display, schedule = config['timing'], config['display'], config['schedule']
    with (run_dir / 'behavior.csv').open('w', newline='') as behavior, \
            (run_dir / 'events.csv').open('w', newline='') as events:
        fields = ['participant', 'trial_number', *rows[0].keys(), 'expected_key', 'response',
                  'correct', 'timeout', 'rt_from_target_ms', 'rt_from_response_window_ms',
                  'fixation_onset_s', 'pretarget_blank_onset_s', 'target_onset_s',
                  'condition_write_s', 'item_write_s', 'response_window_start_s',
                  'response_marker_write_s', 'duplicate_correct_write_s',
                  'target_offset_s', 'target_duration_ms', 'response_window_end_s',
                  'dropped_frames_in_window',
                  'blink_onset_s', 'iti_onset_s', 'trial_end_s']
        writer = csv.DictWriter(behavior, fieldnames=fields); writer.writeheader()
        event_writer = csv.writer(events)
        event_writer.writerow(['trial_number', 'event', 'code', 'mode', 'write_start_s', 'write_return_s'])
        try:
            win = visual.Window(size=display['size_px'], fullscr=display['fullscreen'],
                                screen=display['screen'], color='black', units='pix',
                                waitBlanking=True, checkTiming=True)
            kb = keyboard.Keyboard()
            hz = win.getActualFrameRate(nIdentical=20, nMaxFrames=120, nWarmUpFrames=20)
            if hz is None:
                raise RuntimeError('Could not measure a stable refresh rate. Check display setup.')
            metadata.update(refresh_hz=hz, actual_window_size=list(map(int, win.size)),
                            keyboard_backend=kb.backend, status='running')
            target_frames = max(1, round(timing['target_ms'] * hz / 1000))
            window_frames = max(1, round(timing['response_window_ms'] * hz / 1000))
            if target_frames >= window_frames:
                raise ValueError('Rounded target duration must be shorter than the response window.')
            metadata.update(target_frames=target_frames, response_window_frames=window_frames,
                            nominal_target_ms=target_frames * 1000 / hz,
                            nominal_response_window_ms=window_frames * 1000 / hz)
            save_metadata()
            text = visual.TextStim(win, text='', color='white', font=display['font'],
                                   height=display['text_height_px'], wrapWidth=1600, autoLog=False)
            half = display['fixation_half_length_px']
            vertical = visual.Line(win, start=(0, -half), end=(0, half), lineColor='white', autoLog=False)
            horizontal = visual.Line(win, start=(-half, 0), end=(half, 0), lineColor='white', autoLog=False)
            port = TriggerPort(config['triggers'], clock, core, event_writer, events)

            def check_escape():
                if kb.getKeys(keyList=['escape'], waitRelease=False):
                    raise KeyboardInterrupt

            def flip(draw=None):
                if draw is not None:
                    draw()
                stamp = {}
                win.callOnFlip(lambda: stamp.update(time=clock.getTime()))
                win.flip()
                return stamp['time']

            def hold_ms(duration, next_flip=True):
                # Keep current front buffer visible, polling Escape; next onset uses flip().
                deadline = clock.getTime() + max(0, duration / 1000 - (0.5 / hz if next_flip else 0))
                while clock.getTime() < deadline:
                    check_escape()
                    core.wait(0.001)

            def message(content):
                text.text = content
                flip(text.draw)
                kb.clearEvents()
                while True:
                    keys = kb.getKeys(waitRelease=False)
                    if any(k.name == 'escape' for k in keys):
                        raise KeyboardInterrupt
                    if keys:
                        return
                    core.wait(0.001)

            message('Welcome!\n\nDecide whether each item is a real word or a nonword.\n\n'
                    f'Real word: {config["responses"]["word"]}    Nonword: {config["responses"]["nonword"]}\n\n'
                    f'Blink when (--) appears, every {schedule["blink_every"]} trials.\n'
                    'At other times, please avoid blinking or moving.\n\n'
                    f'You can rest after every {schedule["break_every"]} trials.\n'
                    'Call or wave to the experimenter if you need anything.\n\n'
                    'Press a key to start.')
            completed = 0
            for number, row in enumerate(rows, 1):
                result = dict(participant=args.participant, trial_number=number, **row)
                result['expected_key'] = config['responses']['word' if row['cresp'] == '/' else 'nonword']
                def draw_fixation():
                    vertical.draw(); horizontal.draw()
                result['fixation_onset_s'] = flip(draw_fixation)
                hold_ms(timing['fixation_ms'])
                result['pretarget_blank_onset_s'] = flip()
                hold_ms(timing['pretarget_blank_ms'])
                text.text = row['target']
                # HC def_chain calls cond_trigger() before target presentation.
                kb.clearEvents()
                result['condition_write_s'] = port.write(row['cond_trig'], 'condition', number)
                win.callOnFlip(kb.clock.reset)
                result['target_onset_s'] = flip(text.draw)
                result['response_window_start_s'] = result['target_onset_s']
                response = None
                deadline_s = window_frames / hz
                dropped_before = win.nDroppedFrames
                win.recordFrameIntervals = True
                # Fixed-length window. Early responses never shorten exposure or trial.
                for frame in range(1, window_frames + 1):
                    keys = kb.getKeys(keyList=[*config['responses'].values(), 'escape'], waitRelease=False)
                    if any(k.name == 'escape' for k in keys):
                        raise KeyboardInterrupt
                    eligible = [k for k in keys if 0 <= k.rt <= deadline_s]
                    if response is None and eligible:
                        response = min(eligible, key=lambda k: k.rt)
                    onset = flip(text.draw if frame < target_frames else None)
                    if frame == target_frames:
                        result['target_offset_s'] = onset
                result['response_window_end_s'] = onset
                keys = kb.getKeys(keyList=[*config['responses'].values(), 'escape'], waitRelease=False)
                if any(k.name == 'escape' for k in keys):
                    raise KeyboardInterrupt
                eligible = [k for k in keys if 0 <= k.rt <= deadline_s]
                if response is None and eligible:
                    response = min(eligible, key=lambda k: k.rt)
                win.recordFrameIntervals = False
                result['dropped_frames_in_window'] = win.nDroppedFrames - dropped_before
                result.update(response='' if response is None else response.name,
                              timeout=int(response is None),
                              correct=int(response is not None and response.name == result['expected_key']))
                result['rt_from_response_window_ms'] = '' if response is None else response.rt * 1000
                result['rt_from_target_ms'] = result['rt_from_response_window_ms']
                result['target_duration_ms'] = (result['target_offset_s'] - result['target_onset_s']) * 1000
                # Source writes correct_trigger then incorrect_trigger, both 220 on correct trials.
                result['duplicate_correct_write_s'] = ''
                code = config['triggers']['correct' if result['correct'] else 'incorrect_or_timeout']
                result['response_marker_write_s'] = port.write(code, 'response', number)
                if result['correct']:
                    result['duplicate_correct_write_s'] = port.write(code, 'duplicate_correct', number)
                result['blink_onset_s'] = ''
                if number % schedule['blink_every'] == 0:
                    text.text = '(--)'
                    result['blink_onset_s'] = flip(text.draw)
                    hold_ms(timing['blink_ms'])
                result['iti_onset_s'] = flip()
                hold_ms(row['ITI'], next_flip=False)
                result['item_write_s'] = port.write(row['word_trig'], 'item', number)
                result['trial_end_s'] = clock.getTime()
                # Save before a break so completed trials survive aborts during breaks.
                writer.writerow(result); behavior.flush(); events.flush()
                completed = number
                if number % schedule['break_every'] == 0 and number < len(rows):
                    message('Take a break for as long as you like.\n\n'
                            'Call or wave if you need the experimenter.\n\n'
                            'Press a key when you are ready to resume.')
            message('You have finished!\n\nPlease wait for the experimenter.\n\nThank you!')
            metadata['status'] = 'completed'
        except KeyboardInterrupt:
            metadata['status'] = 'aborted'
        except Exception as error:
            metadata.update(status='error', error=repr(error))
            raise
        finally:
            if win is not None:
                win.saveFrameIntervals(str(run_dir / 'frame_intervals.csv'))
            metadata['completed_trials'] = locals().get('completed', 0)
            save_metadata()
            try:
                if port is not None:
                    port.close()
            finally:
                if win is not None:
                    win.close()
    print(f'Run saved: {run_dir}')


if __name__ == '__main__':
    main()
