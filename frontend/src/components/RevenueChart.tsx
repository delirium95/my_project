import { Box, Paper, Stack, Tooltip, Typography } from "@mui/material";

import type { RevenuePoint } from "../api";
import { formatMoney, formatMonth } from "../format";

interface RevenueChartProps {
  points: RevenuePoint[];
}

export function RevenueChart({ points }: RevenueChartProps) {
  const maximumRevenue = Math.max(...points.map((point) => Number(point.revenue)), 1);

  return (
    <Paper component="section" variant="outlined" sx={{ p: 3 }}>
      <Typography component="h2" variant="h6">
        Monthly delivered revenue
      </Typography>
      <Typography color="text.secondary" variant="body2">
        Revenue includes item price and freight for delivered orders.
      </Typography>
      {points.length === 0 ? (
        <Typography color="text.secondary" sx={{ py: 8 }}>
          Seed the Olist CSV files to populate this chart.
        </Typography>
      ) : (
        <Stack
          aria-label="Monthly delivered revenue"
          direction="row"
          spacing={1}
          sx={{ alignItems: "flex-end", height: 260, mt: 3, overflowX: "auto", pb: 0.5 }}
        >
          {points.map((point) => {
            const height = Math.max((Number(point.revenue) / maximumRevenue) * 100, 2);
            const label = `${formatMonth(point.period)}: ${formatMoney(point.revenue)}, ${point.order_count} orders`;

            return (
              <Tooltip key={point.period} title={label}>
                <Box sx={{ flex: "1 0 52px", height: "100%", minWidth: 52 }}>
                  <Box sx={{ alignItems: "center", display: "flex", height: "calc(100% - 26px)" }}>
                    <Box
                      aria-label={label}
                      role="img"
                      sx={{
                        background: "linear-gradient(180deg, #8177f7 0%, #5246d8 100%)",
                        borderRadius: "6px 6px 2px 2px",
                        height: `${height}%`,
                        width: "100%",
                      }}
                    />
                  </Box>
                  <Typography align="center" color="text.secondary" noWrap variant="caption">
                    {formatMonth(point.period)}
                  </Typography>
                </Box>
              </Tooltip>
            );
          })}
        </Stack>
      )}
    </Paper>
  );
}
