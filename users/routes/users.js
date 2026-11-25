var express = require("express");
var router = express.Router();

const axios = require("axios");
const fs = require("fs");
const https = require("https");

const auth = require("../auth/auth");
const User = require("../controllers/user");   

// lê as chaves/certificados locais (estes ficheiros EXISTEM no api-gateway-ms)

// agente HTTPS com cert + key
// Own certificate, installation CA, no cached TLS sessions (B5).
const httpsAgent = require("../tls/pkiTls").clientAgent();

// hostname interno do microserviço de users
const usersURL = "https://users:10001/";

// URL interna do microserviço de projects
const projects_ms = "https://projects:9001/";

const max_free_daily_op = process.env.FREE_DAILY_OP || 5;

function get_cur_date() {
  const date = new Date();
  const year = date.getUTCFullYear();
  const month = date.getUTCMonth();
  const day = date.getUTCDate();

  return { year: year, month: month, day: day };
}

function removeSensitiveInfo(user) {
  const userObj = user.toObject ? user.toObject() : user; // Ensure it's a plain object
  const { password_hash, ...userWithoutPassword } = userObj; // Destructure to exclude password_hash
  return userWithoutPassword;
}

function getRemainingOperations(user) {
  if (user.type === "premium") return null; 

  const { year, month, day } = get_cur_date();
  const today = new Date(year, month, day);

  const opToday = user.operations.find(
    (o) => o.day.getTime() === today.getTime()
  );

  const used = opToday ? opToday.processed : 0;

  if (user.type === "free")
    return Math.max(0, max_free_daily_op - used);

  // anonymous não pode usar advanced_tools -> 0 operações “pagas”
  if (user.type === "anonymous") return 0;

  return 0;
}


function check_process(user, op, op_num) {
  if (op_num == 0) return true;

  return (
    user.type == "premium" ||
    (user.type == "free" && max_free_daily_op - op.processed >= op_num) ||
    (user.type == "anonymous" && op_num == 0)
  );
}

// Get list of all users
router.get("/", function (req, res, next) {
  User.getAll()
    .then((users) => res.status(200).jsonp(users))
    .catch((_) => res.status(700).jsonp(`Error acquiring all users`));
});

router.get("/validate/:user", function (req, res, next) {
  if (!req.headers.authorization) {
    return res.status(400).jsonp("Missing or invalid Authorization header.");
  }
  User.getOne(req.params.user)
    .then((user) => {
      const token = req.headers.authorization.split(" ")[1];
      try {
        const isValid = auth.validate_jwt(user, token);
        if (isValid) {
          const userResponse = removeSensitiveInfo(user);
          const remaining_operations = getRemainingOperations(user);

          res.status(200).json({
            user: { ...userResponse, remaining_operations },
            token: token,
          });
        } else res.status(401).jsonp("Invalid token.");
      } catch (err) {
        console.error(err);
        res.status(500).jsonp("Error validating token.");
      }
    })
    .catch((_) => res.status(701).jsonp(`Error acquiring user's information.`));
});

// Get specific user
router.get("/:user", function (req, res, next) {
  User.getOne(req.params.user)
    .then((user) => {
      const userResponse = removeSensitiveInfo(user);
      const remaining_operations = getRemainingOperations(user);
      res.status(200).jsonp({ ...userResponse, remaining_operations });
    })
    .catch((_) => res.status(701).jsonp(`Error acquiring user's information.`));
});

// Check user type
router.get("/:user/type/", function (req, res, next) {
  User.getOne(req.params.user)
    .then((user) => {
      res.status(200).send({ type: user.type });
    })
    .catch((_) => res.status(701).jsonp(`Error acquiring user's information.`));
});

// Test if we can process a project based on the number of advanced tools
const quotaLedger = require('../admin/quotaLedger');
router.get("/:user/process/:advanced_tools", async function (req, res) {
  try {
    const amount=Number(req.params.advanced_tools); const context=quotaLedger.contextFrom(req);
    const result=context ? await quotaLedger.admit(req.params.user,amount,context) : await quotaLedger.legacy(req.params.user,amount,'admit');
    return res.status(200).jsonp(result);
  } catch (error) { return res.status(error.status||503).jsonp(error.status?error.message:'Quota unavailable'); }
});


// Create a new user
router.post("/", function (req, res, next) {
  if (req.body.type && !["free", "anonymous"].includes(req.body.type)) {
    return res.status(403).jsonp("Account type not allowed at registration.");
  }
  const user = {
    name: req.body.name || undefined,
    email: req.body.email || undefined,
    type: req.body.type || "free",
    operations: [],
  };

  // Handle anonymous user properly
  if (req.body.type === "anonymous") {
    user.email = undefined;
    user.password = "";
  } else {
    user.password = req.body.password;
  }

  User.create(user)
    .then((createdUser) => {
      const userResponse = removeSensitiveInfo(createdUser);
      const remaining_operations = getRemainingOperations(createdUser);

      res.status(201).jsonp({
        user: { ...userResponse, remaining_operations },
        jwt: auth.get_jwt(createdUser),
      });
    })
    .catch(() => {
      res.status(702).jsonp("Error creating a new user.");
    });
});

// Login user
router.post("/:email/login", function (req, res, next) {
  User.getOneEmailWithPassword(req.params.email)
    .then(async (user) => {
      if (!user || !user.password_hash)
        return res.status(401).jsonp("The provided credentials are incorrect");
      const correct_pass = await auth.authenticate(req.body.password, user);
      if (correct_pass) {
        const userResponse = removeSensitiveInfo(user);
        const remaining_operations = getRemainingOperations(user);

        res.status(200).jsonp({
          user: { ...userResponse, remaining_operations },
          jwt: auth.get_jwt(user),
        });
      } else res.status(401).jsonp("The provided credentials are incorrect");
    })
    .catch((_) => res.status(701).jsonp(`Error acquiring user's information.`));
});

// Update user info
router.put("/:user", function (req, res, next) {
  const identity = req.internalIdentity;
  const subscriptionStart = identity?.originMethod === "POST" &&
    ["/subscriptions", "/subscriptions/"].includes(identity.originPath) && req.body.type === "premium";
  const subscriptionCancel = identity?.originMethod === "PUT" &&
    identity.originPath === `/subscriptions/${req.params.user}/cancel` && req.body.type === "free";
  if (req.body.type !== undefined && !subscriptionStart && !subscriptionCancel) {
    return res.status(403).jsonp("Account type can only change through subscription");
  }
  User.getOne(req.params.user)
    .then((user) => {
      user.name = req.body.name || user.name;
      user.email = req.body.email || user.email;
      if (subscriptionStart || subscriptionCancel) user.type = req.body.type;

      if (req.body.password != null) {
        user.password = req.body.password || user.password;

        User.updatePassword(req.params.user, user)
          .then((_) => res.sendStatus(204))
          .catch((_) =>
            res.status(703).jsonp(`Error updating user's information`),
          );
      } else {
        User.update(req.params.user, user)
          .then((_) => res.sendStatus(204))
          .catch((_) =>
            res.status(704).jsonp(`Error updating user's information`),
          );
      }
    })
    .catch((_) => res.status(701).jsonp(`Error acquiring user's information.`));
});

// Update number of advanced tools used
router.put("/:user/process/:advanced_tools", async function (req,res) {
  try { await quotaLedger.legacy(req.params.user,Number(req.params.advanced_tools),'admit'); return res.sendStatus(204); }
  catch (error) { return res.status(error.status===701?799:error.status||503).jsonp(error.status?error.message:'Quota unavailable'); }
});

// Refund de operações quando um processamento é cancelado
router.post("/:user/process/refund/:advanced_tools", async function (req,res) {
  try {
    const amount=Number(req.params.advanced_tools); const context=quotaLedger.contextFrom(req);
    const result=context ? await quotaLedger.refund(req.params.user,amount,context,'cancel:'+context.run_id) : await quotaLedger.legacy(req.params.user,amount,'refund');
    return res.status(200).jsonp(result);
  } catch (error) { return res.status(error.status||503).jsonp(error.status?error.message:'Quota unavailable'); }
});

// Delete a user + all related data (projects, daily ops, etc.)
router.delete("/:user", async function (req, res, next) {
  const userId = req.params.user;

  try {
    if (req.internalIdentity?.sub !== userId) {
      return res.status(403).jsonp("Account mismatch");
    }

    // Remove this account's projects before deleting the account.
    try {
      await axios.delete(projects_ms + userId, {
        httpsAgent,
      });
    } catch (_) {
      return res.status(502).jsonp("Error deleting user's projects");
    }

    // 2) Apagar o próprio utilizador
    await User.delete(userId);

    // 3) (Opcional) Apagar daily_operations associadas ao user
    // if (dailyoperationsModel) {
    //   await dailyoperationsModel.dailyOperation_deleteByUserId(userId);
    // }

    return res.sendStatus(204);
  } catch (err) {
    console.error("Error deleting user and related data:", err);
    return res
      .status(705)
      .jsonp(`Error deleting user's information and related data`);
  }
});


module.exports = router;
