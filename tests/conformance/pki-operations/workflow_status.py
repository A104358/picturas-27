"""Public B10 progress only; never lists secret files or credential values."""
import json,subprocess
from pathlib import Path
from pilot_paths import ROOT,PROJECT
state=ROOT/'maintenance'/PROJECT/'state.json'
if state.exists():
 s=json.loads(state.read_text());print(json.dumps({'project':PROJECT,'phase':s['phase'],
  'isolation_ms':s.get('isolation_ms'),'controls':s.get('channel_controls',{}).get('passed'),
  'failure':s.get('failure_detail',s.get('failure'))}))
 print(json.dumps({'failed_controls':[r for r in s.get('channel_controls',{}).get('rows',[]) if not r['passed']]}))
for number in range(1,4):
 trial=ROOT/'pilot'/('trial-'+str(number))
 if not trial.exists():continue
 result={'trial':number}
 for filename in ['ready.json','failure.json','isolation.json','quarantine.json','browser-ready.json','browser-failure.json','resumption.json','completed.json']:
  p=trial/filename
  if p.exists():
   value=json.loads(p.read_text())
   result[filename]={k:value[k] for k in ('prepared','error_type','phase','case','control','rows','persistent_cut','independent_cut_ms','completed','manual','all_refused','valid_old_ticket_tested') if k in value}
 print(json.dumps(result))
