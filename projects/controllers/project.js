var Project = require("../models/project");
const ProjectModel = require("../models/project");

// DELETE condicional por versão
module.exports.deleteIfVersion = async (user_id, project_id, expectedVersion) => {
  const res = await Project.deleteOne({
    user_id: user_id,
    _id: project_id,
    version: expectedVersion,
  });

  return res.deletedCount === 1;
};

// Adicionar share link (atómico + versão)
module.exports.addShareLinkIfVersion = async (
  user_id,
  project_id,
  newLink,
  expectedVersion
) => {
  return await Project.findOneAndUpdate(
    { user_id: user_id, _id: project_id, version: expectedVersion },
    { $push: { sharedLinks: newLink }, $inc: { version: 1 } },
    { new: true }
  ).exec();
};

// Revogar share link (atómico + versão)
module.exports.revokeShareLinkIfVersion = async (
  user_id,
  project_id,
  shareId,
  expectedVersion
) => {
  return await Project.findOneAndUpdate(
    {
      user_id: user_id,
      _id: project_id,
      version: expectedVersion,
      "sharedLinks.id": shareId,
    },
    { $set: { "sharedLinks.$.revoked": true }, $inc: { version: 1 } },
    { new: true }
  ).exec();
};

module.exports.getAll = async (user_id) => {
  return await Project.find({ user_id: user_id }).sort({ _id: 1 }).exec();
};

module.exports.getOne = async (user_id, project_id) => {
  return await Project.findOne({ user_id: user_id, _id: project_id }).exec();
};

module.exports.create = async (project) => {
  return await Project.create(project);
};

module.exports.update = (user_id, project_id, project) => {
  return Project.updateOne({ user_id: user_id, _id: project_id }, project);
};

module.exports.delete = (user_id, project_id) => {
  return Project.deleteOne({ user_id: user_id, _id: project_id });
};

// Devolve o projeto que contém este shareId
module.exports.getOneByShareId = (shareId) =>
  Project.findOne({ "sharedLinks.id": shareId }).exec();

module.exports.updateIfVersion = async (user_id, project_id, project, expectedVersion, processing = false) => {
  const raw = project.toObject ? project.toObject() : project;

  // remove campos que não se quer "setar"
  const { _id, user_id: _uid, version, __v, sharedLinks, uploadBarrier, ...rest } = raw;

  // The background video hash changes media without changing the public project
  // version. Retry an internal race and carry its latest hash into the snapshot.
  for (let retry = 0; retry < 5; retry++) {
    const current = await Project.findOne({ user_id, _id: project_id, version: expectedVersion }).lean();
    if (!current) return null;
    // A worker can commit without changing the editor's public version. Ordinary
    // edits must carry forward that state, rather than write an older snapshot.
    const execution = ['activeToken','committedToken','resultsToken','committedTools',
      'committedRun','prevCommittedRun','processingRunId','reconciliationHold','pendingAdvancedOps','chargedAdvancedTools'];
    if (!processing) for (const key of execution) {
      if (current[key] !== undefined) rest[key] = current[key]; else delete rest[key];
    }
    const byId = new Map((current.imgs || []).map((img) => [String(img._id), img]));
    const imgs = (rest.imgs || []).map((img) => {
      const latest = byId.get(String(img._id));
      if (!latest) return img;
      return { ...img, og_sha256: latest.og_sha256, hash_state: latest.hash_state };
    });
    const updated = await Project.findOneAndUpdate(
      { user_id, _id: project_id, version: expectedVersion, __v: current.__v },
      { $set: { ...rest, imgs }, $inc: { version: 1, __v: 1 } },
      { new: true }
    ).exec();
    if (updated) return updated;
  }
  return null;
};

module.exports.updateRaw = async (user_id, project_id, update) => {
  return await ProjectModel.updateOne(
    { user_id, _id: project_id },
    update
  ).exec();
};


// Commit only if cancellation/new processing has not changed the active run.
module.exports.commitRunIfActive = async (user_id, project_id, token, tools, proof = null) => {
  const query = { user_id, _id: project_id, activeToken: token };
  const fields = { committedToken: token, resultsToken: token, committedTools: tools };
  if (proof) {
    query.processingRunId = proof.run_id;
    query.reconciliationHold = { $ne: true };
    Object.assign(fields,{committedRun:proof,processingRunId:null,pendingAdvancedOps:0,chargedAdvancedTools:proof.chargedAdvancedTools});
  }
  return Project.findOneAndUpdate(
    query,
    { $set: fields, $inc: { __v: 1 } },
    { new: true }
  ).exec();
};
