const mongoose=require('mongoose');
const schema=new mongoose.Schema({
  _id:String, schema_version:{type:Number,default:1}, user_id:mongoose.Schema.Types.ObjectId,
  project_id:{type:mongoose.Schema.Types.ObjectId,index:true},runner_id:mongoose.Schema.Types.ObjectId,
  token:Number, phase:{type:String,index:true},debit_state:String,cost:mongoose.Schema.Types.Mixed,
  tools:[mongoose.Schema.Types.Mixed],sources:[mongoose.Schema.Types.Mixed],jobs:[mongoose.Schema.Types.Mixed],
  message_ids: [String], previousCommit: mongoose.Schema.Types.Mixed, previousCharged: Number,
  quotaReceipt:mongoose.Schema.Types.Mixed,commitProof:mongoose.Schema.Types.Mixed,
  invalidated:{type:Boolean,default:false},reconciliation:mongoose.Schema.Types.Mixed,
},{timestamps:true});
module.exports=mongoose.model('processing_run',schema);
