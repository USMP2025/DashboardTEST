import pandas as pd
import streamlit as st
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# Configuración del dashboard
st.set_page_config(
    page_title="Dashboard Interactivo Resultados de Pruebas de Movilidad",
    layout="wide",
    page_icon="⚽"
)

# URLs actualizadas
LOGO_URL = "https://i.ibb.co/5hKcnyZ3/logo-usmp.png"
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

# Función para cargar el logo
def cargar_logo():
    try:
        response = requests.get(LOGO_URL, timeout=10)
        logo = Image.open(BytesIO(response.content))
        return logo
    except Exception as e:
        st.sidebar.warning("El logo no se pudo cargar")
        return None

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        # Leer CSV con nombres exactos de columnas
        df = pd.read_csv(DATA_URL, encoding='utf-8')
        
        # Mapeo exacto de columnas (verificado en tu CSV)
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
            st.error(f"Columnas requeridas faltantes: {', '.join(missing)}")
            st.info(f"Columnas encontradas: {list(df.columns)}")
            return pd.DataFrame()

        # Limpieza y conversión de datos
        df = df.dropna(subset=['Jugador', 'Fecha'])
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
        df = df.dropna(subset=['Fecha'])
        df['Categoría'] = df['Categoría'].fillna('Sin categoría').str.strip()
        
        # Procesar valores numéricos
        pruebas_columns = list(UMBRALES.keys())
        for col in pruebas_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str)
                    .str.replace(',', '.')
                    .str.replace(r'[^\d.]', '', regex=True),
                    errors='coerce'
                ).fillna(0)
        
        return df

    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return pd.DataFrame()

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

def mostrar_icono(valor, umbral):
    try:
        return "👍" if float(valor) >= umbral else "👎"
    except:
        return "❓"

# Interfaz principal
def main():
    # Logo
    logo = cargar_logo()
    if logo:
        st.image(logo, width=200)
    
    st.title("Dashboard Interactivo Resultados de Pruebas de Movilidad")
    
    # Cargar datos
    df = cargar_datos()
    
    if df.empty:
        st.warning("""
            No se pudieron cargar datos. Verifica que:
            1. El CSV tenga columnas: JUGADOR, CATEGORÍA, FECHA
            2. Los nombres de columnas estén exactamente como se muestran arriba
            3. El archivo contenga datos válidos
        """)
        return
    
    # Filtros en sidebar
    st.sidebar.header("Filtros")
    
    # Obtener opciones únicas
    opciones_jugador = sorted(df['Jugador'].unique())
    opciones_categoria = sorted(df['Categoría'].unique())
    opciones_fecha = sorted(df['Fecha'].unique(), reverse=True)
    
    # Widgets de filtro
    jugadores = st.sidebar.multiselect(
        "Jugador",
        options=opciones_jugador,
        default=None
    )
    
    categorias = st.sidebar.multiselect(
        "Categoría",
        options=opciones_categoria,
        default=None
    )
    
    fechas = st.sidebar.multiselect(
        "Fecha",
        options=opciones_fecha,
        default=None
    )
    
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
    
    if df_filtrado.empty:
        st.warning("No hay resultados con los filtros seleccionados")
    else:
        # Crear una copia para mostrar (para no modificar el original)
        df_mostrar = df_filtrado.copy()
        
        # Aplicar iconos a las columnas relevantes
        for col in UMBRALES:
            if col in df_mostrar.columns:
                df_mostrar[col] = df_mostrar[col].apply(
                    lambda x: mostrar_icono(x, UMBRALES[col])
        
        # Mostrar tabla
        st.dataframe(
            df_mostrar[
                ["Jugador", "Categoría", "Fecha"] + 
                list(UMBRALES.keys())
            ].style.applymap(
                lambda x: 'color: green' if x == "👍" else ('color: red' if x == "👎" else ''),
                subset=list(UMBRALES.keys())
            ),
            height=700,
            use_container_width=True,
            hide_index=True
        )

if __name__ == "__main__":
    main()
