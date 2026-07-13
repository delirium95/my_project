import RestartAltRoundedIcon from "@mui/icons-material/RestartAltRounded";
import { Button, Paper, Stack, TextField, Typography } from "@mui/material";

import type { DateRange } from "../api";

interface AnalyticsDateFilterProps {
  dateRange: DateRange;
  onChange: (dateRange: DateRange) => void;
}

export function AnalyticsDateFilter({ dateRange, onChange }: AnalyticsDateFilterProps) {
  return (
    <Paper component="section" variant="outlined" sx={{ p: 2.5 }}>
      <Stack alignItems={{ md: "center" }} direction={{ md: "row", xs: "column" }} spacing={2}>
        <Typography component="h2" fontWeight={700} sx={{ minWidth: 180 }} variant="subtitle1">
          Explore the data
        </Typography>
        <Stack spacing={0.5}>
          <Typography color="text.secondary" component="label" htmlFor="analytics-start-date" variant="caption">
            From
          </Typography>
          <TextField
            id="analytics-start-date"
            inputProps={{ "aria-label": "From date" }}
            size="small"
            type="date"
            value={dateRange.start_date ?? ""}
            onChange={(event) => onChange({ ...dateRange, start_date: event.target.value || undefined })}
          />
        </Stack>
        <Stack spacing={0.5}>
          <Typography color="text.secondary" component="label" htmlFor="analytics-end-date" variant="caption">
            To
          </Typography>
          <TextField
            id="analytics-end-date"
            inputProps={{ "aria-label": "To date" }}
            size="small"
            type="date"
            value={dateRange.end_date ?? ""}
            onChange={(event) => onChange({ ...dateRange, end_date: event.target.value || undefined })}
          />
        </Stack>
        <Button
          disabled={!dateRange.start_date && !dateRange.end_date}
          startIcon={<RestartAltRoundedIcon />}
          onClick={() => onChange({})}
        >
          Reset
        </Button>
      </Stack>
    </Paper>
  );
}
