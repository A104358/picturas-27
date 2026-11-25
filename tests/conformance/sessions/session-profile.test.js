// Synthetic issuer and isolated JWT verifier clock; never alter the host clock.
const assert=require('node:assert/strict');const crypto=require('node:crypto');
process.env.JWT_SECRET_KEY=crypto.randomBytes(48).toString('hex');
process.env.JWT_ISSUER='FIXTURE-issuer';process.env.JWT_AUDIENCE='FIXTURE-audience';
const auth=require('/app/auth/auth');const jwt=require('/app/node_modules/jsonwebtoken');
const user={_id:'000000000000000000000001'};
const token=auth.get_jwt(user),claims=auth.verify_session(token);
assert.equal(claims.sub,user._id);assert.equal(claims.exp-claims.iat,604800);
const options={algorithms:['HS256'],issuer:process.env.JWT_ISSUER,audience:process.env.JWT_AUDIENCE,
 clockTolerance:0,maxAge:604800,clockTimestamp:claims.exp-1};
assert.equal(jwt.verify(token,process.env.JWT_SECRET_KEY,options).sub,user._id);
assert.throws(()=>jwt.verify(token,process.env.JWT_SECRET_KEY,{...options,clockTimestamp:claims.exp}));
assert.throws(()=>jwt.verify(token,process.env.JWT_SECRET_KEY,{...options,clockTimestamp:claims.exp+1}));
assert.throws(()=>jwt.verify(token,crypto.randomBytes(48).toString('hex'),options));
assert.throws(()=>auth.verify_session(jwt.sign({...claims,iat:Math.floor(Date.now()/1000)+60},process.env.JWT_SECRET_KEY,{algorithm:'HS256',header:{typ:'picturas-session+jwt'}})));
assert.equal(auth.validate_jwt({_id:'000000000000000000000002'},token),false);
console.log('PASS S06/SEC-02: normal profile, same subject, absolute 7 days, exact expiry/+1 and different installation refusal');
