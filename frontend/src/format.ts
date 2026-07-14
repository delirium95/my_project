export function formatMoney(value: string | number) {
  return new Intl.NumberFormat("en-US", {
    currency: "BRL",
    style: "currency",
  }).format(Number(value));
}

export function formatMonth(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    timeZone: "UTC",
    year: "2-digit",
  }).format(new Date(`${value}T00:00:00Z`));
}

export function formatTimestamp(value: string | null) {
  if (!value) {
    return "Not imported yet";
  }
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
