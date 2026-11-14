"""Sample only containers belonging to the isolated quality experiment.

Writes compressed JSON lines with cgroup memory/CPU and summed Node process RSS.
No request bodies, command-line arguments, credentials or application logs are read.
"""
import argparse
from datetime import datetime, timezone
import gzip
import json
import os
from pathlib import Path
import subprocess
import time


def descendants(pid):
    found = {pid}
    pending = [pid]
    while pending:
        current = pending.pop()
        try:
            children = (Path('/proc') / str(current) / 'task' / str(current) / 'children').read_text().split()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        for child in map(int, children):
            if child not in found:
                found.add(child)
                pending.append(child)
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default='picturas-quality-20261114')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--stop-file', type=Path, required=True)
    parser.add_argument('--duration', type=float, default=600)
    parser.add_argument('--interval', type=float, default=0.05)
    args = parser.parse_args()
    containers = subprocess.check_output(['docker', 'ps', '--filter', f'label=com.docker.compose.project={args.project}', '--format', '{{.ID}}'], text=True).split()
    wanted = {'api_gateway', 'projects', 'img_storage', 'video_tool', 'nginx'}
    services = {}
    for container in containers:
        fields = subprocess.check_output(['docker', 'inspect', container, '--format', '{{index .Config.Labels "com.docker.compose.service"}} {{.State.Pid}}'], text=True).split()
        name, pid = fields[0], int(fields[1])
        if name not in wanted:
            continue
        group = next(line.split(':', 2)[2] for line in Path(f'/proc/{pid}/cgroup').read_text().splitlines() if line.startswith('0::'))
        services[name] = {'pid': pid, 'cgroup': Path('/sys/fs/cgroup') / group.lstrip('/')}
    if set(services) != wanted:
        raise RuntimeError(f'Missing measurement containers: {sorted(wanted-set(services))}')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    count = 0
    with gzip.open(args.output, 'wt') as stream:
        stream.write(json.dumps({'type': 'metadata', 'recorded_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                                'project': args.project, 'interval_s': args.interval, 'services': sorted(services),
                                'rss_method': 'Sum of RSS for descendants named node or node-*; shared pages may be counted more than once.',
                                'memory_method': 'cgroup v2 memory.current, including descendants and charged cache.'})+'\n')
        while time.monotonic()-started < args.duration and not args.stop_file.exists():
            row = {'type': 'sample', 'unix_ms': time.time()*1000, 'services': {}}
            for name, info in services.items():
                try:
                    memory = int((info['cgroup']/'memory.current').read_text())
                    cpu = dict(line.split() for line in (info['cgroup']/'cpu.stat').read_text().splitlines())
                    rss = 0
                    for pid in descendants(info['pid']):
                        try:
                            directory = Path('/proc')/str(pid)
                            comm = directory.joinpath('comm').read_text().strip()
                            if comm == 'node' or comm.startswith('node-'):
                                rss += int(directory.joinpath('statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
                        except (FileNotFoundError, PermissionError, ProcessLookupError):
                            pass
                    row['services'][name] = {'memory_current_bytes': memory, 'node_rss_sum_bytes': rss,
                                             'cpu_usage_usec': int(cpu['usage_usec'])}
                except (FileNotFoundError, ProcessLookupError):
                    row['services'][name] = {'unavailable': True}
            stream.write(json.dumps(row)+'\n')
            count += 1
            remaining = args.interval - (time.time()*1000-row['unix_ms'])/1000
            if remaining > 0:
                time.sleep(remaining)
    print(f'Saved {count} resource samples to {args.output}')


if __name__ == '__main__':
    main()
