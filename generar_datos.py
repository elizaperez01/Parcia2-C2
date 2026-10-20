"""Genera el inventario sintético (datos.csv) de una empresa salvadoreña
con cinco sucursales"""

import numpy as np
import pandas as pd

rng = np.random.default_rng(2026)

SUCURSALES = ["San Salvador", "Santa Ana", "San Miguel", "La Libertad", "Sonsonate"]
PESO_SUC = [0.30, 0.18, 0.18, 0.20, 0.14]

# categoria -> {producto: (costo_base, margen)}
CATALOGO = {
    "Electrodomésticos": {
        "Licuadora": (22, 0.45), "Refrigeradora": (380, 0.30),
        "Cocina de gas": (210, 0.32), "Plancha": (14, 0.50),
        "Microondas": (75, 0.38),
    },
    "Tecnología": {
        "Laptop": (420, 0.22), "Teléfono celular": (190, 0.25),
        "Audífonos": (12, 0.65), "Televisor 43\"": (260, 0.28),
        "Tablet": (130, 0.27),
    },
    "Hogar": {
        "Juego de sábanas": (18, 0.60), "Colchón matrimonial": (160, 0.40),
        "Silla plástica": (6, 0.55), "Mesa de comedor": (140, 0.42),
        "Ventilador": (25, 0.48),
    },
    "Alimentos y bebidas": {
        "Arroz 25 lb": (13, 0.18), "Frijol rojo 25 lb": (22, 0.20),
        "Aceite 1 L": (2.2, 0.25), "Café 1 lb": (3.0, 0.35),
        "Gaseosa 2 L": (0.9, 0.30),
    },
    "Ferretería": {
        "Taladro": (45, 0.40), "Cemento 42 kg": (8.5, 0.15),
        "Pintura galón": (17, 0.38), "Set de herramientas": (28, 0.50),
        "Lámina galvanizada": (9, 0.22),
    },
}
PROVEEDORES = ["Distribuidora Cuscatlán", "Importadora Pacífico", "Comercial Izalco",
               "Grupo Lempa", "Suministros Maya"]

filas = []
n = 0
for suc, peso in zip(SUCURSALES, PESO_SUC):
    for cat, prods in CATALOGO.items():
        for prod, (costo, margen) in prods.items():
            n += 1
            # Tamaño de stock
            esc = peso / 0.2
            base = {"Alimentos y bebidas": 180, "Ferretería": 90, "Hogar": 60,
                    "Electrodomésticos": 35, "Tecnología": 28}[cat]
            stock = int(max(0, rng.normal(base * esc, base * 0.45)))
            
            if rng.random() < 0.12:
                stock = int(rng.integers(0, 6))
            minimo = int(max(5, base * 0.25))
            costo_u = round(costo * rng.uniform(0.93, 1.08), 2)
            precio = round(costo_u * (1 + margen * rng.uniform(0.85, 1.15)), 2)
            filas.append({
                "id_producto": f"P{n:04d}",
                "producto": prod,
                "categoria": cat,
                "sucursal": suc,
                "proveedor": PROVEEDORES[int(rng.integers(0, len(PROVEEDORES)))],
                "stock": stock,
                "stock_minimo": minimo,
                "costo_unitario": costo_u,
                "precio_venta": precio,
            })

df = pd.DataFrame(filas)
# Algunos datos faltantes realistas en proveedor (para demostrar la inspección)
idx = rng.choice(df.index, size=4, replace=False)
df.loc[idx, "proveedor"] = np.nan

df.to_csv("datos.csv", index=False, encoding="utf-8")
print(f"datos.csv generado: {df.shape[0]} filas x {df.shape[1]} columnas")
