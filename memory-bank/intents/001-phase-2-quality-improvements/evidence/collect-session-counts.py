"""Count local accounts/projects through isolated copies of stopped MongoDB volumes.

Original volumes are mounted read-only only in a networkless copy/hash helper.
MongoDB runs on temporary copies, never on original volumes. No ports are published.
Only aggregate counts, metadata and content-manifest hashes are archived; private
IDs used to associate account profiles with project ownership stay in memory.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import uuid


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
IMAGE_REFERENCE = '0010f63d2695'
DATASETS = ['picturas', 'picturas-quality-20261114']
VOLUMES = {f'{name}-{role}': f'{name}_{role}_data'
           for name in DATASETS for role in ('user', 'project')}


def run(args, **kwargs):
    return subprocess.run(args, check=True, text=True, capture_output=True, **kwargs).stdout


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    work = Path(tempfile.mkdtemp(prefix='picturas-session-counts-'))
    uid, gid = os.getuid(), os.getgid()
    nonce = uuid.uuid4().hex[:10]
    running = set()
    report = {'started_at': now(), 'checkout_commit': run(['git', 'rev-parse', 'HEAD'], cwd=ROOT).strip(),
              'host_ref': 'LOCAL-HOST-01', 'administrator_ref': 'ADM-01',
              'administrator_name': 'Luís Miguel Coelho',
              'preserve_original_sets': DATASETS, 'status': 'in-progress',
              'method': 'Networkless read-only source helper; temporary physical copies; isolated MongoDB 4.4; aggregate-only report',
              'original_volumes_mounted_readonly': True, 'original_databases_started': False,
              'ports_published': False, 'browser_data_read': False,
              'development_or_evaluation_installation_selected': False, 'datasets': {}}
    image = None
    phase = 'source preflight'

    def check_stopped():
        for volume in VOLUMES.values():
            run(['docker', 'volume', 'inspect', volume])  # Missing sources must not be auto-created.
            if run(['docker', 'ps', '-q', '--filter', f'volume={volume}']).strip():
                raise RuntimeError('A source volume has an active container; refusing the offline snapshot.')

    def helper(command, *, with_work=False):
        cmd = ['docker', 'run', '--rm', '--pull=never', '--network=none', '--read-only',
               '--cap-drop=ALL', '--cap-add=DAC_OVERRIDE', '--user=0:0',
               '--security-opt=no-new-privileges', '--memory=256m', '--cpus=1',
               '--tmpfs', '/tmp:rw,nosuid,size=32m', '--tmpfs', '/data/db:rw,size=1m',
               '--tmpfs', '/data/configdb:rw,size=1m']
        for alias, volume in VOLUMES.items():
            cmd += ['--mount', f'type=volume,src={volume},dst=/sources/{alias},readonly']
        if with_work:
            cmd += ['--cap-add=CHOWN', '--cap-add=FOWNER',
                    '--mount', f'type=bind,src={work},dst=/work']
        cmd += ['--entrypoint', '/bin/bash', image, '-euo', 'pipefail', '-c', command]
        return run(cmd)

    def manifests():
        # Paths are constant across reads. Hash file bytes and names; never print per-file data.
        lines = []
        for alias in VOLUMES:
            lines += [f'test -f /sources/{alias}/WiredTiger',
                      f'test -z "$(find /sources/{alias} -type l -print -quit)"',
                      f'printf "{alias} "',
                      f'find /sources/{alias} -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum',
                      f'du -sk /sources/{alias}']
        values = helper('\n'.join(lines)).splitlines()
        result = {}
        for i in range(0, len(values), 2):
            fields = values[i].split()
            result[fields[0]] = {'sha256_file_manifest': fields[1],
                                 'disk_kib': int(values[i + 1].split()[0]),
                                 'source_volume': VOLUMES[fields[0]]}
        return result

    def query_copy(alias, role):
        name = f'picturas-inventory-{nonce}-{role}'
        clone = work / alias
        run(['docker', 'run', '-d', '--rm', '--name', name, '--pull=never', '--network=none',
             '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges',
             '--user', f'{uid}:{gid}', '--memory=512m', '--cpus=1', '--pids-limit=128',
             '--tmpfs', '/tmp:rw,nosuid,size=64m', '--tmpfs', '/data/db:rw,size=1m',
             '--tmpfs', '/data/configdb:rw,size=1m', '--env', 'HOME=/tmp',
             '--mount', f'type=bind,src={clone},dst=/snapshot', '--entrypoint', 'mongod', image,
             '--dbpath', '/snapshot', '--bind_ip', '127.0.0.1', '--port', '27017',
             '--nounixsocket', '--wiredTigerCacheSizeGB', '0.25',
             '--setParameter', 'diagnosticDataCollectionEnabled=false'])
        running.add(name)
        for _ in range(90):
            ping = subprocess.run(['docker', 'exec', name, 'mongo', '--quiet', '--norc',
                                   '--eval', 'quit(db.adminCommand({ping:1}).ok ? 0 : 2)'],
                                  text=True, capture_output=True)
            if ping.returncode == 0:
                break
            if run(['docker', 'inspect', '--format', '{{.State.Running}}', name]).strip() != 'true':
                raise RuntimeError('Temporary MongoDB exited; original volumes remain untouched.')
            time.sleep(1)
        else:
            raise RuntimeError('Temporary MongoDB readiness timed out.')
        database = 'user' if role == 'user' else 'project'
        collection = 'users' if role == 'user' else 'projects'
        projection = '{_id:1,type:1}' if role == 'user' else '{_id:0,user_id:1,"imgs.media_type":1}'
        expression = f'''
const target = db.getSiblingDB("{database}");
const catalog = db.adminCommand({{listDatabases:1,nameOnly:true}}).databases.map(x=>x.name);
const collections = target.getCollectionNames();
const present = collections.indexOf("{collection}") !== -1;
const records = present ? target.getCollection("{collection}").find({{}},{projection}).toArray() : null;
print(JSON.stringify({{database:"{database}",collection:"{collection}",present:present,
  database_names:catalog,collection_names:collections,records:records}}));
'''
        text = run(['docker', 'exec', name, 'mongo', '--quiet', '--norc', '--eval', expression])
        result = json.loads(next(line for line in reversed(text.splitlines()) if line.startswith('{')))
        run(['docker', 'stop', '--time', '20', name])
        running.remove(name)
        if not result['present']:
            raise RuntimeError(f'Expected {database}.{collection} is absent; refusing to report a misleading zero.')
        return result

    try:
        check_stopped()
        image = run(['docker', 'image', 'inspect', '--format', '{{.Id}}', IMAGE_REFERENCE]).strip()
        report['mongo_image_id'] = image
        phase = 'hashing original sources'
        print('Hashing four original read-only database volumes...', flush=True)
        report['sources_before'] = manifests()
        required = sum(item['disk_kib'] * 1024 for item in report['sources_before'].values())
        if required * 2 + 1024**3 > shutil.disk_usage(work).free:
            raise RuntimeError('Insufficient temporary disk headroom for snapshots and recovery.')
        for alias in VOLUMES:
            (work / alias).mkdir(mode=0o700)
        # Read-only source mounts remain separate from the only writable bind mount, /work.
        copy = '\n'.join(f'cp -a --no-preserve=ownership /sources/{alias}/. /work/{alias}/'
                         for alias in VOLUMES)
        # Root can read source mode 600; ownership is fixed only under the private temporary /work.
        copy += f'\nchown -R {uid}:{gid} /work'
        print('Copying source volumes to private temporary snapshots...', flush=True)
        phase = 'copying snapshots'
        helper(copy, with_work=True)
        for dataset in DATASETS:
            print(f'Counting {dataset} on isolated copies...', flush=True)
            phase = f'counting {dataset}'
            users = query_copy(f'{dataset}-user', 'user')
            projects = query_copy(f'{dataset}-project', 'project')
            def oid(value):
                return str(value.get('$oid')) if isinstance(value, dict) else str(value)
            profiles = {oid(row['_id']): row.get('type') if row.get('type') in
                        ('anonymous', 'free', 'premium') else 'other' for row in users['records']}
            account_counts = Counter(profiles.values())
            owner_counts = Counter()
            media_count = 0
            malformed_media_arrays = 0
            for row in projects['records']:
                owner_counts[profiles.get(oid(row.get('user_id')), 'owner-not-found')] += 1
                media = row.get('imgs', [])
                if isinstance(media, list):
                    media_count += len(media)
                else:
                    malformed_media_arrays += 1
            report['datasets'][dataset] = {
                'users_database': users['database'], 'projects_database': projects['database'],
                'accounts_total': len(users['records']),
                'accounts_by_type': {key: account_counts[key] for key in ('anonymous','free','premium','other')},
                'projects_total': len(projects['records']),
                'projects_by_owner_type': {key: owner_counts[key] for key in
                                           ('anonymous','free','premium','other','owner-not-found')},
                'media_references_total': media_count if not malformed_media_arrays else None,
                'malformed_media_arrays': malformed_media_arrays,
                'media_objects_verified': False, 'browser_associations': None}
            del users, projects, profiles
        report['status'] = 'complete'
    except Exception as error:
        report['status'] = 'failed'
        report['failed_phase'] = phase
        report['error_type'] = type(error).__name__
        # Subprocess stderr is intentionally excluded: it may contain private database details.
        report['error'] = str(error) if isinstance(error, RuntimeError) else 'Collector subprocess failed; no private output archived.'
        if isinstance(error, subprocess.CalledProcessError):
            report['subprocess_returncode'] = error.returncode
            report['failure_signals'] = [signal for signal in
                ('Operation not permitted', 'Permission denied', 'No space left on device')
                if signal.lower() in (error.stderr or '').lower()]
    finally:
        for name in list(running):
            subprocess.run(['docker', 'stop', '--time', '20', name], capture_output=True)
        if image and 'sources_before' in report:
            try:
                report['sources_after'] = manifests()
                report['original_file_manifests_unchanged'] = report['sources_before'] == report['sources_after']
                if not report['original_file_manifests_unchanged']:
                    report['status'] = 'failed-source-verification'
            except Exception:
                report['status'] = 'failed-source-verification'
        try:
            if image:
                helper(f'chown -R {uid}:{gid} /work', with_work=True)
            shutil.rmtree(work)
            report['temporary_snapshots_removed'] = True
        except Exception:
            report['temporary_snapshots_removed'] = False
            report['temporary_snapshot_directory'] = str(work)
            report['status'] = 'failed-cleanup'
        report['completed_at'] = now()
        args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report.get(key) for key in
                      ('status','datasets','original_file_manifests_unchanged','temporary_snapshots_removed','error')}), flush=True)
    return 0 if report['status'] == 'complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
