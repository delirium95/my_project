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
