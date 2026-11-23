// D-31: connection reuse only for presence's fresh users/type query. The PKI
// factory retains CA/name/client-certificate checks and disables TLS resumption.
const httpsAgent = require("../tls/pkiTls").clientAgent({ keepAlive: true, maxFreeSockets: 4 });
const keepSocketAlive = httpsAgent.keepSocketAlive.bind(httpsAgent);
const reuseSocket = httpsAgent.reuseSocket.bind(httpsAgent);

httpsAgent.keepSocketAlive = (socket) => {
  const keep = keepSocketAlive(socket);
  if (keep) socket.setTimeout(4000); // Free sockets only; users advertises 5 s.
  return keep;
};
httpsAgent.reuseSocket = (socket, request) => {
  socket.setTimeout(0); // Restore the caller's existing active-request policy.
  return reuseSocket(socket, request);
};

module.exports = { httpsAgent };
