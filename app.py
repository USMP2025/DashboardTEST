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
        # Leer CSV con manejo explícito de formatos
        df = pd.read_csv(
            DATA_URL,
            encoding='latin1',  # Para caracteres especiales
            parse_dates=['Fecha'],
            dayfirst=True  # Formato DD/MM/AAAA
        )
        
        # Limpieza exhaustiva de datos
        pruebas_columns = [
            "THOMAS PSOAS D", "THOMAS PSOAS I",
            "THOMAS CUADRICEPS D", "THOMAS CUADRICEPS I",
            "THOMAS SARTORIO D", "THOMAS SARTORIO I",
            "JURDAN D", "JURDAN I"
        ]
        
        for col in pruebas_columns:
            if col in df.columns:
                # Convertir a número, reemplazar comas por puntos y manejar textos
                df[col] = (
                    pd.to_numeric(
                        df[col].astype(str).str.replace(',', '.'), 
                        errors='coerce'
                    )
                    .fillna(0)  # Rellenar valores faltantes con 0
                    .astype(float)
                )
        
        # Formatear fecha
        df['Fecha'] = df['Fecha'].dt.date
        
        return df
    
    except Exception as e:
        st.error(f"🚨 Error crítico: {str(e)}")
        return pd.DataFrame()

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
    try:
        return "👍" if float(valor) >= umbral else "👎"
    except:
        return "❌"

# Interfaz
st.image(LOGO_URL, width=200)
st.title("📊 Resultados Confiables de Pruebas USMP")

df = cargar_datos()

if not df.empty:
    # Diagnóstico (puedes borrar esto después)
    st.sidebar.success("✅ Datos cargados correctamente")
    st.sidebar.write(f"📅 Fechas disponibles: {len(df['Fecha'].unique()}")
    st.sidebar.write(f"👥 Jugadores cargados: {len(df['Jugador'].unique()}")
    
    # Filtros mejorados
    st.sidebar.header("🔍 Filtros Avanzados")
    
    jugadores = st.sidebar.multiselect(
        "Seleccionar Jugador",
        options=sorted(df['Jugador'].unique()),
        default=df['Jugador'].unique()[0] if len(df['Jugador']) > 0 else None
    )
    
    fechas = st.sidebar.multiselect(
        "Seleccionar Fecha",
        options=sorted(df['Fecha'].unique(), reverse=True),
        default=df['Fecha'].max() if len(df['Fecha']) > 0 else None
    )
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if jugadores:
        df_filtrado = df_filtrado[df_filtrado['Jugador'].isin(jugadores)]
    if fechas:
        df_filtrado = df_filtrado[df_filtrado['Fecha'].isin(fechas)]
    
    # Mostrar resultados
    st.subheader("📋 Resultados por Jugador")
    
    # Crear columnas para mejor visualización
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.metric("Total de Jugadores", len(df_filtrado['Jugador'].unique()))
    
    with col2:
        st.metric("Última Fecha", df_filtrado['Fecha'].max().strftime('%d/%m/%Y'))
    
    # Tabla interactiva
    st.dataframe(
        df_filtrado.style.applymap(
            lambda x: 'color: green' if x == "👍" else ('color: red' if x == "👎" else ''),
            subset=list(UMBRALES.keys())
        ),
        height=700,
        use_container_width=True,
        hide_index=True,
        column_order=["Jugador", "Fecha"] + list(UMBRALES.keys())
    
else:
    st.warning("No se encontraron datos válidos. Verifica tu archivo CSV.")

# Créditos
st.sidebar.markdown("---")
st.sidebar.caption("🔄 Actualizado el: " + datetime.now().strftime('%d/%m/%Y %H:%M'))
