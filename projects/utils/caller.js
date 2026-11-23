function getCallerId(req) {
  return req.internalIdentity?.sub || null;
}

module.exports = { getCallerId };
