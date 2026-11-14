import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./api";
afterEach(() => {
  sessionStorage.clear();
  vi.unstubAllGlobals();
});
describe("API connection", () => {
  it("sends the optional tab credential only to relative application API URLs", async () => {
    sessionStorage.setItem("argus-api-key", "test-key");
    const fetch = vi.fn(async () => new Response(JSON.stringify({ ok: true })));
    vi.stubGlobal("fetch", fetch);
    await api("/settings", {
      headers: new Headers({ "X-Request-ID": "request-1" }),
    });
    const [url, init] = fetch.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/api/v1/settings");
    const headers = new Headers(init.headers);
    expect(headers.get("Authorization")).toBe("Bearer test-key");
    expect(headers.get("X-Request-ID")).toBe("request-1");
  });
  it("preserves upload multipart boundaries and handles non-JSON errors", async () => {
    const fetch = vi.fn(
      async () =>
        new Response("Unavailable", {
          status: 503,
          statusText: "Service unavailable",
        }),
    );
    vi.stubGlobal("fetch", fetch);
    await expect(
      api("/datasets/upload", { method: "POST", body: new FormData() }),
    ).rejects.toThrow("Service unavailable");
    const [, init] = fetch.mock.calls[0] as unknown as [string, RequestInit];
    expect(new Headers(init.headers).has("Content-Type")).toBe(false);
    expect(new Headers(init.headers).has("Authorization")).toBe(false);
  });
});
