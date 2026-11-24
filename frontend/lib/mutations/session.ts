import { useMutation, useQueryClient } from "@tanstack/react-query";
import { deleteAccount } from "../users";
import { useRouter } from "next/navigation";
import {
  login,
  register,
  SessionData,
  validateSession,
  updateUser,
  updatePassword,
} from "../session";
import { saveSessionIfCurrent, signalSessionError, withSessionLock } from "../session-state";

function replaceSession<T>(request: (input: T) => Promise<SessionData>): (input: T) => Promise<SessionData> {
  return (input: T) => withSessionLock<SessionData>(async () => {
    const expected = localStorage.getItem("session");
    const session = await request(input);
    saveSessionIfCurrent(session, expected);
    return session;
  });
}

export const useLogin = () => {
  const qc = useQueryClient();
  return useMutation<SessionData, Error, Parameters<typeof login>[0]>({
    mutationFn: replaceSession(login),
    onSuccess: (session) => {

      qc.invalidateQueries({ refetchType: "all", queryKey: ["session"] });
      qc.removeQueries({ queryKey: ["projects"] });
      qc.removeQueries({ queryKey: ["project"] });
      qc.removeQueries({ queryKey: ["projectImages"] });
      qc.removeQueries({ queryKey: ["projectResults"] });
      qc.removeQueries({ queryKey: ["socket"] });

     //  window.location.href = "/dashboard";

    },
  });
};

export const useRegister = () => {
  const qc = useQueryClient();
  return useMutation<SessionData, Error, Parameters<typeof register>[0]>({
    mutationFn: replaceSession(register),
    onSuccess: (session) => {

      qc.invalidateQueries({ refetchType: "all", queryKey: ["session"] });
      qc.removeQueries({ queryKey: ["projects"] });
      qc.removeQueries({ queryKey: ["project"] });
      qc.removeQueries({ queryKey: ["projectImages"] });
      qc.removeQueries({
        queryKey: ["projectResults"]
      });
      qc.removeQueries({ queryKey: ["socket"] });

      // window.location.href = "/dashboard";

    },
  });
};

export const useLogout = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => withSessionLock(async () => localStorage.removeItem("session")),
    onSuccess: () => {
      window.dispatchEvent(new Event("session-updated")); 

      qc.removeQueries({ queryKey: ["projects"] });
      qc.removeQueries({ queryKey: ["project"] });
      qc.removeQueries({ queryKey: ["projectImages"] });
      qc.removeQueries({ queryKey: ["projectResults"] });
      qc.removeQueries({ queryKey: ["socket"] });
    },
  });
};

export const useUpdateSession = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: Parameters<typeof validateSession>[0]) => withSessionLock(async () => {
      const expected = localStorage.getItem("session");
      if (!expected || JSON.parse(expected).token !== input.token)
        throw new Error("The session changed before validation.");
      const resp = await validateSession(input);
      saveSessionIfCurrent({ user: resp.user, token: resp.token }, expected);
      return resp;
    }),
    onSuccess: (resp) => {
      qc.invalidateQueries({ refetchType: "all", queryKey: ["session"] });
    },
    onError: (error, input) => {
      try {
        const raw = localStorage.getItem("session");
        if (raw && JSON.parse(raw).token === input.token) signalSessionError(error);
      } catch { /* Keep an unreadable or unavailable session for explicit review. */ }
    },
  });
};

export const useUpdateUserProfile = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (variables: Parameters<typeof updateUser>[0]) => withSessionLock(async () => {
      const expected = localStorage.getItem("session");
      const session = expected ? JSON.parse(expected) as SessionData : null;
      if (!session || session.token !== variables.token) throw new Error("The session changed.");
      await updateUser(variables);
      const updatedSession = {
        user: {
          ...session.user,
          name: variables.name,
          email: variables.email,
        },
        token: session.token,
      } as SessionData;
      saveSessionIfCurrent(updatedSession, expected);
    }),
    onSuccess: () => {
      qc.invalidateQueries({ refetchType: "all", queryKey: ["session"] });
    },
  });
};

export const useUpdateUserPassword = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: updatePassword,
    onSuccess: () => {
      qc.invalidateQueries({ refetchType: "all", queryKey: ["session"] });
    },
  });
};

export const useDeleteAccount = (uid: string, token: string) => {
  const qc = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: () => withSessionLock(async () => {
      const expected = localStorage.getItem("session");
      if (!expected || JSON.parse(expected).token !== token) throw new Error("The session changed.");
      await deleteAccount(uid, token);
      if (localStorage.getItem("session") !== expected) throw new Error("The session changed.");
      localStorage.removeItem("session");
    }),
    onSuccess: () => {
      // limpar sessão local
      window.dispatchEvent(new Event("session-updated"));

      // limpar cache relacionada
      qc.removeQueries({ queryKey: ["session"] });
      qc.removeQueries({ queryKey: ["projects"] });
      qc.removeQueries({ queryKey: ["project"] });
      qc.removeQueries({ queryKey: ["projectImages"] });
      qc.removeQueries({ queryKey: ["projectResults"] });
      qc.removeQueries({ queryKey: ["socket"] });

      // redirecionar para o login
      router.push("/login");
    },
  });
};
