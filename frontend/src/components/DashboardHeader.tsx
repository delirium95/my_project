import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";
import { AppBar, Box, Button, Toolbar, Typography } from "@mui/material";

import type { DatasetImportResult } from "../api";
import { KaggleImportDialog } from "./KaggleImportDialog";

interface DashboardHeaderProps {
  onImport: (replaceExisting: boolean) => Promise<DatasetImportResult>;
  onLogout: () => void;
}

export function DashboardHeader({ onImport, onLogout }: DashboardHeaderProps) {
  return (
    <AppBar color="inherit" elevation={0} position="sticky" sx={{ borderBottom: 1, borderColor: "divider" }}>
      <Toolbar sx={{ justifyContent: "space-between", mx: "auto", width: "100%", maxWidth: 1240 }}>
        <Box>
          <Typography color="primary" fontWeight={800} letterSpacing="0.14em" variant="overline">
            BOUTIQUE ANALYTICS
          </Typography>
          <Typography component="h1" variant="h6">
            Commerce overview
          </Typography>
        </Box>
        <Box sx={{ alignItems: "center", display: "flex", gap: 1 }}>
          <KaggleImportDialog onImport={onImport} />
          <Button color="inherit" startIcon={<LogoutRoundedIcon />} onClick={onLogout}>
            Sign out
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
