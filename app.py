import pandas as pd
import streamlit as st
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# Configuración del dashboard
st.set_page_config(
    page_title="Dashboard de Pruebas de Movilidad",
    layout="wide",
    page_icon="⚽"
)

# URLs
LOGO_URL = "https://i.ibb.co/5hKcnyZ3/logo-usmp.png"
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

# Umbrales para las pruebas
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

@st.cache_data
def cargar_logo():
    try:
        response = requests.get(LOGO_URL, timeout=10)
        return Image.open(BytesIO(response.content))
    except:
        return None

@st.cache_data(ttl=3600)
def cargar_datos():
    try:
        df = pd.read_csv(DATA_URL)
        
        # Renombrar columnas para estandarizar
        df = df.rename(columns={
            'JUGADOR': 'Jugador',
            'CATEGORIA': 'Categoría',
            'FECHA': 'Fecha'
        })
        
        # Limpieza de datos
        df = df.dropna(subset=['Jugador', 'Fecha'])
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
        df['Categoría'] = df['Categoría'].fillna('Sin categoría').str.strip()
        
        # Convertir valores numéricos
        for col in UMBRALES:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str)
                    .str.replace(',', '.')
                    .str.replace(r'[^\d.]', '', regex=True),
                    errors='coerce'
                )
        
        return df.dropna(subset=list(UMBRALES.keys())), None
    except Exception as e:
        return pd.DataFrame(), str(e)

def mostrar_icono(valor, umbral):
    if pd.isna(valor):
        return "❓"
    return "👍" if float(valor) >= umbral else "👎"

def main():
    # Logo
    logo = cargar_logo()
    if logo:
        st.sidebar.image(logo, width=150)
    
    st.title("📊 Resultados de Pruebas de Movilidad")
    
    # Cargar datos
    df, error = cargar_datos()
    
    if error:
        st.error(f"Error al cargar datos: {error}")
        return
    
    if df.empty:
        st.warning("No se encontraron datos válidos en el archivo.")
        return
    
    # Filtros
    st.sidebar.header("🔍 Filtros")
    
    jugadores = st.sidebar.multiselect(
        "Jugadores",
        options=sorted(df['Jugador'].unique()))
    
    categorias = st.sidebar.multiselect(
        "Categorías",
        options=sorted(df['Categoría'].unique()))
    
    fechas = st.sidebar.multiselect(
        "Fechas",
        options=sorted(df['Fecha'].unique(), reverse=True))
    
    # Aplicar filtros
    mask = pd.Series(True, index=df.index)
    if jugadores:
        mask &= df['Jugador'].isin(jugadores)
    if categorias:
        mask &= df['Categoría'].isin(categorias)
    if fechas:
        mask &= df['Fecha'].isin(fechas)
    
    df_filtrado = df[mask]
    
    # Mostrar resultados
    if df_filtrado.empty:
        st.warning("No hay datos con los filtros seleccionados")
    else:
        # Aplicar iconos
        df_mostrar = df_filtrado.copy()
        for col in UMBRALES:
            if col in df_mostrar.columns:
                df_mostrar[col] = df_mostrar[col].apply(
                    lambda x: mostrar_icono(x, UMBRALES[col]))
        
        # Seleccionar columnas
        columnas = ['Jugador', 'Categoría', 'Fecha'] + list(UMBRALES.keys())
        columnas = [c for c in columnas if c in df_mostrar.columns]
        
        # Mostrar tabla
        st.dataframe(
            df_mostrar[columnas].style.applymap(
                lambda x: 'color: green' if x == "👍" else 
                         ('color: red' if x == "👎" else 'color: gray'),
                subset=list(UMBRALES.keys())
            ),
            height=600,
            use_container_width=True,
            hide_index=True
        )
        
        # Estadísticas
        st.subheader("📈 Estadísticas")
        st.dataframe(
            df_filtrado[list(UMBRALES.keys())].describe().round(1),
            use_container_width=True
        )

if __name__ == "__main__":
    main()
