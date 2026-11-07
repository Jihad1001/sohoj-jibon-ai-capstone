const BASE = import.meta.env.VITE_API_BASE || "";

async function json(res) {
  if (!res.ok) {
    let msg = res.statusText;
    try { msg = (await res.json()).detail || msg; } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export const getDistricts = () => fetch(`${BASE}/api/v1/districts`).then(json);
export const getDomains = () => fetch(`${BASE}/api/v1/domains`).then(json);

export const transcribe = (blob) => {
  const fd = new FormData();
  fd.append("media_file", blob, "voice.webm");
  return fetch(`${BASE}/api/v1/transcribe`, { method: "POST", body: fd }).then(json);
};

export const processQuery = ({ domain, query_text, district, media_file }) => {
  const fd = new FormData();
  fd.append("domain", domain);
  fd.append("query_text", query_text || "");
  if (district) fd.append("district", district);
  if (media_file) fd.append("media_file", media_file);
  return fetch(`${BASE}/api/v1/agent/process`, { method: "POST", body: fd }).then(json);
};
