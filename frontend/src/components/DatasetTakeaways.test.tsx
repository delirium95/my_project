import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DatasetTakeaways } from "./DatasetTakeaways";

describe("DatasetTakeaways", () => {
  it("turns the analytical outputs into a readable EDA summary", () => {
    render(
      <DatasetTakeaways
        categoryRevenueConcentration={[
          { category: "bed_bath_table", cumulative_share: 0.15, revenue: "1200" },
        ]}
        correlations={[
          { coefficient: 1, x: "Items", y: "Items" },
          { coefficient: 0.72, x: "Item value", y: "Order total" },
        ]}
        fit={{
          aic: 20,
          bic: 22,
          density_points: [],
          kde_points: [],
          log_likelihood: -8,
          mu: 3,
          qq_points: [],
          sample_size: 8,
          sigma: 0.8,
        }}
        summary={{ average_order_value: "75", delivered_orders: 42, revenue: "3150" }}
      />,
    );

    expect(screen.getByText("Dataset takeaways")).toBeInTheDocument();
    expect(screen.getByText(/bed_bath_table is the leading category/i)).toBeInTheDocument();
    expect(screen.getByText(/Pearson r = 0.72/i)).toBeInTheDocument();
  });
});
