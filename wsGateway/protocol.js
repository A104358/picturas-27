const parser = require("socket.io-parser");

// Private metadata cannot be supplied by a JSON client and is not serialized
// into the authorization RPC. No per-packet queue or connection-wide last value.
const JOIN_BYTES = Symbol("received join JSON bytes");

function joinBytes(raw) {
  const array = raw.indexOf("[");
  let index = array + 1;
  while (/\s/.test(raw[index] || "") && index < raw.length) index++;
  if (array < 0 || raw[index++] !== '"') return Infinity;
  // Locate the separator after the event name, respecting JSON string escapes.
  while (index < raw.length) {
    const char = raw[index++];
    if (char === "\\") index++;
    else if (char === '"') break;
  }
  while (/\s/.test(raw[index] || "") && index < raw.length) index++;
  if (raw[index++] !== ",") return Infinity;
  const end = raw.lastIndexOf("]");
  return end >= index ? Buffer.byteLength(raw.slice(index, end)) : Infinity;
}

class ControlDecoder extends parser.Decoder {
  decodeString(raw) {
    // Count received UTF-8, including whitespace/escapes, before parsing can
    // normalize them into a shorter value. Engine.IO separately caps frames.
    if (raw[0] === "0" && Buffer.byteLength(raw.slice(1)) > 8192) {
      throw new Error("Handshake exceeds 8 KiB");
    }
    const packet = super.decodeString(raw);
    if ([parser.PacketType.BINARY_EVENT, parser.PacketType.BINARY_ACK].includes(packet.type)) {
      throw new Error("JSON messages required");
    }
    if ([parser.PacketType.EVENT, parser.PacketType.BINARY_EVENT].includes(packet.type) &&
        packet.data?.[0] === "join-project") {
      if (packet.type !== parser.PacketType.EVENT) throw new Error("JSON control required");
      const payload = packet.data[1];
      if (payload && typeof payload === "object") {
        Object.defineProperty(payload, JOIN_BYTES, { value: joinBytes(raw) });
      }
    }
    return packet;
  }
}

module.exports = { parser: { ...parser, Decoder: ControlDecoder }, JOIN_BYTES, joinBytes };
