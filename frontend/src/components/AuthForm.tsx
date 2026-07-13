import { useState, type FormEvent } from "react";
import {
  Alert,
  Box,
  Button,
  Link,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import { authApi, type Credentials, type Registration } from "../api";

interface AuthFormProps {
  onAuthenticated: (accessToken: string) => void;
}

type AuthMode = "login" | "register";

const initialCredentials: Registration = {
  email: "",
  password: "",
  display_name: "",
};

export function AuthForm({ onAuthenticated }: AuthFormProps) {
  const [mode, setMode] = useState<AuthMode>("login");
  const [credentials, setCredentials] = useState(initialCredentials);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isRegistering = mode === "register";

  function updateField(field: keyof Registration, value: string) {
    setCredentials((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (isRegistering) {
        await authApi.register({
          ...credentials,
          display_name: credentials.display_name?.trim() || undefined,
        });
      }
      const tokens = await authApi.login({
        email: credentials.email,
        password: credentials.password,
      } satisfies Credentials);
      onAuthenticated(tokens.access_token);
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "Unable to sign in.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function toggleMode() {
    setMode((current) => (current === "login" ? "register" : "login"));
    setError(null);
  }

  return (
    <Box
      component="main"
      sx={{
        alignItems: "center",
        display: "flex",
        justifyContent: "center",
        minHeight: "100vh",
        p: 2,
      }}
    >
      <Paper component="section" elevation={3} sx={{ maxWidth: 440, p: { xs: 3, sm: 4 }, width: "100%" }}>
        <Stack component="form" noValidate spacing={2.5} onSubmit={handleSubmit}>
          <Box>
            <Typography color="primary" fontWeight={800} letterSpacing="0.14em" variant="overline">
              BOUTIQUE ANALYTICS
            </Typography>
            <Typography component="h1" variant="h4">
              {isRegistering ? "Create an account" : "Welcome back"}
            </Typography>
            <Typography color="text.secondary" sx={{ mt: 0.5 }} variant="body2">
              Explore the Olist e-commerce dataset.
            </Typography>
          </Box>

          <TextField
            autoComplete="email"
            fullWidth
            label="Email"
            required
            type="email"
            value={credentials.email}
            onChange={(event) => updateField("email", event.target.value)}
          />
          {isRegistering ? (
            <TextField
              autoComplete="name"
              fullWidth
              label="Name"
              value={credentials.display_name}
              onChange={(event) => updateField("display_name", event.target.value)}
            />
          ) : null}
          <TextField
            autoComplete={isRegistering ? "new-password" : "current-password"}
            fullWidth
            inputProps={{ minLength: 8 }}
            label="Password"
            required
            type="password"
            value={credentials.password}
            onChange={(event) => updateField("password", event.target.value)}
          />
          {error ? <Alert severity="error">{error}</Alert> : null}
          <Button disabled={isSubmitting} size="large" type="submit" variant="contained">
            {isSubmitting
              ? "Please wait…"
              : isRegistering
                ? "Register and sign in"
                : "Sign in"}
          </Button>
          <Typography align="center" variant="body2">
            {isRegistering ? "Already have an account? " : "New here? "}
            <Link component="button" type="button" underline="hover" onClick={toggleMode}>
              {isRegistering ? "Sign in" : "Create one"}
            </Link>
          </Typography>
        </Stack>
      </Paper>
    </Box>
  );
}
