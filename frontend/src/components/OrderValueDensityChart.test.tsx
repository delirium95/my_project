import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OrderValueDensityChart } from "./OrderValueDensityChart";

describe("OrderValueDensityChart", () => {
  it("renders KDE and log-normal curves in their own chart", () => {
    const { container } = render(
      <OrderValueDensityChart
        fit={{
          aic: 20,
          bic: 22,
          density_points: [
            { order_value: "10", density: 0.02 },
            { order_value: "100", density: 0.01 },
          ],
          kde_points: [
            { order_value: "10", density: 0.015 },
            { order_value: "100", density: 0.012 },
          ],
          log_likelihood: -8,
          mu: 3,
          qq_points: [],
          sample_size: 8,
          sigma: 0.5,
        }}
      />,
    );

    expect(screen.getByLabelText("Order-value density fit")).toBeInTheDocument();
    expect(screen.getByText("┄ KDE")).toBeInTheDocument();
    expect(container.querySelectorAll("path")).toHaveLength(2);
  });
});
