export async function getJson(path) {
  const res = await fetch(path);
  if (!res.ok) {
    throw new Error(`${path} → ${res.status}`);
  }
  return res.json();
}

export const cop = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});

export const pct = new Intl.NumberFormat("es-CO", {
  style: "percent",
  maximumFractionDigits: 1,
  signDisplay: "exceptZero",
});

export const unid = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 });

export function parseDate(s) {
  return new Date(`${s}T00:00:00`);
}
