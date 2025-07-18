import pandas as pd
import streamlit as st
from datetime import datetime

# Configuración del dashboard
st.set_page_config(
    page_title="Dashboard Interactivo Resultados de Pruebas de Movilidad",
    layout="wide",
    page_icon="⚽"
)

# URLs importantes
LOGO_URL = "https://ibb.co/5hKcnyZ3"  # Cambia por tu logo real
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        # Leer el CSV con manejo robusto de errores
        df = pd.read_csv(
            DATA_URL,
            encoding='utf-8',
            sep=',',
            parse_dates=['Fecha'],
            dayfirst=True
        )
        
        # Verificar columnas esenciales
        columnas_requeridas = ['Jugador', 'Categoría', 'Fecha']
        for col in columnas_requeridas:
            if col not in df.columns:
                st.error(f"Columna faltante: {col}")
                return pd.DataFrame()

        # Limpieza de datos
        df = df.dropna(subset=['Jugador', 'Fecha'])  # Eliminar filas vacías
        
        # Procesamiento de fechas
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
        df = df.dropna(subset=['Fecha'])  # Eliminar fechas inválidas
        
        # Limpieza de categorías
        df['Categoría'] = df['Categoría'].fillna('Sin categoría').str.strip()
        
        # Procesamiento de valores numéricos
        pruebas_columns = [
            "THOMAS PSOAS D", "THOMAS PSOAS I",
            "THOMAS CUADRICEPS D", "THOMAS CUADRICEPS I",
            "THOMAS SARTORIO D", "THOMAS SARTORIO I",
            "JURDAN D", "JURDAN I"
        ]
        
        for col in pruebas_columns:
            if col in df.columns:
                df[col] = (
                    df[col].astype(str)
                    .str.replace(',', '.')
                    .str.replace(r'[^\d.]', '', regex=True)
                    .replace('', '0')
                )
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df

    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return pd.DataFrame()

# Definición de umbrales
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

# Interfaz principal
def main():
    st.image(LOGO_URL, width=200)
    st.title("Dashboard Interactivo Resultados de Pruebas de Movilidad")
    
    # Cargar datos
    df = cargar_datos()
    
    if df.empty:
        st.warning("No hay datos válidos para mostrar. Verifica tu archivo CSV.")
        return
    
    # Sección de filtros
    st.sidebar.header("Filtros")
    
    # Filtro de jugador
    jugadores = st.sidebar.multiselect(
        "Seleccionar Jugador",
        options=sorted(df['Jugador'].unique()),
        default=None
    )
    
    # Filtro de categoría
    categorias = st.sidebar.multiselect(
        "Seleccionar Categoría",
        options=sorted(df['Categoría'].unique()),
        default=None
    )
    
    # Filtro de fecha
    fechas = st.sidebar.multiselect(
        "Seleccionar Fecha",
        options=sorted(df['Fecha'].unique(), reverse=True),
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
        # Aplicar iconos
        for col, umbral in UMBRALES.items():
            if col in df_filtrado.columns:
                df_filtrado[col] = df_filtrado[col].apply(lambda x: mostrar_icono(x, umbral))
        
        # Mostrar tabla
        st.dataframe(
            df_filtrado.style.applymap(
                lambda x: 'color: green' if x == "👍" else ('color: red' if x == "👎" else ''),
                subset=list(UMBRALES.keys())
            ),
            height=700,
            use_container_width=True,
            hide_index=True,
            column_order=["Jugador", "Categoría", "Fecha"] + list(UMBRALES.keys())
    
    # Pie de página
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

if __name__ == "__main__":
    main()
