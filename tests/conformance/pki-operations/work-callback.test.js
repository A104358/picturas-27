// Verify the actual orchestrator adapter preserves ack timing while tracking promises.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
let record, handler, ack=0, resolve;
const channel={on(){},checkExchange(n,cb){cb();},checkQueue(n,cb){cb();},consume(n,cb){handler=cb;},ack(){ack++;}};
const connection={on(){},createChannel(cb){cb(null,channel);}};
const moduleFixture={exports:{}};
const fakeFS={readFileSync:()=>Buffer.from('SYNTHETIC-CA'),writeFileSync:(p,b)=>{record=JSON.parse(b);},renameSync(){}};
vm.runInNewContext(fs.readFileSync('projects/utils/rabbit_mq.js','utf8'),{
 module:moduleFixture,exports:moduleFixture.exports,Buffer,process:{pid:123,env:{}},console,setTimeout(){},
 require:name=>name==='fs'?fakeFS:{connect:(url,opts,cb)=>cb(null,connection)},
});
(async()=>{
 moduleFixture.exports.read_rabbit_msg('project_queue',()=>new Promise(done=>resolve=done));
 handler({});assert.equal(record.active_count,1);assert.equal(ack,1);
 resolve();await Promise.resolve();await Promise.resolve();assert.equal(record.active_count,0);
 console.log('PASS async callback remains visible while ack timing is unchanged; marker clears at completion');
 moduleFixture.exports.read_rabbit_msg('project_queue',()=>{});handler({});
 assert.equal(record.active_count,0);assert.equal(ack,2);
 console.log('PASS synchronous callback releases its marker without changing acknowledgement count');
})().catch(()=>{console.error('FAIL work callback conformance');process.exitCode=1;});
