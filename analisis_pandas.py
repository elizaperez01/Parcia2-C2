"""Inspección del inventario con Pandas: estructura, tipos y estadísticas."""
import pandas as pd


def cargar(ruta="datos.csv"):
    df = pd.read_csv(ruta)
    df["valor_inventario"] = df["stock"] * df["costo_unitario"]
    df["margen_pct"] = (df["precio_venta"] - df["costo_unitario"]) / df["costo_unitario"] * 100
    df["bajo_minimo"] = df["stock"] < df["stock_minimo"]
    return df


def inspeccion(df):
    print("=== head() ===")
    print(df.head())
    print("\n=== shape ===", df.shape)
    print("\n=== info() ===")
    df.info()
    print("\n=== dtypes ===")
    print(df.dtypes)
    print("\n=== describe() numérico ===")
    print(df.describe().round(2))
    print("\n=== describe() categórico ===")
    print(df.describe(exclude=["number", "bool"]))
    print("\n=== Nulos por columna ===")
    print(df.isnull().sum())
    print("\n=== Duplicados ===", df.duplicated().sum())
    print("\n=== Productos por sucursal ===")
    print(df["sucursal"].value_counts())
    print("\n=== Stock total y valor por sucursal ===")
    print(df.groupby("sucursal")[["stock", "valor_inventario"]].sum().round(2))
    print("\n=== Valor por categoría ===")
    print(df.groupby("categoria")["valor_inventario"].sum().round(2).sort_values(ascending=False))
    print("\n=== Margen promedio por categoría (%) ===")
    print(df.groupby("categoria")["margen_pct"].mean().round(2))
    print("\n=== Productos bajo el stock mínimo por sucursal ===")
    print(df.groupby("sucursal")["bajo_minimo"].sum())


if __name__ == "__main__":
    inspeccion(cargar())
