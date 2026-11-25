"""Pure OPS-C1 decisions. Absence of evidence is never evidence for a refund."""
import copy
import datetime as dt
import hashlib
import json

class PendingEvidence(RuntimeError):
    pass

def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,default=str,separators=(',',':')).encode()).hexdigest()

def day_key(value):
    if isinstance(value,dt.datetime):return value.strftime('%Y-%m-%d')
    if not isinstance(value,str):raise PendingEvidence('invalid_original_day')
    try:return dt.date.fromisoformat(value[:10]).isoformat()
    except ValueError:raise PendingEvidence('invalid_original_day')

def quota_receipt(run,account):
    if account is None or str(account['_id'])!=str(run['runner_id']):
        raise PendingEvidence('original_executor_missing')
    matches=[v for v in account.get('quotaLedger',[]) if v['run_id']==str(run['_id'])]
    if len(matches)!=1:raise PendingEvidence('debit_receipt_missing_or_duplicate')
    receipt=matches[0]
    for field,value in [('project_id',run['project_id']),('owner_id',run['user_id']),
                        ('executor_id',run['runner_id']),('generation',run['token'])]:
        if str(receipt.get(field))!=str(value):raise PendingEvidence('debit_binding_conflict')
    cost=run['cost']
    if any(type(cost.get(k)) is not int or cost[k]<0 for k in ('image','video')):
        raise PendingEvidence('cost_unknown')
    if receipt.get('image_cost')!=cost['image'] or receipt.get('video_cost')!=cost['video'] or \
       receipt.get('requested')!=cost['image']+cost['video']:
        raise PendingEvidence('debit_cost_conflict')
    expected=receipt['requested'] if receipt.get('profile')=='free' else 0
    if type(receipt.get('charged')) is not int or receipt.get('profile') not in ('anonymous','free','premium') or receipt.get('charged')!=expected:
        raise PendingEvidence('debit_profile_conflict')
    if receipt.get('profile')=='anonymous' and receipt['requested']!=0:
        raise PendingEvidence('anonymous_charge_conflict')
    return receipt

def refund_change(account,run,identifier):
    """Caller CASes operations, marker and revision together in ONE user update."""
    receipt=quota_receipt(run,account)
    amount=receipt['charged'];original_day=day_key(receipt['day'])
    existing=receipt.get('compensation')
    if existing:
        if not isinstance(existing.get('id'),str) or not existing['id'] or existing.get('amount')!=amount or day_key(existing.get('day'))!=original_day or \
           type(existing.get('before')) is not int or type(existing.get('after')) is not int or \
           existing['before']<amount or existing['after']!=existing['before']-amount:
            raise PendingEvidence('compensation_conflict')
        return None,{'status':'already_applied','identifier':existing['id'],'amount':amount}
    if amount and account.get('legacyQuotaRevision',0)!=receipt.get('legacy_revision',0):
        raise PendingEvidence('untracked_quota_change')
    updated=copy.deepcopy(account)
    days=[entry for entry in updated.get('operations',[]) if day_key(entry['day'])==original_day]
    if amount and (len(days)!=1 or days[0]['processed']<amount):
        raise PendingEvidence('original_day_balance_ambiguous')
    before=days[0]['processed'] if days else 0
    if days:days[0]['processed']-=amount
    entry=next(v for v in updated['quotaLedger'] if v['run_id']==str(run['_id']))
    entry['compensation']={'id':identifier,'amount':amount,'day':original_day,
                           'before':before,'after':before-amount}
    return updated,{'status':'applied','identifier':identifier,'amount':amount,
                    'day':original_day,'before':before,'after':before-amount}

def classification(run,project,account,results,objects):
    """A commit proof is immutable domain evidence, not a queue acknowledgement."""
    if run.get('schema_version')!=1:return {'state':'indeterminate','reason':'legacy_run_without_evidence'}
    proofs=[run.get('commitProof'),project.get('committedRun'),project.get('prevCommittedRun')]
    proof=next((p for p in proofs if p and p.get('run_id')==str(run['_id'])),None)
    try:receipt=quota_receipt(run,account)
    except PendingEvidence as error:
        if not proof and run.get('debit_state') in ('not_requested','rejected') and not results and not run.get('artifacts'):
            return {'state':'lost','reason':'never_admitted','refund':0}
        return {'state':'indeterminate','reason':str(error)}
    if proof:
        manifest=[]
        for row in sorted(results,key=lambda r:str(r['_id'])):
            manifest.append(dict(result_id=str(row['_id']),img_id=str(row['img_id']),
                key=f"users/{run['user_id']}/projects/{run['project_id']}/out/{row['img_key']}",
                img_key=row['img_key'],sha256=row.get('sha256'),size=row.get('size'),type=row.get('type')))
        digest=hashlib.sha256(json.dumps(manifest,separators=(',',':')).encode()).hexdigest()
        if proof.get('token')!=run['token'] or proof.get('manifest_sha256')!=digest or proof.get('output_count')!=len(manifest):
            return {'state':'indeterminate','reason':'commit_manifest_conflict'}
        expected={str(v['img_id']) for v in run.get('jobs',[])}
        if not manifest or {str(v['img_id']) for v in manifest}!=expected:
            return {'state':'indeterminate','reason':'commit_manifest_incomplete'}
        for item in manifest:
            row=next((r for r in results if str(r['_id'])==str(item['result_id'])),None)
            obj=objects.get(item['key'])
            if not row or str(row.get('run_id'))!=str(run['_id']) or row.get('token')!=run['token'] or \
               str(row.get('user_id'))!=str(run['user_id']) or str(row.get('project_id'))!=str(run['project_id']) or \
               row.get('sha256')!=item['sha256'] or row.get('img_key')!=item['img_key'] or \
               not obj or obj.get('sha256')!=item['sha256'] or obj.get('size')!=item['size']:
                return {'state':'indeterminate','reason':'confirmed_output_integrity_unknown'}
        return {'state':'confirmed','reason':'domain_commit_and_all_bytes_verified','refund':0}
    if project.get('committedToken')==run['token']:
        return {'state':'indeterminate','reason':'commit_pointer_without_complete_proof'}
    if receipt.get('charged',0) and account.get('legacyQuotaRevision',0)!=receipt.get('legacy_revision',0):
        return {'state':'indeterminate','reason':'untracked_quota_change'}
    return {'state':'lost','reason':'no_domain_commit_after_observed_isolation',
            'refund':0 if receipt.get('compensation') else receipt['charged']}
