"""Export only OPS-C1 counts, opaque references and assertion receipts. No IDs/body/URLs."""
import datetime as dt,hashlib,json,os,re
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]
ROOT=Path.home()/'picturas-secrets/b11-fixture'
BASE=ROOT/'maintenance/picturas-ops-b11'
OUT=REPO/'tests/conformance/results/2026-11-24'
required=['real-image-autoack-worker-stopped-during-active-callback',
 'crash-generation_after_commit-remains-isolated','crash-object_before_delete-remains-isolated',
 'crash-object_after_delete-remains-isolated','crash-quota_before_commit-remains-isolated','crash-quota_after_commit-remains-isolated',
 'B10-cut-after-real-video-replies-before-domain-commit','lost-quota-response-reads-atomic-marker',
 'message-before-ack-helper-exited-at-target','cleanup-precondition-failure','cleanup-failure-blocks-seal',
 'crash-before-seal-remains-isolated','business-case-sealed-without-technical-fixture-bypass',
 'B10-reopens-only-after-business-proof-and-channel-controls','real-video-stopped-with-active-callback-and-partial-output',
 'quota-helper-exited-86-before-any-journal','native-existing-marker-readback-after-helper-exit',
 'real-video-interruption-before-completion-reconciled','late-reply-does-not-affect-explicit-new-generation',
 'missing-receipt-blocks-seal','missing-receipt-blocks-consumers',
 'indeterminate-case-kept-isolated-with-zero-financial-effect','fixture-stopped-with-volumes-and-private-evidence-preserved']
events=json.loads((OUT/'B11-operations.json').read_text())['checks'];latest={e['case']:e for e in events}
operations=[]
for path in BASE.glob('*.json'):
 if not re.fullmatch('[a-f0-9]{32}',path.stem):continue
 state=json.loads(path.read_text());case=BASE/path.stem/'reconciliation'
 if not (case/'report.json').exists():continue
 report=json.loads((case/'report.json').read_text())
 failures=[json.loads(p.read_text()) for p in (case/'failures').glob('*.json')]
 effects=[json.loads(p.read_text()) for p in (case/'effect-events').glob('*.json')]
 snapshot=json.loads((case/'snapshot.json').read_text())
 start=json.loads((case/'case.json').read_text())['created_at']
 end=report.get('sealed_at')
 seconds=(dt.datetime.fromisoformat(end)-dt.datetime.fromisoformat(start)).total_seconds() if end else None
 operations.append({'reference':hashlib.sha256(path.stem.encode()).hexdigest()[:12],
  'classification':{name:sum(c['state']==name for c in report['cases']) for name in ('confirmed','lost','indeterminate')},
  'unknown':report['unknown'],'sealed':report['sealed'],'maintenance_phase':state['phase'],
  'isolation_ms':state.get('isolation_ms'),'analysis_and_reconciliation_seconds':seconds,
  'protected_objects':len(snapshot['protected']),'archived_messages':len(list((case/'messages').glob('*.json'))),
  'helper_hard_exits':sum(f.get('exit_code')==86 for f in failures),
  'lost_response_marker_observations':sum(e.get('readback_after_lost_response',False) for e in effects)})
receipts=[]
for path in [ROOT/'acceptance/verified.json',*(ROOT/'acceptance/verified-history').glob('*.json')]:
 if path.exists():
  value=json.loads(path.read_text())
  receipts.append({key:value.get(key) for key in ('no_undue_charges','no_undue_compensations',
   'no_partial_visibility','confirmed_preserved','original_day_balances_verified','balance_before','balance_after')})
component=json.loads((OUT/'B11-native-quota.json').read_text()) if (OUT/'B11-native-quota.json').exists() else {}
application=(OUT/'B11-B11-functional.txt').read_text() if (OUT/'B11-B11-functional.txt').exists() else ''
paths_bound='B11 Apply and cancellation: 21/21 checks passed' in application
result={'complete':all(latest.get(case,{}).get('passed') for case in required) and all(component.get(k) is True for k in
 ('native_mongo','lost_response_rereads_marker','no_second_financial_write','private_readback_event_preserved')) and paths_bound,
 'required_checks':{case:latest.get(case,{}).get('passed',False) for case in required},
 'attempts':len(events),'failed_attempts_retained':[e['case'] for e in events if not e['passed']],
 'operations':operations,'native_assertion_receipts':receipts,'native_quota_component':component,
 'application_apply_cancel_and_server_path_binding':{'passed':paths_bound,'checks':21},
 'scope':'Synthetic fixtures only. No automatic replay. Unknown evidence stays isolated.',
 'inherited_limitations':['Early image ack','Projects ack before async callback completion','Non-persistent worker replies can be lost on broker termination'],
 'test_distinction':'Real image/video workers; controlled mixed-cost admission, clock dependency, commit boundary and persistent obsolete-message fixtures.'}
(OUT/'B11-acceptance.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'complete':result['complete'],'operations':len(operations),'required_passed':sum(result['required_checks'].values()),
 'required_total':len(required),'failed_attempts_retained':len(result['failed_attempts_retained'])}))
if not result['complete']:raise SystemExit(1)
