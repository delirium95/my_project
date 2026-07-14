import { Box, Paper, Stack, Typography } from "@mui/material";

import type { LogNormalFit } from "../api";
import { formatMoney } from "../format";

interface LogNormalFitDiagnosticsProps {
  fit: LogNormalFit;
}

function metric(value: number | null, digits = 2) {
  return value === null ? "—" : value.toFixed(digits);
}

export function LogNormalFitDiagnostics({ fit }: LogNormalFitDiagnosticsProps) {
  const maximumValue = Math.max(
    ...fit.qq_points.flatMap((point) => [Number(point.observed_value), Number(point.theoretical_value)]),
    1,
  );

  return (
    <Paper component="section" variant="outlined" sx={{ p: 3 }}>
      <Typography component="h2" variant="h6">Log-normal fit diagnostics</Typography>
      <Typography color="text.secondary" variant="body2">
        Compare a parametric log-normal model against the KDE curve and observed order totals.
      </Typography>
      {fit.mu === null ? (
        <Typography color="text.secondary" sx={{ py: 8 }}>
          At least two varying delivered order totals are required for a distribution fit.
        </Typography>
      ) : (
        <Stack spacing={2.5} sx={{ mt: 3 }}>
          <Box sx={{ display: "grid", gap: 1, gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
            {[
              ["μ", metric(fit.mu, 3)],
              ["σ", metric(fit.sigma, 3)],
              ["Log-likelihood", metric(fit.log_likelihood, 1)],
              ["AIC", metric(fit.aic, 1)],
              ["BIC", metric(fit.bic, 1)],
              ["Orders", fit.sample_size.toLocaleString()],
            ].map(([label, value]) => (
              <Box key={label} sx={{ backgroundColor: "action.hover", borderRadius: 1.5, p: 1.25 }}>
                <Typography color="text.secondary" variant="caption">{label}</Typography>
                <Typography fontWeight={800} variant="body2">{value}</Typography>
              </Box>
            ))}
          </Box>
          <Box>
            <Typography fontWeight={700} variant="subtitle2">QQ plot</Typography>
            <Typography color="text.secondary" variant="caption">
              Points close to the diagonal indicate a closer log-normal fit.
            </Typography>
            <Box component="svg" sx={{ display: "block", height: 170, mt: 1.5, width: "100%" }} viewBox="0 0 100 100">
              <line stroke="#a8a6b4" strokeDasharray="3 2" strokeWidth="1" x1="5" x2="95" y1="95" y2="5" />
              {fit.qq_points.map((point) => {
                const x = 5 + (Number(point.theoretical_value) / maximumValue) * 90;
                const y = 95 - (Number(point.observed_value) / maximumValue) * 90;
                return <circle cx={x} cy={y} fill="#5246d8" key={`${point.theoretical_value}-${point.observed_value}`} r="1.7" />;
              })}
            </Box>
            <Stack direction="row" justifyContent="space-between">
              <Typography color="text.secondary" variant="caption">Theoretical: {formatMoney(0)}</Typography>
              <Typography color="text.secondary" variant="caption">{formatMoney(maximumValue)}</Typography>
            </Stack>
          </Box>
        </Stack>
      )}
    </Paper>
  );
}
