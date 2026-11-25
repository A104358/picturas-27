"use client";

import Loading from "@/components/loading";
import { SessionData, validateSession } from "@/lib/session";
import { createContext, useContext, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useRegister } from "@/lib/mutations/session";
import { parseStoredSession } from "@/lib/session-state";

const SessionContext = createContext<SessionData | undefined>(undefined);

// No bootstrap hooks mount on the recovery or authentication paths.
export function SessionProvider({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  if (["/session-recovery", "/login", "/register"].includes(path)) return <>{children}</>;
  return <ActiveSessionProvider>{children}</ActiveSessionProvider>;
}

function ActiveSessionProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<SessionData>();
  const [status, setStatus] = useState("checking");
  const [revision, setRevision] = useState(0);
  const register = useRegister();
  useEffect(() => {
    let live = true;
    let timer: ReturnType<typeof setTimeout>;
    const refresh = () => { setSession(undefined); setRevision((n) => n + 1); };
    const invalid = () => { live = false; setSession(undefined); setStatus("invalid"); };
    window.addEventListener("session-updated", refresh);
    window.addEventListener("storage", refresh);
    window.addEventListener("picturas-session-invalid", invalid);
    const validate = async () => {
      setStatus("checking");
      let raw: string | null = null;
      try {
        raw = localStorage.getItem("session");
        const stored = parseStoredSession(raw);
        if (!stored) { if (live) setStatus(raw ? "invalid" : "missing"); return; }
        const result = await validateSession({ userId: stored.user._id, token: stored.token });
        if (!live || localStorage.getItem("session") !== raw) return;
        if (result.user._id !== stored.user._id || result.token !== stored.token)
          throw new Error("Session identity changed during validation.");
        const claims = JSON.parse(atob(stored.token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
        const remaining = claims.exp * 1000 - Date.now();
        if (!Number.isFinite(remaining) || remaining <= 0) { invalid(); return; }
        setSession({ user: result.user, token: stored.token });
        setStatus("valid");
        timer = setTimeout(invalid, remaining);
      } catch (error: any) {
        if (!live) return;
        try {
          if (localStorage.getItem("session") === raw)
            setStatus([401, 403].includes(error?.response?.status) ? "invalid" : "network");
        } catch { setStatus("storage"); }
      }
    };
    void validate();
    return () => {
      live = false;
      clearTimeout(timer);
      window.removeEventListener("session-updated", refresh);
      window.removeEventListener("storage", refresh);
      window.removeEventListener("picturas-session-invalid", invalid);
    };
  }, [revision]);

  if (session && status === "valid")
    return <SessionContext.Provider value={session}>{children}</SessionContext.Provider>;
  if (status === "checking") return <div className="p-8"><Loading /></div>;
  return <main className="mx-auto max-w-xl space-y-4 p-8" aria-live="polite">
    <h1 className="text-2xl font-bold">{status === "missing" ? "Welcome to PictuRAS" :
      status === "network" ? "Cannot check your session" : "Your session needs attention"}</h1>
    <p>{status === "storage" ? "Browser storage is unavailable. Enable storage and retry; no identity has been replaced." :
      status === "network" ? "Your saved identity is preserved. Check the connection and try again." :
      "Sign in, explicitly start a new anonymous session, or ask your administrator for assisted recovery of an anonymous account. Your saved session has not been replaced."}</p>
    <div className="flex flex-wrap gap-3">
      <Button asChild><Link href="/login">Sign in</Link></Button>
      <Button variant="outline" asChild><Link href="/session-recovery">Recover anonymous session</Link></Button>
      <Button variant="outline" onClick={() => setRevision((n) => n + 1)}>Retry</Button>
      <Button disabled={register.isPending} onClick={() => {
        if (window.confirm("Start a new anonymous identity? This will replace the session saved in this browser. Existing projects will stay with the previous identity."))
          register.mutate({ type: "anonymous" });
      }}>Start a new anonymous session</Button>
    </div>
    {register.isError && <p role="alert">Could not create a session. The previous session is preserved.</p>}
  </main>;
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) throw new Error("useSession() must be used within a SessionProvider");
  return context;
}
