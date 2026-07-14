import { Box, Paper, Stack, Typography } from "@mui/material";

import type { LogNormalFit, OrderValueDensityPoint } from "../api";

interface OrderValueDensityChartProps {
  fit: LogNormalFit;
}

function formatCompactMoney(value: number) {
  return new Intl.NumberFormat("en-US", {
    currency: "BRL",
    maximumFractionDigits: 0,
    notation: "compact",
    style: "currency",
  }).format(value);
}

function densityPath(
  points: OrderValueDensityPoint[],
  minimumLogValue: number,
  maximumLogValue: number,
  maximumDensity: number,
) {
  return points
    .filter((point) => Number(point.order_value) > 0 && Number(point.density) >= 0)
    .map((point, index) => {
      const orderValue = Number(point.order_value);
      const x = 5 + ((Math.log(orderValue) - minimumLogValue) / (maximumLogValue - minimumLogValue)) * 90;
      const y = 92 - (Number(point.density) / maximumDensity) * 82;
      return `${index === 0 ? "M" : "L"} ${x} ${Math.max(10, Math.min(92, y))}`;
    })
    .join(" ");
}

export function OrderValueDensityChart({ fit }: OrderValueDensityChartProps) {
  const points = [...fit.density_points, ...fit.kde_points].filter(
    (point) => Number(point.order_value) > 0 && Number(point.density) >= 0,
  );
  const values = points.map((point) => Number(point.order_value));
  const densities = points.map((point) => Number(point.density));
  const minimumValue = Math.min(...values);
  const maximumValue = Math.max(...values);
  const minimumLogValue = Math.log(minimumValue);
  const maximumLogValue = Math.log(maximumValue);
  const maximumDensity = Math.max(...densities, Number.EPSILON);
  const canRender =
    fit.sample_size > 1 &&
    Number.isFinite(minimumLogValue) &&
    Number.isFinite(maximumLogValue) &&
    maximumLogValue > minimumLogValue;

  return (
    <Paper component="section" variant="outlined" sx={{ p: 3 }}>
      <Typography component="h2" variant="h6">
        Order-value density fit
      </Typography>
      <Typography color="text.secondary" variant="body2">
        KDE versus a log-normal model. The order-value axis is logarithmic so the long tail stays readable.
      </Typography>
      {!canRender ? (
        <Typography color="text.secondary" sx={{ py: 8 }}>
          At least two varying delivered order totals are required for a density fit.
        </Typography>
      ) : (
        <>
          <Box
            aria-label="Order-value density fit"
            component="svg"
            preserveAspectRatio="none"
            sx={{ display: "block", height: 230, mt: 2.5, overflow: "hidden", width: "100%" }}
            viewBox="0 0 100 100"
          >
            {[28, 51, 74].map((y) => (
              <line key={y} stroke="#e7e6ef" strokeDasharray="2 2" strokeWidth="0.5" x1="5" x2="95" y1={y} y2={y} />
            ))}
            <line stroke="#a8a6b4" strokeWidth="0.7" x1="5" x2="95" y1="92" y2="92" />
            <path
              d={densityPath(fit.density_points, minimumLogValue, maximumLogValue, maximumDensity)}
              fill="none"
              stroke="#5246d8"
              strokeWidth="1.5"
            />
            <path
              d={densityPath(fit.kde_points, minimumLogValue, maximumLogValue, maximumDensity)}
              fill="none"
              stroke="#e96d5d"
              strokeDasharray="3 2"
              strokeWidth="1.5"
            />
          </Box>
          <Stack direction="row" justifyContent="space-between" spacing={1}>
            <Typography color="text.secondary" variant="caption">
              {formatCompactMoney(minimumValue)}
            </Typography>
            <Typography color="text.secondary" variant="caption">
              Relative density · log-scale order value
            </Typography>
            <Typography color="text.secondary" variant="caption">
              {formatCompactMoney(maximumValue)}
            </Typography>
          </Stack>
          <Stack direction="row" spacing={2} sx={{ mt: 1.5 }}>
            <Typography color="primary" variant="caption">
              ━ Log-normal model
            </Typography>
            <Typography sx={{ color: "#e96d5d" }} variant="caption">
              ┄ KDE
            </Typography>
          </Stack>
        </>
      )}
    </Paper>
  );
}
