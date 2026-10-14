"""PetFletes - MVP de economía colaborativa para productos de mascotas.

Roles: usuario, repartidor y administrador.
Ejecutar con:  python -m streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="PetFletes", page_icon="🐾", layout="wide", initial_sidebar_state="collapsed")

import db  # noqa: E402
import estilos  # noqa: E402
import vistas_admin as va  # noqa: E402
import vistas_cliente as vc  # noqa: E402
import vistas_repartidor as vr  # noqa: E402
from componentes import (NAV_CARRITO, NAV_EN_CURSO, NAV_PEDIDOS, NAV_TIENDAS, ZONA_DEFECTO,  # noqa: E402
                         ZONAS, texto_calificacion, vista_comunidad, vista_soporte)

estilos.inyectar_css()


@st.cache_resource
def iniciar_base_de_datos():
    db.init_db()
    return True


iniciar_base_de_datos()

ROLES = {"🧑 Usuario": "usuario", "🛵 Repartidor": "repartidor", "🛠️ Administrador": "admin"}
NOMBRE_ROL = {"usuario": "Usuario", "repartidor": "Repartidor", "admin": "Administrador"}
DEMO_EMAIL = {"usuario": "demo@petfletes.cr", "repartidor": "repartidor@petfletes.cr"}
DESCRIPCION_ROL = {
    "usuario": "Pide productos para tu mascota y ofrece tu tarifa de envío.",
    "repartidor": "Acepta viajes, gana con cada entrega y navega con Waze o Google Maps.",
    "admin": "Panel de control de la plataforma.",
}
VEHICULOS = ["Moto", "Bicicleta", "Carro pequeño", "Pick-up", "Camión pequeño"]

NAVEGACION = {
    "usuario": {
        NAV_TIENDAS: vc.vista_tiendas,
        NAV_CARRITO: vc.vista_carrito,
        NAV_PEDIDOS: vc.vista_seguimiento,
        "💬 Soporte": vista_soporte,
        "👥 Comunidad": vista_comunidad,
        "🗺️ Mapa": vc.vista_mapa,
    },
    "repartidor": {
        "🧭 Viajes disponibles": vr.vista_disponibles,
        NAV_EN_CURSO: vr.vista_en_curso,
        "💰 Ganancias": vr.vista_ganancias,
        "💬 Soporte": vista_soporte,
        "👥 Comunidad": vista_comunidad,
    },
    "admin": {
        "📊 Resumen": va.vista_resumen,
        "📦 Pedidos": va.vista_pedidos_admin,
        "👤 Usuarios": va.vista_usuarios_admin,
        "🛵 Repartidores": va.vista_repartidores_admin,
        "🏪 Tiendas": va.vista_tiendas_admin,
        "📈 Reportes": va.vista_reportes,
        "💬 Soporte": vista_soporte,
    },
}


# --------------------------------------------------------------- Autenticación
def _form_login(rol):
    with st.form("form_login"):
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")
        entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)
    if entrar:
        try:
            usuario = db.autenticar(email, password)
        except ValueError as error:
            st.error(str(error))
            return
        if usuario is None:
            st.error("Correo o contraseña incorrectos.")
        elif usuario["rol"] != rol:
            st.error(f"Esa cuenta es de tipo «{NOMBRE_ROL[usuario['rol']]}». "
                     "Cambia la opción de arriba para entrar.")
        else:
            st.session_state.usuario = usuario
            st.rerun()
    if rol in DEMO_EMAIL and st.button("✨ Probar con la cuenta demo", key="btn_demo", use_container_width=True):
        st.session_state.usuario = db.autenticar(DEMO_EMAIL[rol], "demo123")
        st.rerun()


def _form_registro(rol):
    with st.form("form_registro"):
        nombre = st.text_input("Nombre completo")
        email = st.text_input("Correo electrónico", key="email_registro")
        telefono = st.text_input("Teléfono de contacto", placeholder="8888-0000")
        sinpe, vehiculo = "", ""
        if rol == "repartidor":
            sinpe = st.text_input("Número de SINPE Móvil (para recibir pagos)", placeholder="8888-0000")
            vehiculo = st.selectbox("Tipo de vehículo", VEHICULOS)
        password = st.text_input("Contraseña (mínimo 6 caracteres)", type="password", key="password_registro")
        registrar = st.form_submit_button("Crear cuenta", type="primary", use_container_width=True)
    if registrar:
        try:
            st.session_state.usuario = db.crear_usuario(
                nombre, email, telefono, password, rol=rol, sinpe=sinpe, vehiculo=vehiculo)
            st.rerun()
        except ValueError as error:
            st.error(str(error))


def _popover(etiqueta, primario=False):
    try:
        return st.popover(etiqueta, use_container_width=True, type="primary" if primario else "secondary")
    except TypeError:  # versiones sin el parámetro type
        return st.popover(etiqueta, use_container_width=True)


def _panel_acceso(modo):
    """Contenido de los menús flotantes de acceso (iniciar sesión / registrarme)."""
    opciones = list(ROLES) if modo == "login" else [r for r in ROLES if ROLES[r] != "admin"]
    clave = f"rol_{modo}"
    if st.session_state.get(clave) not in opciones:
        st.session_state[clave] = opciones[0]
    etiqueta = st.pills("¿Cómo quieres entrar?" if modo == "login" else "¿Cómo quieres unirte?", opciones,
                        selection_mode="single", key=clave) or opciones[0]
    rol = ROLES[etiqueta]
    st.caption(DESCRIPCION_ROL[rol])
    if modo == "login":
        _form_login(rol)
        if rol in DEMO_EMAIL:
            st.caption("Cuenta de prueba: " + DEMO_EMAIL[rol] + " / demo123")
    else:
        _form_registro(rol)


def vista_auth():
    # Acceso compacto arriba a la derecha (menús flotantes)
    with st.container(key="topbar"):
        c_logo, c_entrar, c_reg = st.columns([5, 1.7, 2], vertical_alignment="center")
        c_logo.markdown(estilos.logo(), unsafe_allow_html=True)
        with c_entrar:
            with _popover("Entrar"):
                _panel_acceso("login")
        with c_reg:
            with _popover("Registrarme", primario=True):
                _panel_acceso("registro")

    # Banner con la actividad real de la comunidad
    estilos.html(estilos.banner_comunidad(db.actividad_comunidad(12)))

    s = db.estadisticas_publicas()
    cifras = []
    if s["entregados"]:
        cifras.append(("Pedidos entregados", s["entregados"], "en la plataforma"))
    if s["n_cal"]:
        cifras.append(("Calificación de repartidores", f"{s['promedio']} ⭐", f"{s['n_cal']} reseñas"))
    if s["repartidores"]:
        cifras.append(("Repartidores", s["repartidores"], "listos para ofertar"))
    estilos.html(estilos.estadisticas(cifras))

    estilos.html('<div class="pf-solo-desktop">'
                 + estilos.subtitulo("Así de fácil")
                 + estilos.pasos([("Elige tu tienda", "Arma tu carrito con alimento, higiene, juguetes y más."),
                                  ("Ofrece tu tarifa", "Sube o baja el envío de ₡100 en ₡100 y elige la mejor oferta."),
                                  ("Recibe y paga directo", "Sigue el viaje en el mapa y paga por SINPE Móvil o efectivo.")])
                 + estilos.subtitulo("Todo para tu mascota")
                 + estilos.categorias_tira() + '</div>')
    st.caption("👆 Entra o únete a la comunidad desde los botones de arriba a la derecha.")


# ------------------------------------------------------------------- Barra superior
def cerrar_sesion():
    st.session_state.clear()


def ir_a_carrito():
    st.session_state["nav"] = NAV_CARRITO


def barra_superior(usuario):
    es_cliente = usuario["rol"] == "usuario"
    with st.container(key="topbar"):
        if es_cliente:
            c_logo, c_zona, c_busca, c_carro, c_cuenta = st.columns([2.2, 2.6, 4, 1.4, 1], vertical_alignment="center")
        else:
            c_logo, c_cuenta = st.columns([6, 1], vertical_alignment="center")
        c_logo.markdown(estilos.logo(), unsafe_allow_html=True)

        if es_cliente:
            st.session_state.setdefault("zona_actual", ZONA_DEFECTO)
            with c_zona:
                with st.popover(f"📍 {st.session_state['zona_actual']}", use_container_width=True):
                    st.selectbox("Tu zona (para ordenar las tiendas por cercanía)", list(ZONAS), key="zona_actual")
            consulta = c_busca.text_input("Buscar productos", key="busqueda", placeholder="🔎 Buscar productos…",
                                          label_visibility="collapsed")
            if consulta != st.session_state.get("_ultima_busqueda", ""):
                st.session_state["_ultima_busqueda"] = consulta
                if consulta.strip():
                    st.session_state["nav"] = NAV_TIENDAS
            unidades = sum(st.session_state.carrito.values())
            c_carro.button(f"🛒 {unidades}", key="btn_carrito", on_click=ir_a_carrito, use_container_width=True,
                           type="primary" if unidades else "secondary")

        with c_cuenta:
            with st.popover("👤", use_container_width=True):
                st.markdown(f"**{usuario['nombre']}**")
                st.caption(f"Cuenta: {NOMBRE_ROL[usuario['rol']]}")
                if usuario["rol"] == "usuario":
                    promedio, n = db.promedio_usuario(usuario["id"])
                elif usuario["rol"] == "repartidor" and usuario["repartidor_id"]:
                    promedio, n = db.promedio_repartidor(usuario["repartidor_id"])
                else:
                    promedio, n = None, 0
                if n:
                    st.caption(f"Tu calificación: {texto_calificacion(promedio, n)}")
                st.button("Cerrar sesión", key="btn_salir", on_click=cerrar_sesion, use_container_width=True)


# ------------------------------------------------------------------- Principal
def main():
    for clave, valor in {"usuario": None, "carrito": {}, "tienda_carrito": None, "pedido_id": None}.items():
        st.session_state.setdefault(clave, valor)

    if st.session_state.usuario is None:
        vista_auth()
        return

    usuario = st.session_state.usuario
    vistas = NAVEGACION[usuario["rol"]]
    secciones = list(vistas)

    if "ir_a" in st.session_state:
        st.session_state["nav"] = st.session_state.pop("ir_a")
    barra_superior(usuario)
    if st.session_state.get("nav") not in secciones:
        st.session_state["nav"] = secciones[0]

    seleccion = st.pills("Navegación", secciones, selection_mode="single", key="nav", label_visibility="collapsed")
    seccion = seleccion or st.session_state.get("_nav_previa", secciones[0])
    st.session_state["_nav_previa"] = seccion
    vistas[seccion]()


main()
