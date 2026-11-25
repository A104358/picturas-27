"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SESSION_LOCK } from "@/lib/session-state";
import { confirmRecovery, parseRecoveryBundle, RECOVERY_MAX_BYTES, validateRecovery } from "@/lib/session-recovery";
import type { SessionData } from "@/lib/session";

export default function SessionRecovery() {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [subject, setSubject] = useState("");
  const [installation, setInstallation] = useState("");
  const [controlled, setControlled] = useState(false);
  const [busy, setBusy] = useState(false);
  const [verified, setVerified] = useState(false);
  const [imported, setImported] = useState(false);
  const candidate = useRef<SessionData | undefined>(undefined);
  const baseline = useRef<string | null>(null);
  const generation = useRef(0);
  useEffect(() => {
    let live = true;
    let release: (() => void) | undefined;
    if (!navigator.locks) { setError("This browser cannot lock session recovery. Use a supported secure browser and close other PictuRAS tabs."); return; }
    navigator.locks.request(SESSION_LOCK, { ifAvailable: true }, async (lock) => {
      if (!live) return;
      if (!lock) { setError("Another tab is changing or recovering this session. Close it and reload."); return; }
      try { baseline.current = localStorage.getItem("session"); }
      catch { setError("Browser storage is unavailable. Nothing has been imported."); return; }
      setReady(true);
      await new Promise<void>((done) => { release = done; });
    }).catch(() => { if (live) setError("Cannot lock session recovery."); });
    const conflict = () => {
      generation.current++;
      candidate.current = undefined;
      setVerified(false); setReady(false);
      setError("Another tab changed storage. Stop and reconcile this browser profile before retrying.");
    };
    window.addEventListener("storage", conflict);
    return () => { live = false; generation.current++; candidate.current = undefined;
      release?.(); window.removeEventListener("storage", conflict); };
  }, []);

  const resetCandidate = () => { generation.current++; candidate.current = undefined; setVerified(false); };
  const readFile = async (file?: File) => {
    resetCandidate(); setError("");
    if (!file || !ready || !controlled) return;
    const current = generation.current;
    setBusy(true);
    try {
      if (file.size > RECOVERY_MAX_BYTES || !file.name.endsWith(".json") ||
          !["", "application/json"].includes(file.type)) throw new Error("Choose a JSON recovery file no larger than 16 KiB.");
      const bundle = parseRecoveryBundle(await file.text(), window.location.origin);
      const session = await validateRecovery(bundle, subject, installation);
      if (current !== generation.current) return;
      if (localStorage.getItem("session") !== baseline.current) throw new Error("Session changed during validation. Stop and reconcile.");
      candidate.current = session; setVerified(true);
    } catch (error: any) {
      if (current === generation.current) setError(error?.response ? "The server refused validation or is unavailable. Nothing has been imported." : error.message);
    } finally { if (current === generation.current) setBusy(false); }
  };
  return <main className="mx-auto max-w-xl space-y-4 p-8">
    <h1 className="text-2xl font-bold">Recover an anonymous session</h1>
    <p>Ask the installation administrator to verify independent evidence and approve a recovery case. Knowing an ID or an old token is insufficient. Keep the delivery file private.</p>
    <p>Close other PictuRAS tabs, including older clients. Confirm the browser profile, installation and identity using the administrator&apos;s independent record.</p>
    <label className="block">Installation reference from the approved record
      <Input aria-label="Installation reference" value={installation} disabled={busy || imported} onChange={(e) => { resetCandidate(); setInstallation(e.target.value); }} /></label>
    <label className="block">Anonymous account ID from the approved record
      <Input aria-label="Approved anonymous account ID" value={subject} disabled={busy || imported} onChange={(e) => { resetCandidate(); setSubject(e.target.value); }} /></label>
    <label className="block"><input type="checkbox" checked={controlled} disabled={busy || imported} onChange={(e) => { resetCandidate(); setControlled(e.target.checked); }} /> I have checked the approved case and browser profile, and closed other PictuRAS tabs.</label>
    <input aria-label="Recovery file" type="file" accept="application/json,.json" disabled={!ready || !controlled || busy || imported}
      onChange={(e) => { void readFile(e.target.files?.[0]); e.target.value = ""; }} />
    {busy && <p role="status">Validating with the installation server…</p>}
    {verified && !imported && <div className="space-y-3"><p>Server validation confirmed the approved anonymous identity. Confirm import to replace only the saved session for this identity.</p>
      <Button disabled={busy} onClick={async () => {
        if (!candidate.current || !ready) return;
        const current = generation.current;
        setBusy(true);
        try {
          await confirmRecovery(candidate.current, baseline.current, () => current === generation.current);
          setImported(true); setError(""); candidate.current = undefined;
        } catch { setError("Import could not be confirmed. Preserve the saved session and retry validation or ask the administrator to reconcile."); }
        finally { setBusy(false); }
      }}>Confirm import</Button></div>}
    {imported && <div className="space-y-3"><p>Session saved. Continue to reconnect, then ask the administrator to verify your projects, media and quota before completing the case.</p>
      <Button onClick={() => window.location.assign("/dashboard")}>Continue and reconnect</Button></div>}
    {error && <p role="alert">{error}</p>}
    <p><Link href="/login">Sign in to a registered account</Link></p>
  </main>;
}
