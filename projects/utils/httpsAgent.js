// Own certificate, installation CA, no cached TLS sessions (B5).
const httpsAgent = require("../tls/pkiTls").clientAgent();

module.exports = { httpsAgent };
