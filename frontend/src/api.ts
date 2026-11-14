async function request(path: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers);
  if (!(init?.body instanceof FormData) && !headers.has("Content-Type"))
    headers.set("Content-Type", "application/json");
  const key = sessionStorage.getItem("argus-api-key");
  if (key) headers.set("Authorization", `Bearer ${key}`);
  const response = await fetch("/api/v1" + path, { ...init, headers });
  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : JSON.stringify(body.detail),
    );
  }
  return response;
}
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  return (await request(path, init)).json();
}
export async function downloadFile(path: string, name: string): Promise<void> {
  const response = await request(path);
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}
export const send = (method: string, body: unknown): RequestInit => ({
  method,
  body: JSON.stringify(body),
});
export function download(name: string, data: unknown) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}
export const percent = (n: number | null | undefined) =>
  n == null ? "—" : `${(n * 100).toFixed(1)}%`;
export const amount = (n: number) =>
  new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(n);
