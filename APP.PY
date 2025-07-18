import pandas as pd
import streamlit as st
from datetime import datetime

# Configuración
st.set_page_config(
    page_title="Dashboard de Resultados de Pruebas de Movilidad",
    layout="wide",
    page_icon="⚽"
)

# URLs - ¡ACTUALIZAR ESTAS!
LOGO_URL = "https://ibb.co/5hKcnyZ3"  # Cambiar por tu logo
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

@st.cache_data(ttl=300)
def cargar_datos():
    return pd.read_csv(DATA_URL)

# Umbrales para pruebas
UMBRALES = {
    "THOMAS PSOAS (D)": 10, "THOMAS PSOAS (I)": 10,
    "THOMAS CUADRICEPS (D)": 50, "THOMAS CUADRICEPS (I)": 50,
    "THOMAS SARTORIO (D)": 80, "THOMAS SARTORIO (I)": 80,
    "JURDAN (D)": 75, "JURDAN (I)": 75
}

def mostrar_icono(valor, umbral):
    return "👍" if valor >= umbral else "👎"

# Interfaz
st.image(LOGO_URL, width=200)
st.title("Dashboard de Resultados de Pruebas de Movilidad")

try:
    df = cargar_datos()
    
    # DIAGNÓSTICO: Mostrar columnas reales
    st.sidebar.info(f"Columnas detectadas: {', '.join(df.columns)}")
    
    # Renombrar columnas según tu CSV - ¡AJUSTA ESTOS NOMBRES!
    columnas_renombradas = {
        'Jugador': 'JUGADOR',        # Si en CSV es "Jugador"
        'Categoría': 'CATEGORÍA',     # Si en CSV es "Categoría"
        'Fecha': 'FECHA',             # Si en CSV es "Fecha"
        # Agregar otras columnas si tienen nombres diferentes
    }
    df = df.rename(columns=columnas_renombradas)
    
    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha']).dt.date
except Exception as e:
    st.error(f"Error cargando datos: {e}")
    st.stop()

# Filtros
st.sidebar.header("Filtros")

# Usar nombres estandarizados
if 'jugador' in df.columns:
    jugadores = st.sidebar.multiselect("Jugador", df['jugador'].unique(), default=df['jugador'].unique())
else:
    st.error("Columna 'jugador' no encontrada")

if 'categoria' in df.columns:
    categorias = st.sidebar.multiselect("Categoría", df['categoria'].unique(), default=df['categoria'].unique())

if 'fecha' in df.columns:
    fechas = st.sidebar.multiselect("Fecha", df['fecha'].unique(), default=df['fecha'].unique())

# Aplicar filtros
df_filtrado = df.copy()
if 'jugador' in df.columns:
    df_filtrado = df_filtrado[df_filtrado['jugador'].isin(jugadores)]
if 'categoria' in df.columns:
    df_filtrado = df_filtrado[df_filtrado['categoria'].isin(categorias)]
if 'fecha' in df.columns and fechas:
    df_filtrado = df_filtrado[df_filtrado['fecha'].isin(fechas)]

# Botón actualización
if st.sidebar.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.experimental_rerun()

# Mostrar tabla con iconos
df_mostrar = df_filtrado.copy()
for col, umbral in UMBRALES.items():
    if col in df_mostrar.columns:
        df_mostrar[col] = df_mostrar[col].apply(lambda x: mostrar_icono(x, umbral))

st.dataframe(df_mostrar, height=700, use_container_width=True)

# Pie de página
st.sidebar.markdown("---")
st.sidebar.info(f"Registros mostrados: {len(df_filtrado)}/{len(df)}")
st.sidebar.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")