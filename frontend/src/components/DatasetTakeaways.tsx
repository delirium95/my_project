import { Paper, Stack, Typography } from "@mui/material";

import type {
  CategoryRevenueConcentrationPoint,
  DashboardSummary,
  LogNormalFit,
  PearsonCorrelation,
} from "../api";
import { formatMoney } from "../format";

interface DatasetTakeawaysProps {
  categoryRevenueConcentration: CategoryRevenueConcentrationPoint[];
  correlations: PearsonCorrelation[];
  fit: LogNormalFit;
  summary: DashboardSummary;
}

function strongestRelationship(correlations: PearsonCorrelation[]) {
  return correlations
    .filter(
      (correlation): correlation is PearsonCorrelation & { coefficient: number } =>
        correlation.coefficient !== null && correlation.x !== correlation.y,
    )
    .reduce<PearsonCorrelation | null>((strongest, correlation) => {
      if (!strongest || Math.abs(correlation.coefficient ?? 0) > Math.abs(strongest.coefficient ?? 0)) {
        return correlation;
      }
      return strongest;
    }, null);
}

export function DatasetTakeaways({
  categoryRevenueConcentration,
  correlations,
  fit,
  summary,
}: DatasetTakeawaysProps) {
  const leadingCategory = categoryRevenueConcentration[0];
  const strongestCorrelation = strongestRelationship(correlations);
  const insights = [
    `${summary.delivered_orders.toLocaleString()} delivered orders generated ${formatMoney(summary.revenue)} in revenue, with an average order value of ${formatMoney(summary.average_order_value)}.`,
    leadingCategory
      ? `${leadingCategory.category} is the leading category, accounting for ${(leadingCategory.cumulative_share * 100).toFixed(1)}% of delivered revenue.`
      : null,
    strongestCorrelation
      ? `The strongest order-level relationship is ${strongestCorrelation.x} and ${strongestCorrelation.y} (Pearson r = ${strongestCorrelation.coefficient?.toFixed(2)}).`
      : null,
    fit.sigma !== null
      ? `Order values are strongly right-skewed; the log-normal fit has σ = ${fit.sigma.toFixed(2)} across ${fit.sample_size.toLocaleString()} orders.`
      : null,
  ].filter((insight): insight is string => insight !== null);

  return (
    <Paper component="section" variant="outlined" sx={{ p: 3 }}>
      <Typography component="h2" variant="h6">
        Dataset takeaways
      </Typography>
      <Typography color="text.secondary" variant="body2">
        A concise EDA read-out generated from the imported data and selected date range.
      </Typography>
      <Stack component="ul" spacing={1} sx={{ mb: 0, mt: 2, pl: 2.5 }}>
        {insights.map((insight) => (
          <Typography component="li" key={insight} variant="body2">
            {insight}
          </Typography>
        ))}
      </Stack>
    </Paper>
  );
}
