import { Box, Paper, Stack, Tooltip, Typography } from "@mui/material";

import type { CategoryRevenueConcentrationPoint } from "../api";
import { formatMoney } from "../format";

interface CategoryRevenueConcentrationChartProps {
  points: CategoryRevenueConcentrationPoint[];
}

export function CategoryRevenueConcentrationChart({ points }: CategoryRevenueConcentrationChartProps) {
  const maximumRevenue = Math.max(...points.map((point) => Number(point.revenue)), 1);

  return (
    <Paper component="section" variant="outlined" sx={{ p: 3 }}>
      <Typography component="h2" variant="h6">Category revenue concentration</Typography>
      <Typography color="text.secondary" variant="body2">
        Pareto view: bars show revenue; labels show cumulative share of delivered revenue.
      </Typography>
      {points.length === 0 ? (
        <Typography color="text.secondary" sx={{ py: 8 }}>Import data to calculate revenue concentration.</Typography>
      ) : (
        <Stack spacing={1.25} sx={{ mt: 3 }}>
          {points.map((point) => {
            const share = (Number(point.revenue) / maximumRevenue) * 100;
            const label = `${point.category}: ${formatMoney(point.revenue)}, ${(point.cumulative_share * 100).toFixed(1)}% cumulative`;
            return (
              <Tooltip key={point.category} title={label}>
                <Box>
                  <Stack direction="row" justifyContent="space-between" spacing={1}>
                    <Typography noWrap variant="caption">{point.category}</Typography>
                    <Typography color="text.secondary" variant="caption">{(point.cumulative_share * 100).toFixed(1)}%</Typography>
                  </Stack>
                  <Box sx={{ backgroundColor: "action.hover", borderRadius: 4, height: 9, mt: 0.5, overflow: "hidden" }}>
                    <Box sx={{ background: "linear-gradient(90deg, #5246d8, #8177f7)", borderRadius: 4, height: "100%", width: `${share}%` }} />
                  </Box>
                </Box>
              </Tooltip>
            );
          })}
        </Stack>
      )}
    </Paper>
  );
}
