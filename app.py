import pandas as pd
import streamlit as st
from datetime import datetime

# Configuración
st.set_page_config(
    page_title="Dashboard USMP - Resultados Confiables",
    layout="wide",
    page_icon="⚽"
)

# URLs (¡Actualiza estos!)
LOGO_URL = "https://ibb.co/5hKcnyZ3"  # Cambia por tu logo
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        # Leer CSV con manejo robusto de errores
        df = pd.read_csv(
            DATA_URL,
            encoding='utf-8',
            sep=',',
            parse_dates=['Fecha'],
            dayfirst=True,
            on_bad_lines='skip'
        )
        
        # Limpieza exhaustiva de datos
        columnas_pruebas = [
            "THOMAS PSOAS D", "THOMAS PSOAS I",
            "THOMAS CUADRICEPS D", "THOMAS CUADRICEPS I",
            "THOMAS SARTORIO D", "THOMAS SARTORIO I",
            "JURDAN D", "JURDAN I"
        ]
        
        for col in columnas_pruebas:
            if col in df.columns:
                # Convertir a texto, limpiar y luego a número
                df[col] = (
                    df[col].astype(str)
                    .str.replace(',', '.')
                    .str.replace('[^0-9.]', '', regex=True)
                    .replace('', '0')
                )
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Asegurar columnas críticas
        df['Jugador'] = df['Jugador'].fillna('Desconocido')
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce').dt.date
        
        return df
    
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return pd.DataFrame(columns=['Jugador', 'Fecha'] + columnas_pruebas)

# Umbrales
UMBRALES = {
    "THOMAS PSOAS D": 10, "THOMAS PSOAS I": 10,
    "THOMAS CUADRICEPS D": 50, "THOMAS CUADRICEPS I": 50,
    "THOMAS SARTORIO D": 80, "THOMAS SARTORIO I": 80,
    "JURDAN D": 75, "JURDAN I": 75
}

def mostrar_icono(valor, umbral):
    try:
        return "👍" if float(valor) >= umbral else "👎"
    except:
        return "❓"

# Interfaz
st.image(LOGO_URL, width=200)
st.title("Resultados de Pruebas USMP")

df = cargar_datos()

if not df.empty:
    # Filtros
    st.sidebar.header("Filtros")
    jugadores = st.sidebar.multiselect(
        "Jugador",
        options=sorted(df['Jugador'].unique()),
        default=None
    )
    
    fechas = st.sidebar.multiselect(
        "Fecha",
        options=sorted(df['Fecha'].unique(), reverse=True),
        default=None
    )
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if jugadores:
        df_filtrado = df_filtrado[df_filtrado['Jugador'].isin(jugadores)]
    if fechas:
        df_filtrado = df_filtrado[df_filtrado['Fecha'].isin(fechas)]
    
    # Mostrar tabla
    st.dataframe(
        df_filtrado.style.applymap(
            lambda x: 'background-color: #e6ffe6' if x == "👍" else 
                     ('background-color: #ffe6e6' if x == "👎" else ''),
            subset=list(UMBRALES.keys())
        ),
        height=700,
        use_container_width=True,
        column_config={
            "Jugador": "Jugador",
            "Fecha": st.column_config.DateColumn("Fecha")
        }
    )
else:
    st.warning("No se encontraron datos válidos. Verifica el archivo CSV.")

st.sidebar.markdown("---")
st.sidebar.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
