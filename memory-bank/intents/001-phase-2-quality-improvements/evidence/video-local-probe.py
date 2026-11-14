"""Small processor-only exploration; no application services or Whisper model.

Run from any directory with an absolute input and output path, or from the repo root.
Generated outputs are temporary. Persisted JSON contains timings and metadata only.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time

import PIL

ROOT = Path(__file__).resolve().parents[4]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'Tools/video'))
from video_processor import process_video, probe  # noqa: E402


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(*args):
    return subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'samples/video/sample_10s_720p.mp4')
    parser.add_argument('--runs', type=int, default=3)
    parser.add_argument('--revision', help='Source revision supplied when git is unavailable in an isolated container')
    parser.add_argument('--environment-label', default='host', help='Label describing isolation and resource limits')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.runs <= 10:
        parser.error('--runs must be between 1 and 10 for this bounded probe')
    source = args.input.resolve()
    ordinary = [{'procedure': 'brightness', 'params': {'brightness': 0.6}},
                {'procedure': 'resize', 'params': {'width': 320, 'height': 240}}]
    extraction = {'procedure': 'extract_frames', 'params': {'mode': 'count', 'count': 3, 'format': 'png'}}
    cases = [('ordinary', ordinary, False), ('ordinary-preview', ordinary, True),
             ('frames', ordinary + [extraction], False),
             ('frames-preview', ordinary + [extraction], True)]
    report = {
        'recorded_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'commit': args.revision or command('git', 'rev-parse', 'HEAD'),
        'revision_origin': 'CLI argument; verify against the recorded source hashes' if args.revision else 'git rev-parse HEAD',
        'scope': 'Local process_video call only; excludes upload, queue, storage, quota, WebSocket and browser.',
        'environment': {'label': args.environment_label, 'platform': platform.platform(), 'python': platform.python_version(),
                        'pillow': PIL.__version__, 'ffmpeg': command('ffmpeg', '-version').splitlines()[0],
                        'ffprobe': command('ffprobe', '-version').splitlines()[0]},
        'source_hashes': {f'Tools/video/{name}': digest(ROOT / 'Tools/video' / name)
                          for name in ('video_processor.py', 'effects.py', 'frame_extraction.py', 'subtitles.py')},
        'input': {'path': str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else str(source),
                  'sha256_before': digest(source), 'metadata': probe(str(source))},
        'design': 'Sequential case order, no discarded warm-up, three default repetitions. Shared host, unrestricted FFmpeg threads.',
        'runs': [],
        'limits': ['Host Pillow may differ from the pinned Docker environment.',
                   'Small pilot: do not infer p95, capacity, speedup or an acceptance threshold.',
                   'No Whisper recognition, failure injection, concurrent requests or service memory sampling.',
                   'Callbacks are local processor progress, not WebSocket delivery.',
                   'Repeated reads may benefit from filesystem cache; case order is not randomized.'],
    }
    with tempfile.TemporaryDirectory(prefix='picturas-inception-probe-') as directory:
        work = Path(directory)
        for name, tools, preview in cases:
            for repetition in range(1, args.runs + 1):
                output = work / f'{name}-{repetition}.mp4'
                events = []
                started = time.perf_counter()
                result = process_video(str(source), str(output), tools,
                                       lambda percent: events.append({'elapsed_s': time.perf_counter() - started,
                                                                       'percent': percent}), preview=preview)
                elapsed = time.perf_counter() - started
                timeline = [0.0, *(event['elapsed_s'] for event in events), elapsed]
                paths = [Path(frame['file']) for frame in result['frames']] if result.get('output_type') == 'frames' else [Path(result.get('output_path', output))]
                report['runs'].append({
                    'case': name, 'repetition': repetition, 'tools': tools, 'preview': preview,
                    'elapsed_s': elapsed, 'local_progress_events': events,
                    'max_local_progress_gap_including_boundaries_s': max(b - a for a, b in zip(timeline, timeline[1:])),
                    'output_type': result.get('output_type', 'video'), 'output_count': len(paths),
                    'output_bytes': sum(path.stat().st_size for path in paths),
                    'output_sha256': [digest(path) for path in paths],
                    'video_metadata': probe(str(output)) if output.exists() else None,
                })
        invalid_output = work / 'invalid.mp4'
        try:
            process_video(str(ROOT / 'samples/video/corrupted.mp4'), str(invalid_output), ordinary)
            invalid = {'exception': None, 'output_exists': invalid_output.exists()}
        except Exception as error:
            invalid = {'exception': type(error).__name__, 'output_exists': invalid_output.exists()}
        report['invalid_input_probe'] = invalid
    report['input']['sha256_after'] = digest(source)
    report['input']['unchanged'] = report['input']['sha256_before'] == report['input']['sha256_after']
    report['summary'] = {}
    for name, _, _ in cases:
        times = [run['elapsed_s'] for run in report['runs'] if run['case'] == name]
        report['summary'][name] = {'n': len(times), 'min_s': min(times),
                                 'median_s': statistics.median(times), 'max_s': max(times)}
    if str(args.output) == '-':
        print(json.dumps(report, indent=2))
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'output': str(args.output), 'summary': report['summary'],
                      'input_unchanged': report['input']['unchanged'], 'invalid_input_probe': invalid}, indent=2))


if __name__ == '__main__':
    main()
