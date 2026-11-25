import axios from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api-gateway/";

export const api = axios.create({
  baseURL: API_BASE_URL,
});

// Every gateway route except the closed public ones needs the session JWT (B4).
// Calls that already set Authorization (e.g. session validation) keep theirs.
api.interceptors.request.use((config) => {
  if (typeof window === "undefined" || config.headers.has("Authorization"))
    return config;
  try {
    const raw = window.localStorage.getItem("session");
    const token = raw ? JSON.parse(raw)?.token : undefined;
    if (typeof token === "string" && token)
      config.headers.set("Authorization", `Bearer ${token}`);
  } catch {
    // No usable stored session: send the request without a token.
  }
  return config;
});
