import streamlit as st
from models import SessionLocal, Empleado, Licencia, Puesto, Usuario
import pandas as pd
from sqlalchemy.orm import joinedload
import networkx as nx
import matplotlib.pyplot as plt
import tempfile
import os

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
def obtener_usuarios():
    db = SessionLocal()
    usuarios = db.query(Usuario).all()
    db.close()
    return usuarios

def autenticar_usuario(username, password):
    usuarios = obtener_usuarios()
    return next((u for u in usuarios if u.username == username and u.password == password), None)

def iniciar_sesion():
    st.title("🔐 Iniciar sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        usuario = autenticar_usuario(username, password)
        if usuario:
            st.session_state["usuario"] = {
                "id": usuario.id,
                "username": usuario.username,
                "rol": usuario.rol
            }
            st.success(f"Bienvenido, {usuario.username}")
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

def cerrar_sesion():
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.pop("usuario", None)
        st.rerun()
# Agregá esta función acá arriba:
def generar_reporte_empleados_pdf(empleados):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp.name, pagesize=letter)
    width, height = letter
    y = height - 50

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Reporte de Empleados")
    y -= 30
    c.setFont("Helvetica", 10)

    for emp in empleados:
        texto = f"{emp.apellido}, {emp.nombre} | DNI: {emp.dni} | Puesto: {emp.puesto} | Estado: {emp.estado}"
        c.drawString(50, y, texto)
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    return temp.name

st.set_page_config(page_title="RRHH", layout="wide")
if "usuario" not in st.session_state:
    iniciar_sesion()
    st.stop()
else:
    usuario_actual = st.session_state["usuario"]
    st.sidebar.markdown(f"👤 Usuario: **{usuario_actual['username']}** ({usuario_actual['rol']})")
    cerrar_sesion()

# ======================== FUNCIONES BASE DE DATOS ==========================
def obtener_empleados():
    db = SessionLocal()
    empleados = db.query(Empleado).all()
    db.close()
    return empleados

def obtener_licencias():
    db = SessionLocal()
    licencias = db.query(Licencia).options(joinedload(Licencia.empleado)).all()
    db.close()
    return licencias

def obtener_puestos():
    db = SessionLocal()
    puestos = db.query(Puesto).all()
    db.close()
    return puestos

def agregar_empleado(**kwargs):
    db = SessionLocal()
    nuevo = Empleado(**kwargs)
    db.add(nuevo)
    db.commit()
    db.close()

def editar_empleado(empleado_id, **kwargs):
    db = SessionLocal()
    empleado = db.query(Empleado).filter_by(id=empleado_id).first()
    for key, value in kwargs.items():
        setattr(empleado, key, value)
    db.commit()
    db.close()

def eliminar_empleado(empleado_id):
    db = SessionLocal()
    empleado = db.query(Empleado).filter_by(id=empleado_id).first()
    if empleado:
        db.delete(empleado)
        db.commit()
    db.close()

def agregar_licencia(empleado_id, tipo, fecha_inicio, fecha_fin, observaciones):
    db = SessionLocal()
    nueva = Licencia(
        empleado_id=empleado_id,
        tipo=tipo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        observaciones=observaciones
    )
    db.add(nueva)
    db.commit()
    db.close()

def editar_licencia(licencia_id, tipo, fecha_inicio, fecha_fin, observaciones):
    db = SessionLocal()
    licencia = db.query(Licencia).filter_by(id=licencia_id).first()
    if licencia:
        licencia.tipo = tipo
        licencia.fecha_inicio = fecha_inicio
        licencia.fecha_fin = fecha_fin
        licencia.observaciones = observaciones
        db.commit()
    db.close()

def eliminar_licencia(licencia_id):
    db = SessionLocal()
    licencia = db.query(Licencia).filter_by(id=licencia_id).first()
    if licencia:
        db.delete(licencia)
        db.commit()
    db.close()

def agregar_puesto(nombre, descripcion, jefe_id=None):
    db = SessionLocal()
    nuevo = Puesto(nombre=nombre, descripcion=descripcion, jefe_id=jefe_id)
    db.add(nuevo)
    db.commit()
    db.close()

def editar_puesto(puesto_id, nombre, descripcion, jefe_id):
    db = SessionLocal()
    puesto = db.query(Puesto).filter_by(id=puesto_id).first()
    if puesto:
        puesto.nombre = nombre
        puesto.descripcion = descripcion
        puesto.jefe_id = jefe_id
        db.commit()
    db.close()

def eliminar_puesto(puesto_id):
    db = SessionLocal()
    puesto = db.query(Puesto).filter_by(id=puesto_id).first()
    if puesto:
        db.delete(puesto)
        db.commit()
    db.close()

# ========================= INTERFAZ STREAMLIT =============================
st.sidebar.title("RRHH")

menu_principal = st.sidebar.radio("Menú", ["Inicio", "Gestión Nómina", "Asesoramiento"])

if menu_principal == "Inicio":
    st.title("🏠 Bienvenido al sistema RRHH")
    st.markdown("Accedé a las funciones del sistema desde el menú lateral.")
    st.title("🏠 Dashboard de RRHH")

    empleados = obtener_empleados()
    licencias = obtener_licencias()
    puestos = obtener_puestos()

    total_empleados = len(empleados)
    activos = sum(1 for e in empleados if e.estado == "Activo")
    inactivos = total_empleados - activos
    total_licencias = len(licencias)
    total_puestos = len(puestos)

    col1, col2, col3 = st.columns(3)
    col1.metric("👥 Empleados activos", activos)
    col2.metric("🛌 Licencias registradas", total_licencias)
    col3.metric("🏷️ Puestos definidos", total_puestos)

    st.markdown("---")
    st.markdown("Bienvenido al sistema. Usá el menú lateral para navegar por las funcionalidades.")

if menu_principal == "Gestión Nómina":
    seccion = st.sidebar.radio("Administración del Personal", ["Empleados", "Licencias", "Puestos", "Organigrama"])

    if seccion == "Empleados":
        st.title("👥 Gestión de Empleados")
        empleados = obtener_empleados()
        puestos = obtener_puestos()

        # Filtros visuales
        with st.container():
            st.subheader("🔍 Filtros")
            col1, col2, col3 = st.columns(3)

            opciones_estado = ["Todos"] + sorted(list(set(e.estado for e in empleados)))
            opciones_cc = ["Todos"] + sorted(list(set(e.centro_costo for e in empleados)))
            opciones_puesto = ["Todos"] + sorted(list(set(e.puesto for e in empleados)))

            with col1:
                filtro_estado = st.selectbox("Estado", opciones_estado, index=0)
            with col2:
                filtro_centro_costo = st.selectbox("Centro de Costo", opciones_cc, index=0)
            with col3:
                filtro_puesto = st.selectbox("Puesto", opciones_puesto, index=0)

        # Aplicar filtros
        empleados_filtrados = empleados
        if filtro_estado != "Todos":
            empleados_filtrados = [e for e in empleados_filtrados if e.estado == filtro_estado]
        if filtro_centro_costo != "Todos":
            empleados_filtrados = [e for e in empleados_filtrados if e.centro_costo == filtro_centro_costo]
        if filtro_puesto != "Todos":
            empleados_filtrados = [e for e in empleados_filtrados if e.puesto == filtro_puesto]
            

        df = pd.DataFrame([{k: getattr(e, k) for k in [
            "apellido", "nombre", "legajo", "genero", "estado_civil", "fecha_nacimiento",
            "dni", "direccion", "telefono", "centro_costo", "puesto",
            "remuneracion_bruta", "estado", "fecha_alta", "fecha_baja"
        ]} for e in empleados_filtrados])
        st.dataframe(df, use_container_width=True)

        if st.button("📄 Descargar PDF de empleados filtrados"):
            if empleados_filtrados:
                path_pdf = generar_reporte_empleados_pdf(empleados_filtrados)
                with open(path_pdf, "rb") as file:
                    st.download_button(
                        label="Descargar PDF",
                        data=file,
                        file_name="reporte_empleados_filtrados.pdf",
                        mime="application/pdf"
                    )
                os.remove(path_pdf)
            else:
                st.warning("No hay empleados filtrados para incluir en el PDF.")
        with st.expander("➕ Agregar nuevo empleado"):
            datos = {}
            datos["apellido"] = st.text_input("Apellido", key="nuevo_apellido")
            datos["nombre"] = st.text_input("Nombre", key="nuevo_nombre")
            datos["legajo"] = st.text_input("Legajo", key="nuevo_legajo")
            datos["genero"] = st.selectbox("Género", ["Masculino", "Femenino", "Otro"], key="nuevo_genero")
            datos["estado_civil"] = st.selectbox("Estado Civil", ["Soltero/a", "Casado/a", "Divorciado/a", "Otro"], key="nuevo_estado_civil")
            datos["fecha_nacimiento"] = str(st.date_input("Fecha de Nacimiento", key="nuevo_fecha_nacimiento"))
            datos["dni"] = st.text_input("DNI", key="nuevo_dni")
            datos["direccion"] = st.text_input("Dirección", key="nuevo_direccion")
            datos["telefono"] = st.text_input("Teléfono", key="nuevo_telefono")
            datos["centro_costo"] = st.text_input("Centro de Costo", key="nuevo_centro_costo")
            datos["puesto"] = st.selectbox("Puesto", [p.nombre for p in puestos], key="nuevo_puesto")
            datos["remuneracion_bruta"] = st.number_input("Remuneración Bruta", min_value=0, key="nuevo_remuneracion")
            datos["estado"] = st.selectbox("Estado", ["Activo", "Inactivo"], key="nuevo_estado")
            datos["fecha_alta"] = str(st.date_input("Fecha de Alta", key="nuevo_fecha_alta"))
            datos["fecha_baja"] = None
            opciones_jefes = {"Ninguno": None}
            for p in puestos:
                opciones_jefes[p.nombre] = p.id
            jefe_nombre = st.selectbox("Puesto superior", list(opciones_jefes.keys()), key="nuevo_jefe")
            datos["jefe_id"] = opciones_jefes[jefe_nombre]

            if st.button("Agregar empleado"):
                agregar_empleado(**datos)
                st.success("Empleado agregado correctamente.")

        with st.expander("✏️ Editar empleado"):
            if empleados:
                opciones = {f"{e.id} - {e.apellido}, {e.nombre}": e.id for e in empleados}
                seleccionado = st.selectbox("Seleccionar empleado", list(opciones.keys()), key="editar_empleado")
                eid = opciones[seleccionado]
                emp = next(e for e in empleados if e.id == eid)

                datos = {
                    "apellido": st.text_input("Apellido", value=emp.apellido, key=f"edit_apellido_{eid}"),
                    "nombre": st.text_input("Nombre", value=emp.nombre, key=f"edit_nombre_{eid}"),
                    "legajo": st.text_input("Legajo", value=emp.legajo, key=f"edit_legajo_{eid}"),
                    "genero": st.selectbox("Género", ["Masculino", "Femenino", "Otro"], index=["Masculino", "Femenino", "Otro"].index(emp.genero), key=f"edit_genero_{eid}"),
                    "estado_civil": st.selectbox("Estado Civil", ["Soltero/a", "Casado/a", "Divorciado/a", "Otro"], index=["Soltero/a", "Casado/a", "Divorciado/a", "Otro"].index(emp.estado_civil), key=f"edit_estado_civil_{eid}"),
                    "fecha_nacimiento": str(st.date_input("Fecha de Nacimiento", value=pd.to_datetime(emp.fecha_nacimiento), key=f"edit_fecha_nac_{eid}")),
                    "dni": st.text_input("DNI", value=emp.dni, key=f"edit_dni_{eid}"),
                    "direccion": st.text_input("Dirección", value=emp.direccion, key=f"edit_direccion_{eid}"),
                    "telefono": st.text_input("Teléfono", value=emp.telefono, key=f"edit_telefono_{eid}"),
                    "centro_costo": st.text_input("Centro de Costo", value=emp.centro_costo, key=f"edit_cc_{eid}"),
                    "puesto": st.text_input("Puesto", value=emp.puesto, key=f"edit_puesto_{eid}"),
                    "remuneracion_bruta": st.number_input("Remuneración Bruta", value=emp.remuneracion_bruta, min_value=0, key=f"edit_remu_{eid}"),
                    "estado": st.selectbox("Estado", ["Activo", "Inactivo"], index=0 if emp.estado == "Activo" else 1, key=f"edit_estado_{eid}"),
                    "fecha_alta": str(st.date_input("Fecha de Alta", value=pd.to_datetime(emp.fecha_alta), key=f"edit_fecha_alta_{eid}")),
                    "fecha_baja": str(emp.fecha_baja) if emp.fecha_baja else None,
                }

                opciones_jefes = {"Ninguno": None}
                for p in puestos:
                     opciones_jefes[p.nombre] = p.id

                jefe_valor = next((k for k, v in opciones_jefes.items() if v == emp.jefe_id), "Ninguno")
                jefe_nombre = st.selectbox("Puesto superior", list(opciones_jefes.keys()), index=list(opciones_jefes.keys()).index(jefe_valor), key=f"edit_jefe_{eid}")
                datos["jefe_id"] = opciones_jefes[jefe_nombre]
                

                if st.button("Guardar cambios", key=f"btn_guardar_{eid}"):
                    editar_empleado(eid, **datos)
                    st.success("Empleado actualizado")
            else:
                st.info("No hay empleados para editar.")

        with st.expander("🗑️ Eliminar empleado"):
            if empleados:
                opciones = {f"{e.id} - {e.apellido}, {e.nombre}": e.id for e in empleados}
                seleccionado = st.selectbox("Seleccionar empleado", list(opciones.keys()), key="eliminar_empleado")
                eid = opciones[seleccionado]
                if st.button("Eliminar empleado"):
                    eliminar_empleado(eid)
                    st.success("Empleado eliminado")
            else:
                st.info("No hay empleados para eliminar.")
    
    if seccion == "Licencias":
        st.title("📅 Registro de Licencias")
        licencias = obtener_licencias()
        empleados = obtener_empleados()

        data = [
            {
                "ID": l.id,
                "Empleado": f"{l.empleado.apellido}, {l.empleado.nombre}" if l.empleado else "-",
                "Tipo": l.tipo,
                "Desde": l.fecha_inicio,
                "Hasta": l.fecha_fin,
                "Observaciones": l.observaciones
            } for l in licencias
        ]
        st.dataframe(pd.DataFrame(data), use_container_width=True)

        with st.expander("➕ Agregar licencia"):
            opciones = {f"{e.apellido}, {e.nombre}": e.id for e in empleados}
            seleccionado = st.selectbox("Empleado", list(opciones.keys()), key="lic_nueva")
            tipo = st.text_input("Tipo de licencia")
            desde = st.date_input("Desde")
            hasta = st.date_input("Hasta")
            observaciones = st.text_area("Observaciones")
            if st.button("Guardar licencia"):
                agregar_licencia(opciones[seleccionado], tipo, str(desde), str(hasta), observaciones)
                st.success("Licencia registrada")

        with st.expander("✏️ Editar licencia"):
            if licencias:
                opciones = {f"{l.id} - {l.tipo} ({l.empleado.nombre if l.empleado else 'Sin asignar'})": l.id for l in licencias}
                seleccion = st.selectbox("Seleccionar licencia", list(opciones.keys()), key="lic_edit")
                lid = opciones[seleccion]
                lic = next(l for l in licencias if l.id == lid)

                tipo_edit = st.text_input("Tipo", value=lic.tipo)
                desde_edit = st.date_input("Desde", value=pd.to_datetime(lic.fecha_inicio))
                hasta_edit = st.date_input("Hasta", value=pd.to_datetime(lic.fecha_fin))
                obs_edit = st.text_area("Observaciones", value=lic.observaciones)

                if st.button("Guardar cambios licencia"):
                    editar_licencia(lid, tipo_edit, str(desde_edit), str(hasta_edit), obs_edit)
                    st.success("Licencia actualizada")
            else:
                st.info("No hay licencias para editar.")

        with st.expander("🗑️ Eliminar licencia"):
            if licencias:
                opciones = {f"{l.id} - {l.tipo} ({l.empleado.nombre if l.empleado else 'Sin asignar'})": l.id for l in licencias}
                seleccion = st.selectbox("Seleccionar licencia", list(opciones.keys()), key="lic_eliminar")
                if st.button("Eliminar licencia"):
                    eliminar_licencia(opciones[seleccion])
                    st.success("Licencia eliminada")
            else:
                st.info("No hay licencias registradas.")


    if seccion == "Puestos":
        st.title("🏷️ Gestión de Puestos")
        puestos = obtener_puestos()
        df = pd.DataFrame([p.__dict__ for p in puestos]).drop(columns=["_sa_instance_state"], errors='ignore')
        st.dataframe(df, use_container_width=True)

        with st.expander("➕ Crear nuevo puesto"):
            nombre = st.text_input("Nombre del puesto")
            descripcion = st.text_area("Descripción")
            opciones_jefes = {"Sin jefe": None}
            for p in puestos:
                opciones_jefes[p.nombre] = p.id
            jefe_nombre = st.selectbox("Depende de", list(opciones_jefes.keys()))
            if st.button("Guardar puesto"):
                agregar_puesto(nombre, descripcion, opciones_jefes[jefe_nombre])
                st.success("Puesto creado")

        with st.expander("✏️ Editar puesto"):
            if puestos:
                opciones = {f"{p.id} - {p.nombre}": p.id for p in puestos}
                seleccionado = st.selectbox("Seleccionar puesto", list(opciones.keys()), key="editar_puesto")
                pid = int(seleccionado.split(" - ")[0])
                puesto = next(p for p in puestos if p.id == pid)

                nuevo_nombre = st.text_input("Nuevo nombre", value=puesto.nombre, key="nuevo_nombre_puesto")
                nueva_desc = st.text_area("Nueva descripción", value=puesto.descripcion, key="nueva_desc_puesto")
                opciones_jefes = {"Sin jefe": None}
                for p in puestos:
                    if p.id != puesto.id:
                        opciones_jefes[p.nombre] = p.id
                jefe_actual = next((k for k, v in opciones_jefes.items() if v == puesto.jefe_id), "Sin jefe")
                nuevo_jefe = st.selectbox("Nuevo superior", list(opciones_jefes.keys()), index=list(opciones_jefes.keys()).index(jefe_actual), key="nuevo_jefe_puesto")

                if st.button("Guardar cambios puesto"):
                    editar_puesto(pid, nuevo_nombre, nueva_desc, opciones_jefes[nuevo_jefe])
                    st.success("Puesto actualizado")

        with st.expander("🗑️ Eliminar puesto"):
            if puestos:
                opciones = {f"{p.id} - {p.nombre}": p.id for p in puestos}
                seleccionado = st.selectbox("Puesto a eliminar", list(opciones.keys()), key="eliminar_puesto")
                if seleccionado:
                    pid = int(seleccionado.split(" - ")[0])
                    if st.button("Eliminar puesto"):
                        eliminar_puesto(pid)
                        st.success("Puesto eliminado")
            else:
                st.info("No hay puestos registrados.")

    if seccion == "Organigrama":
        st.title("🏢 Organigrama Jerárquico de Puestos")
        puestos = obtener_puestos()

        if puestos:
            G = nx.DiGraph()
            etiquetas = {}

            # Crear nodos y aristas
            for puesto in puestos:
                G.add_node(puesto.id)
                etiquetas[puesto.id] = puesto.nombre
                if puesto.jefe_id:
                    G.add_edge(puesto.jefe_id, puesto.id)

            # Calcular niveles jerárquicos
            niveles = {}
            def asignar_niveles(p, nivel=0):
                niveles[p.id] = nivel
                hijos = [x for x in puestos if x.jefe_id == p.id]
                for hijo in hijos:
                    asignar_niveles(hijo, nivel + 1)

            raices = [p for p in puestos if p.jefe_id is None]
            for raiz in raices:
                asignar_niveles(raiz)

            # Posicionar: mismo nivel → misma fila (mismo Y), separados horizontalmente (X)
            posiciones = {}
            x_counter = {}

            for nivel in sorted(set(niveles.values())):
                puestos_nivel = [pid for pid, lvl in niveles.items() if lvl == nivel]
                for idx, pid in enumerate(puestos_nivel):
                    posiciones[pid] = (idx, -nivel)

            # Dibujar el organigrama
            fig, ax = plt.subplots(figsize=(10, 6))
            nx.draw(
                G,
                pos=posiciones,
                labels=etiquetas,
                with_labels=True,
                node_color="lightblue",
                node_size=3000,
                font_size=10,
                font_weight='bold',
                edge_color="gray",
                ax=ax
            )
            st.pyplot(fig)
        else:
            st.info("No hay puestos cargados aún.")
if menu_principal == "Asesoramiento":
    st.title("🧠 Asesoramiento Interactivo")

    st.markdown("""
    Bienvenido al módulo de Asesoramiento. Aquí podrás acceder a:

    - 📄 Plantillas interactivas para documentos, procesos y reportes de RRHH.
    - 🤖 En el futuro, vas a poder usar un Asistente IA con memoria y contexto para responder dudas de gestión, normativa, o ayudarte con decisiones.

    """)
    st.info("💡 Funcionalidad en desarrollo. Próximamente vas a poder usar asistentes personalizados con inteligencia artificial.")