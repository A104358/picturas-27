const {test}=require('node:test');
const assert=require('node:assert/strict');
test('tool parameters cannot replace the input or output bound to the run',()=>{
  const rabbitPath=require.resolve('../utils/rabbit_mq'),messagePath=require.resolve('../utils/project_msg');
  const rabbitBefore=require.cache[rabbitPath],messageBefore=require.cache[messagePath];
  let sent;
  require.cache[rabbitPath]={id:rabbitPath,filename:rabbitPath,loaded:true,exports:{
    send_rabbit_msg:(message,queue)=>{sent={message,queue};},read_rabbit_msg:()=>{},
  }};
  delete require.cache[messagePath];
  try {
    require('../utils/project_msg').send_msg_tool('request','time','/own/src/input.png','/own/out/output.png','resize',
      {width:16,height:16,inputImageURI:'/another/run/src/input.png',outputImageURI:'/another/run/out/output.png'});
    assert.equal(sent.queue,'resize_queue');
    assert.deepEqual(sent.message.parameters,{width:16,height:16,
      inputImageURI:'/own/src/input.png',outputImageURI:'/own/out/output.png'});
  } finally {
    if(rabbitBefore)require.cache[rabbitPath]=rabbitBefore;else delete require.cache[rabbitPath];
    if(messageBefore)require.cache[messagePath]=messageBefore;else delete require.cache[messagePath];
  }
});
