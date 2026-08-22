from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

SEED = 42

STORES = [
    (1, "Super Andina Bogotá", "Andina", 4.711, -74.072),
    (2, "Super Andina Medellín", "Andina", 6.247, -75.566),
    (3, "Super Caribe Barranquilla", "Caribe", 10.968, -74.781),
    (4, "Super Caribe Cartagena", "Caribe", 10.391, -75.479),
    (5, "Super Pacífico Cali", "Pacífico", 3.451, -76.532),
    (6, "Super Pacífico Palmira", "Pacífico", 3.539, -76.304),
    (7, "Super Cafetero Pereira", "Eje Cafetero", 4.813, -75.696),
    (8, "Super Cafetero Manizales", "Eje Cafetero", 5.070, -75.517),
]

CATEGORIES = {
    "Abarrotes": [
        ("Arroz 5kg", 18_000),
        ("Aceite 1L", 12_500),
        ("Azúcar 1kg", 4_800),
        ("Pasta 500g", 3_900),
        ("Frijol 500g", 6_200),
        ("Sal 1kg", 2_100),
        ("Café 500g", 22_000),
        ("Harina 1kg", 4_400),
    ],
    "Lácteos": [
        ("Leche 1L", 4_200),
        ("Queso fresco 500g", 14_000),
        ("Yogur 1L", 7_800),
        ("Mantequilla 250g", 9_500),
        ("Crema de leche", 6_400),
        ("Kumís 1L", 5_900),
        ("Queso mozzarella", 16_500),
        ("Avena líquida", 4_700),
    ],
    "Limpieza": [
        ("Detergente 2kg", 18_500),
        ("Jabón líquido", 8_900),
        ("Cloro 1L", 4_300),
        ("Suavizante", 11_200),
        ("Esponjas x3", 5_600),
        ("Papel higiénico x12", 19_800),
        ("Lavaloza", 6_100),
        ("Desinfectante", 9_400),
    ],
    "Electrónica": [
        ("Audífonos", 45_000),
        ("Cargador USB-C", 28_000),
        ("Bombillo LED", 8_500),
        ("Extensión 5m", 22_000),
        ("Mouse", 35_000),
        ("Pila AA x4", 9_800),
        ("Cable HDMI", 24_000),
        ("Parlante bluetooth", 89_000),
    ],
    "Ropa": [
        ("Camiseta básica", 29_000),
        ("Medias x3", 14_500),
        ("Gorra", 22_000),
        ("Pantalón jean", 79_000),
        ("Sudadera", 65_000),
        ("Boxer x3", 27_000),
        ("Toalla baño", 32_000),
        ("Pijama", 48_000),
    ],
}

STORE_MULT = {
    1: 1.35,
    2: 1.20,
    3: 1.05,
    4: 0.95,
    5: 1.15,
    6: 0.80,
    7: 0.90,
    8: 0.85,
}

CAT_BASE_QTY = {
    "Abarrotes": 14,
    "Lácteos": 11,
    "Limpieza": 8,
    "Electrónica": 2.2,
    "Ropa": 3.5,
}

HOLIDAYS = [
    (date(2024, 1, 1), "Año Nuevo"),
    (date(2024, 1, 8), "Reyes Magos"),
    (date(2024, 3, 25), "San José"),
    (date(2024, 3, 28), "Jueves Santo"),
    (date(2024, 3, 29), "Viernes Santo"),
    (date(2024, 5, 1), "Día del Trabajo"),
    (date(2024, 5, 13), "Ascensión"),
    (date(2024, 6, 3), "Corpus Christi"),
    (date(2024, 6, 10), "Sagrado Corazón"),
    (date(2024, 7, 1), "San Pedro y San Pablo"),
    (date(2024, 7, 20), "Independencia"),
    (date(2024, 8, 7), "Batalla de Boyacá"),
    (date(2024, 8, 19), "Asunción"),
    (date(2024, 10, 14), "Día de la Raza"),
    (date(2024, 11, 4), "Todos los Santos"),
    (date(2024, 11, 11), "Independencia de Cartagena"),
    (date(2024, 12, 8), "Inmaculada Concepción"),
    (date(2024, 12, 25), "Navidad"),
    (date(2025, 1, 1), "Año Nuevo"),
    (date(2025, 1, 6), "Reyes Magos"),
    (date(2025, 3, 24), "San José"),
    (date(2025, 4, 17), "Jueves Santo"),
    (date(2025, 4, 18), "Viernes Santo"),
    (date(2025, 5, 1), "Día del Trabajo"),
    (date(2025, 6, 2), "Ascensión"),
    (date(2025, 6, 23), "Corpus Christi"),
    (date(2025, 6, 30), "Sagrado Corazón / San Pedro y San Pablo"),
    (date(2025, 7, 20), "Independencia"),
    (date(2025, 8, 7), "Batalla de Boyacá"),
    (date(2025, 8, 18), "Asunción"),
    (date(2025, 10, 13), "Día de la Raza"),
    (date(2025, 11, 3), "Todos los Santos"),
    (date(2025, 11, 17), "Independencia de Cartagena"),
    (date(2025, 12, 8), "Inmaculada Concepción"),
    (date(2025, 12, 25), "Navidad"),
    (date(2026, 1, 1), "Año Nuevo"),
    (date(2026, 1, 12), "Reyes Magos"),
    (date(2026, 3, 23), "San José"),
    (date(2026, 4, 2), "Jueves Santo"),
    (date(2026, 4, 3), "Viernes Santo"),
    (date(2026, 5, 1), "Día del Trabajo"),
    (date(2026, 5, 18), "Ascensión"),
    (date(2026, 6, 8), "Corpus Christi"),
    (date(2026, 6, 15), "Sagrado Corazón"),
    (date(2026, 6, 29), "San Pedro y San Pablo"),
    (date(2026, 7, 20), "Independencia"),
    (date(2026, 8, 7), "Batalla de Boyacá"),
    (date(2026, 8, 17), "Asunción"),
]


def _products() -> list[tuple[int, str, str, int]]:
    rows = []
    pid = 1
    for category, items in CATEGORIES.items():
        for name, price in items:
            rows.append((pid, name, category, price))
            pid += 1
    return rows


def _month_factor(month: int) -> float:
    seasonal = {
        1: 0.82,
        2: 0.88,
        3: 0.95,
        4: 0.97,
        5: 1.00,
        6: 1.04,
        7: 1.08,
        8: 1.02,
        9: 0.98,
        10: 1.06,
        11: 1.22,
        12: 1.45,
    }
    return seasonal[month]


def generate(end: date | None = None, days: int = 730) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    end = end or date.today()
    start = end - timedelta(days=days - 1)
    dates = pd.date_range(start, end, freq="D")

    products = _products()
    holiday_map = {d: name for d, name in HOLIDAYS}
    holiday_set = set(holiday_map)

    n_stores = len(STORES)
    n_products = len(products)
    n_days = len(dates)

    store_ids = np.array([s[0] for s in STORES])
    store_mult = np.array([STORE_MULT[s[0]] for s in STORES])
    prod_ids = np.array([p[0] for p in products])
    prod_cat = np.array([p[2] for p in products])
    prod_price = np.array([p[3] for p in products], dtype=np.float64)
    cat_qty = np.array([CAT_BASE_QTY[c] for c in prod_cat], dtype=np.float64)

    # Promo calendar: ~18% of store-days, clustered mid-week campaigns
    promo = np.zeros((n_days, n_stores), dtype=bool)
    for d_i, ts in enumerate(dates):
        d = ts.date()
        if d.weekday() in (2, 3, 4) and rng.random() < 0.28:
            promo[d_i] = rng.random(n_stores) < 0.7
        elif rng.random() < 0.08:
            promo[d_i, rng.integers(0, n_stores)] = True

    qty = np.empty((n_days, n_stores, n_products), dtype=np.int16)
    revenue = np.empty((n_days, n_stores, n_products), dtype=np.float64)
    promo_line = np.empty((n_days, n_stores, n_products), dtype=bool)

    for d_i, ts in enumerate(dates):
        d = ts.date()
        elapsed = (d - start).days
        trend = 1.0 + 0.12 * (elapsed / max(days, 1))
        dow = 1.18 if d.weekday() >= 5 else (0.92 if d.weekday() == 0 else 1.0)
        month = _month_factor(d.month)
        hol = 1.35 if d in holiday_set else 1.0
        base = (
            cat_qty[None, :]
            * store_mult[:, None]
            * trend
            * dow
            * month
            * hol
        )
        is_promo = promo[d_i][:, None]
        promo_boost = np.where(is_promo, 1.38, 1.0)
        noise = rng.lognormal(mean=0.0, sigma=0.18, size=base.shape)
        q = np.maximum(np.round(base * promo_boost * noise), 0).astype(np.int16)
        price = prod_price[None, :] * np.where(is_promo, 0.88, 1.0)
        qty[d_i] = q
        revenue[d_i] = np.round(q * price, 2)
        promo_line[d_i] = np.repeat(is_promo, n_products, axis=1)

    # Flatten only positive qty to keep the table smaller
    di, si, pi = np.nonzero(qty)
    sales = pd.DataFrame(
        {
            "date": dates[di].date,
            "store_id": store_ids[si],
            "product_id": prod_ids[pi],
            "qty": qty[di, si, pi],
            "revenue": revenue[di, si, pi],
            "promo": promo_line[di, si, pi],
        }
    )

    stores_df = pd.DataFrame(STORES, columns=["id", "name", "region", "lat", "lon"])
    products_df = pd.DataFrame(
        [(p[0], p[1], p[2]) for p in products],
        columns=["id", "name", "category"],
    )
    holidays_df = pd.DataFrame(
        [(d, n) for d, n in HOLIDAYS if start <= d <= end],
        columns=["date", "name"],
    )
    return {
        "stores": stores_df,
        "products": products_df,
        "holidays": holidays_df,
        "sales": sales,
    }
