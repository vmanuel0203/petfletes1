"""PetFletes - MVP de economía colaborativa para productos de mascotas.

Roles: usuario, repartidor y administrador (centro de control).
Ejecutar con:  python -m streamlit run app.py
"""
from datetime import datetime

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

import db
import tarifas
import tracking

st.set_page_config(page_title="PetFletes", page_icon="🐾", layout="centered")


@st.cache_resource
def iniciar_base_de_datos():
    db.init_db()
    return True


iniciar_base_de_datos()

# ------------------------------------------------------------------ Constantes
ZONAS = {
    "San Pedro de Montes de Oca": (9.9347, -84.0510),
    "Santa Ana centro": (9.9328, -84.1833),
    "Desamparados centro": (9.8975, -84.0661),
    "Heredia - Barreal": (9.9972, -84.1523),
    "Alajuela centro": (10.0162, -84.2140),
    "Cartago centro": (9.8644, -83.9194),
}
ROLES = {"🧑 Usuario": "usuario", "🛵 Repartidor": "repartidor", "🛠️ Administrador": "admin"}
NOMBRE_ROL = {"usuario": "Usuario", "repartidor": "Repartidor", "admin": "Administrador"}
VEHICULOS = ["Moto", "Bicicleta", "Carro pequeño", "Pick-up", "Camión pequeño"]

ESTADOS = {"Buscando repartidor": "🔎", "Tiempo agotado": "⏰", "Aceptado": "🛵",
           "Entregado": "✅", "Cancelado": "❌"}
TIPOS_PUBLICACION = ["Oferta de tienda", "Tip de mascotas", "Pregunta"]
ICONOS_TIPO = {"Oferta de tienda": "🏷️", "Tip de mascotas": "💡", "Pregunta": "❓"}

COLOR_TIENDA = "#2E7D32"
COLOR_DESTINO = "#D32F2F"
CENTRO_DEFECTO = (9.9281, -84.0907)  # San José, Costa Rica


def colones(monto):
    return "₡{:,.0f}".format(monto)


def mostrar_mapa(puntos):
    """Mapa simple (st.map). Cada punto: lat, lon, color, size."""
    df = pd.DataFrame(puntos)
    st.map(df, latitude="lat", longitude="lon", color="color", size="size", zoom=11)
    leyenda = []
    if (df["color"] == COLOR_TIENDA).any():
        leyenda.append("🟢 Inicio / tienda")
    if (df["color"] == COLOR_DESTINO).any():
        leyenda.append("🔴 Destino")
    st.caption(" · ".join(leyenda))


def puntos_ruta(p):
    return [
        {"lat": p["origen_lat"], "lon": p["origen_lon"], "color": COLOR_TIENDA, "size": 250},
        {"lat": p["destino_lat"], "lon": p["destino_lon"], "color": COLOR_DESTINO, "size": 250},
    ]


# ------------------------------------------------------ Selector de pin (mapa)
def _mapa_clicable(mapa, key):
    try:
        return st_folium(mapa, height=320, use_container_width=True,
                         returned_objects=["last_clicked"], key=key)
    except TypeError:  # versiones de streamlit-folium sin use_container_width
        return st_folium(mapa, height=320, returned_objects=["last_clicked"], key=key)


def quitar_pin(clave):
    st.session_state[clave] = None


def selector_pin(clave, centro, etiqueta, color, zoom=13):
    """Mapa donde el usuario toca para fijar un pin. Devuelve (lat, lon) o None."""
    pin = st.session_state.get(clave)
    mapa = folium.Map(location=list(pin or centro), zoom_start=15 if pin else zoom, control_scale=True)
    if pin:
        folium.Marker(list(pin), tooltip=etiqueta, icon=folium.Icon(color=color)).add_to(mapa)
    salida = _mapa_clicable(mapa, "mapa_" + clave)
    click = salida.get("last_clicked") if salida else None
    if click:
        nuevo = (round(click["lat"], 6), round(click["lng"], 6))
        if st.session_state.get("ult_" + clave) != nuevo:
            st.session_state["ult_" + clave] = nuevo
            st.session_state[clave] = nuevo
            st.rerun()
    pin = st.session_state.get(clave)
    if pin:
        col_txt, col_btn = st.columns([3, 1])
        col_txt.caption(f"📍 {etiqueta}: {pin[0]:.5f}, {pin[1]:.5f}")
        col_btn.button("Quitar", key="quitar_" + clave, on_click=quitar_pin, args=(clave,))
    else:
        st.caption(f"👆 Toca el mapa para fijar el pin ({etiqueta.lower()}).")
    return pin


# --------------------------------------------------------------- Autenticación
def _form_login(rol):
    with st.form("form_login"):
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")
        entrar = st.form_submit_button("Entrar", use_container_width=True)
    if entrar:
        usuario = db.autenticar(email, password)
        if usuario is None:
            st.error("Correo o contraseña incorrectos.")
        elif usuario["rol"] != rol:
            st.error(f"Esa cuenta es de tipo «{NOMBRE_ROL[usuario['rol']]}». "
                     f"Cambia la opción de arriba para entrar.")
        else:
            st.session_state.usuario = usuario
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
        password = st.text_input("Contraseña (mínimo 6 caracteres)", type="password",
                                 key="password_registro")
        registrar = st.form_submit_button("Crear cuenta", use_container_width=True)
    if registrar:
        try:
            st.session_state.usuario = db.crear_usuario(
                nombre, email, telefono, password, rol=rol, sinpe=sinpe, vehiculo=vehiculo)
            st.rerun()
        except ValueError as error:
            st.error(str(error))


def vista_auth():
    st.title("🐾 PetFletes")
    st.caption("Pedí arena, alimento y más para tu mascota. Vos proponés la tarifa del envío.")
    etiqueta = st.radio("¿Cómo quieres entrar?", list(ROLES), horizontal=True)
    rol = ROLES[etiqueta]

    if rol == "admin":
        st.caption("Acceso exclusivo para el administrador de la plataforma.")
        _form_login(rol)
        return

    tab_login, tab_registro = st.tabs(["Iniciar sesión", "Registrarme"])
    with tab_login:
        _form_login(rol)
        if rol == "usuario":
            st.caption("Cuenta de prueba: demo@petfletes.cr / demo123")
        else:
            st.caption("Cuenta de prueba: repartidor@petfletes.cr / demo123")
    with tab_registro:
        _form_registro(rol)


# ------------------------------------------------------------ Módulo 1: Pedidos
def agregar_al_carrito(producto_id):
    clave = f"q_{producto_id}"
    cantidad = st.session_state.get(clave, 1)
    carrito = st.session_state.carrito
    carrito[producto_id] = carrito.get(producto_id, 0) + cantidad
    st.session_state[clave] = 1


def quitar_del_carrito(producto_id):
    st.session_state.carrito.pop(producto_id, None)


def vaciar_carrito():
    st.session_state.carrito = {}


def vista_pedidos():
    usuario = st.session_state.usuario
    st.header("🛒 Nuevo pedido")

    # 1. Tienda
    tiendas = db.listar_tiendas()
    nombres = {t["id"]: t["nombre"] for t in tiendas}
    tienda_id = st.selectbox("1. Elegí una tienda", options=list(nombres),
                             format_func=lambda i: nombres[i])
    if st.session_state.tienda_carrito != tienda_id:
        st.session_state.carrito = {}
        st.session_state.tienda_carrito = tienda_id
    tienda = db.obtener_tienda(tienda_id)
    st.caption(f"📍 {tienda['direccion']} — {tienda['descripcion']}")

    # 2. Productos
    st.subheader("2. Agregá productos")
    productos = db.listar_productos(tienda_id)
    producto_por_id = {p["id"]: p for p in productos}
    for p in productos:
        st.session_state.setdefault(f"q_{p['id']}", 1)
        with st.container(border=True):
            st.markdown(f"**{p['nombre']}**")
            st.caption(f"{colones(p['precio'])} · {p['peso_kg']:g} kg")
            col_cant, col_btn = st.columns(2)
            col_cant.number_input("Cantidad", min_value=1, max_value=20, step=1,
                                  key=f"q_{p['id']}", label_visibility="collapsed")
            col_btn.button("➕ Agregar", key=f"add_{p['id']}", on_click=agregar_al_carrito,
                           args=(p["id"],), use_container_width=True)

    st.subheader("🧺 Tu carrito")
    carrito = st.session_state.carrito
    if not carrito:
        st.info("Tu carrito está vacío. Agregá productos para continuar.")
    else:
        for pid, cantidad in list(carrito.items()):
            p = producto_por_id[pid]
            col_txt, col_del = st.columns([4, 1])
            col_txt.write(f"{cantidad} × {p['nombre']} — **{colones(cantidad * p['precio'])}**")
            col_del.button("🗑️", key=f"del_{pid}", on_click=quitar_del_carrito, args=(pid,))
        st.button("Vaciar carrito", on_click=vaciar_carrito)

    # 3. Ruta con pines
    st.subheader("3. Ruta de entrega")

    st.markdown("**Punto de inicio**")
    modo_origen = st.radio("Inicio", ["Tienda", "Pin en el mapa"], horizontal=True,
                           label_visibility="collapsed")
    origen_lat = origen_lon = None
    origen_nombre = ""
    if modo_origen == "Tienda":
        origen_lat, origen_lon, origen_nombre = tienda["lat"], tienda["lon"], tienda["nombre"]
        st.caption(f"Se retira en {tienda['nombre']}.")
    else:
        pin = selector_pin("pin_origen", (tienda["lat"], tienda["lon"]), "Punto de inicio", "green")
        if pin:
            origen_lat, origen_lon = pin
            origen_nombre = "Pin de inicio ({:.4f}, {:.4f})".format(*pin)

    st.markdown("**Punto de entrega**")
    modo_destino = st.radio("Entrega", ["Pin en el mapa", "Zona rápida"], horizontal=True,
                            label_visibility="collapsed")
    dest_lat = dest_lon = None
    destino_nombre = ""
    if modo_destino == "Zona rápida":
        zona = st.selectbox("Zona", list(ZONAS))
        dest_lat, dest_lon = ZONAS[zona]
        destino_nombre = zona
    else:
        centro = (origen_lat, origen_lon) if origen_lat is not None else (tienda["lat"], tienda["lon"])
        pin = selector_pin("pin_destino", centro, "Punto de entrega", "red")
        if pin:
            dest_lat, dest_lon = pin
            destino_nombre = "Pin de entrega ({:.4f}, {:.4f})".format(*pin)

    senas = st.text_input("Señas exactas de entrega",
                          placeholder="Ej: casa blanca, portón negro, 100 m sur de la escuela")

    if origen_lat is None or dest_lat is None:
        st.info("Fijá el punto de inicio y el de entrega para ver la tarifa.")
        return

    mostrar_mapa([
        {"lat": origen_lat, "lon": origen_lon, "color": COLOR_TIENDA, "size": 250},
        {"lat": dest_lat, "lon": dest_lon, "color": COLOR_DESTINO, "size": 250},
    ])
    distancia = tarifas.distancia_estimada_km(origen_lat, origen_lon, dest_lat, dest_lon)

    if not carrito:
        st.caption(f"Distancia estimada: {distancia:g} km")
        return

    # 4. Tarifa
    peso_total = round(sum(producto_por_id[pid]["peso_kg"] * c for pid, c in carrito.items()), 2)
    subtotal = sum(producto_por_id[pid]["precio"] * c for pid, c in carrito.items())
    desglose = tarifas.calcular_desglose(distancia, peso_total)
    minimo = desglose["total"]

    st.subheader("4. Tarifa del envío")
    col1, col2, col3 = st.columns(3)
    col1.metric("Distancia", f"{distancia:g} km")
    col2.metric("Peso", f"{peso_total:g} kg")
    col3.metric("Mínimo sugerido", colones(minimo))
    with st.expander("¿Cómo se calcula el mínimo?"):
        st.write(f"- Tarifa base: {colones(desglose['base'])}")
        st.write(f"- Distancia ({distancia:g} km × {colones(tarifas.COSTO_POR_KM)}): {colones(desglose['distancia'])}")
        st.write(f"- Peso extra ({desglose['kg_extra']:g} kg sobre {tarifas.PESO_LIBRE_KG:g} kg): {colones(desglose['peso'])}")

    oferta = st.number_input("Tu oferta por el envío (₡)", min_value=minimo, value=minimo,
                             step=100, help="Una oferta mayor al mínimo suele ser aceptada más rápido.")
    st.write(f"Productos: **{colones(subtotal)}** · Envío: **{colones(oferta)}** · "
             f"Total a pagar: **{colones(subtotal + oferta)}**")

    if st.button("🚀 Enviar pedido", type="primary", use_container_width=True):
        if not senas.strip():
            st.error("Agregá las señas exactas de entrega.")
            return
        items = [{
            "producto_id": pid,
            "nombre": producto_por_id[pid]["nombre"],
            "cantidad": cantidad,
            "precio": producto_por_id[pid]["precio"],
            "peso_kg": producto_por_id[pid]["peso_kg"],
        } for pid, cantidad in carrito.items()]
        pedido_id = db.crear_pedido(
            usuario["id"], tienda_id, items, peso_total, subtotal, distancia, minimo, int(oferta),
            origen_nombre, origen_lat, origen_lon, destino_nombre, senas.strip(), dest_lat, dest_lon,
        )
        st.session_state.pedido_id = pedido_id
        st.session_state.carrito = {}
        st.session_state.pop("pin_origen", None)
        st.session_state.pop("pin_destino", None)
        st.session_state.ir_a = "📦 Seguimiento y entrega"
        st.rerun()


# ------------------------------------------------- Utilidades de tiempo, mapas y navegación
FMT_FECHA = "%Y-%m-%d %H:%M:%S"
GATO_HTML = '<div style="font-size:30px;line-height:30px;text-align:center">🐱🚲</div>'


def fmt_mmss(segundos):
    m, s = divmod(int(max(0, segundos)), 60)
    return f"{m:02d}:{s:02d}"


def fmt_duracion(segundos):
    h, resto = divmod(int(max(0, segundos)), 3600)
    m, s = divmod(resto, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def duracion_entre(inicio, fin):
    return (datetime.strptime(fin, FMT_FECHA) - datetime.strptime(inicio, FMT_FECHA)).total_seconds()


def texto_calificacion(promedio, n):
    return f"⭐ {promedio:.1f} ({n})" if n else "Sin calificaciones aún"


def _render_folium(mapa, key, objetos, alto=320):
    try:
        return st_folium(mapa, height=alto, use_container_width=True,
                         returned_objects=objetos, key=key)
    except TypeError:  # versiones de streamlit-folium sin use_container_width
        return st_folium(mapa, height=alto, returned_objects=objetos, key=key)


def render_tracking(p, key):
    """Métricas de tiempo + mapa con el repartidor (🐱🚲), la tienda y el destino."""
    factor = 10.0 if st.session_state.get("acel_demo") else 1.0
    t = tracking.estado_tracking(p, factor)

    c1, c2, c3 = st.columns(3)
    c1.metric("Tiempo de la orden", fmt_duracion(tracking.segundos_desde(p["creado"])))
    c2.metric("Llega a la tienda", f"{t['eta_tienda_min']} min" if t["eta_tienda_min"] else "En tienda")
    c3.metric("Tienda → destino", f"{t['eta_destino_min']} min" if t["eta_destino_min"] else "Llegó")
    st.info(t["mensaje"] + (" (simulación x10)" if factor > 1 else ""))

    origen = [p["origen_lat"], p["origen_lon"]]
    destino = [p["destino_lat"], p["destino_lon"]]
    pos = [t["lat"], t["lon"]]
    mapa = folium.Map(location=pos, zoom_start=13, control_scale=True)
    folium.Marker(origen, tooltip="Tienda / punto de inicio",
                  icon=folium.Icon(color="green", icon="home")).add_to(mapa)
    folium.Marker(destino, tooltip="Destino del cliente",
                  icon=folium.Icon(color="red", icon="flag")).add_to(mapa)
    folium.PolyLine([origen, destino], color="#0F5C4D", weight=4, opacity=0.7).add_to(mapa)
    if t["fase"] == "hacia_tienda":
        folium.PolyLine([pos, origen], color="#E8A33D", weight=3, dash_array="6 8").add_to(mapa)
    folium.Marker(pos, tooltip="Repartidor",
                  icon=folium.DivIcon(html=GATO_HTML, icon_size=(60, 40), icon_anchor=(30, 20))).add_to(mapa)
    mapa.fit_bounds([origen, destino, pos], padding=(30, 30))
    _render_folium(mapa, key, [], 300)
    st.caption("🟢 Tienda · 🔴 Destino · 🐱🚲 Repartidor (ubicación simulada)")


def botones_navegacion(p):
    """Abre la tienda o al cliente en Waze / Google Maps."""
    st.markdown("**🧭 Navegar con una app externa**")
    for etiqueta, lat, lon in (("🏪 Ir a la tienda / punto de inicio", p["origen_lat"], p["origen_lon"]),
                               ("🏠 Ir al destino del cliente", p["destino_lat"], p["destino_lon"])):
        st.caption(etiqueta)
        c1, c2 = st.columns(2)
        c1.link_button("Waze", tracking.enlace_waze(lat, lon), use_container_width=True)
        c2.link_button("Google Maps", tracking.enlace_google_maps(lat, lon), use_container_width=True)


# ------------------------------------------------------------------------ Chats
def _lista_mensajes(mensajes, mi_id, vacio):
    with st.container(height=260, border=True):
        if not mensajes:
            st.caption(vacio)
        for m in mensajes:
            propio = m["autor_id"] == mi_id
            with st.chat_message("user" if propio else "assistant"):
                st.markdown(f"**{'Tú' if propio else m['autor']}** · {m['creado'][11:16]}")
                st.write(m["texto"])


def _form_mensaje(clave):
    with st.form(clave, clear_on_submit=True):
        texto = st.text_input("Mensaje", placeholder="Escribe un mensaje…", label_visibility="collapsed")
        enviar = st.form_submit_button("Enviar", use_container_width=True)
    return texto if enviar else None


@st.fragment(run_every=4)
def chat_pedido(pedido_id):
    """Chat cliente ↔ repartidor (se actualiza solo cada 4 s)."""
    usuario = st.session_state.usuario
    mensajes = db.listar_mensajes_pedido(pedido_id, usuario["id"])
    _lista_mensajes(mensajes, usuario["id"], "Aún no hay mensajes. ¡Saluda para coordinar la entrega!")
    if db.estado_pedido(pedido_id) != "Aceptado":
        st.caption("El chat se cerró porque el viaje ya no está activo.")
        return
    texto = _form_mensaje(f"chat_pedido_{pedido_id}")
    if texto and texto.strip():
        try:
            db.enviar_mensaje_pedido(pedido_id, usuario["id"], texto)
            st.rerun(scope="fragment")
        except ValueError as error:
            st.error(str(error))


@st.fragment(run_every=4)
def chat_soporte(hilo_usuario_id):
    """Chat de soporte con el administrador (se actualiza solo cada 4 s)."""
    usuario = st.session_state.usuario
    mensajes = db.listar_mensajes_soporte(hilo_usuario_id, usuario["id"])
    vacio = ("Cuéntanos tu incidencia y el administrador te responderá aquí."
             if usuario["rol"] != "admin" else "Esta conversación aún no tiene mensajes.")
    _lista_mensajes(mensajes, usuario["id"], vacio)
    texto = _form_mensaje(f"chat_soporte_{hilo_usuario_id}")
    if texto and texto.strip():
        try:
            db.enviar_mensaje_soporte(hilo_usuario_id, usuario["id"], texto)
            st.rerun(scope="fragment")
        except ValueError as error:
            st.error(str(error))


# ---------------------------------------------------------------- Calificaciones
def form_calificacion(pedido_id, autor_rol, actor_id, a_quien):
    """Encuesta mutua tras la entrega: estrellas + comentario opcional."""
    previa = db.obtener_calificacion(pedido_id, autor_rol)
    if previa:
        st.success(f"Calificaste {a_quien} con {'⭐' * previa['estrellas']}. ¡Gracias!")
        return
    st.markdown(f"#### ⭐ Califica {a_quien}")
    with st.form(f"cal_{pedido_id}_{autor_rol}"):
        estrellas = st.radio("Calificación", [5, 4, 3, 2, 1], horizontal=True,
                             format_func=lambda n: "⭐" * n)
        comentario = st.text_area("Comentario (opcional)", max_chars=300)
        enviar = st.form_submit_button("Enviar calificación", use_container_width=True)
    if enviar:
        try:
            db.guardar_calificacion(pedido_id, autor_rol, actor_id, estrellas, comentario)
            st.rerun()
        except ValueError as error:
            st.error(str(error))


# --------------------------------------------------- Flujo del cliente: puja y viaje
def _resumen_pedido(p):
    with st.container(border=True):
        st.markdown(f"**Tienda:** {p['tienda_nombre']}")
        st.markdown(f"**Inicio:** {p['origen_nombre']}")
        st.markdown(f"**Destino:** {p['destino_nombre']}")
        st.caption(p["destino_senas"])
        st.write(f"Distancia: {p['distancia_km']:g} km · Peso: {p['peso_total']:g} kg")
        for item in p["items"]:
            st.write(f"• {item['cantidad']} × {item['nombre']} ({colones(item['precio'] * item['cantidad'])})")
        st.write(f"Productos: **{colones(p['subtotal'])}** · Envío: **{colones(p['oferta'])}** · "
                 f"Total: **{colones(p['subtotal'] + p['oferta'])}**")


def _ui_puja(p, usuario):
    restante = p["segundos_restantes"]
    st.progress(min(1.0, restante / p["puja_segundos"]),
                text=f"⏳ Tiempo de la puja: {fmt_mmss(restante)}")

    st.markdown("#### 💰 Tu oferta por el envío")
    diferencia = int(p["oferta"] - p["oferta_inicial"])
    st.metric("Tarifa actual", colones(p["oferta"]), delta=diferencia if diferencia else None)
    c1, c2 = st.columns(2)
    c1.button("➖ Bajar ₡100", key=f"baj_{p['id']}", on_click=db.ajustar_tarifa,
              args=(p["id"], usuario["id"], -db.PASO_TARIFA),
              disabled=p["oferta"] - db.PASO_TARIFA < p["tarifa_minima"], use_container_width=True)
    c2.button("➕ Aumentar ₡100", key=f"sub_{p['id']}", on_click=db.ajustar_tarifa,
              args=(p["id"], usuario["id"], db.PASO_TARIFA), use_container_width=True)
    st.caption(f"Mínimo sugerido: {colones(p['tarifa_minima'])} · Iniciaste en {colones(p['oferta_inicial'])}. "
               "Cada clic suma o resta ₡100 a la tarifa actual.")

    c3, c4 = st.columns(2)
    if c3.button("Cancelar pedido", key=f"can_{p['id']}", use_container_width=True):
        db.cancelar_pedido(p["id"], usuario["id"])
        st.rerun()
    if c4.button("🧪 Simular ofertas (demo)", key=f"sim_{p['id']}", use_container_width=True):
        db.simular_ofertas(p["id"])

    st.markdown("#### 📨 Ofertas de repartidores")
    ofertas = db.listar_ofertas(p["id"])
    if not ofertas:
        st.info("Esperando ofertas… Subir un poco la tarifa suele atraer más repartidores.")
    for o in ofertas:
        with st.container(border=True):
            st.markdown(f"**Repartidor: {o['repartidor_nombre']}** — Oferta: **{colones(o['monto'])}**")
            st.caption(f"{o['vehiculo']} · {texto_calificacion(o['promedio'], o['n_cal'])}")
            if st.button(f"Aceptar oferta de {colones(o['monto'])}", key=f"el_{o['id']}",
                         type="primary", use_container_width=True):
                if db.elegir_oferta(p["id"], o["id"], usuario["id"]):
                    st.rerun()
                else:
                    st.error("Esa oferta ya no está disponible.")


def _ui_timeout(p, usuario):
    minutos = max(1, p["puja_segundos"] // 60)
    st.warning(f"⏰ Pasaron {minutos} minutos y ningún repartidor aceptó ni elegiste una oferta.")
    st.markdown("**¿Qué quieres hacer con tu orden?**")
    c1, c2 = st.columns(2)
    if c1.button(f"🔁 Seguir esperando {minutos} min más", key=f"seg_{p['id']}", type="primary",
                 use_container_width=True):
        db.reactivar_pedido(p["id"], usuario["id"])
        st.rerun()
    if c2.button("❌ Cancelar la orden", key=f"cant_{p['id']}", use_container_width=True):
        db.cancelar_pedido(p["id"], usuario["id"])
        st.rerun()
    st.caption("Si sigues esperando, la orden se republica, el ciclo se reinicia y podrás modificar la tarifa de nuevo.")


def _ui_viaje(p, usuario):
    st.toggle("⏩ Acelerar simulación x10 (demo)", key="acel_demo")
    render_tracking(p, f"trk_{p['id']}")

    total = p["subtotal"] + p["oferta"]
    st.markdown("### 🛵 Datos del viaje")
    with st.container(border=True):
        promedio, n = db.promedio_repartidor(p["repartidor_id"])
        st.write(f"**Repartidor:** {p['repartidor_nombre']} · {p['repartidor_vehiculo']}")
        st.caption(texto_calificacion(promedio, n))
        st.write(f"**Ruta:** {p['origen_nombre']} → {p['destino_nombre']}")
        st.write(f"**Tarifa acordada:** {colones(p['oferta'])}")
    st.success(
        f"**Pago contra entrega:** Transfiere por SINPE Móvil al número "
        f"**{p['repartidor_sinpe']}** (a nombre de {p['repartidor_nombre']}), "
        f"o paga en efectivo al recibir tu paquete. Monto total: **{colones(total)}**."
    )
    st.caption("PetFletes no procesa tarjetas ni dinero: el pago es un acuerdo directo entre tú y el repartidor.")
    if st.button("✅ Ya recibí mi pedido", key=f"rec_{p['id']}", type="primary", use_container_width=True):
        if db.marcar_entregado_usuario(p["id"], usuario["id"]):
            st.balloons()
        st.rerun()


def _ui_entregado(p, usuario):
    st.success("¡Pedido entregado! Gracias por usar PetFletes 🐾")
    if p.get("entregado_en"):
        st.caption(f"Duración total de la orden: {fmt_duracion(duracion_entre(p['creado'], p['entregado_en']))}")
    form_calificacion(p["id"], "usuario", usuario["id"], f"al repartidor {p['repartidor_nombre']}")


def panel_pedido(pedido_id, estado_visto):
    """Panel del pedido (se refresca solo mientras la orden está activa)."""
    usuario = st.session_state.usuario
    p = db.obtener_pedido(pedido_id, usuario["id"])
    if p is None:
        st.error("Pedido no encontrado.")
        return
    if p["estado"] != estado_visto:
        st.rerun()  # el estado cambió: se redibuja la página completa (por ejemplo, para abrir el chat)

    st.subheader(f"{ESTADOS[p['estado']]} Pedido #{p['id']} — {p['estado']}")
    estado = p["estado"]
    if estado == "Buscando repartidor":
        _ui_puja(p, usuario)
    elif estado == "Tiempo agotado":
        _ui_timeout(p, usuario)
    elif estado == "Aceptado":
        _ui_viaje(p, usuario)
    elif estado == "Entregado":
        _ui_entregado(p, usuario)
    else:
        st.warning("Este pedido fue cancelado.")
    with st.expander("Ver detalle del pedido"):
        _resumen_pedido(p)
    if estado in ("Cancelado", "Tiempo agotado"):
        mostrar_mapa(puntos_ruta(p))


def vista_seguimiento():
    usuario = st.session_state.usuario
    st.header("📦 Seguimiento y entrega")
    pedidos = db.listar_pedidos_usuario(usuario["id"])
    if not pedidos:
        st.info("Aún no tienes pedidos. Crea uno en «Nuevo pedido».")
        return

    ids = [p["id"] for p in pedidos]
    por_id = {p["id"]: p for p in pedidos}
    indice = ids.index(st.session_state.pedido_id) if st.session_state.pedido_id in ids else 0
    seleccionado = st.selectbox(
        "Tus pedidos", ids, index=indice,
        format_func=lambda i: f"{ESTADOS[por_id[i]['estado']]} Pedido #{i} · {por_id[i]['tienda_nombre']} · {por_id[i]['estado']}",
    )
    pedido = por_id[seleccionado]
    activo = pedido["estado"] in ("Buscando repartidor", "Tiempo agotado", "Aceptado")
    st.fragment(run_every=3 if activo else None)(panel_pedido)(pedido["id"], pedido["estado"])

    if pedido["estado"] == "Aceptado":
        with st.expander("💬 Chat con el repartidor", expanded=True):
            if pedido["repartidor_usuario_id"] is None:
                st.caption("Este repartidor es una cuenta de demostración y no responderá mensajes.")
            chat_pedido(pedido["id"])
        st.caption("¿Algún problema con el viaje? Reporta la incidencia en «Soporte».")


# -------------------------------------------------------------- Panel del repartidor
def _tarjeta_pedido(p):
    st.markdown(f"**Pedido #{p['id']} · {p['tienda_nombre']}**")
    st.write(f"{p['origen_nombre']} → {p['destino_nombre']}")
    st.caption(f"{p['distancia_km']:g} km · {p['peso_total']:g} kg · Cliente: {p['cliente_nombre']}")


@st.fragment(run_every=4)
def _lista_disponibles():
    usuario = st.session_state.usuario
    rid = usuario["repartidor_id"]
    pedidos = db.listar_pedidos_disponibles()
    if not pedidos:
        st.info("No hay pedidos con puja abierta en este momento. La lista se actualiza sola.")
    for p in pedidos:
        with st.container(border=True):
            _tarjeta_pedido(p)
            promedio, n = db.promedio_usuario(p["usuario_id"])
            st.caption(f"Cliente: {texto_calificacion(promedio, n)}")
            st.progress(min(1.0, p["segundos_restantes"] / p["puja_segundos"]),
                        text=f"⏳ Cierra en {fmt_mmss(p['segundos_restantes'])}")
            st.markdown(f"Tarifa del cliente: **{colones(p['oferta'])}** "
                        f"(mínimo sugerido {colones(p['tarifa_minima'])}) · Ofertas recibidas: {p['n_ofertas']}")
            with st.expander("Ver ruta y productos"):
                st.caption(f"Señas: {p['destino_senas']}")
                for item in p["items"]:
                    st.write(f"• {item['cantidad']} × {item['nombre']}")
                mostrar_mapa(puntos_ruta(p))

            mia = db.obtener_oferta_repartidor(p["id"], rid)
            if mia:
                st.info(f"Tu oferta actual: {colones(mia['monto'])} — esperando que el cliente elija.")
            col_monto, col_btn = st.columns([2, 1])
            monto = col_monto.number_input("Tu oferta (₡)", min_value=500, step=100,
                                           value=int(mia["monto"] if mia else p["oferta"]),
                                           key=f"of_{p['id']}", label_visibility="collapsed")
            if col_btn.button("Actualizar" if mia else "Ofertar", key=f"env_{p['id']}", type="primary",
                              use_container_width=True):
                try:
                    db.enviar_oferta(p["id"], rid, monto)
                    st.toast("Oferta enviada ✅")
                    st.rerun(scope="fragment")
                except ValueError as error:
                    st.error(str(error))


def vista_disponibles():
    usuario = st.session_state.usuario
    st.header("🛵 Pedidos disponibles")
    if usuario["repartidor_id"] is None:
        st.error("Tu cuenta no tiene perfil de repartidor.")
        return
    st.caption("Envía tu oferta: el cliente verá todas las ofertas y elegirá la que prefiera.")
    _lista_disponibles()


@st.fragment(run_every=5)
def tracking_repartidor(pedido_id):
    rid = st.session_state.usuario["repartidor_id"]
    p = db.obtener_pedido_repartidor(pedido_id, rid)
    if p is None or p["estado"] != "Aceptado":
        st.rerun()
        return
    render_tracking(p, f"trk_rep_{pedido_id}")


def vista_entregas():
    usuario = st.session_state.usuario
    st.header("📋 Mis entregas")
    rid = usuario["repartidor_id"]
    if rid is None:
        st.error("Tu cuenta no tiene perfil de repartidor.")
        return
    col_a, col_b = st.columns(2)
    col_a.button("🔄 Actualizar lista", use_container_width=True)
    col_b.toggle("⏩ Acelerar simulación x10 (demo)", key="acel_demo")

    entregas = db.listar_entregas_repartidor(rid)
    promedio, n = db.promedio_repartidor(rid)
    m1, m2, m3 = st.columns(3)
    m1.metric("Entregas", sum(1 for e in entregas if e["estado"] == "Entregado"))
    m2.metric("Cobrado", colones(sum(e["oferta"] for e in entregas if e["estado"] == "Entregado")))
    m3.metric("Calificación", f"{promedio:.1f} ⭐" if n else "—")

    if not entregas:
        st.info("Aún no tienes entregas. Envía ofertas en «Pedidos disponibles».")
    for e in entregas:
        with st.container(border=True):
            st.markdown(f"{ESTADOS[e['estado']]} **{e['estado']}**")
            _tarjeta_pedido(e)
            st.write(f"Cliente: {e['cliente_nombre']} · Tel: {e['cliente_telefono'] or '—'}")
            st.caption(f"Señas: {e['destino_senas']}")
            st.write(f"Cobrar: **{colones(e['subtotal'] + e['oferta'])}** "
                     f"(productos {colones(e['subtotal'])} + envío {colones(e['oferta'])})")
            if e["estado"] == "Aceptado":
                tracking_repartidor(e["id"])
                botones_navegacion(e)
                with st.expander("💬 Chat con el cliente"):
                    chat_pedido(e["id"])
                if st.button("📦 Marcar como entregado", key=f"ent_{e['id']}", type="primary",
                             use_container_width=True):
                    db.marcar_entregado_repartidor(e["id"], rid)
                    st.rerun()
            elif e["estado"] == "Entregado":
                form_calificacion(e["id"], "repartidor", rid, f"al cliente {e['cliente_nombre']}")


# ------------------------------------------------------ Módulo 2: Feed comunitario
def vista_comunidad():
    usuario = st.session_state.usuario
    st.header("👥 Comunidad")
    st.caption("Compartí ofertas de tiendas, tips y preguntas con otros dueños de mascotas.")

    with st.form("form_publicacion", clear_on_submit=True):
        tipo = st.selectbox("Tipo de publicación", TIPOS_PUBLICACION)
        titulo = st.text_input("Título", max_chars=80)
        contenido = st.text_area("Contenido", max_chars=500)
        publicar = st.form_submit_button("Publicar", type="primary", use_container_width=True)
    if publicar:
        if not titulo.strip() or not contenido.strip():
            st.error("Completá el título y el contenido.")
        else:
            db.crear_publicacion(usuario["id"], tipo, titulo, contenido)
            st.success("¡Publicación creada!")

    st.subheader("Últimas publicaciones")
    filtro = st.selectbox("Filtrar", ["Todas"] + TIPOS_PUBLICACION)
    publicaciones = db.listar_publicaciones(None if filtro == "Todas" else filtro)
    if not publicaciones:
        st.info("Todavía no hay publicaciones.")
    for pub in publicaciones:
        with st.container(border=True):
            st.markdown(f"{ICONOS_TIPO.get(pub['tipo'], '📝')} **{pub['titulo']}**")
            st.write(pub["contenido"])
            st.caption(f"{pub['tipo']} · por {pub['autor']} · {pub['creado']}")


# ------------------------------------------------------- Módulo 3: Mapa interactivo
def vista_mapa():
    usuario = st.session_state.usuario
    st.header("🗺️ Mapa")
    tiendas = db.listar_tiendas()
    pedidos = db.listar_pedidos_usuario(usuario["id"])

    opciones = {0: "Solo tiendas"}
    for p in pedidos:
        opciones[p["id"]] = f"Pedido #{p['id']} · {p['origen_nombre']} → {p['destino_nombre']}"
    elegido = st.selectbox("Qué querés ver", list(opciones), format_func=lambda k: opciones[k])

    puntos = [{"lat": t["lat"], "lon": t["lon"], "color": COLOR_TIENDA, "size": 250} for t in tiendas]
    if elegido:
        puntos = puntos_ruta(next(p for p in pedidos if p["id"] == elegido))
    mostrar_mapa(puntos)

    st.subheader("Tiendas disponibles")
    for t in tiendas:
        with st.container(border=True):
            st.markdown(f"**{t['nombre']}**")
            st.caption(f"📍 {t['direccion']}")
            st.write(t["descripcion"])


# ------------------------------------------------------------ Soporte y centro de control
def vista_soporte():
    usuario = st.session_state.usuario
    st.header("💬 Soporte")
    if usuario["rol"] == "admin":
        hilos = db.listar_hilos_soporte()
        pendientes = sum(1 for h in hilos if h["pendiente"])
        st.caption(f"Conversaciones: {len(hilos)} · Pendientes de responder: {pendientes}")
        if not hilos:
            st.info("Aún no hay incidencias reportadas.")
            return
        sel = st.selectbox(
            "Conversación", [h["id"] for h in hilos],
            format_func=lambda i: next(
                f"{'🔴' if h['pendiente'] else '🟢'} {h['nombre']} ({h['rol']}) · {h['ultimo_creado'][5:16]}"
                for h in hilos if h["id"] == i))
        chat_soporte(sel)
        return
    st.caption("Reporta incidencias al administrador de PetFletes; te responderá por este chat.")
    chat_soporte(usuario["id"])


def _panel_admin():
    s = db.estadisticas_admin()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("En curso", s["buscando"] + s["agotados"] + s["aceptados"])
    c2.metric("Entregados", s["entregados"])
    c3.metric("Usuarios", s["usuarios"])
    c4.metric("Repartidores", s["repartidores"])
    pendientes = sum(1 for h in db.listar_hilos_soporte() if h["pendiente"])
    st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')} · "
               f"Pujando: {s['buscando']} · Tiempo agotado: {s['agotados']} · "
               f"En viaje: {s['aceptados']} · 💬 Soporte pendiente: {pendientes}")

    tab_pedidos, tab_repartidores, tab_usuarios = st.tabs(
        ["📦 Pedidos en curso", "🛵 Repartidores", "🧑 Usuarios"])

    with tab_pedidos:
        pedidos = db.listar_pedidos_admin(solo_en_curso=True)
        if not pedidos:
            st.info("No hay pedidos en curso.")
        else:
            st.dataframe(pd.DataFrame([{
                "Pedido": p["id"],
                "Estado": f"{ESTADOS[p['estado']]} {p['estado']}",
                "Cliente": p["cliente_nombre"],
                "Tienda": p["tienda_nombre"],
                "Destino": p["destino_nombre"],
                "Repartidor": p["repartidor_nombre"] or "—",
                "Ofertas": p["n_ofertas"],
                "Envío": colones(p["oferta"]),
                "Creado": p["creado"],
            } for p in pedidos]), hide_index=True)

            st.markdown("**Todas las rutas en curso**")
            puntos = []
            for p in pedidos:
                puntos.extend(puntos_ruta(p))
            mostrar_mapa(puntos)

            sel = st.selectbox("Ver detalle del pedido", [p["id"] for p in pedidos],
                               format_func=lambda i: f"Pedido #{i}")
            p = next(x for x in pedidos if x["id"] == sel)
            with st.container(border=True):
                st.markdown(f"**Pedido #{p['id']}** — {ESTADOS[p['estado']]} {p['estado']}")
                st.write(f"Cliente: {p['cliente_nombre']} · Tel: {p['cliente_telefono'] or '—'}")
                st.write(f"Ruta: {p['origen_nombre']} → {p['destino_nombre']}")
                st.caption(f"Señas: {p['destino_senas']}")
                st.write(f"Repartidor: {p['repartidor_nombre'] or 'sin asignar'}"
                         + (f" · SINPE {p['repartidor_sinpe']}" if p["repartidor_sinpe"] else ""))
                for item in p["items"]:
                    st.write(f"• {item['cantidad']} × {item['nombre']}")
                st.write(f"Productos {colones(p['subtotal'])} · Envío {colones(p['oferta'])} · "
                         f"Distancia {p['distancia_km']:g} km · Ofertas pendientes: {p['n_ofertas']}")
            if p["estado"] == "Aceptado":
                render_tracking(p, f"adm_trk_{p['id']}")
            else:
                mostrar_mapa(puntos_ruta(p))

    with tab_repartidores:
        repartidores = db.listar_repartidores_admin()
        st.write(f"**{len(repartidores)}** repartidores en la plataforma")
        st.dataframe(pd.DataFrame([{
            "ID": r["id"], "Nombre": r["nombre"], "Correo": r["email"] or "—",
            "Teléfono": r["telefono"] or "—", "SINPE": r["sinpe"], "Vehículo": r["vehiculo"],
            "Tipo": r["tipo"], "Registrado": r["registrado"] or "—",
            "En curso": r["en_curso"], "Entregas": r["entregas"],
            "Calificación": f"{r['calificacion']} ({r['n_cal']})" if r["n_cal"] else "—",
        } for r in repartidores]), hide_index=True)

    with tab_usuarios:
        usuarios = db.listar_usuarios_admin()
        st.write(f"**{len(usuarios)}** usuarios registrados")
        st.dataframe(pd.DataFrame([{
            "ID": u["id"], "Nombre": u["nombre"], "Correo": u["email"],
            "Teléfono": u["telefono"] or "—", "Registrado": u["registrado"], "Pedidos": u["pedidos"],
            "Calificación": f"{u['calificacion']} ({u['n_cal']})" if u["n_cal"] else "—",
        } for u in usuarios]), hide_index=True)


def vista_admin():
    st.header("🛠️ Centro de control")
    col_a, col_b = st.columns([2, 1])
    auto = col_a.toggle("Actualizar automáticamente (cada 10 s)", value=False)
    col_b.button("🔄 Actualizar ahora")
    st.toggle("⏩ Acelerar simulación x10 (demo)", key="acel_demo")
    st.fragment(run_every=10 if auto else None)(_panel_admin)()


# ------------------------------------------------------------------- Principal
NAVEGACION = {
    "usuario": {
        "🛒 Nuevo pedido": vista_pedidos,
        "📦 Seguimiento y entrega": vista_seguimiento,
        "💬 Soporte": vista_soporte,
        "👥 Comunidad": vista_comunidad,
        "🗺️ Mapa": vista_mapa,
    },
    "repartidor": {
        "🛵 Pedidos disponibles": vista_disponibles,
        "📋 Mis entregas": vista_entregas,
        "💬 Soporte": vista_soporte,
        "👥 Comunidad": vista_comunidad,
    },
    "admin": {
        "🛠️ Centro de control": vista_admin,
        "💬 Soporte": vista_soporte,
        "👥 Comunidad": vista_comunidad,
    },
}


def main():
    for clave, valor in {"usuario": None, "carrito": {}, "tienda_carrito": None,
                         "pedido_id": None}.items():
        st.session_state.setdefault(clave, valor)

    if st.session_state.usuario is None:
        vista_auth()
        return

    usuario = st.session_state.usuario
    vistas = NAVEGACION[usuario["rol"]]
    secciones = list(vistas)

    if "ir_a" in st.session_state:
        st.session_state["nav"] = st.session_state.pop("ir_a")
    if st.session_state.get("nav") not in secciones:
        st.session_state.pop("nav", None)

    with st.sidebar:
        st.title("🐾 PetFletes")
        st.write(f"Hola, **{usuario['nombre']}**")
        st.caption(f"Cuenta: {NOMBRE_ROL[usuario['rol']]}")
        if usuario["rol"] == "usuario":
            promedio, n = db.promedio_usuario(usuario["id"])
        elif usuario["rol"] == "repartidor" and usuario["repartidor_id"]:
            promedio, n = db.promedio_repartidor(usuario["repartidor_id"])
        else:
            promedio, n = None, 0
        if n:
            st.caption(f"Tu calificación: {texto_calificacion(promedio, n)}")
        seccion = st.radio("Navegación", secciones, key="nav")
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    vistas[seccion]()


main()
