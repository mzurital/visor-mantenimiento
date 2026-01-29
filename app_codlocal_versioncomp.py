import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
import plotly.graph_objects as go

st.title("Detalle por Código Local")
st.markdown("""
<style>
/* Fondo blanco + texto negro */
.stApp { background: #ffffff !important; color: #111111 !important; }
html, body, [class*="css"]  { color: #111111 !important; }

.block-container {
    max-width: 1400px;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* Compactar padding */
.block-container { padding-top: 0.8rem; padding-bottom: 0.8rem; }

/* Quitar espacios excesivos entre bloques */
div[data-testid="stVerticalBlock"] > div { gap: 0.5rem; }

/* Títulos más compactos */
h1 { font-size: 1.4rem !important; margin-bottom: 0.2rem !important; }
h2, h3 { margin-bottom: 0.15rem !important; }

/* Texto pequeño para tarjetas */
.monto-label { font-size: 1.05rem; color:#444; margin-bottom: 0.15rem; }
.monto-value { font-size: 1.45rem; font-weight: 800; color:#111; line-height: 1.1; margin-bottom: 0.55rem; }
.montos-wrap { margin-top: -0.8rem; }   /* sube el bloque hacia el título */

/* Datos del local educativo */
.small-label {
    font-size: 0.75rem;
    color: #555;
    margin-bottom: 0.1rem;
}

.small-value {
    font-size: 0.95rem;
    font-weight: 800;
    color: #111;
}

/* Estado con colores */
.badge { display:inline-block; padding: 2px 8px; border-radius: 10px; font-weight: 700; font-size: 0.85rem; }
.badge-red { background:#ffe5e5; color:#b10000; }
.badge-green { background:#e7f8ed; color:#116b2a; }
.badge-yellow { background:#fff4cc; color:#7a5a00; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.card{
  border: 1px solid #e6e6e6;
  border-radius: 12px;
  padding: 14px 16px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  margin-top: 6px;
}
.card h3{ margin-top: 0; }
.tight p { margin: 0.15rem 0; }
</style>
""", unsafe_allow_html=True)


# ===============================
# DATA
# ===============================
URL_CODLOCAL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTI2_JlaCmYeeyQ3XCSRwS-wSgJYnG6F7-CVsLh3ygHMTDjc_yegxnPDic0IRoE7xytylT1TMCGIfgj/pub?gid=1857612585&single=true&output=csv"

@st.cache_data(ttl=3600)
def load_data():
    df = pd.read_csv(URL_CODLOCAL, dtype=str)   # <-- todo como texto (más seguro)
    df.columns = df.columns.str.strip()

    if "CODLOCAL" in df.columns:
        df["CODLOCAL"] = (
            df["CODLOCAL"]
            .astype(str)
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
            .str.zfill(6)
        )

    return df

df = load_data()

# ===============================
# HELPERS
# ===============================
HOY = pd.to_datetime(date.today())

def semaforo(dias):
    if pd.isna(dias):
        return "⚪ No aplica"
    if dias <= 7:
        return "🔴"
    elif dias <= 21:
        return "🟡"
    else:
        return "🟢"

def dias_restantes(fecha_plazo):
    return (fecha_plazo - HOY).days

def to_number(x):
    """Convierte valores tipo 'S/ 1,234.56', '1,234', '1234' a float. Devuelve NaN si no se puede."""
    if pd.isna(x):
        return np.nan
    s = str(x).strip()
    if s == "" or s.upper() in ["NA", "N/A", "NONE", "NULL"]:
        return np.nan

    # Quita símbolos y espacios
    s = s.replace("S/", "").replace("s/", "").replace(" ", "")

    # Quita separador de miles (coma) y convierte
    # Si tu data usa coma decimal (1.234,56), avísame y lo adapto.
    s = s.replace(",", "")
    try:
        return float(s)
    except:
        return np.nan

def formato_soles(x):
    v = to_number(x)
    if pd.isna(v):
        return "No aplica"
    return f"S/ {v:,.0f}"


def estado_badge(valor):
    if pd.isna(valor) or str(valor).strip() == "":
        return '<span class="badge badge-yellow">SIN DATO</span>'

    v = str(valor).upper().strip()

    if "SIN REGISTRAR" in v:
        return '<span class="badge badge-red">SIN REGISTRAR</span>'

    if "VERIFIC" in v:  # VERIFICADA / VERIFICADO
        return '<span class="badge badge-green">VERIFICADA</span>'

    # otros estados
    return f'<span class="badge badge-yellow">{str(valor).strip()}</span>'


def is_verificada(x):
    if pd.isna(x): 
        return False
    return "VERIFIC" in str(x).upper()

def line(label, value):
    st.markdown(f"**{label}:** {value}")

MESES = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}

def fmt_fecha(x):
    if pd.isna(x) or str(x).strip() in ["", "nan", "None"]:
        return "—"
    dt = pd.to_datetime(x, errors="coerce")
    if pd.isna(dt):
        return str(x)
    return f"{dt.day:02d} - {MESES[dt.month]} - {dt.year}"



# ===============================
# FILTRO CODLOCAL (tipo Power BI)
# ===============================

st.title("Detalle de Ejecución por Código Local")


codlocal_list = sorted(df["CODLOCAL"].unique())
cod_sel = st.selectbox("Buscar Código Local", codlocal_list)

row = df[df["CODLOCAL"] == cod_sel].iloc[0]

st.markdown('<div class="card tight">', unsafe_allow_html=True)
st.subheader("🏫 Datos del local educativo")

def info_cell(label, value):
    v = "—" if value is None or str(value).strip() in ["", "nan"] else str(value)
    st.markdown(f'<div class="small-label">{label}</div><div class="small-value">{v}</div>',
                unsafe_allow_html=True)

# Fila 1 (orden solicitado)
r1 = st.columns(6)
with r1[0]: info_cell("Sector", row.get("SECTOR", "—"))
with r1[1]: info_cell("Región educativa", row.get("REGION", "—"))
with r1[2]: info_cell("Departamento", row.get("DEPARTAMENTO", "—"))
with r1[3]: info_cell("Provincia", row.get("PROVINCIA", "—"))
with r1[4]: info_cell("Distrito", row.get("DISTRITO", "—"))
with r1[5]: info_cell("Centro poblado", row.get("CENTROPOBLADO", "—"))

# Fila 2 (IIEE ancho + mini datos a la derecha)
left, right = st.columns([2.2, 1.0])

with left:
    info_cell("IIEE", row.get("NOMBRE_IIEE", "—"))
    info_cell("DRE/UGEL", row.get("DRE_UGEL", "—"))

with right:
    info_cell("Ruralidad", row.get("RURALIDAD", "—"))
    info_cell("Estudiantes", row.get("ESTUDIANTES", "—"))
    info_cell("Cod. Modular", row.get("COD_MODULAR", "—"))

st.markdown('</div>', unsafe_allow_html=True)



# ===============================
# BLOQUE 1: MONTOS
# ===============================
st.markdown('<div class="card tight">', unsafe_allow_html=True)
st.subheader("💰 Montos")

monto_prog = to_number(row.get("MONTOTOTAL_PROGRAMADO", np.nan))
monto_trans = to_number(row.get("MONTO_TRANSFERENCIAS", np.nan))
monto_ret  = to_number(row.get("MONTO_RETIRADO", np.nan))

c1, c2 = st.columns([1.1, 1.0])  # izquierda montos, derecha KPI

with c1:
    st.markdown('<div class="montos-wrap">', unsafe_allow_html=True)
    st.markdown(f'<div class="monto-label">Monto programado</div><div class="monto-value">{formato_soles(monto_prog)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="monto-label">Monto transferido</div><div class="monto-value">{formato_soles(monto_trans)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="monto-label">Monto retirado</div><div class="monto-value">{formato_soles(monto_ret)}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


avance = 0.0
if (not pd.isna(monto_prog)) and monto_prog > 0 and (not pd.isna(monto_ret)):
    avance = float((monto_ret / monto_prog) * 100)

# asegurar rango 0-100
avance = max(0.0, min(100.0, avance))


# KPI mini tipo gauge (más pequeño)
with c2:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avance,
        number={"suffix": "%", "font": {"size": 40, "color": "white"}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickmode": "array",
                "tickvals": [0, 25, 50, 75, 100],
                "ticktext": ["0", "25", "50", "75", "100"],
                "tickfont": {"size": 14, "color": "white"},
            },
            "bar": {"color": "#2e7d32"},
            "bgcolor": "#111111",
            "borderwidth": 0,
        },
        domain={"x": [0, 1], "y": [0, 1]},
    ))

    fig.update_layout(
        height=300,
        margin=dict(l=15, r=15, t=30, b=15),
        paper_bgcolor="#111111",
        plot_bgcolor="#111111",
        font=dict(color="white"),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# BLOQUE 2: RESPONSABLE + FAM
# ===============================

colL, colR = st.columns(2)

with colL:
    st.markdown('<div class="card tight">', unsafe_allow_html=True)
    st.subheader("👤 Responsable")

    # Ajusta nombres reales (yo sigo tu lógica)
    resp_sin = to_number(row.get("RESPONSABLE_SIN_RESPONSABLE", 0))  # o tu nombre ya normalizado
    resp_con = to_number(row.get("RESPONSABLE_CON_CUENTA", 0))

    if resp_sin == 1:
        line("Cuenta con responsable", "NO")
        line("Responsable con cuenta", "NO APLICA")
        # alerta solo si NO tiene responsable
        plazo_reg = pd.to_datetime("2026-04-22")
        dias = (plazo_reg - HOY).days
        st.warning(f"Alerta registro: {dias} días {semaforo(dias)}")
    else:
        line("Cuenta con responsable", "SI")
        line("Responsable con cuenta", "SI" if resp_con == 1 else "NO")

    # Fecha de registro solo si tiene cuenta
    if resp_con == 1:
        line("Fecha de registro", str(row.get("FECHA_REGISTRO", "")))

    nota = row.get("NOTA", "")
    if isinstance(nota, str) and nota.strip():
        st.info(f"Nota: {nota}")

st.markdown('</div>', unsafe_allow_html=True)


with colR:
    st.markdown('<div class="card tight">', unsafe_allow_html=True)
    st.subheader("📄 Ficha de Acciones de Mantenimiento (FAM)")

    estado_fam = row.get("ESTADO_FAM", row.get("ESTADOFAM", row.get("AS", "—")))
    st.markdown(f"**Estado FAM:** {estado_badge(estado_fam)}", unsafe_allow_html=True)

    # Monto: muéstralo siempre
    monto_fam = row.get("MONTO_FAM", row.get("TOTAL_FAM", row.get("BZ", np.nan)))
    st.markdown(f"**Monto FAM:** {formato_soles(monto_fam)}")

    # Fechas: muéstralas siempre
    f_envio = row.get("FECHA_PRIMERENVIO_FAM", row.get("FECHA_ENVIO_FAM", np.nan))
    f_verif = row.get("FECHA_VERIFICACION_FAM", row.get("FECHA_VERIF_FAM", np.nan))
    st.markdown(f"**Fecha de primer envío:** {fmt_fecha(f_envio)}")
    st.markdown(f"**Fecha de verificación:** {fmt_fecha(f_verif)}")

    # Alertas SOLO si NO está verificada
    if not is_verificada(estado_fam):
        plazo_reg_fam = pd.to_datetime("2026-04-29")
        dias_reg = dias_restantes(plazo_reg_fam)
        st.markdown(
            f"**Plazo registro FAM:** 29 - Abr - 2026 | "
            f"**Días al plazo:** {dias_reg} {semaforo(dias_reg)}"
        )

        plazo_ver_fam = pd.to_datetime("2026-05-20")
        dias_ver = dias_restantes(plazo_ver_fam)
        st.markdown(
            f"**Plazo aprobación FAM:** 20 - May - 2026 | "
            f"**Días al plazo:** {dias_ver} {semaforo(dias_ver)}"
        )

    st.markdown('</div>', unsafe_allow_html=True)


# ===============================
# BLOQUE 3: PCA + DG
# ===============================

colL2, colR2 = st.columns(2)

with colL2:
    st.markdown('<div class="card tight">', unsafe_allow_html=True)
    st.subheader("📑 Panel de Culminación de Acciones (PCA)")

    estado_pca = row.get("ESTADO_PCA", row.get("CA", "—"))
    st.markdown(f"**Estado PCA:** {estado_badge(estado_pca)}", unsafe_allow_html=True)

    if not is_verificada(estado_pca):
        f_envio = row.get("FECHA_ENVIO_PCA", row.get("FECHAPRIMERENVIO_PCA", row.get("CD", np.nan)))
        f_verif = row.get("FECHA_VERIF_PCA", row.get("FECHAVERIF_PCA", row.get("CF", np.nan)))

        plazo_reg_pca = pd.to_datetime("2026-08-05")
        dias_reg = dias_restantes(plazo_reg_pca)
        st.markdown(
            f"**Plazo registro PCA:** 05 - Ago - 2026 | "
            f"**Días al plazo:** {dias_reg} {semaforo(dias_reg)}"
        )
        st.markdown(f"**Fecha de primer envío:** {fmt_fecha(f_envio)}")

        plazo_ver_pca = pd.to_datetime("2026-08-26")
        dias_ver = dias_restantes(plazo_ver_pca)
        st.markdown(
            f"**Plazo aprobación PCA:** 26 - Ago - 2026 | "
            f"**Días al plazo:** {dias_ver} {semaforo(dias_ver)}"
        )
        st.markdown(f"**Fecha de verificación:** {fmt_fecha(f_verif)}")

    st.markdown('</div>', unsafe_allow_html=True)

with colR2:
    st.markdown('<div class="card tight">', unsafe_allow_html=True)
    st.subheader("🧾 Declaración de Gastos (DG)")

    estado_dg = row.get("ESTADO_DG", row.get("CS", "—"))
    st.markdown(f"**Estado DG:** {estado_badge(estado_dg)}", unsafe_allow_html=True)

    st.markdown(f"**Monto DG:** {formato_soles(row.get('MONTO_DG', row.get('DZ', np.nan)))}")

    if not is_verificada(estado_dg):
        f_envio = row.get("FECHA_ENVIO_DG", row.get("FECHA_PRIMERENVIO_DG", row.get("CV", np.nan)))
        f_verif = row.get("FECHA_VERIF_DG", row.get("FECHAVERIF_DG", row.get("CX", np.nan)))

        plazo_reg_dg = pd.to_datetime("2026-08-05")
        dias_reg = dias_restantes(plazo_reg_dg)
        st.markdown(
            f"**Plazo registro DG:** 05 - Ago - 2026 | "
            f"**Días al plazo:** {dias_reg} {semaforo(dias_reg)}"
        )
        st.markdown(f"**Fecha de primer envío:** {fmt_fecha(f_envio)}")

        plazo_ver_dg = pd.to_datetime("2026-08-26")
        dias_ver = dias_restantes(plazo_ver_dg)
        st.markdown(
            f"**Plazo aprobación DG:** 26 - Ago - 2026 | "
            f"**Días al plazo:** {dias_ver} {semaforo(dias_ver)}"
        )
        st.markdown(f"**Fecha de verificación:** {fmt_fecha(f_verif)}")

    st.markdown('</div>', unsafe_allow_html=True)

