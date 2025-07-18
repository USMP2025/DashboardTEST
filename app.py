import pandas as pd
import streamlit as st
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# Configuración
st.set_page_config(
    page_title="Dashboard Interactivo Resultados de Pruebas de Movilidad",
    layout="wide",
    page_icon="⚽"
)

# URLs actualizadas
LOGO_URL = "https://i.ibb.co/5hKcnyZ3/logo-usmp.png"  # URL directa del logo
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

# Función para cargar el logo con manejo de errores
def cargar_logo():
    try:
        response = requests.get(LOGO_URL)
        logo = Image.open(BytesIO(response.content))
        return logo
    except Exception as e:
        st.error(f"Error cargando logo: {str(e)}")
        return None

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        # Leer CSV con nombres exactos de columnas
        df = pd.read_csv(DATA_URL, encoding='utf-8')
        
        # Mapeo exacto de columnas (verificado)
        column_map = {
            'JUGADOR': 'Jugador',
            'CATEGORÍA': 'Categoría',
            'FECHA': 'Fecha',
            'THOMAS PSOAS D': 'THOMAS PSOAS D',
            'THOMAS PSOAS I': 'THOMAS PSOAS I',
            'THOMAS CUADRICEPS D': 'THOMAS CUADRICEPS D',
            'THOMAS CUADRICEPS I': 'THOMAS CUADRICEPS I',
            'THOMAS SARTORIO D': 'THOMAS SARTORIO D',
            'THOMAS SARTORIO I': 'THOMAS SARTORIO I',
            'JURDAN D': 'JURDAN D',
            'JURDAN I': 'JURDAN I'
        }
        
        df = df.rename(columns=column_map)
        
        # Verificación de columnas
        required_columns = ['Jugador', 'Categoría', 'Fecha']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            st.error(f"Columnas faltantes: {', '.join(missing)}")
            return pd.DataFrame()

        # Limpieza de datos
        df = df.dropna(subset=['Jugador', 'Fecha'])
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
        df = df.dropna(subset=['Fecha'])
        df['Categoría'] = df['Categoría'].fillna('Sin categoría').str.strip()
        
        # Procesar valores numéricos
        pruebas_columns = list(UMBRALES.keys())
        for col in pruebas_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        return df

    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return pd.DataFrame()

# Umbrales
UMBRALES = {
    "THOMAS PSOAS D": 10, "THOMAS PSOAS I": 10,
    "THOMAS CUADRICEPS D": 50, "THOMAS CUADRICEPS I": 50,
    "THOMAS SARTORIO D": 80, "THOMAS SARTORIO I": 80,
    "JURDAN D": 75, "JURDAN I": 75
}

def mostrar_icono(valor, umbral):
    return "👍" if valor >= umbral else "👎"

# Interfaz
def main():
    # Mostrar logo
    logo = cargar_logo()
    if logo:
        st.image(logo, width=200)
    else:
        st.warning("Logo no disponible")

    st.title("Dashboard Interactivo Resultados de Pruebas de Movilidad")
    
    df = cargar_datos()
    
    if df.empty:
        st.warning("No hay datos válidos. Verifica tu archivo CSV.")
        return
    
    # Filtros
    st.sidebar.header("Filtros")
    jugadores = st.sidebar.multiselect("Jugador", sorted(df['Jugador'].unique()))
    categorias = st.sidebar.multiselect("Categoría", sorted(df['Categoría'].unique()))
    fechas = st.sidebar.multiselect("Fecha", sorted(df['Fecha'].unique(), reverse=True))
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if jugadores:
        df_filtrado = df_filtrado[df_filtrado['Jugador'].isin(jugadores)]
    if categorias:
        df_filtrado = df_filtrado[df_filtrado['Categoría'].isin(categorias)]
    if fechas:
        df_filtrado = df_filtrado[df_filtrado['Fecha'].isin(fechas)]
    
    # Mostrar resultados
    st.subheader("Resultados Filtrados")
    
    if not df_filtrado.empty:
        for col in UMBRALES:
            if col in df_filtrado.columns:
                df_filtrado[col] = df_filtrado[col].apply(lambda x: mostrar_icono(x, UMBRALES[col]))
        
        st.dataframe(
            df_filtrado[["Jugador", "Categoría", "Fecha"] + list(UMBRALES.keys())],
            height=700,
            use_container_width=True,
            hide_index=True
        )

if __name__ == "__main__":
    main()
