const mongoose = require("mongoose");

const schema = new mongoose.Schema({
  _id: Number,
  uploadId: mongoose.Schema.Types.ObjectId,
  leaseUntil: Date,
}, { versionKey: false });

module.exports = mongoose.model("uploadSlot", schema);
