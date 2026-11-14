import { afterEach, describe, expect, it, vi } from "vitest";
import { api, downloadFile } from "./api";
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

it("exports CSV with the same API credential and releases its temporary URL", async () => {
  sessionStorage.setItem("argus-api-key", "test-key");
  const fetch = vi.fn(
    async () =>
      new Response("id,amount\n1,42\n", {
        headers: { "Content-Type": "text/csv" },
      }),
  );
  vi.stubGlobal("fetch", fetch);
  const create = vi.fn((blob: Blob) =>
      blob instanceof Blob ? "blob:test-export" : "invalid",
    ),
    revoke = vi.fn();
  vi.stubGlobal(
    "URL",
    class extends URL {
      static createObjectURL = create;
      static revokeObjectURL = revoke;
    },
  );
  const click = vi
    .spyOn(HTMLAnchorElement.prototype, "click")
    .mockImplementation(() => {});
  await downloadFile("/transactions/export?min_amount=20", "filtered.csv");
  expect(
    new Headers(
      (fetch.mock.calls[0] as unknown as [string, RequestInit])[1].headers,
    ).get("Authorization"),
  ).toBe("Bearer test-key");
  expect(create.mock.calls[0][0]).toBeInstanceOf(Blob);
  expect(revoke).toHaveBeenCalledWith("blob:test-export");
  expect(click).toHaveBeenCalledOnce();
  click.mockRestore();
});
