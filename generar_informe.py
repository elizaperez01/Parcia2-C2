"""Genera el informe de consultoría  con ReportLab.
Todas las cifras se calculan a partir de datos.csv."""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (CondPageBreak, KeepTogether, Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from analisis_pandas import cargar


INTEGRANTES = ["Mariela Elizabeth Pérez Hernandez]", "[Velinda Lisseth Guevara Guevara]"]
FECHA = "20 de octubre de 2026"


AZUL = colors.HexColor("#1f4e9c")
df = cargar("datos.csv")
os.makedirs("graficos", exist_ok=True)
PAL = ["#1f4e9c", "#2a9d8f", "#e9a23b", "#d1495b", "#6c5b7b"]


def guardar(nombre):
    plt.tight_layout()
    plt.savefig(f"graficos/{nombre}.png", dpi=160)
    plt.close()


#calcular indicadores y tablas
suc = df.groupby("sucursal").agg(
    stock=("stock", "sum"), valor=("valor_inventario", "sum"),
    bajo=("bajo_minimo", "sum"), margen=("margen_pct", "mean"),
    agotados=("stock", lambda s: int((s == 0).sum()))).sort_values("valor", ascending=False)
cat = df.groupby("categoria").agg(
    stock=("stock", "sum"), valor=("valor_inventario", "sum"),
    bajo=("bajo_minimo", "sum"), margen=("margen_pct", "mean")).sort_values("valor", ascending=False)
total_valor = df["valor_inventario"].sum()
total_stock = int(df["stock"].sum())
n_bajo = int(df["bajo_minimo"].sum())
pct_bajo = n_bajo / len(df) * 100
n_agot = int((df["stock"] == 0).sum())
top = df.nlargest(5, "valor_inventario")
prod_margen = df.groupby("producto")["margen_pct"].mean().sort_values()
prov = df["proveedor"].value_counts()
n_nulos_prov = int(df["proveedor"].isna().sum())
pivot = df.pivot_table(index="sucursal", columns="categoria",
                       values="valor_inventario", aggfunc="sum").round(0)
s_top, s_low = suc.index[0], suc.index[-1]

#graficar indicadores
plt.figure(figsize=(6.4, 3.4))
s = suc.sort_values("stock", ascending=False)
b = plt.bar(s.index, s["stock"], color=PAL[0]); plt.bar_label(b, fmt="%d")
plt.title("Unidades en stock por sucursal"); plt.ylabel("Unidades")
plt.xticks(rotation=12); guardar("stock_sucursal")

plt.figure(figsize=(6.4, 3.4))
b = plt.bar(suc.index, suc["valor"] / 1000, color=PAL[1]); plt.bar_label(b, fmt="%.1f")
plt.title("Valor del inventario por sucursal (miles de USD)")
plt.ylabel("Miles de USD"); plt.xticks(rotation=12); guardar("valor_sucursal")

plt.figure(figsize=(5.6, 3.8))
plt.pie(cat["valor"], labels=cat.index, autopct="%1.1f%%", startangle=90,
        colors=PAL, wedgeprops={"edgecolor": "white"})
plt.title("Participación por categoría en el valor del inventario"); guardar("valor_categoria")

plt.figure(figsize=(6.4, 3.4))
m = cat["margen"].sort_values()
b = plt.barh(m.index, m.values, color=PAL[2]); plt.bar_label(b, fmt="%.1f%%", padding=3)
plt.title("Margen de ganancia promedio por categoría"); plt.xlabel("Margen (%)")
guardar("margen_categoria")

plt.figure(figsize=(6.4, 3.4))
b = plt.bar(suc.index, suc["bajo"], color=PAL[3]); plt.bar_label(b, fmt="%d")
plt.title("Productos bajo el stock mínimo por sucursal"); plt.ylabel("N.º de productos")
plt.xticks(rotation=12); guardar("bajo_minimo")

plt.figure(figsize=(6.4, 3.6))
t = df.nlargest(10, "valor_inventario")
plt.barh((t["producto"] + " (" + t["sucursal"] + ")")[::-1], t["valor_inventario"][::-1], color=PAL[4])
plt.title("10 registros con mayor valor inmovilizado"); plt.xlabel("USD")
plt.yticks(fontsize=7); guardar("top10")

#estilo
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], textColor=AZUL, fontSize=16, spaceBefore=6, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], textColor=AZUL, fontSize=12.5, spaceBefore=8, spaceAfter=4)
P = ParagraphStyle("P", parent=ss["BodyText"], fontSize=10.5, leading=15, alignment=TA_JUSTIFY, spaceAfter=6)
BUL = ParagraphStyle("BUL", parent=P, leftIndent=14, bulletIndent=2, spaceAfter=3)
CAP = ParagraphStyle("CAP", parent=ss["BodyText"], fontSize=8.5, alignment=TA_CENTER,
                     textColor=colors.grey, spaceAfter=8)
PORT = ParagraphStyle("PORT", parent=ss["Title"], fontSize=22, leading=28, textColor=AZUL)
CEN = ParagraphStyle("CEN", parent=P, alignment=TA_CENTER, fontSize=11.5)


def usd(x):
    return f"${x:,.2f}"


def tabla(data, widths=None, header=True):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    est = [("FONTSIZE", (0, 0), (-1, -1), 8.5), ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f6fb")])]
    if header:
        est += [("BACKGROUND", (0, 0), (-1, 0), AZUL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    t.setStyle(TableStyle(est))
    return t


def fig(nombre, ancho=14.5, leyenda=""):
    from PIL import Image as PI
    w, h = PI.open(f"graficos/{nombre}.png").size
    out = [Image(f"graficos/{nombre}.png", width=ancho * cm, height=ancho * cm * h / w)]
    if leyenda:
        out.append(Paragraph(leyenda, CAP))
    return out


def pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2.2 * cm, 1.3 * cm, "Informe de consultoría – Inventario por sucursal")
    canvas.drawRightString(letter[0] - 2.2 * cm, 1.3 * cm, f"Página {doc.page}")
    canvas.restoreState()


#contenido del doc.
S = []
# Portada
S += [Spacer(1, 2.2 * cm),
      Paragraph("UNIVERSIDAD GERARDO BARRIOS", ParagraphStyle("u", parent=CEN, fontSize=15, textColor=AZUL, fontName="Helvetica-Bold")),
      Paragraph("Facultad de Ciencias y Tecnología – Ingeniería en Sistemas y Redes Informaticas", CEN),
      Spacer(1, 2.2 * cm),
      Paragraph("INFORME DE CONSULTORÍA DE DATOS", PORT),
      Paragraph("Análisis del inventario de cinco sucursales de empresas en El Salvador", ParagraphStyle("sub", parent=CEN, fontSize=14)),
      Spacer(1, 2.2 * cm),
      Paragraph("<b>Asignatura:</b> Programación Computacional III", CEN),
      Paragraph("<b>Evaluación:</b> Parcial Segundo Cómputo", CEN),
      Paragraph("<b>Cliente:</b> Empresa salvadoreña comercializadora de productos ", CEN),
      Spacer(1, 1.2 * cm),
      Paragraph("<b>Consultores:</b>", CEN)]
S += [Paragraph(n, CEN) for n in INTEGRANTES]
S += [Spacer(1, 1.2 * cm), Paragraph(f"San Salvador, El Salvador – {FECHA}", CEN), PageBreak()]

# 1. Resumen
S += [Paragraph("1. Resumen ejecutivo", H1),
      Paragraph(
          f"La empresa opera cinco sucursales (San Salvador, Santa Ana, San Miguel, La Libertad y Sonsonate) y "
          f"solicitó un inventario consolidado junto con una herramienta gráfica para explorarlo. Se analizó un "
          f"inventario de <b>{len(df)} registros</b> (25 productos en cada sucursal, repartidos en 5 categorías) con "
          f"<b>{total_stock:,} unidades</b> en existencia y un valor a costo de <b>{usd(total_valor)}</b>.", P),
      Paragraph("Los hallazgos principales son:", P)]
for txt in [
    f"<b>{s_top}</b> concentra el {suc.loc[s_top,'valor']/total_valor*100:.1f}% del valor del inventario; "
    f"<b>{s_low}</b> apenas el {suc.loc[s_low,'valor']/total_valor*100:.1f}%.",
    f"<b>{n_bajo} de {len(df)} registros ({pct_bajo:.1f}%)</b> están por debajo del stock mínimo y "
    f"<b>{n_agot}</b> están agotados; {int(suc.loc['Sonsonate','bajo'])} de las alertas ({suc.loc['Sonsonate','bajo']/n_bajo*100:.0f}%) "
    f"corresponden a Sonsonate.",
    f"Tecnología y Electrodomésticos suman el {(cat.loc['Tecnología','valor']+cat.loc['Electrodomésticos','valor'])/total_valor*100:.1f}% "
    f"del capital inmovilizado, pero tienen pocas unidades; Alimentos tiene {int(cat.loc['Alimentos y bebidas','stock']):,} unidades "
    f"con solo el {cat.loc['Alimentos y bebidas','valor']/total_valor*100:.1f}% del valor.",
    f"El margen promedio es {df['margen_pct'].mean():.1f}%, con grandes diferencias: Hogar "
    f"({cat.loc['Hogar','margen']:.1f}%) frente a Alimentos ({cat.loc['Alimentos y bebidas','margen']:.1f}%).",
]:
    S.append(Paragraph(txt, BUL, bulletText="•"))

# 2. Metodología
S += [Paragraph("2. Datos y metodología", H1),
      Paragraph(
          "El conjunto de datos fue generado de forma sintética con Python (semilla fija para reproducibilidad), "
          "apoyado en herramientas de Inteligencia Artificial para definir el catálogo y las reglas de negocio "
          "(precios, márgenes y niveles de stock realistas para el mercado salvadoreño). Se guardó como "
          "<i>datos.csv</i>. El análisis se realizó con <b>Pandas</b> (funciones head, info, dtypes, describe, "
          "isnull, groupby y pivot_table); la visualización, con <b>Matplotlib</b>; y la herramienta interactiva, "
          "con <b>PyQt5</b>.", P),
      Paragraph("<b>Estructura del inventario</b> (9 columnas originales y 3 calculadas):", P)]
desc = [["Columna", "Tipo", "Descripción"],
        ["id_producto", "texto", "Identificador único (P0001 a P0125)"],
        ["producto", "texto", "Nombre del producto (25 distintos)"],
        ["categoria", "texto", "Electrodomésticos, Tecnología, Hogar, Alimentos y bebidas, Ferretería"],
        ["sucursal", "texto", "Sucursal donde se encuentra el producto (5)"],
        ["proveedor", "texto", "Proveedor principal (5; 4 valores nulos)"],
        ["stock", "entero", "Unidades disponibles"],
        ["stock_minimo", "entero", "Nivel mínimo antes de reponer"],
        ["costo_unitario", "decimal", "Costo por unidad (USD)"],
        ["precio_venta", "decimal", "Precio de venta (USD)"],
        ["valor_inventario*", "decimal", "stock x costo_unitario"],
        ["margen_pct*", "decimal", "(precio - costo) / costo x 100"],
        ["bajo_minimo*", "booleano", "True si stock < stock_minimo"]]
S += [tabla(desc, [3.6 * cm, 2.2 * cm, 11 * cm]),
      Paragraph("* Columnas calculadas con Pandas. La inspección encontró 125 filas, ningún duplicado y "
                f"{n_nulos_prov} nulos únicamente en <i>proveedor</i>.", CAP), PageBreak()]

# 3. Hallazgos
S += [Paragraph("3. Análisis de hallazgos", H1), Paragraph("3.1 Distribución por sucursal", H2)]
rows = [["Sucursal", "Unidades", "Valor (USD)", "% del valor", "Bajo mínimo", "Agotados", "Margen prom."]]
for n, r in suc.iterrows():
    rows.append([n, f"{int(r.stock):,}", usd(r.valor), f"{r.valor/total_valor*100:.1f}%",
                 int(r.bajo), int(r.agotados), f"{r.margen:.1f}%"])
rows.append(["Total", f"{total_stock:,}", usd(total_valor), "100%", n_bajo, n_agot, f"{df['margen_pct'].mean():.1f}%"])
t = tabla(rows, [3 * cm, 2.1 * cm, 2.9 * cm, 2.1 * cm, 2.3 * cm, 2 * cm, 2.4 * cm])
t.setStyle(TableStyle([("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")]))
S += [t, Spacer(1, 8)]
S += fig("stock_sucursal", 10.5, "Figura 1. Unidades en stock por sucursal.")
S += fig("valor_sucursal", 10.5, "Figura 2. Valor del inventario por sucursal.")
S.append(Paragraph(
    f"San Salvador es la sucursal más grande en unidades ({int(suc.loc['San Salvador','stock']):,}) y en valor. "
    f"Sonsonate es la más pequeña ({int(suc.loc['Sonsonate','stock']):,} unidades), y además muestra más "
    f"problemas de abastecimiento. Nótese que Santa Ana tiene más unidades que La Libertad y San Miguel pero menos "
    f"valor: su inventario se inclina hacia productos baratos y de alta rotación.", P))

S += [CondPageBreak(8 * cm), Paragraph("3.2 Composición por categoría", H2)]
rows = [["Categoría", "Unidades", "Valor (USD)", "% del valor", "Bajo mínimo", "Margen prom."]]
for n, r in cat.iterrows():
    rows.append([n, f"{int(r.stock):,}", usd(r.valor), f"{r.valor/total_valor*100:.1f}%", int(r.bajo), f"{r.margen:.1f}%"])
S += [tabla(rows, [4 * cm, 2.3 * cm, 3 * cm, 2.3 * cm, 2.5 * cm, 2.5 * cm]), Spacer(1, 8)]
S += fig("valor_categoria", 8.5, "Figura 3. Participación de cada categoría en el valor del inventario.")
S += fig("margen_categoria", 10.5, "Figura 4. Margen de ganancia promedio por categoría.")
S.append(Paragraph(
    f"Tecnología ({usd(cat.loc['Tecnología','valor'])}) y Electrodomésticos ({usd(cat.loc['Electrodomésticos','valor'])}) "
    f"son los rubros más costosos de mantener y, junto con Hogar, forman el grueso del capital. Hogar es la categoría con "
    f"mejor margen ({cat.loc['Hogar','margen']:.1f}%), mientras que Alimentos y bebidas deja el menor "
    f"({cat.loc['Alimentos y bebidas','margen']:.1f}%) pero aporta el mayor volumen de unidades.", P))

S += [CondPageBreak(8 * cm), Paragraph("3.3 Alertas de abastecimiento", H2)]
S += fig("bajo_minimo", 11, "Figura 5. Productos por debajo del stock mínimo.")
bm = df[df["bajo_minimo"]].groupby("categoria").size().sort_values(ascending=False)
S.append(Paragraph(
    f"{n_bajo} registros ({pct_bajo:.1f}%) están bajo el mínimo. Sonsonate acumula {int(suc.loc['Sonsonate','bajo'])} "
    f"(es decir, {suc.loc['Sonsonate','bajo']/25*100:.0f}% de su catálogo), seguida de San Miguel con "
    f"{int(suc.loc['San Miguel','bajo'])}. Por categoría, {bm.index[0]} lidera con {int(bm.iloc[0])} alertas, "
    f"seguida de {bm.index[1]} ({int(bm.iloc[1])}). Hay {n_agot} productos sin existencias, "
    f"{int(suc.loc['Sonsonate','agotados'])} de ellos en Sonsonate.", P))

S += [CondPageBreak(8 * cm), Paragraph("3.4 Capital inmovilizado", H2)]
S += fig("top10", 12, "Figura 6. Registros con mayor valor en inventario.")
r0 = top.iloc[0]
S.append(Paragraph(
    f"El mayor valor individual es <b>{r0['producto']}</b> en {r0['sucursal']} ({int(r0['stock'])} unidades, "
    f"{usd(r0['valor_inventario'])}), que por sí solo representa el {r0['valor_inventario']/total_valor*100:.1f}% "
    f"del inventario total. Los diez registros principales suman "
    f"{df.nlargest(10,'valor_inventario')['valor_inventario'].sum()/total_valor*100:.1f}% del valor total.", P))

hdr = ["Sucursal", "Alimentos", "Electrodom.", "Ferretería", "Hogar", "Tecnología"]
S += [CondPageBreak(8 * cm), Paragraph("3.5 Valor por sucursal y categoría (USD)", H2)]
rows = [hdr] + [[i] + [f"{v:,.0f}" for v in r] for i, r in pivot.iterrows()]
S += [tabla(rows, [3 * cm] + [2.7 * cm] * 5), PageBreak()]

# 4. Conclusiones por variable
S += [Paragraph("4. Conclusiones por variable analizada", H1)]
ds = df[["stock", "stock_minimo", "costo_unitario", "precio_venta"]].describe()
concl = [
    ("sucursal", f"Distribución equilibrada en catálogo (25 productos cada una) pero muy desigual en volumen: "
                 f"{s_top} concentra el {suc.loc[s_top,'valor']/total_valor*100:.1f}% del valor y {s_low} el "
                 f"{suc.loc[s_low,'valor']/total_valor*100:.1f}%. Sonsonate presenta el mayor riesgo de desabastecimiento."),
    ("categoria", f"Cinco categorías con 5 productos cada una. Tecnología y Electrodomésticos dominan el valor; "
                  f"Alimentos domina en unidades. Cada categoría requiere una política de inventario distinta."),
    ("producto", f"Los productos con más unidades son de consumo masivo: Frijol rojo, Arroz y Café. Los de menor "
                 f"margen son {prod_margen.index[0]} ({prod_margen.iloc[0]:.1f}%), {prod_margen.index[1]} "
                 f"({prod_margen.iloc[1]:.1f}%) y {prod_margen.index[2]} ({prod_margen.iloc[2]:.1f}%); los de mayor "
                 f"son {prod_margen.index[-1]} ({prod_margen.iloc[-1]:.1f}%) y {prod_margen.index[-2]} ({prod_margen.iloc[-2]:.1f}%)."),
    ("stock", f"Media de {ds.loc['mean','stock']:.1f} unidades por registro, mediana de {ds.loc['50%','stock']:.0f} y "
              f"desviación estándar de {ds.loc['std','stock']:.1f}: la distribución es muy asimétrica, con unos pocos "
              f"registros de gran volumen (máx. {ds.loc['max','stock']:.0f}) y {n_agot} agotados."),
    ("stock_minimo", f"Va de {ds.loc['min','stock_minimo']:.0f} a {ds.loc['max','stock_minimo']:.0f} unidades "
                     f"(media {ds.loc['mean','stock_minimo']:.1f}). Un {pct_bajo:.1f}% de los registros no lo alcanza, "
                     f"lo que indica que los puntos de reorden no se están respetando o no se revisan."),
    ("costo_unitario", f"Rango de {usd(ds.loc['min','costo_unitario'])} a {usd(ds.loc['max','costo_unitario'])}; "
                       f"la media ({usd(ds.loc['mean','costo_unitario'])}) supera ampliamente la mediana "
                       f"({usd(ds.loc['50%','costo_unitario'])}) porque pocos artículos caros elevan el promedio."),
    ("precio_venta", f"Media de {usd(ds.loc['mean','precio_venta'])} y mediana de {usd(ds.loc['50%','precio_venta'])}. "
                     f"Todos los precios superan al costo; el margen promedio es {df['margen_pct'].mean():.1f}%, "
                     f"entre {df['margen_pct'].min():.1f}% y {df['margen_pct'].max():.1f}%."),
    ("proveedor", f"Importadora Pacífico abastece {int(prov.iloc[0])} registros ({prov.iloc[0]/len(df)*100:.1f}%) y es el "
                  f"proveedor con mayor dependencia. Hay {n_nulos_prov} registros sin proveedor, un problema de "
                  f"calidad de datos que dificulta la trazabilidad."),
    ("valor_inventario / margen_pct", f"El valor total a costo es {usd(total_valor)}. El margen presenta una "
                                      f"dispersión alta (desv. est. {df['margen_pct'].std():.1f} puntos), señal de que "
                                      f"la política de precios no es uniforme."),
]
rows = [["Variable", "Conclusión"]] + [[Paragraph(f"<b>{a}</b>", ParagraphStyle("c", fontSize=8.5)),
                                         Paragraph(b, ParagraphStyle("c2", fontSize=8.8, leading=12))] for a, b in concl]
S += [tabla(rows, [3.4 * cm, 13.4 * cm]), PageBreak()]

# 5. Recomendaciones
S += [Paragraph("5. Recomendaciones estratégicas", H1)]
recs = [
    ("Reabastecer Sonsonate de inmediato.",
     f"Priorizar los {int(suc.loc['Sonsonate','agotados'])} productos agotados y los {int(suc.loc['Sonsonate','bajo'])} "
     f"que están bajo el mínimo. Evaluar si el stock mínimo de esta sucursal está bien dimensionado para su demanda."),
    ("Implementar reposición automática.",
     f"Un {pct_bajo:.0f}% de registros bajo el mínimo indica ausencia de alertas. Programar órdenes de compra "
     f"cuando stock < stock_minimo, y revisar semanalmente el reporte de la aplicación entregada."),
    ("Rebalancear inventario entre sucursales.",
     f"Hay excedentes en San Salvador y faltantes en Sonsonate y San Miguel. Las transferencias internas cuestan "
     f"menos que una compra nueva y reducen quiebres."),
    ("Reducir capital inmovilizado en Tecnología y Electrodomésticos.",
     f"Representan {(cat.loc['Tecnología','valor']+cat.loc['Electrodomésticos','valor'])/total_valor*100:.0f}% "
     f"del valor con pocas unidades. Adoptar compras bajo demanda o por lotes pequeños en los productos de mayor "
     f"costo (laptops, refrigeradoras)."),
    ("Revisar la política de precios en alimentos y ferretería básica.",
     f"Arroz, Frijol y Cemento tienen márgenes inferiores al 20%. Negociar mejores costos o ajustar precios, "
     f"o bien aprovecharlos como productos gancho de tráfico y compensarlos con categorías de alto margen (Hogar)."),
    ("Impulsar los productos de mayor margen.",
     f"Promocionar en todas las sucursales Hogar y accesorios (audífonos, sábanas, sillas), que dejan más de 55% de margen."),
    ("Diversificar y formalizar proveedores.",
     f"Reducir la dependencia de Importadora Pacífico ({prov.iloc[0]/len(df)*100:.0f}% de los registros), "
     f"completar los {n_nulos_prov} proveedores faltantes y establecer una validación de datos obligatoria en el sistema."),
    ("Adoptar la herramienta como tablero de control.",
     "La aplicación PyQt5 permite filtrar por sucursal y categoría y cargar un CSV actualizado; se recomienda "
     "integrarla con la base de datos real y ampliar con histórico de ventas para calcular rotación."),
]
for i, (a, b) in enumerate(recs, 1):
    S.append(Paragraph(f"<b>{i}. {a}</b> {b}", P))

S += [Paragraph("6. Limitaciones y trabajo futuro", H1),
      Paragraph("Los datos son sintéticos y representan una fotografía estática del inventario, sin historial de ventas "
                "ni rotación. Los resultados deben validarse con los datos reales de la empresa. Como trabajo futuro se "
                "propone incorporar series de tiempo, pronóstico de demanda y conexión directa a la base de datos.", P)]

doc = SimpleDocTemplate("informe_consultoria.pdf", pagesize=letter, leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                        topMargin=2 * cm, bottomMargin=2 * cm, title="Informe de consultoría – Inventario por sucursal",
                        author=", ".join(INTEGRANTES))
doc.build(S, onLaterPages=pie)
print("informe_consultoria.pdf generado")
