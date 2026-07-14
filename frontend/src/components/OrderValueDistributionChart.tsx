import { Box, Paper, Stack, Tooltip, Typography } from "@mui/material";

import type { OrderValueDistributionBin } from "../api";
import { formatMoney } from "../format";

interface OrderValueDistributionChartProps {
  bins: OrderValueDistributionBin[];
}

export function OrderValueDistributionChart({ bins }: OrderValueDistributionChartProps) {
  const maximumOrders = Math.max(...bins.map((bin) => bin.order_count), 1);
  // Four labels leave enough room for real currency values on a two-column dashboard.
  const tickStride = Math.max(1, Math.ceil(bins.length / 4));

  return (
    <Paper component="section" variant="outlined" sx={{ p: 3 }}>
      <Typography component="h2" variant="h6">
        Order-value distribution
      </Typography>
      <Typography color="text.secondary" variant="body2">
        Histogram of delivered order totals, including freight. Hover a bar for its exact range.
      </Typography>
      {bins.length === 0 ? (
        <Typography color="text.secondary" sx={{ py: 8 }}>
          Import data to explore the order-value distribution.
        </Typography>
      ) : (
        <Stack
          aria-label="Order-value distribution"
          direction="row"
          spacing={0.75}
          sx={{ height: 250, mt: 3 }}
        >
          {bins.map((bin, index) => {
            const height = Math.max((bin.order_count / maximumOrders) * 100, 2);
            const label = `${formatMoney(bin.lower_bound)} – ${formatMoney(bin.upper_bound)}: ${bin.order_count.toLocaleString()} orders`;
            const showTick = index % tickStride === 0 || index === bins.length - 1;

            return (
              <Tooltip key={`${bin.lower_bound}-${bin.upper_bound}`} title={label}>
                <Box sx={{ flex: "1 1 0", minWidth: 0 }}>
                  <Box
                    sx={{ alignItems: "flex-end", display: "flex", height: "calc(100% - 42px)" }}
                  >
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
                  <Typography
                    aria-hidden={!showTick}
                    color="text.secondary"
                    noWrap
                    sx={{ visibility: showTick ? "visible" : "hidden" }}
                    textAlign="center"
                    variant="caption"
                  >
                    {formatMoney(bin.lower_bound)}
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
