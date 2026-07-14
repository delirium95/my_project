import { Box, Paper, Tooltip, Typography } from "@mui/material";

import type { CohortRetentionPoint } from "../api";
import { formatMonth } from "../format";

interface CohortRetentionHeatmapProps {
  points: CohortRetentionPoint[];
}

function colorForRetention(retentionRate: number) {
  const lightness = 96 - Math.round(retentionRate * 56);
  return `hsl(250 72% ${lightness}%)`;
}

export function CohortRetentionHeatmap({ points }: CohortRetentionHeatmapProps) {
  const cohortMonths = [...new Set(points.map((point) => point.cohort_month))];
  const months = Array.from({ length: Math.min(Math.max(...points.map((point) => point.month_number), 0) + 1, 12) }, (_, index) => index);
  const values = new Map(points.map((point) => [`${point.cohort_month}:${point.month_number}`, point]));

  return (
    <Paper component="section" variant="outlined" sx={{ overflowX: "auto", p: 3 }}>
      <Typography component="h2" variant="h6">Customer cohort retention</Typography>
      <Typography color="text.secondary" variant="body2">
        Delivered-order cohorts use Olist’s repeat-customer identity and full order history; M0 is the first purchase month.
      </Typography>
      {cohortMonths.length === 0 ? (
        <Typography color="text.secondary" sx={{ py: 8 }}>Re-import Olist data to build customer retention cohorts.</Typography>
      ) : (
        <Box sx={{ display: "grid", gap: 0.5, gridTemplateColumns: `82px repeat(${months.length}, minmax(58px, 1fr))`, minWidth: 600, mt: 3 }}>
          <Box />
          {months.map((month) => <Typography align="center" fontWeight={700} key={month} variant="caption">M{month}</Typography>)}
          {cohortMonths.flatMap((cohortMonth) => [
            <Typography alignSelf="center" fontWeight={700} key={`${cohortMonth}:label`} variant="caption">{formatMonth(cohortMonth)}</Typography>,
            ...months.map((month) => {
              const point = values.get(`${cohortMonth}:${month}`);
              const retention = point?.retention_rate ?? 0;
              const label = point
                ? `${formatMonth(cohortMonth)}, month ${month}: ${(retention * 100).toFixed(1)}% (${point.active_customers.toLocaleString()} customers)`
                : `${formatMonth(cohortMonth)}, month ${month}: no activity`;
              return (
                <Tooltip key={`${cohortMonth}:${month}`} title={label}>
                  <Box aria-label={label} role="img" sx={{ backgroundColor: colorForRetention(retention), borderRadius: 1, fontSize: 12, fontWeight: 700, p: 1, textAlign: "center" }}>
                    {point ? `${(retention * 100).toFixed(0)}%` : "—"}
                  </Box>
                </Tooltip>
              );
            }),
          ])}
        </Box>
      )}
    </Paper>
  );
}
