import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/client";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

const login = vi.fn();
vi.mock("@/lib/auth/session", () => ({
  login: (...args: unknown[]) => login(...args),
}));

import LoginPage from "./page";

describe("LoginPage", () => {
  beforeEach(() => {
    push.mockClear();
    login.mockReset();
  });

  it("submits credentials and redirects to /campaigns on success", async () => {
    login.mockResolvedValueOnce({ id: "user-1" });
    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "dm@anahita.dev" },
    });
    fireEvent.change(screen.getByLabelText(/senha/i), {
      target: { value: "correct-horse" },
    });
    fireEvent.click(screen.getByRole("button", { name: /entrar/i }));

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith("dm@anahita.dev", "correct-horse");
      expect(push).toHaveBeenCalledWith("/campaigns");
    });
  });

  it("shows an error message for invalid credentials and does not redirect", async () => {
    login.mockRejectedValueOnce(new ApiError(401, "Invalid credentials"));
    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "dm@anahita.dev" },
    });
    fireEvent.change(screen.getByLabelText(/senha/i), {
      target: { value: "wrong-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: /entrar/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /email ou senha inválidos/i,
    );
    expect(push).not.toHaveBeenCalled();
  });
});
