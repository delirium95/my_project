import { afterEach, describe, expect, it, vi } from "vitest";

import { authApi } from "./api";

describe("auth API", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("turns FastAPI validation details into a readable error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: [{ msg: "Email is invalid" }] }), {
          headers: { "Content-Type": "application/json" },
          status: 422,
        }),
      ),
    );

    await expect(authApi.register({ email: "bad", password: "password" })).rejects.toThrow(
      "Email is invalid",
    );
  });
});
