const mongoose = require("mongoose");

const uploadSchema = new mongoose.Schema({
  ownerId: { type: mongoose.Schema.Types.ObjectId, required: true },
  projectId: { type: mongoose.Schema.Types.ObjectId, required: true },
  callerId: { type: mongoose.Schema.Types.ObjectId, required: true },
  shareId: String,
  transport: { type: String, enum: ["legacy", "direct"], required: true },
  state: { type: String, required: true },
  cleanup: { type: String, default: "none" },
  lateCleanupDone: { type: Boolean, default: false },
  generation: { type: Number, default: 1 },
  deadline: { type: Date, required: true },
  tokenExpiresAt: Date,
  tokenHash: { type: String, index: { unique: true, sparse: true } },
  slot: Number,
  name: String,
  mime: String,
  size: Number,
  maxBytes: Number,
  userType: String,
  objectName: String,
  stage: String,
  expectedVersion: Number,
  barrier: Number,
  mediaId: mongoose.Schema.Types.ObjectId,
  resultVersion: Number,
  declaredDuration: Number,
  declaredWidth: Number,
  declaredHeight: Number,
  cancelRequested: { type: Boolean, default: false },
  error: String,
}, { timestamps: true });

uploadSchema.index({ state: 1, deadline: 1 });
uploadSchema.index({ ownerId: 1, projectId: 1, state: 1 });

module.exports = mongoose.model("upload", uploadSchema);
