import { Card, CardContent, Typography } from "@mui/material";

interface MetricCardProps {
  label: string;
  value: string | number;
}

export function MetricCard({ label, value }: MetricCardProps) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography color="text.secondary" variant="body2">
          {label}
        </Typography>
        <Typography component="p" sx={{ mt: 1 }} variant="h5">
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
}
