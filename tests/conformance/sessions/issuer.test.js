const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execute, fingerprint } = require('../../../users/admin/sessionRecovery');
const template = require('../../../docs/templates/anonymous-session-recovery-case.template.json');
const account = { _id: '000000000000000000000001', type: 'anonymous', operations: [] };
const expected = { installation: 'FIXTURE-installation', dataset: 'FIXTURE-dataset', issuer: 'FIXTURE-issuer' };
function fixture() {
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'picturas-b9-unit-')); fs.chmodSync(dir,0o700);
 const file=path.join(dir,'case.json');
 const record=structuredClone(template);
 Object.assign(record,{template_only:false,case_ref:'FIXTURE-case',installation_ref:expected.installation,
   dataset_ref:expected.dataset,administrator_ref:'FIXTURE-admin',browser_profile_ref:'FIXTURE-browser',
   subject_id:account._id,state:'approved'});
 Object.assign(record.evidence,{existence_status:'verified',source_ref:'FIXTURE-independent-source',
   trusted_provenance_basis:'Synthetic test only',independent_association_basis:'Synthetic test only',
   verified_by:'FIXTURE-admin',verified_at:'2026-11-24T00:00:00Z', account_fingerprint:fingerprint(account)});
 Object.assign(record.approval,{status:'approved',approved_by:'FIXTURE-admin',approved_at:'2026-11-24T00:00:00Z'});
 Object.assign(record.target,{issuer:expected.issuer,expected_subject_id:account._id,
   controlled_destination_verified_at:'2026-11-24T00:00:00Z'});
 const save=()=>fs.writeFileSync(file,JSON.stringify(record),{mode:0o600}); save();
 let issued=0;
 const deps={findAccount:async()=>structuredClone(account), issue:()=>{issued++;return 'SYNTHETIC-NON-JWT';},
   verify:()=>({sub:account._id,iat:100,exp:604900})};
 return {dir,file,record,save,deps,count:()=>issued, run:()=>execute('issue',file,'delivery.json',expected,deps),
   close:()=>fs.rmSync(dir,{recursive:true,force:true})};
}
test('AR-01 evidence/template/approval gates preserve case and issue nothing',async()=>{
 for(const alter of [r=>r.template_only=true,r=>r.state='pending_evidence',r=>r.evidence.source_ref='',
  r=>r.evidence.independent_association_basis='',r=>r.approval.status='pending']) {
  const f=fixture();try{alter(f.record);f.save();const before=fs.readFileSync(f.file);await assert.rejects(f.run());
   assert.equal(f.count(),0);assert.deepEqual(fs.readFileSync(f.file),before);}finally{f.close();}
 }
});
test('AR-02 same identity, private exclusive delivery and journal contains no token',async()=>{
 const f=fixture();try{assert.equal((await f.run()).state,'issued');
 const st=fs.statSync(path.join(f.dir,'delivery.json'));assert.equal(st.mode&0o777,0o600);
 const journal=fs.readFileSync(f.file,'utf8');assert(!journal.includes('SYNTHETIC-NON-JWT'));
 assert.equal(JSON.parse(fs.readFileSync(path.join(f.dir,'delivery.json'))).token,'SYNTHETIC-NON-JWT');
 await assert.rejects(f.run());assert.equal(f.count(),1);}finally{f.close();}
});
test('AR-03 missing/registered/changed account and wrong destination fail before issuance',async()=>{
 for(const other of [null,{...account,type:'free'},{...account,operations:[{processed:1}]}]){
 const f=fixture();try{f.deps.findAccount=async()=>other;await assert.rejects(f.run());assert.equal(f.count(),0);}finally{f.close();}}
 for(const alter of [r=>r.dataset_ref='WRONG',r=>r.target.issuer='WRONG',r=>r.target.expected_subject_id='WRONG']){
 const f=fixture();try{alter(f.record);f.save();await assert.rejects(f.run());assert.equal(f.count(),0);}finally{f.close();}}
});
test('AR-04 existing output, concurrent lock and ambiguous crash are reconciliable',async()=>{
 const f=fixture();try{
 fs.writeFileSync(path.join(f.dir,'delivery.json'),'existing',{mode:0o600});await assert.rejects(f.run());assert.equal(f.count(),0);
 fs.unlinkSync(path.join(f.dir,'delivery.json'));
 fs.writeFileSync(f.file+'.lock','',{mode:0o600});await assert.rejects(f.run(),{code:'case_locked'});fs.unlinkSync(f.file+'.lock');
 f.deps.issue=()=>{throw Error('crash fixture');};await assert.rejects(f.run());
 assert.equal(JSON.parse(fs.readFileSync(f.file)).state,'issued_unconfirmed');await assert.rejects(f.run());
 const s=await execute('status',f.file,null,expected,f.deps);assert.equal(s.reconciliation_required,true);
 }finally{f.close();}
});
test('AR-12 unsafe permissions, symlink and path traversal are refused',async()=>{
 const f=fixture();try{fs.chmodSync(f.file,0o644);await assert.rejects(f.run(),{code:'unsafe_permissions'});fs.chmodSync(f.file,0o600);
 await assert.rejects(execute('issue',f.file,'../leak.json',expected,f.deps),{code:'unsafe_output'});
 assert.equal(f.count(),0);const link=path.join(f.dir,'link.json');fs.symlinkSync(f.file,link);
 await assert.rejects(execute('issue',link,'delivery.json',expected,f.deps),{code:'unsafe_path'});
 }finally{f.close();}
});
test('AR-04 real concurrent attempts serialize and post-output crash keeps durable ambiguity',async()=>{
 const f=fixture();try{
 let release;f.deps.findAccount=()=>new Promise(done=>{release=done;});
 const first=f.run();await assert.rejects(f.run(),{code:'case_locked'});release(structuredClone(account));await first;
 assert.equal(f.count(),1);
 }finally{f.close();}
 const g=fixture();const originalRename=fs.renameSync;let calls=0;
 try{
 fs.renameSync=(...args)=>{if(++calls===2)throw Error('post-output crash fixture');return originalRename(...args);};
 await assert.rejects(g.run());assert.equal(g.count(),1);
 assert(fs.existsSync(path.join(g.dir,'delivery.json')));
 assert.equal(JSON.parse(fs.readFileSync(g.file)).state,'issued_unconfirmed');
 await assert.rejects(g.run());assert.equal(g.count(),1);
 }finally{fs.renameSync=originalRename;g.close();}
});
test('AR-12 case storage in the application or repository is refused',async()=>{
 await assert.rejects(execute('status',path.resolve('users/private-case.json'),null,expected,{}),
  {code:'case_must_be_outside_application'});
});
