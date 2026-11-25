const {test}=require('node:test');
const assert=require('node:assert/strict');

async function withProjectModel(callback) {
  const modelPath=require.resolve('../models/project'),controllerPath=require.resolve('../controllers/project');
  const modelBefore=require.cache[modelPath],controllerBefore=require.cache[controllerPath];
  const state={_id:'p',user_id:'u',name:'old',version:4,__v:1,imgs:[],tools:[],activeToken:7,
    committedToken:6,resultsToken:6,processingRunId:'RUN',pendingAdvancedOps:2,committedRun:{run_id:'PREVIOUS'}};
  const stale=structuredClone(state);let raced=false;
  const finishWorker=()=>Object.assign(state,{__v:state.__v+1,committedToken:7,resultsToken:7,
    committedRun:{run_id:'RUN'},processingRunId:null,pendingAdvancedOps:0});
  const model={
    findOne:()=>({lean:async()=>structuredClone(state)}),
    findOneAndUpdate(query,update){return {exec:async()=>{
      if(model.injectRace&&!raced){raced=true;finishWorker();}
      if(Object.entries(query).some(([key,value])=>state[key]!==value))return null;
      Object.assign(state,structuredClone(update.$set));
      for(const [key,value] of Object.entries(update.$inc))state[key]=(state[key]||0)+value;
      return structuredClone(state);
    }};},
  };
  require.cache[modelPath]={id:modelPath,filename:modelPath,loaded:true,exports:model};
  delete require.cache[controllerPath];
  try {await callback({Project:require('../controllers/project'),state,stale,finishWorker,model});}
  finally {
    if(modelBefore)require.cache[modelPath]=modelBefore;else delete require.cache[modelPath];
    if(controllerBefore)require.cache[controllerPath]=controllerBefore;else delete require.cache[controllerPath];
  }
}
test('an editor snapshot cannot roll back a worker commit with the same public version',async()=>{
  await withProjectModel(async({Project,state,stale,finishWorker})=>{
    finishWorker();stale.name='edited';await Project.updateIfVersion('u','p',stale,4);
    assert.equal(state.name,'edited');assert.equal(state.version,5);
    assert.deepEqual(state.committedRun,{run_id:'RUN'});assert.equal(state.processingRunId,null);
    assert.equal(state.committedToken,7);assert.equal(state.pendingAdvancedOps,0);
  });
});
test('a worker commit between read and CAS is preserved when the editor retries',async()=>{
  await withProjectModel(async({Project,state,stale,model})=>{
    model.injectRace=true;stale.name='edited';await Project.updateIfVersion('u','p',stale,4);
    assert.equal(state.name,'edited');assert.equal(state.version,5);assert.equal(state.__v,3);
    assert.deepEqual(state.committedRun,{run_id:'RUN'});assert.equal(state.processingRunId,null);
  });
});
