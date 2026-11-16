"""Extract existing baseline numbers and instrument limitations without running services.

Original November 16 results are immutable inputs. This audit deliberately does
not turn HTTP 500, a missing response field or a missing object into a security
success/failure count. No application code is changed or executed.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import subprocess

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
RAW = BASE / 'nfr-2026-11-16'


def stats(values):
    return {'n': len(values), 'min': min(values), 'median': statistics.median(values), 'max': max(values)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BASE/'baseline-audit-2026-11-16.json')
    args = parser.parse_args()
    paths = [RAW/'uploads-result.json', RAW/'security-result.json', *sorted(RAW.glob('reliability-*-result.json'))]
    report = {'recorded_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
              'review_commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'source_hashes': {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
              'environment': 'Reported Apple M4 Pro / Docker Desktop ARM64, 2 CPU / 2 GiB for four Node/video services. Not the earlier Linux x86_64 experiment.',
              'runtime_rerun': False, 'upload_groups': [], 'security_case_audit': [],
              'limits': ['Original records do not contain a complete environment/image/source manifest.',
                         'HWM baseline reset precedes a 300 ms idle and post-read follows 700 ms idle plus sequential Docker calls.',
                         'Node request completion is a client/OS send marker, not server receipt.',
                         'Tiny samples; no p95 or cross-architecture speedup is inferred.']}
    uploads = json.loads(paths[0].read_text())
    success = [r for r in uploads['runs'] if r['status']==204]
    groups = [('10MiB-cold-first',[r for r in success if r['label']=='free-10MiB-#1']),
              ('10MiB-warm-observed',[r for r in success if '-10MiB-' in r['label'] and r['label']!='free-10MiB-#1']),
              ('100MiB-observed',[r for r in success if '-100MiB-' in r['label']]),
              ('500MiB-observed',[r for r in success if '-500MiB-' in r['label']])]
    for label, runs in groups:
        row={'label':label,'runs':[r['label'] for r in runs],
             'total_ms':stats([r['total_ms'] for r in runs]),
             'client_post_send_ms':stats([r['post_send_ms'] for r in runs]), 'services':{}}
        for service in ('api_gateway','projects','img_storage'):
            row['services'][service]={field:stats([r['mem'][service][field] for r in runs])
                                      for field in ('pre_rss_mib','peak_rss_mib','delta_mib','post_rss_mib')}
        report['upload_groups'].append(row)
    report['uploads_completed']=len(success)
    report['upload_failures_or_rejections']=[{k:r.get(k) for k in ('label','status','bytes','total_ms','send_ms','post_send_ms','mem')} for r in uploads['runs'] if r['status']!=204]
    security=json.loads(paths[1].read_text())
    report['reported_security_summary']=security['summary']
    issues={
        'G02':('inconclusive-assertion','HTTP 200 is recorded, but user_id is absent from the public response and the test uses it for ownership. verify.mjs stdout is not archived.'),
        'G08':('not-measured-dependency-absent','Subscription service absent; HTTP 500 is neither an authorization denial nor a successful unauthorized read.'),
        'G09':('not-measured-dependency-absent','HTTP 500 cannot prove a cancellation took effect; do not count as an admitted unauthorized operation.'),
        'D04':('malformed-token-only','The hand-made x.payload.x token does not prove rejection of a validly structured forged JWT.'),
        'D05':('status-only-empty-fixture','HTTP 204 against an account without projects; nonempty deletion needs state verification. verify.mjs output is not archived.'),
        'D06':('signer-issued-object-not-verified','og_img_key is absent from the public response, and bytes match=false. This demonstrates signer issuance, not retrieval of this source.'),
        'D07':('write-status-only','HTTP 201; final protocol must read back the created marker and verify the target prefix/content.'),
        'D08':('delete-status-only','HTTP 201; final protocol must verify the known marker existed and is absent afterward.'),
        'D10':('known-credential-observation','Known committed management credentials granted access; separate from user ownership and credential-free access.'),
        'D11':('database-configuration-observation','Unauthenticated Mongo read inside DB container; host reachability is not established by docker exec.'),
        'Q01':('separate-concurrency-scenario','20 grants, remaining 2; not the same binary authorization metric as G/D/W cases.')}
    for case in security['cases']:
        level,note=issues.get(case['id'],('recorded-state-effect' if case['id'] in ('G03','G04','G05','G06','G07','D09','W01') else 'recorded-response', 'Retain raw observation; repeat with case-specific payload/state assertions and positive controls.'))
        report['security_case_audit'].append({'id':case['id'],'raw_observation':case['observed'],
                                               'raw_admitted':case['unauthorized_admitted'],'audit_status':level,'interpretation':note})
    report['security_global_adjusted_rate']=None
    report['security_global_adjusted_rate_reason']='Heterogeneous scopes and incomplete assertions must be repaired and rerun; no replacement population-like percentage is manufactured.'
    report['reliability']={p.stem:json.loads(p.read_text()) for p in paths[2:]}
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f'Saved audit: {args.output}; {len(success)} completed uploads, {len(security["cases"])} case reviews; no runtime requests.')


if __name__=='__main__':
    main()
