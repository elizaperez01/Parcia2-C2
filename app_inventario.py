"""Aplicación gráfica (PyQt5 + Matplotlib) para visualizar el inventario
por sucursal. 
y ejecutamos:  python app_inventario.py"""

import sys

import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as Toolbar
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QComboBox, QFileDialog, QHBoxLayout,
                             QHeaderView, QLabel, QMainWindow, QMessageBox,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QTabWidget, QVBoxLayout, QWidget)

from analisis_pandas import cargar

COLORES = ["#1f4e9c", "#2a9d8f", "#e9a23b", "#d1495b", "#6c5b7b"]


class Grafico(QWidget):
    """Lienzo de Matplotlib con barra de herramientas."""

    def __init__(self):
        super().__init__()
        self.fig = Figure(figsize=(6, 4), tight_layout=True)
        self.canvas = FigureCanvas(self.fig)
        lay = QVBoxLayout(self)
        lay.addWidget(Toolbar(self.canvas, self))
        lay.addWidget(self.canvas)

    def limpiar(self):
        self.fig.clear()
        return self.fig.add_subplot(111)

    def dibujar(self):
        self.canvas.draw_idle()


class Ventana(QMainWindow):
    def __init__(self, ruta="datos.csv"):
        super().__init__()
        self.setWindowTitle("Inventario por sucursal – Consultoría de datos")
        self.resize(1100, 720)
        self.df_total = cargar(ruta)

    
        self.combo_suc = QComboBox()
        self.combo_suc.addItem("Todas")
        self.combo_suc.addItems(sorted(self.df_total["sucursal"].unique()))
        self.combo_cat = QComboBox()
        self.combo_cat.addItem("Todas")
        self.combo_cat.addItems(sorted(self.df_total["categoria"].unique()))
        self.combo_suc.currentIndexChanged.connect(self.actualizar)
        self.combo_cat.currentIndexChanged.connect(self.actualizar)
        btn_csv = QPushButton("Abrir otro CSV…")
        btn_csv.clicked.connect(self.abrir_csv)

        filtros = QHBoxLayout()
        filtros.addWidget(QLabel("Sucursal:"))
        filtros.addWidget(self.combo_suc)
        filtros.addWidget(QLabel("Categoría:"))
        filtros.addWidget(self.combo_cat)
        filtros.addStretch()
        filtros.addWidget(btn_csv)

        #Indicadores
        self.lbl_kpi = QLabel()
        self.lbl_kpi.setAlignment(Qt.AlignCenter)
        self.lbl_kpi.setStyleSheet(
            "background:#eef3fb; border:1px solid #c5d3ea; border-radius:6px;"
            "padding:8px; font-size:14px;")

        #Pestañas de gráfic
        self.g_stock = Grafico()
        self.g_valor_cat = Grafico()
        self.g_margen = Grafico()
        self.g_bajo = Grafico()
        self.g_top = Grafico()
        self.tabla = QTableWidget()
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.g_stock, "Stock por sucursal")
        self.tabs.addTab(self.g_valor_cat, "Valor por categoría")
        self.tabs.addTab(self.g_margen, "Margen por categoría")
        self.tabs.addTab(self.g_bajo, "Alertas de stock")
        self.tabs.addTab(self.g_top, "Top 10 productos")
        self.tabs.addTab(self.tabla, "Tabla de datos")

        centro = QWidget()
        lay = QVBoxLayout(centro)
        lay.addLayout(filtros)
        lay.addWidget(self.lbl_kpi)
        lay.addWidget(self.tabs)
        self.setCentralWidget(centro)
        self.actualizar()

    
    def abrir_csv(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar CSV", "", "CSV (*.csv)")
        if not ruta:
            return
        try:
            nuevo = cargar(ruta)
            requeridas = {"sucursal", "categoria", "producto", "stock",
                          "stock_minimo", "costo_unitario", "precio_venta"}
            if not requeridas.issubset(nuevo.columns):
                raise ValueError("Faltan columnas: " + ", ".join(sorted(requeridas - set(nuevo.columns))))
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Error al cargar", str(e))
            return
        self.df_total = nuevo
        for combo, col in ((self.combo_suc, "sucursal"), (self.combo_cat, "categoria")):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Todas")
            combo.addItems(sorted(nuevo[col].unique()))
            combo.blockSignals(False)
        self.actualizar()

    def filtrado(self):
        df = self.df_total
        if self.combo_suc.currentText() != "Todas":
            df = df[df["sucursal"] == self.combo_suc.currentText()]
        if self.combo_cat.currentText() != "Todas":
            df = df[df["categoria"] == self.combo_cat.currentText()]
        return df

    def actualizar(self):
        df = self.filtrado()
        if df.empty:
            self.lbl_kpi.setText("Sin datos para el filtro seleccionado")
            return
        self.lbl_kpi.setText(
            f"<b>Productos:</b> {len(df)} &nbsp;|&nbsp; "
            f"<b>Unidades en stock:</b> {df['stock'].sum():,} &nbsp;|&nbsp; "
            f"<b>Valor del inventario:</b> ${df['valor_inventario'].sum():,.2f} &nbsp;|&nbsp; "
            f"<b>Margen promedio:</b> {df['margen_pct'].mean():.1f}% &nbsp;|&nbsp; "
            f"<b>Bajo mínimo:</b> {int(df['bajo_minimo'].sum())}")
        self.graf_stock(df)
        self.graf_valor_cat(df)
        self.graf_margen(df)
        self.graf_bajo(df)
        self.graf_top(df)
        self.llenar_tabla(df)

    #Gráficos
    def graf_stock(self, df):
        ax = self.g_stock.limpiar()
        s = df.groupby("sucursal")["stock"].sum().sort_values(ascending=False)
        barras = ax.bar(s.index, s.values, color=COLORES[0])
        ax.bar_label(barras, fmt="%d", padding=2)
        ax.set_title("Unidades en stock por sucursal")
        ax.set_ylabel("Unidades")
        ax.tick_params(axis="x", rotation=15)
        self.g_stock.dibujar()

    def graf_valor_cat(self, df):
        ax = self.g_valor_cat.limpiar()
        v = df.groupby("categoria")["valor_inventario"].sum().sort_values(ascending=False)
        v = v[v > 0]
        ax.pie(v.values, labels=v.index, autopct="%1.1f%%", startangle=90,
               colors=COLORES[:len(v)], wedgeprops={"edgecolor": "white"})
        ax.set_title("Participación en el valor del inventario")
        self.g_valor_cat.dibujar()

    def graf_margen(self, df):
        ax = self.g_margen.limpiar()
        m = df.groupby("categoria")["margen_pct"].mean().sort_values()
        barras = ax.barh(m.index, m.values, color=COLORES[1])
        ax.bar_label(barras, fmt="%.1f%%", padding=3)
        ax.set_title("Margen de ganancia promedio por categoría")
        ax.set_xlabel("Margen (%)")
        self.g_margen.dibujar()

    def graf_bajo(self, df):
        ax = self.g_bajo.limpiar()
        b = df.groupby("sucursal")["bajo_minimo"].sum().sort_values(ascending=False)
        barras = ax.bar(b.index, b.values, color=COLORES[3])
        ax.bar_label(barras, fmt="%d", padding=2)
        ax.set_title("Productos por debajo del stock mínimo")
        ax.set_ylabel("N.º de productos")
        ax.tick_params(axis="x", rotation=15)
        self.g_bajo.dibujar()

    def graf_top(self, df):
        ax = self.g_top.limpiar()
        t = df.nlargest(10, "valor_inventario")
        etiquetas = t["producto"] + " (" + t["sucursal"] + ")"
        ax.barh(etiquetas[::-1], t["valor_inventario"][::-1], color=COLORES[2])
        ax.set_title("10 productos con mayor valor en inventario")
        ax.set_xlabel("Valor (USD)")
        ax.tick_params(axis="y", labelsize=8)
        self.g_top.dibujar()

    def llenar_tabla(self, df):
        cols = ["id_producto", "producto", "categoria", "sucursal", "proveedor",
                "stock", "stock_minimo", "costo_unitario", "precio_venta"]
        self.tabla.setRowCount(len(df))
        self.tabla.setColumnCount(len(cols))
        self.tabla.setHorizontalHeaderLabels(cols)
        for i, (_, fila) in enumerate(df[cols].iterrows()):
            for j, c in enumerate(cols):
                val = fila[c]
                self.tabla.setItem(i, j, QTableWidgetItem("" if pd.isna(val) else str(val)))
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


def main():
    app = QApplication(sys.argv)
    ventana = Ventana()
    ventana.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
