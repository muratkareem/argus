import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { SystemInformation } from "./SystemInformation";
afterEach(() => {
  cleanup();
  sessionStorage.clear();
  vi.unstubAllGlobals();
});
it("keeps the credential control available when a protected backend rejects requests", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response(JSON.stringify({ detail: "API key required" }), {
          status: 401,
        }),
    ),
  );
  const reconnect = vi.fn();
  render(
    <SystemInformation settings={null} revision={0} reconnect={reconnect} />,
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "API key required",
  );
  fireEvent.change(screen.getByLabelText("API access key"), {
    target: { value: "private-key" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Apply connection key" }));
  expect(sessionStorage.getItem("argus-api-key")).toBe("private-key");
  expect(reconnect).toHaveBeenCalledOnce();
  fireEvent.change(screen.getByLabelText("API access key"), {
    target: { value: "" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Apply connection key" }));
  expect(sessionStorage.getItem("argus-api-key")).toBeNull();
});
