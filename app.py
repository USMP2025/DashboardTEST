import pandas as pd
import streamlit as st
from datetime import datetime

# Configuración
st.set_page_config(
    page_title="Dashboard USMP",
    layout="wide",
    page_icon="⚽"
)

# URLs (¡cambia el logo!)
LOGO_URL = "https://ibb.co/5hKcnyZ3"  # Sube tu logo a imgbb.com
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

@st.cache_data(ttl=300)
def cargar_datos():
    df = pd.read_csv(DATA_URL)
    
    # Convertir fechas (formato DD/MM/AAAA)
    df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True).dt.date
    
    return df

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
    return "👍" if valor >= umbral else "👎"

# Interfaz
st.image(LOGO_URL, width=200)
st.title("Resultados de Pruebas USMP")

try:
    df = cargar_datos()
    
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
        use_container_width=True
    )
    
except Exception as e:
    st.error(f"Error: {str(e)}")
