import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OrderValueDistributionChart } from "./OrderValueDistributionChart";

describe("OrderValueDistributionChart", () => {
  it("renders histogram bars without density curve overlays", () => {
    render(
      <OrderValueDistributionChart
        bins={[
          { lower_bound: "10", upper_bound: "20", order_count: 3 },
          { lower_bound: "20", upper_bound: "30", order_count: 5 },
        ]}
      />,
    );

    expect(screen.getByLabelText("Order-value distribution")).toBeInTheDocument();
    expect(screen.queryByLabelText("Log-normal and KDE density curves")).not.toBeInTheDocument();
  });
});
