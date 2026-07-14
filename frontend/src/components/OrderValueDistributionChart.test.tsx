import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OrderValueDistributionChart } from "./OrderValueDistributionChart";

describe("OrderValueDistributionChart", () => {
  it("renders KDE alongside the log-normal fitted curve", () => {
    const { container } = render(
      <OrderValueDistributionChart
        bins={[
          { lower_bound: "10", upper_bound: "20", order_count: 3 },
          { lower_bound: "20", upper_bound: "30", order_count: 5 },
        ]}
        fit={{
          aic: 20,
          bic: 22,
          density_points: [
            { order_value: "10", density: 0.02 },
            { order_value: "30", density: 0.01 },
          ],
          kde_points: [
            { order_value: "10", density: 0.015 },
            { order_value: "30", density: 0.012 },
          ],
          log_likelihood: -8,
          mu: 3,
          qq_points: [],
          sample_size: 8,
          sigma: 0.5,
        }}
      />,
    );

    expect(screen.getByText("┄ KDE")).toBeInTheDocument();
    expect(screen.getByLabelText("Log-normal and KDE density curves")).toBeInTheDocument();
    expect(container.querySelectorAll("polyline")).toHaveLength(2);
  });

  it("keeps density curves inside the visible histogram range", () => {
    const { container } = render(
      <OrderValueDistributionChart
        bins={[
          { lower_bound: "10", upper_bound: "20", order_count: 3 },
          { lower_bound: "20", upper_bound: "30", order_count: 5 },
        ]}
        fit={{
          aic: 20,
          bic: 22,
          density_points: [
            { order_value: "5", density: 0.5 },
            { order_value: "10", density: 0.02 },
            { order_value: "30", density: 0.01 },
            { order_value: "35", density: 0.5 },
          ],
          kde_points: [],
          log_likelihood: -8,
          mu: 3,
          qq_points: [],
          sample_size: 8,
          sigma: 0.5,
        }}
      />,
    );

    expect(container.querySelector("polyline")).toHaveAttribute("points", "0,68 100,84");
  });
});
