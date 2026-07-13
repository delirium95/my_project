import { Box, Paper, Tooltip, Typography } from "@mui/material";

import type { PearsonCorrelation } from "../api";

interface PearsonCorrelationHeatmapProps {
  correlations: PearsonCorrelation[];
}

function colorForCoefficient(coefficient: number | null) {
  if (coefficient === null) {
    return "#ececf3";
  }
  const intensity = Math.round(Math.abs(coefficient) * 62) + 18;
  return coefficient >= 0 ? `hsl(250 72% ${100 - intensity}%)` : `hsl(8 76% ${100 - intensity}%)`;
}

export function PearsonCorrelationHeatmap({ correlations }: PearsonCorrelationHeatmapProps) {
  const labels = [...new Set(correlations.map((correlation) => correlation.x))];
  const cells = new Map(correlations.map((correlation) => [`${correlation.x}:${correlation.y}`, correlation]));

  return (
    <Paper component="section" variant="outlined" sx={{ overflowX: "auto", p: 3 }}>
      <Typography component="h2" variant="h6">
        Pearson correlation heatmap
      </Typography>
      <Typography color="text.secondary" variant="body2">
        Order-level relationships. Purple is positive, coral is negative; hover a cell for the value.
      </Typography>
      {labels.length === 0 ? (
        <Typography color="text.secondary" sx={{ py: 8 }}>
          Import data to calculate correlations.
        </Typography>
      ) : (
        <Box
          aria-label="Pearson correlation heatmap"
          sx={{
            display: "grid",
            gap: 0.5,
            gridTemplateColumns: `120px repeat(${labels.length}, minmax(78px, 1fr))`,
            minWidth: 460,
            mt: 3,
          }}
        >
          <Box />
          {labels.map((label) => (
            <Typography key={label} align="center" fontWeight={700} variant="caption">
              {label}
            </Typography>
          ))}
          {labels.flatMap((x) => [
            <Typography key={`${x}:label`} alignSelf="center" fontWeight={700} variant="caption">
              {x}
            </Typography>,
            ...labels.map((y) => {
              const cell = cells.get(`${x}:${y}`);
              const coefficient = cell?.coefficient ?? null;
              const label = `${x} × ${y}: ${coefficient === null ? "insufficient variation" : coefficient.toFixed(3)}`;
              return (
                <Tooltip key={`${x}:${y}`} title={label}>
                  <Box
                    aria-label={label}
                    role="img"
                    sx={{
                      backgroundColor: colorForCoefficient(coefficient),
                      borderRadius: 1,
                      color: coefficient !== null && Math.abs(coefficient) > 0.62 ? "common.white" : "text.primary",
                      fontSize: 12,
                      fontWeight: 700,
                      p: 1.25,
                      textAlign: "center",
                    }}
                  >
                    {coefficient === null ? "—" : coefficient.toFixed(2)}
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
