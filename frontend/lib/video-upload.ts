import { api } from "./axios";

function videoMetadata(file: File): Promise<{ duration: number; width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const element = document.createElement("video");
    const url = URL.createObjectURL(file);
    const finish = () => { element.removeAttribute("src"); element.load(); URL.revokeObjectURL(url); };
    element.preload = "metadata";
    element.onloadedmetadata = () => {
      const result = { duration: element.duration, width: element.videoWidth, height: element.videoHeight };
      finish();
      if (Number.isFinite(result.duration) && result.duration > 0 && result.width && result.height) resolve(result);
      else reject(new Error("Could not read video metadata"));
    };
    element.onerror = () => { finish(); reject(new Error("Could not read video metadata")); };
    element.src = url;
  });
}

function putVideo(url: string, file: File, token: string, type: string, signal?: AbortSignal,
  onProgress?: (percent: number) => void): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const abort = () => xhr.abort();
    xhr.open("PUT", url);
    xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.setRequestHeader("Content-Type", type);
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress?.(Math.round(100 * event.loaded / event.total));
    };
    xhr.onload = () => {
      signal?.removeEventListener("abort", abort);
      if (xhr.status >= 200 && xhr.status < 300) resolve();
      else reject(new Error(`Video transfer failed (${xhr.status})`));
    };
    xhr.onerror = () => { signal?.removeEventListener("abort", abort); reject(new Error("Video transfer failed")); };
    xhr.onabort = () => { signal?.removeEventListener("abort", abort); reject(new DOMException("Upload cancelled", "AbortError")); };
    signal?.addEventListener("abort", abort, { once: true });
    if (signal?.aborted) { abort(); return; }
    xhr.send(file);
  });
}

export async function uploadVideo(args: {
  path: string; query: string; file: File; token: string; version: number;
  signal?: AbortSignal; onProgress?: (percent: number) => void;
}): Promise<string | undefined> {
  const { path, query, file, token, version, signal, onProgress } = args;
  const metadata = await videoMetadata(file);
  const type = file.type || ({ ".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm" }[
    file.name.slice(file.name.lastIndexOf(".")).toLowerCase()] || "");
  const start = await api.post<{ token: string; uploadUrl: string }>(`${path}/uploads${query}`, {
    name: file.name, size: file.size, type, ...metadata,
  }, { headers: { Authorization: `Bearer ${token}`, "X-Project-Version": String(version) }, signal });
  try {
    await putVideo(start.data.uploadUrl, file, token, type, signal, onProgress);
    onProgress?.(100);
    const confirmed = await api.post(`${path}/uploads/${start.data.token}/confirm${query}`, null,
      { headers: { Authorization: `Bearer ${token}` }, signal });
    return confirmed.headers?.["x-project-version"];
  } catch (error) {
    if (signal?.aborted) {
      await api.post(`${path}/uploads/${start.data.token}/cancel${query}`, null,
        { headers: { Authorization: `Bearer ${token}` } }).catch(() => {});
    }
    throw error;
  }
}
