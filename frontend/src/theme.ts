import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    background: { default: "#f6f6fb", paper: "#ffffff" },
    primary: { main: "#5246d8" },
  },
  shape: { borderRadius: 12 },
  typography: {
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
    h4: { fontWeight: 700 },
    h5: { fontWeight: 700 },
    h6: { fontWeight: 700 },
  },
});
