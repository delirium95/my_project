const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export interface AccessTokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in_seconds: number;
}

export interface CurrentUser {
  id: string;
  email: string;
  display_name: string | null;
}

export interface DashboardSummary {
  revenue: string;
  delivered_orders: number;
  average_order_value: string;
}

export interface RevenuePoint {
  period: string;
  revenue: string;
  order_count: number;
}

export interface OrderValueDistributionBin {
  lower_bound: string;
  order_count: number;
  upper_bound: string;
}

export interface PearsonCorrelation {
  coefficient: number | null;
  x: string;
  y: string;
}

export interface OrderValueDensityPoint {
  order_value: string;
  density: number;
}

export interface LogNormalQuantilePoint {
  observed_value: string;
  theoretical_value: string;
}

export interface LogNormalFit {
  aic: number | null;
  bic: number | null;
  density_points: OrderValueDensityPoint[];
  kde_points: OrderValueDensityPoint[];
  log_likelihood: number | null;
  mu: number | null;
  qq_points: LogNormalQuantilePoint[];
  sample_size: number;
  sigma: number | null;
}

export interface CategoryRevenueConcentrationPoint {
  category: string;
  cumulative_share: number;
  revenue: string;
}

export interface CohortRetentionPoint {
  active_customers: number;
  cohort_month: string;
  month_number: number;
  retention_rate: number;
}

export interface DataFreshness {
  last_imported_at: string | null;
}

export interface RecentOrder {
  id: string;
  customer_id: string;
  status: string;
  purchased_at: string;
  total: string;
}

export interface DatasetImportResult {
  customers: number;
  order_items: number;
  orders: number;
  products: number;
  source: string;
}

interface RequestOptions extends Omit<RequestInit, "headers"> {
  token?: string;
  headers?: HeadersInit;
}

export interface Credentials {
  email: string;
  password: string;
}

export interface Registration extends Credentials {
  display_name?: string;
}

export interface KaggleOlistImport {
  replace_existing: boolean;
}

export interface DateRange {
  end_date?: string;
  start_date?: string;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { token, headers, ...fetchOptions } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...fetchOptions,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  if (!response.ok) {
    const body: { detail?: unknown } = await response.json().catch(() => ({}));
    throw new Error(getErrorMessage(body.detail));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

function getErrorMessage(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail.flatMap((error) => {
      if (typeof error !== "object" || error === null || !("msg" in error)) {
        return [];
      }
      const { msg } = error;
      return typeof msg === "string" ? [msg] : [];
    });
    if (messages.length > 0) {
      return messages.join(" ");
    }
  }

  return "The request could not be completed.";
}

export const authApi = {
  register: (payload: Registration): Promise<CurrentUser> =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  login: (payload: Credentials): Promise<AccessTokenResponse> =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  refresh: (): Promise<AccessTokenResponse> =>
    request("/auth/refresh", { method: "POST" }),
  logout: (): Promise<void> => request("/auth/logout", { method: "POST" }),
  me: (token: string): Promise<CurrentUser> => request("/auth/me", { token }),
};

export const datasetApi = {
  importKaggleOlist: (
    payload: KaggleOlistImport,
    token: string,
  ): Promise<DatasetImportResult> =>
    request("/dataset/import/kaggle", {
      body: JSON.stringify(payload),
      method: "POST",
      token,
    }),
};

export const dashboardApi = {
  categoryRevenueConcentration: (
    dateRange: DateRange,
    token: string,
  ): Promise<CategoryRevenueConcentrationPoint[]> =>
    request(`/dashboard/pareto${dateRangeQuery(dateRange)}`, { token }),
  cohortRetention: (token: string): Promise<CohortRetentionPoint[]> =>
    request("/dashboard/cohorts", { token }),
  correlations: (dateRange: DateRange, token: string): Promise<PearsonCorrelation[]> =>
    request(`/dashboard/correlations${dateRangeQuery(dateRange)}`, { token }),
  dataFreshness: (token: string): Promise<DataFreshness> =>
    request("/dashboard/data-freshness", { token }),
  distribution: (dateRange: DateRange, token: string): Promise<OrderValueDistributionBin[]> =>
    request(`/dashboard/distribution${dateRangeQuery(dateRange)}`, { token }),
  logNormalFit: (dateRange: DateRange, token: string): Promise<LogNormalFit> =>
    request(`/dashboard/fit/log-normal${dateRangeQuery(dateRange)}`, { token }),
  orders: (token: string): Promise<RecentOrder[]> =>
    request("/dashboard/orders?limit=20", { token }),
  revenue: (dateRange: DateRange, token: string): Promise<RevenuePoint[]> =>
    request(`/dashboard/revenue${dateRangeQuery(dateRange)}`, { token }),
  summary: (token: string): Promise<DashboardSummary> =>
    request("/dashboard/summary", { token }),
};

function dateRangeQuery({ end_date, start_date }: DateRange): string {
  const params = new URLSearchParams();
  if (start_date) {
    params.set("start_date", start_date);
  }
  if (end_date) {
    params.set("end_date", end_date);
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}
