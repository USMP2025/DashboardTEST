import pandas as pd
import streamlit as st
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# 1. Configuración inicial
st.set_page_config(
    page_title="Dashboard de Pruebas USMP",
    layout="wide",
    page_icon="⚽"
)

# 2. URLs de recursos
LOGO_URL = "https://i.ibb.co/5hKcnyZ3/logo-usmp.png"
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

# 3. Umbrales de evaluación
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

# 4. Funciones principales
def cargar_logo():
    try:
        response = requests.get(LOGO_URL, timeout=10)
        return Image.open(BytesIO(response.content))
    except:
        return None

def cargar_datos():
    try:
        df = pd.read_csv(DATA_URL)
        
        # Estandarizar nombres de columnas
        column_map = {
            'JUGADOR': 'Jugador',
            'CATEGORIA': 'Categoría',
            'FECHA': 'Fecha'
        }
        df = df.rename(columns=column_map)
        
        # Limpieza de datos
        df = df.dropna(subset=['Jugador', 'Fecha'])
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce').dt.date
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
        
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return pd.DataFrame()

def mostrar_icono(valor, umbral):
    try:
        if pd.isna(valor):
            return "❓"
        return "👍" if float(valor) >= umbral else "👎"
    except:
        return "❓"

# 5. Interfaz principal
def main():
    # Configuración inicial
    logo = cargar_logo()
    if logo:
        st.sidebar.image(logo, width=150)
    
    st.title("Dashboard de Pruebas de Movilidad")
    st.markdown("---")
    
    # Carga de datos
    df = cargar_datos()
    
    if df.empty:
        st.warning("No se encontraron datos válidos.")
        return
    
    # Filtros
    st.sidebar.header("Filtros")
    
    jugadores = st.sidebar.multiselect(
        "Jugadores",
        options=sorted(df['Jugador'].unique())
    )
    
    categorias = st.sidebar.multiselect(
        "Categorías",
        options=sorted(df['Categoría'].unique())
    )
    
    fechas = st.sidebar.multiselect(
        "Fechas",
        options=sorted(df['Fecha'].unique(), reverse=True)
    )
    
    # Aplicar filtros
    if jugadores:
        df = df[df['Jugador'].isin(jugadores)]
    if categorias:
        df = df[df['Categoría'].isin(categorias)]
    if fechas:
        df = df[df['Fecha'].isin(fechas)]
    
    # Procesar datos para visualización
    df_mostrar = df.copy()
    for col in UMBRALES:
        if col in df_mostrar.columns:
            df_mostrar[col] = df_mostrar[col].apply(
                lambda x: mostrar_icono(x, UMBRALES[col])
            )
    
    # Mostrar resultados
    st.header("Resultados")
    
    if df.empty:
        st.warning("No hay datos con los filtros seleccionados")
    else:
        # Seleccionar columnas a mostrar
        columnas = ['Jugador', 'Categoría', 'Fecha'] + list(UMBRALES.keys())
        columnas = [c for c in columnas if c in df_mostrar.columns]
        
        # Mostrar tabla principal
        st.dataframe(
            df_mostrar[columnas].style.applymap(
                lambda x: 'color: green' if x == "👍" else 
                         ('color: red' if x == "👎" else 'color: gray'),
                subset=list(UMBRALES.keys())
            ),
            height=600,
            use_container_width=True
        )
        
        # Mostrar estadísticas
        st.subheader("Estadísticas")
        st.dataframe(
            df[list(UMBRALES.keys())].describe().round(1),
            use_container_width=True
        )

if __name__ == "__main__":
    main()
