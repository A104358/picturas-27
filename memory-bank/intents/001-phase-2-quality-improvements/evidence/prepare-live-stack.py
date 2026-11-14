"""Prepare an isolated measurement slice from the repository Compose definition.

The generated configuration contains inherited configuration secrets and stays
outside the repository with owner-only permissions. Only a sanitized manifest is
written to the evidence directory. Requires PyYAML and locally available images.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

import yaml

ROOT = Path(__file__).resolve().parents[4]
SELECTED = ('nginx', 'frontend', 'api_gateway', 'ws_gateway', 'projects', 'users',
            'img_storage', 'seaweedfs', 'rabbitmq', 'projects_mongoDB',
            'users_mongoDB', 'video_tool', 'brightness_tool')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--project', default='picturas-quality-20261114')
    args = parser.parse_args()
    source = ROOT / 'docker-compose.yaml'
    original = yaml.safe_load(source.read_text())
    config = {'name': args.project, 'services': {}, 'volumes': {},
              'networks': {'elk': {'internal': True}}}
    manifest = {'recorded_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'compose_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'project': args.project, 'services': {},
                'differences': ['13-service slice; omitted tools/billing/backup are not evaluated.',
                                'Fresh project-scoped volumes and internal Docker network.',
                                'Host ports retain their original numbers but bind to loopback only.',
                                'Resource ceilings recorded per service; not the unrestricted default deployment.',
                                'Local immutable image IDs; development source/node_modules binds removed.',
                                'No downloads or model loading from the internet.']}
    for name in SELECTED:
        service = copy.deepcopy(original['services'][name])
        image = service.get('image', f'picturas-{name}:latest')
        image_id = subprocess.check_output(['docker', 'image', 'inspect', image, '--format', '{{.Id}}'], text=True).strip()
        service.pop('build', None)
        service.pop('container_name', None)
        service['image'] = image_id
        service['restart'] = 'no'
        deps = service.get('depends_on', {})
        service['depends_on'] = {k:v for k,v in deps.items() if k in SELECTED} if isinstance(deps, dict) else [k for k in deps if k in SELECTED]
        ports=[]
        for port in service.get('ports', []):
            published, target = str(port).split(':')[-2:]
            ports.append({'target': int(target), 'published': published, 'host_ip': '127.0.0.1', 'protocol': 'tcp'})
        if ports:
            service['ports'] = ports
        volumes=[]
        for volume in service.get('volumes', []):
            parts = volume.split(':')
            if len(parts) == 1 or (parts[0].startswith('.') and parts[1] in ('/app', '/usr/src/app')):
                continue
            if parts[0].startswith('.'):
                parts[0] = str((ROOT / parts[0]).resolve())
            else:
                config['volumes'][parts[0]] = {}
            volumes.append(':'.join(parts))
        service['volumes'] = volumes
        service['cpus'] = 2 if name == 'video_tool' else 1
        service['mem_limit'] = '1g' if name in ('video_tool', 'projects', 'seaweedfs') else ('128m' if name == 'nginx' else '512m')
        config['services'][name] = service
        manifest['services'][name] = {'image_id': image_id, 'cpus': service['cpus'],
                                      'memory_limit': service['mem_limit'], 'host_ports': ports,
                                      'named_volumes': [v.split(':')[0] for v in volumes if not v.startswith('/')]}
    args.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(args.directory, 0o700)
    config_path = args.directory / 'compose.json'
    descriptor = os.open(config_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump(config, stream, indent=2)
    probe_env = {k:v for k,v in config['services']['projects']['environment'].items() if k.startswith('RABBITMQ_')}
    descriptor = os.open(args.directory / 'probe.env', os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        stream.write(''.join(f'{key}={value}\n' for key,value in probe_env.items()))
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Prepared {len(SELECTED)} services; private configuration: {config_path}')
    print(f'Sanitized manifest: {args.manifest}')


if __name__ == '__main__':
    main()
