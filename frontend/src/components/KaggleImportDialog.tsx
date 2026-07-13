import CloudDownloadRoundedIcon from "@mui/icons-material/CloudDownloadRounded";
import {
  Alert,
  Button,
  Checkbox,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Stack,
  Typography,
} from "@mui/material";
import { useState } from "react";

import type { DatasetImportResult } from "../api";

interface KaggleImportDialogProps {
  onImport: (replaceExisting: boolean) => Promise<DatasetImportResult>;
}

export function KaggleImportDialog({ onImport }: KaggleImportDialogProps) {
  const [isImporting, setIsImporting] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [replaceExisting, setReplaceExisting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DatasetImportResult | null>(null);

  function openDialog() {
    setError(null);
    setResult(null);
    setIsOpen(true);
  }

  async function importDataset() {
    setError(null);
    setIsImporting(true);
    try {
      setResult(await onImport(replaceExisting));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to import the dataset.");
    } finally {
      setIsImporting(false);
    }
  }

  return (
    <>
      <Button color="inherit" startIcon={<CloudDownloadRoundedIcon />} onClick={openDialog}>
        Import Olist data
      </Button>
      <Dialog fullWidth maxWidth="sm" open={isOpen} onClose={isImporting ? undefined : () => setIsOpen(false)}>
        <DialogTitle>Import Olist data from Kaggle</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <Typography color="text.secondary">
              The API downloads the configured Olist archive from Kaggle and imports its customers,
              products, orders, and order items. This can take a few minutes.
            </Typography>
            <FormControlLabel
              control={
                <Checkbox
                  checked={replaceExisting}
                  onChange={(event) => setReplaceExisting(event.target.checked)}
                />
              }
              label="Replace data that is already imported"
            />
            {replaceExisting ? (
              <Alert severity="warning">Existing Olist dashboard data will be replaced.</Alert>
            ) : null}
            {isImporting ? (
              <Stack alignItems="center" direction="row" spacing={1.5}>
                <CircularProgress size={20} />
                <Typography>Downloading and importing data…</Typography>
              </Stack>
            ) : null}
            {error ? <Alert severity="error">{error}</Alert> : null}
            {result ? (
              <Alert severity="success">
                Imported {result.orders.toLocaleString()} orders, {result.order_items.toLocaleString()} items,
                {" "}{result.customers.toLocaleString()} customers, and {result.products.toLocaleString()} products.
              </Alert>
            ) : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button disabled={isImporting} onClick={() => setIsOpen(false)}>
            {result ? "Done" : "Cancel"}
          </Button>
          <Button
            disabled={isImporting || result !== null}
            startIcon={isImporting ? <CircularProgress size={16} /> : <CloudDownloadRoundedIcon />}
            variant="contained"
            onClick={() => void importDataset()}
          >
            Import dataset
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
