const mongoose=require('mongoose');
const schema=new mongoose.Schema({
  run_id:{type:String,index:true},artifact_id:String,img_id:mongoose.Schema.Types.ObjectId,
  key:String,img_key:String,sha256:String,size:Number,type:String,file_name:String,
  result_id:mongoose.Schema.Types.ObjectId,
},{timestamps:true});
schema.index({run_id:1,artifact_id:1},{unique:true});
module.exports=mongoose.model('processing_artifact',schema);
