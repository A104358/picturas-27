"""Known-state financial fixtures: no host clocks, Docker or real user data."""
import copy,datetime,hashlib,json,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('policy',Path(__file__).resolve().parents[3]/'ops/reconcile_policy.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class PolicyTests(unittest.TestCase):
 def fixtures(self):
  run={'_id':'RUN','schema_version':1,'runner_id':'EDITOR','user_id':'OWNER','project_id':'PROJECT','token':7,
       'cost':{'image':2,'video':3},'jobs':[{'img_id':'IMAGE'},{'img_id':'VIDEO'}],'debit_state':'requested'}
  receipt={'run_id':'RUN','project_id':'PROJECT','owner_id':'OWNER','executor_id':'EDITOR','generation':7,
           'day':'2026-11-23','image_cost':2,'video_cost':3,'requested':5,'charged':5,'profile':'free','legacy_revision':0}
  account={'_id':'EDITOR','quotaLedger':[receipt],'operations':[
   {'day':datetime.datetime(2026,11,23),'processed':5},{'day':datetime.datetime(2026,11,24),'processed':3}]}
  return run,account
 def test_mixed_refund_uses_original_editor_and_day_not_current_day(self):
  run,user=self.fixtures();changed,effect=p.refund_change(user,run,'CASE:RUN')
  self.assertEqual(changed['operations'][0]['processed'],0);self.assertEqual(changed['operations'][1]['processed'],3)
  self.assertEqual(effect['amount'],5);self.assertEqual(user['operations'][0]['processed'],5)
 def test_crash_after_atomic_effect_before_journal_never_refunds_twice(self):
  run,user=self.fixtures();changed,_=p.refund_change(user,run,'CASE:RUN')
  again,effect=p.refund_change(changed,run,'CASE:RUN')
  self.assertIsNone(again);self.assertEqual(effect['status'],'already_applied')
 def test_new_case_identifier_cannot_repeat_the_same_run_compensation(self):
  run,user=self.fixtures();changed,_=p.refund_change(user,run,'FIRST:RUN')
  again,effect=p.refund_change(changed,run,'SECOND:RUN');self.assertIsNone(again)
  self.assertEqual(effect['identifier'],'FIRST:RUN')
 def test_absent_or_ambiguous_receipt_stays_pending_without_financial_effect(self):
  run,user=self.fixtures();user['quotaLedger']=[]
  self.assertEqual(p.classification(run,{},user,[],{})['state'],'indeterminate')
  with self.assertRaises(p.PendingEvidence):p.refund_change(user,run,'CASE:RUN')
 def test_owner_is_never_substituted_for_executor(self):
  run,user=self.fixtures();user['_id']='OWNER'
  with self.assertRaisesRegex(p.PendingEvidence,'executor'):p.refund_change(user,run,'CASE:RUN')
 def test_untracked_change_or_underflow_does_not_invent_credit(self):
  for mutate in [lambda u:u.update(legacyQuotaRevision=1),lambda u:u['operations'][0].update(processed=4)]:
   run,user=self.fixtures();mutate(user)
   with self.assertRaises(p.PendingEvidence):p.refund_change(user,run,'CASE:RUN')
 def test_premium_receipt_has_zero_compensation(self):
  run,user=self.fixtures();user['quotaLedger'][0].update(profile='premium',charged=0)
  changed,effect=p.refund_change(user,run,'CASE:RUN');self.assertEqual(effect['amount'],0)
  self.assertEqual(changed['operations'],user['operations'])
 def test_reply_without_domain_commit_does_not_promote_output(self):
  run,user=self.fixtures();result=p.classification(run,{'activeToken':7,'committedToken':6},user,[],{})
  self.assertEqual(result['state'],'lost');self.assertEqual(result['refund'],5)
 def test_commit_pointer_without_manifest_remains_indeterminate(self):
  run,user=self.fixtures();self.assertEqual(p.classification(run,{'committedToken':7},user,[],{})['state'],'indeterminate')
 def confirmed(self):
  run,user=self.fixtures();rows=[];objects={};manifest=[]
  for image in ('IMAGE','VIDEO'):
   key=f'users/OWNER/projects/PROJECT/out/{image}.png';sha=hashlib.sha256(image.encode()).hexdigest()
   row={'_id':image,'img_id':image,'run_id':'RUN','token':7,'user_id':'OWNER','project_id':'PROJECT',
        'img_key':image+'.png','sha256':sha,'size':5,'type':'image'}
   rows.append(row);objects[key]={'sha256':sha,'size':5}
   manifest.append(dict(result_id=image,img_id=image,key=key,img_key=row['img_key'],sha256=sha,size=5,type='image'))
  proof={'run_id':'RUN','token':7,'output_count':2,'manifest_sha256':hashlib.sha256(json.dumps(manifest,separators=(',',':')).encode()).hexdigest()}
  return run,user,rows,objects,{'committedToken':7,'committedRun':proof}
 def test_confirmed_requires_domain_digest_and_all_actual_bytes(self):
  run,user,rows,objects,project=self.confirmed()
  self.assertEqual(p.classification(run,project,user,rows,objects)['state'],'confirmed')
  next(iter(objects.values()))['sha256']='changed'
  self.assertEqual(p.classification(run,project,user,rows,objects)['state'],'indeterminate')
 def test_result_binding_or_missing_frame_cannot_be_promoted(self):
  run,user,rows,objects,project=self.confirmed();rows[0]['run_id']='OTHER'
  self.assertEqual(p.classification(run,project,user,rows,objects)['state'],'indeterminate')
  run,user,rows,objects,project=self.confirmed();rows.pop()
  self.assertEqual(p.classification(run,project,user,rows,objects)['state'],'indeterminate')
if __name__=='__main__':unittest.main(verbosity=2)
