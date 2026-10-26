import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Risk, Empty } from "./App";
import { percent } from "./api";
import type { Tx } from "./types";
const tx = { id: 1, flagged: null, risk_score: null } as Tx;

describe("analyst evidence states", () => {
  it("does not call unscored transactions clear", () => {
    render(<Risk tx={tx} />);
    expect(screen.getByText("Unscored")).toBeInTheDocument();
    expect(screen.queryByText("Clear")).toBeNull();
  });
  it("marks model alerts for review", () => {
    render(<Risk tx={{ ...tx, flagged: true, risk_score: 0.8 }} />);
    expect(screen.getByText("Flagged")).toBeInTheDocument();
  });
  it("shows honest missing data", () => {
    render(<Empty>No trained model available</Empty>);
    expect(screen.getByText("No trained model available")).toBeVisible();
    expect(percent(null)).toBe("—");
    expect(percent(0)).toBe("0.0%");
  });
});
