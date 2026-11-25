// Exercise the actual hooks' mutation functions under delayed network completion.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const ts=require(process.env.B9_TS_COMPILER||'typescript');
const id='000000000000000000000001';
const original={user:{_id:id,type:'anonymous',operations:[]},token:'FIXTURE-old'};
const replacement={...original,token:'FIXTURE-new'};
let raw=JSON.stringify(original), events=[],registers=0,held=false;
let validate=async()=>original;
const qc={invalidateQueries(){},removeQueries(){}};
const storage={getItem:()=>raw,setItem:(k,v)=>{raw=v;},removeItem:()=>{raw=null;}};
const env={console,Event:class{constructor(type){this.type=type;}},localStorage:storage,
 window:{dispatchEvent:e=>events.push(e.type)},navigator:{locks:{request:async(name,opts,work)=>{
 if(held)return work(null);held=true;try{return await work({});}finally{held=false;}
 }}}};
const modules={};
function load(name){
 if(modules[name])return modules[name].exports;
 const m={exports:{}};modules[name]=m;
 const source=fs.readFileSync(path.join('frontend/lib',name+'.ts'),'utf8');
 const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText;
 vm.runInNewContext(compiled,{...env,module:m,exports:m.exports,require:(dep)=>{
 if(dep==='@tanstack/react-query')return {useMutation:c=>c,useQuery:c=>c,useQueryClient:()=>qc};
 if(dep==='next/navigation')return {useRouter:()=>({push(){}})};
 if(dep==='../users')return {deleteAccount:async()=>{}};
 if(dep==='../session')return {validateSession:i=>validate(i),register:async()=>{registers++;return replacement;},login:async()=>replacement};
 return load(path.posix.normalize(path.posix.join(path.posix.dirname(name),dep)));
 }},{filename:name});return m.exports;
}
(async()=>{
 const m=load('mutations/session'),q=load('queries/session');
 raw=null;assert.equal(q.useGetSession().queryFn(),null);assert.equal(registers,0);
 raw=JSON.stringify(original);const update=m.useUpdateSession();let resolve;
 validate=()=>new Promise(done=>{resolve=done;});
 const stale=update.mutationFn({userId:id,token:original.token});
 // An older client ignores the lock. CAS must still prevent the stale writer.
 raw=JSON.stringify(replacement);resolve(original);await assert.rejects(stale,/changed/);
 assert.equal(JSON.parse(raw).token,replacement.token);
 update.onError({response:{status:401}},{userId:id,token:original.token});assert.deepEqual(events,[]);
 console.log('PASS AR-10: delayed validation cannot replace or invalidate a newer saved session');
 held=true;const register=m.useRegister();await assert.rejects(register.mutationFn({type:'anonymous'}),/another tab/);
 assert.equal(registers,0);held=false;
 console.log('PASS AR-09/10: empty query never registers; an active recovery lock rejects registration before its request');
 raw=JSON.stringify(original);events=[];update.onError(new Error('network'),{token:original.token});assert.equal(events.length,0);
 update.onError({response:{status:401}},{token:original.token});assert.deepEqual(events,['picturas-session-invalid']);
 assert.equal(JSON.parse(raw).token,original.token);assert.equal(registers,0);
 console.log('PASS SEC-01/02: rejected/network validation never logs out or creates an identity');
 const logout=m.useLogout();await logout.mutationFn();logout.onSuccess();assert.equal(raw,null);assert.equal(registers,0);
 console.log('PASS SEC-02: voluntary logout removes only the local session, without registration');
})().catch(()=>{console.error('FAIL B9 mutation conformance');process.exitCode=1;});
