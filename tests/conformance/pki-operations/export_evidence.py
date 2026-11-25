"""Export an explicit public allowlist, never the private installation contents."""
import hashlib,json
from pathlib import Path
from pilot_paths import ROOT,PROJECT
REPO=Path(__file__).resolve().parents[3]
OUT=REPO/'tests/conformance/results/2026-11-24'
fields=['schema_version','operation','project','mode','commit','t_detectado','t_comando','t_isolado','t_reabertura',
 'isolation_ms','isolation_limit_met','isolation_target_met','phase','events','participants_before','participants_isolated',
 'participants_loaded','certificates_before','certificates_expected','certificates_loaded','loaded_material',
 'registered_consumers','cut_observation','persistent_cut_witness','channel_controls','persistent_controls',
 'browser_proof','verification_failures','failure','failure_detail','interrupted_work']
summary=[]
for name in ['diagnostic-control-retry','initial-trial-1','initial-trial-2','initial-trial-3','trial-1','trial-2','trial-3']:
 trial=ROOT/'pilot'/name
 if not (trial/'isolation.json').exists():continue
 isolation=json.loads((trial/'isolation.json').read_text())
 state=json.loads((ROOT/'maintenance'/PROJECT/(isolation['operation']+'.json')).read_text())
 exported={k:state[k] for k in fields if k in state}
 fixture=json.loads((trial/'fixture.json').read_text())
 exported['technical_fixture_correlation_sha256']=hashlib.sha256(fixture['message_id'].encode()).hexdigest()
 # Compare private bytes in memory; export only equality assertions. For an older
 # trial the "new" tree is the next operation's withdrawn tree, never today's CA.
 new_ca=next(iter(state['certificates_expected'].values()))['ca']
 candidates=[ROOT/'pki']
 for record in (ROOT/'maintenance'/PROJECT).glob('*.json'):
  other=json.loads(record.read_text())
  if other.get('pki_change',{}).get('old_archive'):candidates.append(Path(other['pki_change']['old_archive']))
 def fingerprint(path):
  import ssl
  return hashlib.sha256(ssl.PEM_cert_to_DER_cert(path.read_text())).hexdigest()
 new=next(p for p in candidates if (p/'ca/ca.crt').exists() and fingerprint(p/'ca/ca.crt')==new_ca)
 old=Path(state['pki_change']['old_archive'])
 leaves={svc:(old/'services'/svc/'service.key').read_bytes()!=(new/'services'/svc/'service.key').read_bytes()
         for svc in state['certificates_expected']}
 exported['key_replacement']={'ca_key_changed':(old/'ca/ca.key').read_bytes()!=(new/'ca/ca.key').read_bytes(),
                              'all_leaf_keys_changed':all(leaves.values()),'leaves':leaves}
 for file in ['ready','cut','isolation','resumption','completed','browser-ready','browser-proof','browser-failure','browser-failures','job-active','broker-before','broker-isolated','broker-reopened']:
  path=trial/(file+'.json')
  if path.exists():
   value=json.loads(path.read_text())
   if isinstance(value,dict):value.pop('message_id',None)
   exported[file]=value
   exported[file+'_written_at_ns']=path.stat().st_mtime_ns
 quarantine=trial/'quarantine.json'
 if quarantine.exists():
  value=json.loads(quarantine.read_text());value.pop('message_id',None);exported['quarantine']=value
  exported['quarantine_written_at_ns']=quarantine.stat().st_mtime_ns
 (OUT/('B10-'+name+'.json')).write_text(json.dumps(exported,indent=2)+'\n')
 summary.append({'trial':name,'phase':state['phase'],'isolation_ms':state.get('isolation_ms')})
preparations=[]
for path in (ROOT/'pilot').glob('trial-*-preparation-*/failure.json'):
 preparations.append({'name':path.parent.name,**json.loads(path.read_text())})
(OUT/'B10-preparation-failures.json').write_text(json.dumps(preparations,indent=2)+'\n')
print(json.dumps({'public_exports':summary,'preparation_failures_retained':len(preparations),'secret_values_exported':False}))
