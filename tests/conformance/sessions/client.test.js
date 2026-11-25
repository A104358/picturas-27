// Execute production TS modules with controlled transport/storage failures.
const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');
const path=require('node:path');const ts=require(process.env.B9_TS_COMPILER||'typescript');
let raw=null, failWrite=false, checked=0, writes=0, events=0;
const id='000000000000000000000001';
const token='fixture.'+Buffer.from(JSON.stringify({sub:id})).toString('base64url')+'.signature';
const session={user:{_id:id,type:'anonymous',operations:[]},token};
let validate=async()=>session;
const cache={};const env={console,TextEncoder,atob,Event:class{},navigator:{},
 localStorage:{getItem:()=>raw,setItem:(k,v)=>{if(failWrite)throw Error('storage unavailable');raw=v;writes++;}},
 window:{dispatchEvent:()=>events++}};
function load(file){if(cache[file])return cache[file].exports;const m={exports:{}};cache[file]=m;
 const src=fs.readFileSync(path.resolve('frontend/lib',file+'.ts'),'utf8');
 const compiled=ts.transpileModule(src,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText;
 vm.runInNewContext(compiled,{...env,module:m,exports:m.exports,require:(name)=>name==='./session'?{
 validateSession:async(input)=>{checked++;assert.equal(input.userId,id);return validate(input);}}:load(name.replace('./',''))},{filename:file});return m.exports;}
(async()=>{
 const state=load('session-state'),r=load('session-recovery');
 const bundle={schema_version:1,case_ref:'FIXTURE',installation_ref:'FIXTURE',intended_origin:'https://fixture.invalid',
 issued_at:'2026-11-24T00:00:00Z',expires_at:'2026-12-01T00:00:00Z',token};
 const text=JSON.stringify(bundle);
 assert.equal(r.parseRecoveryBundle(text+' '.repeat(16384-text.length),bundle.intended_origin).token,token);
 assert.throws(()=>r.parseRecoveryBundle(text+' '.repeat(16385-text.length),bundle.intended_origin));
 for(const bad of ['{',JSON.stringify({...bundle,token:'x'.repeat(8193)}),JSON.stringify({...bundle,intended_origin:'https://wrong.invalid'}),JSON.stringify({...bundle,user:{_id:id}})])
 assert.throws(()=>r.parseRecoveryBundle(bad,bundle.intended_origin));
 console.log('PASS AR-07: exact 16 KiB/+1, 8 KiB token, invalid JSON, origin and untrusted fields');
 const valid=await r.validateRecovery(bundle,id,'FIXTURE');assert.equal(writes,0);
 validate=async()=>{throw {response:{status:401}};};await assert.rejects(r.validateRecovery(bundle,id,'FIXTURE'));assert.equal(writes,0);
 validate=async()=>{throw Error('network');};await assert.rejects(r.validateRecovery(bundle,id,'FIXTURE'));assert.equal(writes,0);
 validate=async()=>({...session,user:{...session.user,type:'premium'}});await assert.rejects(r.validateRecovery(bundle,id,'FIXTURE'));
 validate=async()=>session;await assert.rejects(r.validateRecovery(bundle,'000000000000000000000002','FIXTURE'));
 console.log('PASS AR-05/08: only server-validated matching anonymous subject can reach import; failures write nothing');
 validate=async()=>{throw {response:{status:401}};};
 await assert.rejects(r.confirmRecovery(valid,null,()=>true));assert.equal(writes,0);
 validate=async()=>session;await assert.rejects(r.confirmRecovery(valid,null,()=>false));assert.equal(writes,0);
 console.log('PASS AR-06/10: expiry during confirmation and invalidated generation never write a candidate');
 raw=JSON.stringify({...session,user:{...session.user,_id:'000000000000000000000002'}});
 assert.throws(()=>r.importRecovery(valid,raw));const other=raw;assert.equal(raw,other);
 raw=JSON.stringify(session);const original=raw;raw='changed';assert.throws(()=>state.saveSessionIfCurrent(session,original));
 raw=original;failWrite=true;assert.throws(()=>r.importRecovery(valid,original));assert.equal(raw,original);failWrite=false;
 r.importRecovery(valid,original);assert.equal(JSON.parse(raw).token,token);
 console.log('PASS AR-08/10: storage refusal, different identity and stale completion preserve saved session');
 env.navigator.locks={request:async(name,options,callback)=>callback(null)};
 await assert.rejects(state.withSessionLock(async()=>{throw Error('must not run');}),/another tab/);
 assert.equal(state.parseStoredSession('{'),null);
 state.signalSessionError({});assert.equal(events,1);state.signalSessionError({response:{status:401}});assert.equal(events,2);
 console.log('PASS AR-10/SEC-02: held recovery lock rejects writers; network errors never signal logout');
})().catch(()=>{console.error('FAIL B9 client conformance');process.exitCode=1;});
