var express = require("express");
var router = express.Router();

const axios = require("axios");

const https = require("https");
const fs = require("fs");


// Own certificate, installation CA, no cached TLS sessions (B5).
const httpsAgent = require("../tls/pkiTls").clientAgent();

const subscriptionsURL = "https://subscriptions:11001/";
const usersURL = "https://users:10001/";

// Keep the service's refusal codes (4xx); anything else stays a generic 500.
function upstreamError(res, err, fallback) {
  const status = err.response?.status;
  if (status >= 400 && status < 500) return res.status(status).jsonp(err.response.data);
  return res.status(500).jsonp(fallback);
}

/*
Subscription structure
{
    "_id": Mongoose.type.id,
    "subscribedAt": Date,
    "expiresAt": Date,
    "interval": Number,
    "status": String,
    "userId": Mongoose.type.id
}

*/

/*
Card structure
{
    "cardHolderName": String,
    "last4": String,
    "expiryMonth": String,
    "expiryYear": String,"
}
*/

function removeUncessaryInformationCard(card) {
    delete card._id;
    delete card.subscriptionId;
    delete card.cardToken;
    return card;
}

/**
 * Get subscription
 * @returns Subscription structure
 */
router.get("/:user", function (req, res, next) {
    axios
        .get(subscriptionsURL + req.params.user, {
            httpsAgent: httpsAgent,
        })
        .then((resp) => res.status(201).jsonp(resp.data))
        .catch((err) => upstreamError(res, err, "Error getting subsbcription"));
});

/**
 * Get subscription status
 * @returns { "status": String }
 */
router.get("/:user/status", function (req, res, next) {
    axios
        .get(subscriptionsURL + req.params.user + "/status", {
            httpsAgent: httpsAgent,
        })
        .then((resp) => res.status(201).jsonp(resp.data))
        .catch((err) => upstreamError(res, err, "Error getting subsbcription status"));
});

/**
 * Get subscription card
 * @returns Card structure
 * 
 * Only use this route if subsbcription is active, if not, it will return null
 */

router.get("/:user/card", function (req, res, next) {
    axios
        .get(subscriptionsURL + req.params.user + "/card", {
            httpsAgent: httpsAgent,
        })
        .then((resp) => res.status(200).jsonp(removeUncessaryInformationCard(resp.data)))
        .catch((err) => upstreamError(res, err, "Error getting subsbcription card"));
});

/**
 * Subscribe to a plan
 * @param {Object} req.body.subscription - The subscription details
 * @param {Object} req.body.card - The card details
 * @returns {Object} - The created subscription
 * 
 * Example of req.body:
   {
    "subscription": {
        "user_id" : "67859c0c9bb5f2a85a2f5b36"
    },
    "card": {
        "cardHolderName": "jose",
        "cardNumber": "5236412032716377",
        "expiryMonth": "09",
        "expiryYear": "26",
        "cvc": 123
    }
}

 * O frontend precisa de atualizar o type do user para premium se sucesso
**/

router.post("/", async function (req, res, next) {
    if (String(req.body?.subscription?.user_id) !== req.authUserId) {
      return res.status(403).jsonp({ error: "Subscription owner mismatch" });
    }
    try {
      // Step 1: Create the subscription
      const subscriptionResponse = await axios.post(subscriptionsURL, req.body, {
        httpsAgent: httpsAgent,
      });
  
      const subscription = subscriptionResponse.data;
  
      try {
        // Step 2: Update the user's type to "premium"
        await axios.put(`${usersURL}${req.body.subscription.user_id}`, { type: "premium" }, {
          httpsAgent: httpsAgent,
        });
  
        // Step 3: Respond with the data
        return res.status(200).jsonp(subscription);
      } catch (userUpdateError) {
        // Step 4: If user update fails, delete the created subscription
        await axios.delete(`${subscriptionsURL}${subscription._id}`, {
          httpsAgent: httpsAgent,
        });
  
        return res
          .status(500)
          .jsonp({ error: "Failed to update user type." });
      }
    } catch (subscriptionError) {
      // Handle errors during subscription creation
      const status = subscriptionError.response?.status || 500;
      const data = subscriptionError.response?.data || { error: "Failed to create subscription." };
      return res.status(status).jsonp(data);
    }
  });
  

/**
 * Update a subscription
 * @param {Object} req.body - The subscription details
 * @returns {Object} - The updated subscription
 *
 * Example of req.body para dar update do tipo de anualidade:
 * {
 *  "interval": 12
 * } 
*/
router.put("/:user", function (req, res, next) {
    axios
        .put(subscriptionsURL + req.params.user, req.body, {
            httpsAgent: httpsAgent,
        })
        .then((resp) => res.status(200).jsonp(resp.data))
        .catch((err) => upstreamError(res, err, "Error updating subsbcription"));
});


/**
 * Cancel a subscription
 * @returns Subscription structure
 * 
 * O frontend precisa de atualizar o type do user para free se sucesso
 */
router.put("/:user/cancel", async function (req, res, next) {
    try {
      // Step 1: Cancel the user's subscription
      const subscriptionResponse = await axios.put(
        `${subscriptionsURL}${req.params.user}/cancel`,
        req.body,
        { httpsAgent: httpsAgent }
      );
  
      const subscriptionData = subscriptionResponse.data;
  
      try {
        // Step 2: Update the user's type to "free"
        await axios.put(
          `${usersURL}${req.params.user}`,
          { type: "free" },
          { httpsAgent: httpsAgent }
        );
  
        // Step 3: Respond with the updated subscription data
        return res.status(200).jsonp(subscriptionData);
      } catch (userUpdateError) {
        // Handle error during user type update
        return res.status(500).jsonp({
          error: "Failed to update user type to 'free'.",
          details: userUpdateError.response?.data || userUpdateError.message,
        });
      }
    } catch (subscriptionError) {
      // Handle error during subscription cancellation
      const status = subscriptionError.response?.status;
      if (status >= 400 && status < 500) return res.status(status).jsonp(subscriptionError.response.data);
      return res.status(500).jsonp({
        error: "Failed to cancel the subscription.",
        details: subscriptionError.response?.data || subscriptionError.message,
      });
    }
  });

router.put("/:user/card", function (req, res, next) {
  axios
    .put(subscriptionsURL + req.params.user + "/card", req.body, {
        httpsAgent: httpsAgent,
    })
    .then((resp) => res.status(200).jsonp(removeUncessaryInformationCard(resp.data)))
    .catch((err) => upstreamError(res, err, "Error updating subsbcription card"));
});

module.exports = router;
