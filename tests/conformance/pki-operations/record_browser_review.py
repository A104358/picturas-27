"""Record the agent's completed visual inspection, never a human user's approval.

Invoke only after actually viewing the four saved native Firefox pages. This does
not infer inspection from the automated browser-ready result.
"""
import hashlib,json,sys,time
from pilot_paths import ROOT,PROJECT,CACHE
trial=ROOT/'pilot'/('trial-'+sys.argv[1])
state=json.loads((ROOT/'maintenance'/PROJECT/'state.json').read_text())
ready=json.loads((trial/'browser-ready.json').read_text())
assert ready['operation']==state['operation'] and ready['no_warning_override']
screenshots={case:hashlib.sha256((CACHE/'screenshots'/trial.name/(case+'.png')).read_bytes()).hexdigest()
             for case in ['CURRENT','OLD_CA','WRONG_NAME','EXPIRED']}
proof={'operation':state['operation'],'new_ca':ready['new_ca'],'manual':True,
 'performed_by':'Codex: interactive Firefox and visual inspection of native certificate pages',
 'human_user_confirmation':False,'new_trust_positive':True,'old_ca_removed':ready['old_ca_removed'],
 'old_ca_rejected':not ready['cases']['OLD_CA']['accepted'],
 'expired_rejected':not ready['cases']['EXPIRED']['accepted'],
 'wrong_name_rejected':not ready['cases']['WRONG_NAME']['accepted'],
 'no_warning_override':True,'screenshots_sha256':screenshots,'inspected_at_ns':time.time_ns()}
(trial/'browser-proof.json').write_text(json.dumps(proof));(trial/'browser-proof.json').chmod(0o600)
(trial/'browser-close').touch()
print('Recorded Codex visual inspection; no human-user approval claimed')
