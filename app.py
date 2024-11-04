import streamlit as st
import pandas as pd
import pickle
import os

# Directorio para guardar archivos temporales
SAVE_DIR = 'saved_data'

# Crear el directorio si no existe
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# Función para guardar un archivo usando pickle
def guardar_archivo(archivo, nombre_archivo):
    with open(os.path.join(SAVE_DIR, nombre_archivo), 'wb') as f:
        pickle.dump(archivo, f)

# Función para cargar un archivo usando pickle
def cargar_archivo(nombre_archivo):
    archivo_path = os.path.join(SAVE_DIR, nombre_archivo)
    if os.path.exists(archivo_path):
        with open(archivo_path, 'rb') as f:
            return pickle.load(f)
    return None

# Función para cargar archivo Excel y convertirlo en DataFrame
def cargar_excel(archivo, hoja, fila_encabezado):
    try:
        df = pd.read_excel(archivo, sheet_name=hoja, header=fila_encabezado-1, engine='openpyxl')
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return None

# Aplicar estilos para mejorar la estética del dashboard
def aplicar_estilos():
    st.markdown("""
    <style>
    body {
        background-color: #0a0a0a;
        color: #ffffff;
    }
    .titulo-seccion {
        font-size: 24px;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 10px;
        color: #4B4B4B;
    }
    </style>
    """, unsafe_allow_html=True)

# Función para configurar el dashboard
def configurar_dashboard(df):
    st.title("Configurar Dashboard")
    config_cargada = cargar_archivo('config_dashboard.pkl')
    if 'config' not in st.session_state:
        if config_cargada:
            st.session_state.config = config_cargada
        else:
            st.session_state.config = {'sumatorias': [], 'cantidades': [], 'promedios': []}

    if df is not None:
        campos = df.columns.tolist()
        sumatorias_default = [x for x in st.session_state.config['sumatorias'] if x in campos]
        cantidades_default = [x for x in st.session_state.config['cantidades'] if x in campos]
        promedios_default = [x for x in st.session_state.config['promedios'] if x in campos]

        sumatorias = st.multiselect("Campos para sumatoria", campos, default=sumatorias_default)
        cantidades = st.multiselect("Campos para cantidad", campos, default=cantidades_default)
        promedios = st.multiselect("Campos para promedio", campos, default=promedios_default)

        for campo in sumatorias + promedios + cantidades:
            df[campo] = pd.to_numeric(df[campo], errors='coerce').fillna(0)

        configuracion = {'sumatorias': sumatorias, 'cantidades': cantidades, 'promedios': promedios}
        st.session_state.config = configuracion

        if st.button("Guardar configuración"):
            guardar_archivo(configuracion, 'config_dashboard.pkl')
            st.success("Configuración guardada correctamente.")
    else:
        st.warning("Primero debes cargar un archivo.")

def mostrar_dashboard(df):
    st.title("Dashboard")
    aplicar_estilos()

    # Mostrar el nombre del archivo seleccionado
    if 'archivo_seleccionado' in st.session_state:
        st.markdown(f"<h5 style='color: #ffffff;'>Archivo seleccionado: {st.session_state.archivo_seleccionado}</h5>", unsafe_allow_html=True)

    config = cargar_archivo('config_dashboard.pkl')

    if config is not None and df is not None:
        # Crear dos columnas para los filtros
        col_filtro1, col_filtro2 = st.columns(2)

        # Agregar primer filtro en el Dashboard
        with col_filtro1:
            campos = df.columns.tolist()
            filtro1 = st.selectbox("Seleccionar primer campo para filtrar", ["Elige una opción"] + campos, key='filtro1')
            if filtro1 != "Elige una opción":
                valores_filtro1_disponibles = df[filtro1].unique().tolist()
                valor_filtro1 = st.multiselect(f"Valores de {filtro1}", valores_filtro1_disponibles, key='valor_filtro1')
            else:
                valor_filtro1 = []

        # Agregar segundo filtro en el Dashboard
        with col_filtro2:
            campos_restantes = [campo for campo in campos if campo != filtro1]
            filtro2 = st.selectbox("Seleccionar segundo campo para filtrar", ["Elige una opción"] + campos_restantes, key='filtro2')
            if filtro2 != "Elige una opción":
                valores_filtro2_disponibles = df[filtro2].unique().tolist()
                valor_filtro2 = st.multiselect(f"Valores de {filtro2}", valores_filtro2_disponibles, key='valor_filtro2')
            else:
                valor_filtro2 = []

        # Aplicar filtros principales
        if valor_filtro1 and valor_filtro2:
            df_filtrado = df[df[filtro1].isin(valor_filtro1) & df[filtro2].isin(valor_filtro2)]
        elif valor_filtro1:
            df_filtrado = df[df[filtro1].isin(valor_filtro1)]
        elif valor_filtro2:
            df_filtrado = df[df[filtro2].isin(valor_filtro2)]
        else:
            df_filtrado = df

        if df_filtrado.empty:
            st.error("No hay datos disponibles después de aplicar los filtros.")
            return

        # Crear tres columnas para las métricas
        col1, col2, col3 = st.columns(3)

        # Mostrar Sumatorias
        with col1:
            st.markdown("<div class='titulo-seccion'>Sumatorias</div>", unsafe_allow_html=True)
            for campo in config['sumatorias']:
                try:
                    suma_total = int(df_filtrado[campo].sum())
                    display_watchlist_card(campo, f"{suma_total:,}")
                except Exception as e:
                    st.error(f"Error al calcular la sumatoria para {campo}: {e}")

        # Mostrar Cantidades
        with col2:
            st.markdown("<div class='titulo-seccion'>Cantidades</div>", unsafe_allow_html=True)
            for campo in config['cantidades']:
                try:
                    cantidad_total = int(df_filtrado[campo].count())
                    display_watchlist_card(campo, f"{cantidad_total:,}")
                except Exception as e:
                    st.error(f"Error al calcular la cantidad para {campo}: {e}")

        # Mostrar Promedios
        with col3:
            st.markdown("<div class='titulo-seccion'>Promedios</div>", unsafe_allow_html=True)
            for campo in config['promedios']:
                try:
                    promedio_total = int(df_filtrado[campo].mean())
                    display_watchlist_card(campo, f"{promedio_total:,}")
                except Exception as e:
                    st.error(f"Error al calcular el promedio para {campo}: {e}")

        # Sección de análisis detallado
        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("Análisis Detallado")

        col1, col2, col3 = st.columns(3)
        
        with col1:
            campo_categoria = st.selectbox("Seleccionar campo categórico", df.select_dtypes(include=['object']).columns.tolist(), key='campo_categoria')
            valores_seleccionados = st.multiselect(f"Valores de {campo_categoria}", df[campo_categoria].unique().tolist(), key='valores_categoria')

        with col2:
            campo_numerico = st.selectbox("Seleccionar campo numérico", df.select_dtypes(include=['int64', 'float64']).columns.tolist(), key='campo_numerico')

        with col3:
            operaciones = st.multiselect("Seleccionar operaciones", ["Sumatoria", "Cantidad", "Promedio"], key='operaciones')

        # Aplicar filtro adicional en Análisis Detallado
        st.markdown("<div style='font-size: 18px; font-weight: bold; margin-top: 20px;'>Filtro Adicional</div>", unsafe_allow_html=True)
        
        col_filtro1, col_filtro2 = st.columns(2)
        
        with col_filtro1:
            filtro_adicional = st.selectbox("Seleccionar filtro", ["Ninguno"] + [c for c in df.columns if c != campo_categoria], key='filtro_adicional')

        with col_filtro2:
            if filtro_adicional != "Ninguno":
                valores_filtro = df[filtro_adicional].unique().tolist()
                valores_filtro_seleccionados = st.multiselect(f"Valores de {filtro_adicional}", valores_filtro, key='valores_filtro_adicional')
            else:
                valores_filtro_seleccionados = []

        # Mostrar resultados de análisis detallado
        if valores_seleccionados and campo_numerico and operaciones:
            df_filtrado = df[df[campo_categoria].isin(valores_seleccionados)]
            if filtro_adicional != "Ninguno" and valores_filtro_seleccionados:
                df_filtrado = df_filtrado[df_filtrado[filtro_adicional].isin(valores_filtro_seleccionados)]

            col_resultados1, col_resultados2, col_resultados3 = st.columns(3)
            
            if "Sumatoria" in operaciones:
                with col_resultados1:
                    suma = int(df_filtrado[campo_numerico].sum())
                    display_watchlist_card(f"Suma de {campo_numerico}", f"{suma:,}")

            if "Cantidad" in operaciones:
                with col_resultados2:
                    cantidad = int(df_filtrado[campo_numerico].count())
                    display_watchlist_card(f"Cantidad de {campo_numerico}", f"{cantidad:,}")

            if "Promedio" in operaciones:
                with col_resultados3:
                    promedio = int(df_filtrado[campo_numerico].mean())
                    display_watchlist_card(f"Promedio de {campo_numerico}", f"{promedio:,}")

            # Mostrar tabla de resultados
            st.markdown("<div class='titulo-seccion'>Resultados Detallados</div>", unsafe_allow_html=True)
            resultados = df_filtrado.groupby(campo_categoria).agg({
                campo_numerico: [
                    ('Sumatoria', lambda x: int(x.sum())),
                    ('Cantidad', 'count'),
                    ('Promedio', lambda x: int(x.mean()))
                ]
            })
            resultados.columns = resultados.columns.droplevel()
            resultados_formateados = resultados.applymap(lambda x: f"{int(x):,}")
            st.dataframe(resultados_formateados)

    else:
        st.warning("No hay configuración previa o datos cargados. Por favor, configura el dashboard y carga un archivo.")

# Función para mostrar los resultados de la métrica
def display_watchlist_card(label, value):
    st.markdown(
        f"""
        <div style="
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 10px;
            margin: 5px 0;
            background-color: #f9f9f9;
        ">
            <p style="font-size: 14px; color: #666; margin-bottom: 5px;">{label}</p>
            <p style="font-size: 20px; font-weight: bold; color: #333; margin: 0;">{value}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Panel izquierdo: Adjuntar archivo y configurar dashboard
def menu_panel_izquierdo():
    st.sidebar.title("Menú Principal")
    seleccion = st.sidebar.radio("Selecciona una página", ['Adjuntar Archivo', 'Configurar', 'Dashboard', 'Consulta'])
    return seleccion

# Página de adjuntar archivo
def adjuntar_archivo():
    st.title("Adjuntar Archivo")
    archivo_guardado = cargar_archivo('archivo.pkl')
    archivo = st.file_uploader("Subir archivo Excel", type=['xlsx'])
    df = None
    if archivo:
        hojas = pd.ExcelFile(archivo, engine='openpyxl').sheet_names
        hoja_seleccionada = st.selectbox("Selecciona la hoja del archivo", hojas)
        fila_encabezado = st.number_input("Número de fila del encabezado del archivo", min_value=1, value=1, step=1)
        df = cargar_excel(archivo, hoja_seleccionada, fila_encabezado)
        if df is not None:
            st.success("Archivo cargado exitosamente.")
            st.write(df.head())
            guardar_archivo(df, 'archivo.pkl')
            st.session_state.df = df
            st.session_state.archivo_seleccionado = archivo.name
    elif archivo_guardado is not None:
        df = archivo_guardado
        st.session_state.df = df
        st.write(df.head())
    return df

# Página de consulta
def mostrar_consulta(df):
    st.title("Consulta de Datos")
    if df is not None:
        st.write("Aquí está la tabla adjuntada:")
        st.markdown("<h3 style='font-size: 18px;'>Filtro</h3>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            select_filter = st.selectbox("Selecciona un filtro", ["Elige un filtro"] + df.columns.tolist())
        with col2:
            if select_filter != "Elige un filtro":
                unique_values = df[select_filter].unique().tolist()
                selected_value = st.selectbox(f"Selecciona un valor de {select_filter}", ["Elige un valor"] + unique_values)
            else:
                selected_value = None
        if selected_value and selected_value != "Elige un valor":
            df_filtrado = df[df[select_filter] == selected_value]
            st.dataframe(df_filtrado, hide_index=True)
            with st.container():
                st.subheader("Count")
                st.write(f"Número de registros: {len(df_filtrado)}")
        else:
            st.dataframe(df, hide_index=True)
    else:
        st.warning("No hay datos disponibles. Por favor, adjunta un archivo primero.")

# Función principal para ejecutar la aplicación
def main():
    seleccion = menu_panel_izquierdo()
    if 'df' not in st.session_state:
        st.session_state.df = None
    if seleccion == 'Adjuntar Archivo':
        st.session_state.df = adjuntar_archivo()
    elif seleccion == 'Configurar':
        configurar_dashboard(st.session_state.df)
    elif seleccion == 'Dashboard':
        mostrar_dashboard(st.session_state.df)
    elif seleccion == 'Consulta':
        mostrar_consulta(st.session_state.df)

if __name__ == "__main__":
    main()
