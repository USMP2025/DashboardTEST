import pandas as pd
import streamlit as st
from datetime import datetime

# Configuración
st.set_page_config(
    page_title="Dashboard USMP",
    layout="wide",
    page_icon="⚽"
)

# URLs (¡Actualiza estos enlaces!)
LOGO_URL = "https://ibb.co/5hKcnyZ3"  # Cambia por tu logo
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        df = pd.read_csv(DATA_URL)
        
        # Limpieza de datos
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
        
        # Columnas de pruebas (convertir a números y limpiar)
        columnas_pruebas = [
            "THOMAS PSOAS D", "THOMAS PSOAS I",
            "THOMAS CUADRICEPS D", "THOMAS CUADRICEPS I",
            "THOMAS SARTORIO D", "THOMAS SARTORIO I",
            "JURDAN D", "JURDAN I"
        ]
        
        for col in columnas_pruebas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')  # Convierte a número (NaN si falla)
                df[col] = df[col].fillna(0)  # Reemplaza NaN por 0
        
        return df
    
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return pd.DataFrame()  # Devuelve un DataFrame vacío para evitar errores

# Umbrales exactos para tus columnas
UMBRALES = {
    "THOMAS PSOAS D": 10,
    "THOMAS PSOAS I": 10,
    "THOMAS CUADRICEPS D": 50,
    "THOMAS CUADRICEPS I": 50,
    "THOMAS SARTORIO D": 80,
    "THOMAS SARTORIO I": 80,
    "JURDAN D": 75,
    "JURDAN I": 75
}

def mostrar_icono(valor, umbral):
    if pd.isna(valor):  # Maneja valores faltantes
        return "❓"
    return "👍" if valor >= umbral else "👎"

# Interfaz
st.image(LOGO_URL, width=200)
st.title("Resultados de Pruebas USMP")

df = cargar_datos()

if not df.empty:
    # Filtros
    st.sidebar.header("Filtros")
    jugadores = st.sidebar.multiselect("Jugador", df['Jugador'].unique())
    fechas = st.sidebar.multiselect("Fecha", df['Fecha'].unique())
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if jugadores:
        df_filtrado = df_filtrado[df_filtrado['Jugador'].isin(jugadores)]
    if fechas:
        df_filtrado = df_filtrado[df_filtrado['Fecha'].isin(fechas)]
    
    # Mostrar tabla con iconos
    df_mostrar = df_filtrado.copy()
    for col, umbral in UMBRALES.items():
        if col in df_mostrar.columns:
            df_mostrar[col] = df_mostrar[col].apply(lambda x: mostrar_icono(x, umbral))
    
    st.dataframe(
        df_mostrar,
        column_config={
            "Jugador": "Jugador",
            "Fecha": st.column_config.DateColumn("Fecha"),
        },
        height=700,
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("No se pudieron cargar los datos. Verifica el archivo CSV.")
