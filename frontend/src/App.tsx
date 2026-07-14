import { useEffect, useState } from "react";
import { Alert, Box, CircularProgress, Container, Grid, Stack } from "@mui/material";

import {
  authApi,
  dashboardApi,
  datasetApi,
  type CategoryRevenueConcentrationPoint,
  type CohortRetentionPoint,
  type DataFreshness,
  type DateRange,
  type DashboardSummary,
  type DatasetImportResult,
  type LogNormalFit,
  type OrderValueDistributionBin,
  type PearsonCorrelation,
  type RecentOrder,
  type RevenuePoint,
} from "./api";
import { AnalyticsDateFilter } from "./components/AnalyticsDateFilter";
import { AuthForm } from "./components/AuthForm";
import { CategoryRevenueConcentrationChart } from "./components/CategoryRevenueConcentrationChart";
import { CohortRetentionHeatmap } from "./components/CohortRetentionHeatmap";
import { DashboardHeader } from "./components/DashboardHeader";
import { DatasetTakeaways } from "./components/DatasetTakeaways";
import { LogNormalFitDiagnostics } from "./components/LogNormalFitDiagnostics";
import { MetricCard } from "./components/MetricCard";
import { OrderValueDistributionChart } from "./components/OrderValueDistributionChart";
import { OrderValueDensityChart } from "./components/OrderValueDensityChart";
import { PearsonCorrelationHeatmap } from "./components/PearsonCorrelationHeatmap";
import { RecentOrdersTable } from "./components/RecentOrdersTable";
import { RevenueChart } from "./components/RevenueChart";
import { formatMoney } from "./format";

interface DashboardData {
  categoryRevenueConcentration: CategoryRevenueConcentrationPoint[];
  cohortRetention: CohortRetentionPoint[];
  correlations: PearsonCorrelation[];
  dataFreshness: DataFreshness;
  distribution: OrderValueDistributionBin[];
  logNormalFit: LogNormalFit;
  orders: RecentOrder[];
  revenue: RevenuePoint[];
  summary: DashboardSummary;
}

function LoadingScreen() {
  return (
    <Box sx={{ alignItems: "center", display: "flex", justifyContent: "center", minHeight: "100vh" }}>
      <CircularProgress aria-label="Loading application" />
    </Box>
  );
}

function Dashboard({ accessToken, onLogout }: { accessToken: string; onLogout: () => Promise<void> }) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [dataVersion, setDataVersion] = useState(0);
  const [dateRange, setDateRange] = useState<DateRange>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCurrent = true;

    async function loadDashboard() {
      setError(null);
      try {
        const [
          summary,
          revenue,
          orders,
          distribution,
          correlations,
          logNormalFit,
          categoryRevenueConcentration,
          cohortRetention,
          dataFreshness,
        ] = await Promise.all([
          dashboardApi.summary(accessToken),
          dashboardApi.revenue(dateRange, accessToken),
          dashboardApi.orders(accessToken),
          dashboardApi.distribution(dateRange, accessToken),
          dashboardApi.correlations(dateRange, accessToken),
          dashboardApi.logNormalFit(dateRange, accessToken),
          dashboardApi.categoryRevenueConcentration(dateRange, accessToken),
          dashboardApi.cohortRetention(accessToken),
          dashboardApi.dataFreshness(accessToken),
        ]);
        if (isCurrent) {
          setData({
            categoryRevenueConcentration,
            cohortRetention,
            correlations,
            dataFreshness,
            distribution,
            logNormalFit,
            orders,
            revenue,
            summary,
          });
        }
      } catch (requestError) {
        if (isCurrent) {
          setError(
            requestError instanceof Error ? requestError.message : "Unable to load the dashboard.",
          );
        }
      }
    }

    void loadDashboard();
    return () => {
      isCurrent = false;
    };
  }, [accessToken, dataVersion, dateRange]);

  async function importKaggleOlist(replaceExisting: boolean): Promise<DatasetImportResult> {
    const result = await datasetApi.importKaggleOlist(
      { replace_existing: replaceExisting },
      accessToken,
    );
    setDataVersion((current) => current + 1);
    return result;
  }

  if (!data && !error) {
    return <LoadingScreen />;
  }

  return (
    <>
      <DashboardHeader
        lastImportedAt={data?.dataFreshness.last_imported_at ?? null}
        onImport={importKaggleOlist}
        onLogout={() => void onLogout()}
      />
      <Container component="main" maxWidth="lg" sx={{ py: 4 }}>
        {error ? (
          <Alert severity="error">{error}</Alert>
        ) : data ? (
          <Stack spacing={3}>
            <Grid container spacing={2}>
              <Grid size={{ md: 4, xs: 12 }}>
                <MetricCard label="Delivered revenue" value={formatMoney(data.summary.revenue)} />
              </Grid>
              <Grid size={{ md: 4, xs: 12 }}>
                <MetricCard label="Delivered orders" value={data.summary.delivered_orders} />
              </Grid>
              <Grid size={{ md: 4, xs: 12 }}>
                <MetricCard label="Average order value" value={formatMoney(data.summary.average_order_value)} />
              </Grid>
            </Grid>
            <AnalyticsDateFilter dateRange={dateRange} onChange={setDateRange} />
            <DatasetTakeaways
              categoryRevenueConcentration={data.categoryRevenueConcentration}
              correlations={data.correlations}
              fit={data.logNormalFit}
              summary={data.summary}
            />
            <RevenueChart points={data.revenue} />
            <Grid container spacing={3}>
              <Grid size={{ md: 6, xs: 12 }}>
                <Stack spacing={3}>
                  <OrderValueDistributionChart bins={data.distribution} />
                  <OrderValueDensityChart fit={data.logNormalFit} />
                </Stack>
              </Grid>
              <Grid size={{ md: 6, xs: 12 }}>
                <PearsonCorrelationHeatmap correlations={data.correlations} />
              </Grid>
            </Grid>
            <Grid container spacing={3}>
              <Grid size={{ md: 6, xs: 12 }}>
                <CategoryRevenueConcentrationChart points={data.categoryRevenueConcentration} />
              </Grid>
              <Grid size={{ md: 6, xs: 12 }}>
                <LogNormalFitDiagnostics fit={data.logNormalFit} />
              </Grid>
            </Grid>
            <CohortRetentionHeatmap points={data.cohortRetention} />
            <RecentOrdersTable orders={data.orders} />
          </Stack>
        ) : null}
      </Container>
    </>
  );
}

export default function App() {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  useEffect(() => {
    async function restoreSession() {
      try {
        const tokens = await authApi.refresh();
        setAccessToken(tokens.access_token);
      } catch {
        // A missing or expired refresh cookie simply means the user must sign in.
      } finally {
        setIsBootstrapping(false);
      }
    }

    void restoreSession();
  }, []);

  async function logout() {
    try {
      await authApi.logout();
    } finally {
      setAccessToken(null);
    }
  }

  if (isBootstrapping) {
    return <LoadingScreen />;
  }

  return accessToken ? (
    <Dashboard accessToken={accessToken} onLogout={logout} />
  ) : (
    <AuthForm onAuthenticated={setAccessToken} />
  );
}
