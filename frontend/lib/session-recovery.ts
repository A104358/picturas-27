import { validateSession, type SessionData } from "./session";
import { parseStoredSession, saveSessionIfCurrent } from "./session-state";

export const RECOVERY_MAX_BYTES = 16384;
const KEYS = ["schema_version", "case_ref", "installation_ref", "intended_origin", "issued_at", "expires_at", "token"];
export interface RecoveryBundle {
  schema_version: 1;
  case_ref: string;
  installation_ref: string;
  intended_origin: string;
  issued_at: string;
  expires_at: string;
  token: string;
}
export function parseRecoveryBundle(text: string, origin: string): RecoveryBundle {
  if (new TextEncoder().encode(text).length > RECOVERY_MAX_BYTES) throw new Error("Recovery file exceeds 16 KiB.");
  let value: any;
  try { value = JSON.parse(text); } catch { throw new Error("Invalid recovery JSON."); }
  if (!value || value.schema_version !== 1 || Object.keys(value).length !== KEYS.length ||
      KEYS.some((key) => !(key in value)) || KEYS.slice(1).some((key) => typeof value[key] !== "string") ||
      !value.case_ref || value.case_ref.length > 128 || !value.installation_ref || value.installation_ref.length > 128 ||
      value.intended_origin !== origin || !Number.isFinite(Date.parse(value.issued_at)) ||
      !Number.isFinite(Date.parse(value.expires_at)) || !value.token ||
      new TextEncoder().encode(value.token).length > 8192) throw new Error("Invalid recovery file, origin or token size.");
  return value;
}
export function candidateSubject(token: string): string {
  try {
    const claims = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    if (/^[a-f0-9]{24}$/.test(claims.sub)) return claims.sub;
  } catch { /* Candidate routing only; validation always belongs to the server. */ }
  throw new Error("Invalid candidate token.");
}
export async function validateRecovery(bundle: RecoveryBundle, expectedSubject: string,
  expectedInstallation: string): Promise<SessionData> {
  if (!/^[a-f0-9]{24}$/.test(expectedSubject) || !expectedInstallation ||
      bundle.installation_ref !== expectedInstallation) throw new Error("Case or installation does not match the independent record.");
  const subject = candidateSubject(bundle.token);
  // Do not send an operator-entered ID as an authority or request issuance.
  const result = await validateSession({ userId: subject, token: bundle.token });
  if (result.user?._id !== expectedSubject || subject !== expectedSubject ||
      result.user.type !== "anonymous" || result.token !== bundle.token)
    throw new Error("The validated account does not match the approved anonymous identity.");
  return { user: result.user, token: bundle.token };
}
export function importRecovery(session: SessionData, expectedRaw: string | null) {
  const existing = parseStoredSession(expectedRaw);
  if (expectedRaw && (!existing || existing.user._id !== session.user._id))
    throw new Error("A different or unreadable session is saved here. Stop and reconcile this profile.");
  saveSessionIfCurrent(session, expectedRaw);
  if (localStorage.getItem("session") !== JSON.stringify(session))
    throw new Error("Could not verify the saved session. Preserve it and ask the administrator to reconcile.");
}

export async function confirmRecovery(session: SessionData, expectedRaw: string | null,
  stillCurrent: () => boolean) {
  // The operator may have waited beyond exp after the initial inspection.
  const result = await validateSession({ userId: session.user._id, token: session.token });
  if (!stillCurrent() || result.user?._id !== session.user._id ||
      result.user.type !== "anonymous" || result.token !== session.token)
    throw new Error("The candidate changed or is no longer valid. Nothing has been imported.");
  importRecovery({ user: result.user, token: result.token }, expectedRaw);
}
