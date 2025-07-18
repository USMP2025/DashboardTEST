import pandas as pd
import streamlit as st
from datetime import datetime

# Configuración
st.set_page_config(
    page_title="Dashboard Interactivo Resultados de Pruebas de Movilidad",
    layout="wide",
    page_icon="⚽"
)

# URLs (¡Actualiza el logo!)
LOGO_URL = "https://ibb.co/5hKcnyZ3"
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        # Leer CSV sin parseo automático de fechas
        df = pd.read_csv(DATA_URL, encoding='utf-8')
        
        # Verificar y renombrar columnas críticas
        column_map = {
            'Fecha de prueba': 'Fecha',  # Nombre actual → Nombre deseado
            'Jugador': 'Jugador',
            'Categoría': 'Categoría'
        }
        
        # Renombrar columnas
        df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
        
        # Verificar columnas esenciales
        required_columns = ['Jugador', 'Categoría', 'Fecha']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            st.error(f"Columnas faltantes: {', '.join(missing)}")
            return pd.DataFrame()

        # Limpieza de datos
        df = df.dropna(subset=['Jugador', 'Fecha'])
        
        # Convertir fechas (formato DD/MM/AAAA)
        df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
        df = df.dropna(subset=['Fecha'])
        
        # Limpieza de categorías
        df['Categoría'] = df['Categoría'].fillna('Sin categoría').str.strip()
        
        # Procesar valores numéricos
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
def main():
    st.image(LOGO_URL, width=200)
    st.title("Dashboard Interactivo Resultados de Pruebas de Movilidad")
    
    df = cargar_datos()
    
    if df.empty:
        return  # Ya se mostró el mensaje de error
    
    # Filtros
    st.sidebar.header("Filtros")
    
    jugadores = st.sidebar.multiselect(
        "Jugador",
        options=sorted(df['Jugador'].unique()),
        default=None
    )
    
    categorias = st.sidebar.multiselect(
        "Categoría",
        options=sorted(df['Categoría'].unique()),
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
            df_filtrado[
                ["Jugador", "Categoría", "Fecha"] + 
                [c for c in UMBRALES.keys() if c in df_filtrado.columns]
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
