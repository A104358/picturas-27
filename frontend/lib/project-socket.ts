import io, { Socket } from "socket.io-client";
import { validateSession } from "./session";

const lifetimes = new WeakMap<Socket, { retain: () => void; release: () => void }>();

export function createProjectSocket(token: string) {
  const socket = io(window.location.origin, {
    transports: ["websocket"], secure: true, auth: { token },
    autoConnect: false, reconnection: false,
  });
  let users = 0;
  let generation = 0;
  let stopped = false;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let connecting = false;
  const invalid = () => {
    stopped = true;
    window.dispatchEvent(new CustomEvent("picturas-session-invalid"));
  };
  const reconnect = async () => {
    if (!users || stopped || connecting || socket.connected) return;
    connecting = true;
    const current = generation;
    try {
      const claims = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
      await validateSession({ userId: claims.sub, token });
      if (current === generation && users && !stopped) {
        socket.auth = { token };
        socket.connect();
      }
    } catch (error: any) {
      if (current !== generation || !users) return;
      if ([401, 403].includes(error?.response?.status) || error instanceof SyntaxError) invalid();
      else timer = setTimeout(reconnect, 1000);
    } finally {
      connecting = false;
      if (current !== generation && users && !stopped) void reconnect();
    }
  };
  const retry = () => {
    clearTimeout(timer);
    if (users && !stopped) timer = setTimeout(reconnect, 1000);
  };
  socket.on("disconnect", retry);
  socket.on("connect_error", (error: any) => {
    if (["denied", "session_expired"].includes(error?.data?.status)) invalid();
    else retry();
  });
  socket.on("session-expired", invalid);
  lifetimes.set(socket, {
    retain: () => { if (users++ === 0) { generation++; stopped = false; void reconnect(); } },
    release: () => {
      if (--users === 0) {
        generation++;
        clearTimeout(timer);
        socket.disconnect();
      }
    },
  });
  return socket;
}

export function retainProjectSocket(socket: Socket) {
  const lifetime = lifetimes.get(socket);
  lifetime?.retain();
  return () => lifetime?.release();
}
