import type { SessionData } from "./session";

export const SESSION_LOCK = "picturas-session";

export function parseStoredSession(raw: string | null): SessionData | null {
  if (!raw) return null;
  try {
    const value = JSON.parse(raw);
    return typeof value?.token === "string" && typeof value?.user?._id === "string"
      && ["anonymous", "free", "premium"].includes(value.user.type) ? value : null;
  } catch { return null; }
}

// All updated clients serialize writes. Recovery holds this lock through confirmation.
export async function withSessionLock<T>(work: () => Promise<T>): Promise<T> {
  if (!navigator.locks) return work();
  return await navigator.locks.request<Promise<T>>(SESSION_LOCK, { ifAvailable: true }, async (lock) => {
    if (!lock) throw new Error("Session recovery is active in another tab. Close that tab first.");
    return work();
  });
}

export function saveSessionIfCurrent(session: SessionData, expected: string | null) {
  if (localStorage.getItem("session") !== expected)
    throw new Error("The session changed in another tab. Review it before continuing.");
  localStorage.setItem("session", JSON.stringify(session));
  window.dispatchEvent(new Event("session-updated"));
}

export function signalSessionError(error: any) {
  if ([401, 403].includes(error?.response?.status))
    window.dispatchEvent(new Event("picturas-session-invalid"));
}
