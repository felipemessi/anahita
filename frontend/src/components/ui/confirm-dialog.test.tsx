import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import { ConfirmDialog } from "./confirm-dialog";

it("renders nothing when closed", () => {
  const { container } = render(
    <ConfirmDialog
      open={false}
      title="Descanso longo"
      onConfirm={vi.fn()}
      onCancel={vi.fn()}
    />,
  );

  expect(container).toBeEmptyDOMElement();
});

it("cancel calls onCancel, not onConfirm", () => {
  const onConfirm = vi.fn();
  const onCancel = vi.fn();
  render(
    <ConfirmDialog
      open={true}
      title="Descanso longo"
      description="Isso reseta PV e espaços de magia."
      onConfirm={onConfirm}
      onCancel={onCancel}
    />,
  );

  expect(screen.getByRole("alertdialog", { name: "Descanso longo" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));

  expect(onCancel).toHaveBeenCalledTimes(1);
  expect(onConfirm).not.toHaveBeenCalled();
});

it("confirm calls onConfirm", () => {
  const onConfirm = vi.fn();
  render(
    <ConfirmDialog
      open={true}
      title="Descanso curto"
      onConfirm={onConfirm}
      onCancel={vi.fn()}
    />,
  );

  fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

  expect(onConfirm).toHaveBeenCalledTimes(1);
});
