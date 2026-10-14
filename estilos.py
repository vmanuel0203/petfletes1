"""Estilos y componentes HTML de PetFletes (verde bosque, naranja y crema)."""
from html import escape

import streamlit as st

CATEGORIAS = {
    "Alimento": ("🍖", "#FDE7C8"),
    "Higiene": ("🧼", "#D9F0E6"),
    "Juguetes": ("🧸", "#FBE0E0"),
    "Accesorios": ("🎀", "#E3E8FB"),
    "Salud": ("💊", "#EAF6D5"),
}
TONOS_ESTADO = {
    "Buscando repartidor": "amarillo", "Tiempo agotado": "naranja",
    "Aceptado": "verde", "Entregado": "verde", "Cancelado": "rojo",
}

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
.stApp, .stApp button, .stApp input, .stApp textarea { font-family: 'Plus Jakarta Sans', system-ui, sans-serif; }
header[data-testid="stHeader"] { background: transparent; height: 0; visibility: hidden; }
#MainMenu, footer { visibility: hidden; }
section[data-testid="stSidebar"] { display: none; }
.block-container { max-width: 1180px; padding: 1rem 1.25rem 4rem; }
h1, h2, h3, h4 { color: #0E4F39; font-weight: 800; letter-spacing: -0.01em; }

.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button, .stLinkButton > a {
  border-radius: 999px; font-weight: 700; }
.stButton > button[kind="secondary"], .stDownloadButton > button, .stLinkButton > a {
  border: 1.5px solid #14664A; color: #14664A; background: #fff; }

[class*="st-key-card_"], [class*="st-key-cardsel_"] {
  background: #fff; border: 1px solid #EBDFCD; border-radius: 20px; padding: 1rem 1.1rem;
  box-shadow: 0 4px 14px rgba(14, 79, 57, 0.06); }
[class*="st-key-cardsel_"] { border: 2px solid #14664A; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 18px; border-color: #EBDFCD; }

.st-key-topbar { background: #fff; border-radius: 22px; padding: 0.55rem 1rem;
  box-shadow: 0 4px 16px rgba(14, 79, 57, 0.08); margin-bottom: 0.7rem; }
.st-key-topbar [data-testid="stHorizontalBlock"],
[class*="st-key-card_linea_"] [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0.4rem; align-items: center; }
.st-key-topbar [data-testid="stColumn"], .st-key-topbar [data-testid="column"],
[class*="st-key-card_linea_"] [data-testid="stColumn"], [class*="st-key-card_linea_"] [data-testid="column"] { min-width: 0 !important; }
.st-key-card_resumen { position: sticky; top: 0.8rem; }

.pf-logo { font-weight: 800; font-size: 1.35rem; color: #0E4F39; white-space: nowrap; }
.pf-logo span { color: #F97316; }
.pf-hero { background: linear-gradient(120deg, #14664A 0%, #0E4F39 100%); color: #fff; border-radius: 26px;
  padding: 2.2rem; position: relative; overflow: hidden; margin-bottom: 1rem; }
.pf-hero h1 { color: #fff; font-size: 2.3rem; line-height: 1.15; margin: 0 0 0.6rem; max-width: min(36rem, calc(100% - 7.5rem)); }
.pf-hero p { color: #D6EBE1; margin: 0; max-width: min(32rem, calc(100% - 7.5rem)); }
.pf-badge { display: inline-block; background: #F6C945; color: #0E4F39; font-weight: 800; border-radius: 999px;
  padding: 0.25rem 0.8rem; font-size: 0.8rem; margin-bottom: 0.8rem; }
.pf-emoji { position: absolute; right: 1.6rem; bottom: 0.4rem; font-size: 6rem; opacity: 0.95; }

.pf-kpi { background: #fff; border: 1px solid #EBDFCD; border-radius: 18px; padding: 0.8rem 1rem; }
.pf-kpi .l { font-size: 0.76rem; color: #5E7A6E; font-weight: 600; }
.pf-kpi .v { font-size: 1.55rem; font-weight: 800; color: #0E4F39; line-height: 1.2; }
.pf-kpi .d { font-size: 0.72rem; color: #8A9A92; }

.pf-chip { display: inline-block; border-radius: 999px; padding: 0.15rem 0.65rem; font-size: 0.75rem;
  font-weight: 700; margin: 0 0.25rem 0.25rem 0; }
.pf-chip.verde { background: #D9F0E6; color: #0E4F39; } .pf-chip.naranja { background: #FFE3CC; color: #B24A00; }
.pf-chip.amarillo { background: #FBEFC2; color: #7A5B00; } .pf-chip.rojo { background: #FBDADA; color: #9B1C1C; }
.pf-chip.gris { background: #EFEAE1; color: #5B6B64; }

.pf-ico { width: 64px; height: 64px; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-size: 30px; margin-bottom: 0.5rem; }
.pf-nombre { font-weight: 700; color: #123D2E; line-height: 1.25; min-height: 2.5em; }
.pf-meta { font-size: 0.78rem; color: #6B7F75; margin: 0.15rem 0 0.4rem; }
.pf-precio { font-size: 1.3rem; font-weight: 800; color: #14664A; margin-bottom: 0.3rem; }
.pf-tarifa { font-size: 1.7rem; font-weight: 800; color: #F97316; line-height: 1.1; }
.pf-fila { display: flex; justify-content: space-between; gap: 0.6rem; padding: 0.28rem 0; font-size: 0.92rem; color: #35574A; }
.pf-fila.fuerte { font-weight: 800; color: #0E4F39; border-top: 1px dashed #D9C9B0; margin-top: 0.3rem; padding-top: 0.5rem; }
.pf-total { display: flex; justify-content: space-between; align-items: center; font-weight: 700; color: #0E4F39; }
.pf-total b { font-size: 1.8rem; color: #F97316; }
.pf-sec { display: flex; align-items: center; gap: 0.6rem; font-weight: 800; color: #0E4F39; font-size: 1.1rem; margin: 1rem 0 0.5rem; }
.pf-sec i { font-style: normal; width: 1.7rem; height: 1.7rem; border-radius: 50%; background: #F97316; color: #fff;
  display: inline-flex; align-items: center; justify-content: center; font-size: 0.9rem; }

.pf-pasos { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.8rem; margin: 0.2rem 0 1.2rem; }
.pf-paso { background: #fff; border: 1px solid #EBDFCD; border-radius: 18px; padding: 0.9rem 1rem; }
.pf-paso i { font-style: normal; width: 1.6rem; height: 1.6rem; border-radius: 50%; background: #F97316; color: #fff;
  display: inline-flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.85rem; }
.pf-paso b { display: block; color: #0E4F39; margin: 0.45rem 0 0.15rem; }
.pf-paso span { font-size: 0.82rem; color: #5E7A6E; }
.pf-subtitulo { font-weight: 800; color: #0E4F39; font-size: 1.05rem; margin: 0.4rem 0 0.7rem; }
.pf-cats { display: flex; gap: 1.1rem; flex-wrap: wrap; margin-bottom: 1.2rem; }
.pf-cat { text-align: center; font-size: 0.78rem; font-weight: 700; color: #35574A; }
.pf-cat span { display: flex; width: 58px; height: 58px; border-radius: 50%; align-items: center;
  justify-content: center; font-size: 27px; margin: 0 auto 0.3rem; }
.st-key-card_auth [data-testid="stForm"] { border: none; padding: 0; }
.st-key-card_auth [data-baseweb="input"] { background: #FBF6EE; border: 1.5px solid #E3D5BF; border-radius: 12px; }
.st-key-card_auth [data-baseweb="input"]:focus-within { border-color: #14664A; }
.st-key-card_auth [data-baseweb="base-input"] { background: transparent; }
.st-key-card_auth { padding: 1.4rem 1.5rem; }

@media (max-width: 640px) {
  .pf-hero h1, .pf-hero p { max-width: calc(100% - 4.2rem); }
  .pf-solo-desktop { display: none; }
  .block-container { padding: 0.6rem 0.7rem 4rem; }
  .pf-hero { padding: 1.3rem; } .pf-hero h1 { font-size: 1.55rem; } .pf-emoji { font-size: 3.4rem; }
  .pf-logo { font-size: 1.1rem; }
}
"""


def inyectar_css():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def html(contenido):
    st.markdown(contenido, unsafe_allow_html=True)


def colones(monto):
    return "₡{:,.0f}".format(monto)


def logo():
    return '<div class="pf-logo">🐾 Pet<span>Fletes</span></div>'


def hero(insignia, titulo, texto, emoji="🐶"):
    return (f'<div class="pf-hero"><span class="pf-badge">{escape(insignia)}</span>'
            f'<h1>{escape(titulo)}</h1><p>{escape(texto)}</p><div class="pf-emoji">{emoji}</div></div>')


def kpi(etiqueta, valor, detalle=""):
    extra = f'<div class="d">{escape(str(detalle))}</div>' if detalle else ""
    return (f'<div class="pf-kpi"><div class="l">{escape(etiqueta)}</div>'
            f'<div class="v">{escape(str(valor))}</div>{extra}</div>')


def chip(texto, tono="gris"):
    return f'<span class="pf-chip {tono}">{escape(str(texto))}</span>'


def chip_estado(estado):
    return chip(estado, TONOS_ESTADO.get(estado, "gris"))


def seccion(numero, titulo):
    return f'<div class="pf-sec"><i>{numero}</i>{escape(titulo)}</div>'


def fila(etiqueta, valor, fuerte=False):
    clase = "pf-fila fuerte" if fuerte else "pf-fila"
    return f'<div class="{clase}"><span>{escape(str(etiqueta))}</span><span>{escape(str(valor))}</span></div>'


def total(etiqueta, valor):
    return f'<div class="pf-total"><span>{escape(etiqueta)}</span><b>{escape(str(valor))}</b></div>'


def tarjeta_producto(p, mostrar_tienda=False):
    emoji, color = CATEGORIAS.get(p.get("categoria") or "Accesorios", ("🐾", "#F7E7CF"))
    tienda = f'<div class="pf-meta">🏪 {escape(p["tienda_nombre"])}</div>' if mostrar_tienda else ""
    return (f'<div class="pf-ico" style="background:{color}">{emoji}</div>'
            f'<div class="pf-nombre">{escape(p["nombre"])}</div>{tienda}'
            f'<div class="pf-meta">{escape(p.get("categoria") or "")} · {p["peso_kg"]:g} kg</div>'
            f'<div class="pf-precio">{colones(p["precio"])}</div>')


def tarjeta_tienda(t, km):
    return (f'<div class="pf-ico" style="background:#D9F0E6">🏪</div>'
            f'<div class="pf-nombre">{escape(t["nombre"])}</div>'
            f'<div class="pf-meta">📍 {escape(t["direccion"])}</div>'
            f'{chip(f"a {km:.1f} km", "verde")}'
            f'<div class="pf-meta">{escape(t.get("descripcion") or "")}</div>')


def tarjeta_viaje(p, cliente_txt, restante_txt):
    km = f"{p['distancia_km']:g} km"
    peso = f"{p['peso_total']:g} kg"
    ofertas = f"{p['n_ofertas']} ofertas"
    return (f'<div class="pf-meta">Pedido #{p["id"]} · {escape(p["tienda_nombre"])}</div>'
            f'<div class="pf-tarifa">{colones(p["oferta"])}</div>'
            f'<div class="pf-nombre" style="min-height:0">📍 {escape(p["destino_nombre"])}</div>'
            + chip(km, "verde") + chip(peso, "gris") + chip("⏳ " + restante_txt, "amarillo") + chip(ofertas, "gris")
            + f'<div class="pf-meta">Cliente: {escape(p["cliente_nombre"])} · {escape(cliente_txt)}</div>')


def pasos(items):
    """Tarjetas numeradas 'cómo funciona'. items: [(titulo, texto)]."""
    celdas = "".join(f'<div class="pf-paso"><i>{n}</i><b>{escape(t)}</b><span>{escape(x)}</span></div>'
                     for n, (t, x) in enumerate(items, 1))
    return f'<div class="pf-pasos">{celdas}</div>'


def categorias_tira():
    celdas = "".join(f'<div class="pf-cat"><span style="background:{color}">{emoji}</span>{escape(nombre)}</div>'
                     for nombre, (emoji, color) in CATEGORIAS.items())
    return f'<div class="pf-cats">{celdas}</div>'


def subtitulo(texto):
    return f'<div class="pf-subtitulo">{escape(texto)}</div>'
