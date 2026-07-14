import { Box, Paper, Stack, Tooltip, Typography } from "@mui/material";

import type { LogNormalFit, OrderValueDensityPoint, OrderValueDistributionBin } from "../api";
import { formatMoney } from "../format";

interface OrderValueDistributionChartProps {
  bins: OrderValueDistributionBin[];
  fit: LogNormalFit;
}

function curvePoints(
  points: OrderValueDensityPoint[],
  bins: OrderValueDistributionBin[],
  sampleSize: number,
  maximumOrders: number,
) {
  const lowerBound = Number(bins[0]?.lower_bound ?? 0);
  const upperBound = Number(bins.at(-1)?.upper_bound ?? 0);
  const binWidth = bins.length > 0 ? (upperBound - lowerBound) / bins.length : 0;
  if (upperBound <= lowerBound || binWidth <= 0) {
    return "";
  }
  return points
    .map((point) => {
      const x = ((Number(point.order_value) - lowerBound) / (upperBound - lowerBound)) * 100;
      const expectedOrders = point.density * sampleSize * binWidth;
      const y = 100 - Math.min((expectedOrders / maximumOrders) * 100, 100);
      return `${x},${y}`;
    })
    .join(" ");
}

export function OrderValueDistributionChart({ bins, fit }: OrderValueDistributionChartProps) {
  const maximumOrders = Math.max(...bins.map((bin) => bin.order_count), 1);
  const logNormalCurve = curvePoints(fit.density_points, bins, fit.sample_size, maximumOrders);
  const kdeCurve = curvePoints(fit.kde_points, bins, fit.sample_size, maximumOrders);

  return (
    <Paper component="section" variant="outlined" sx={{ p: 3 }}>
      <Typography component="h2" variant="h6">
        Order-value distribution
      </Typography>
      <Typography color="text.secondary" variant="body2">
        Histogram of delivered order totals, including freight.
      </Typography>
      {bins.length === 0 ? (
        <Typography color="text.secondary" sx={{ py: 8 }}>
          Import data to explore the order-value distribution.
        </Typography>
      ) : (
        <>
          <Box sx={{ position: "relative" }}>
            <Stack aria-label="Order-value distribution" direction="row" spacing={0.75} sx={{ height: 250, mt: 3 }}>
            {bins.map((bin) => {
              const height = Math.max((bin.order_count / maximumOrders) * 100, 2);
              const label = `${formatMoney(bin.lower_bound)} – ${formatMoney(bin.upper_bound)}: ${bin.order_count.toLocaleString()} orders`;

              return (
                <Tooltip key={`${bin.lower_bound}-${bin.upper_bound}`} title={label}>
                  <Box sx={{ flex: "1 1 0", minWidth: 0 }}>
                    <Box sx={{ alignItems: "flex-end", display: "flex", height: "calc(100% - 42px)" }}>
                      <Box
                        aria-label={label}
                        role="img"
                        sx={{
                          backgroundColor: "secondary.main",
                          borderRadius: "5px 5px 1px 1px",
                          height: `${height}%`,
                          width: "100%",
                        }}
                      />
                    </Box>
                    <Typography color="text.secondary" noWrap textAlign="center" variant="caption">
                      {formatMoney(bin.lower_bound)}
                    </Typography>
                  </Box>
                </Tooltip>
              );
            })}
            </Stack>
            {fit.sample_size > 1 ? (
            <Box
              aria-label="Log-normal and KDE density curves"
              component="svg"
              preserveAspectRatio="none"
              sx={{ bottom: 42, left: 0, pointerEvents: "none", position: "absolute", right: 0, top: 24 }}
              viewBox="0 0 100 100"
            >
              <polyline fill="none" points={logNormalCurve} stroke="#5246d8" strokeWidth="1.5" />
              <polyline fill="none" points={kdeCurve} stroke="#e96d5d" strokeDasharray="3 2" strokeWidth="1.5" />
            </Box>
            ) : null}
          </Box>
          <Stack direction="row" spacing={2} sx={{ mt: 1 }}>
            <Typography color="primary" variant="caption">━ Log-normal fit</Typography>
            <Typography sx={{ color: "#e96d5d" }} variant="caption">┄ KDE</Typography>
          </Stack>
        </>
      )}
    </Paper>
  );
}
