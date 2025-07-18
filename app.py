import pandas as pd
import streamlit as st
from datetime import datetime

# Configuración a prueba de errores
st.set_page_config(
    page_title="Dashboard USMP - Versión Estable",
    layout="wide",
    page_icon="⚽"
)

# URLs (VERIFICA ESTOS ENLACES)
LOGO_URL = "https://ibb.co/5hKcnyZ3"  # Reemplaza con tu logo real
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        # Lectura robusta del CSV
        df = pd.read_csv(
            DATA_URL,
            encoding='utf-8',
            sep=',',
            parse_dates=['Fecha'],
            dayfirst=True,
            dtype={'Jugador': str},
            on_bad_lines='warn'
        )
        
        # Columnas obligatorias
        columnas_requeridas = ['Jugador', 'Fecha']
        for col in columnas_requeridas:
            if col not in df.columns:
                st.error(f"❌ Columna faltante: {col}")
                return pd.DataFrame()

        # Limpieza de datos
        df = df.dropna(subset=['Jugador'])  # Elimina filas sin jugador
        df['Jugador'] = df['Jugador'].str.strip()  # Limpia espacios
        
        # Procesamiento de fechas
        try:
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.date
            df = df.dropna(subset=['Fecha'])  # Elimina filas sin fecha válida
        except Exception as e:
            st.error(f"Error en fechas: {str(e)}")
            return pd.DataFrame()

        # Columnas de pruebas con limpieza exhaustiva
        pruebas_columns = [
            "THOMAS PSOAS D", "THOMAS PSOAS I",
            "THOMAS CUADRICEPS D", "THOMAS CUADRICEPS I",
            "THOMAS SARTORIO D", "THOMAS SARTORIO I",
            "JURDAN D", "JURDAN I"
        ]
        
        for col in pruebas_columns:
            if col in df.columns:
                # Conversión segura a números
                df[col] = (
                    df[col].astype(str)
                    .str.replace(',', '.', regex=False)
                    .str.replace(r'[^\d.]', '', regex=True)
                    .replace('', '0')
                )
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0  # Columna faltante se llena con 0

        return df

    except Exception as e:
        st.error(f"🚨 Error crítico al cargar datos: {str(e)}")
        return pd.DataFrame()

# Umbrales predefinidos
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

# Interfaz mejorada
def main():
    st.image(LOGO_URL, width=200)
    st.title("📊 Dashboard de Pruebas USMP - Versión Estable")
    
    df = cargar_datos()
    
    if df.empty:
        st.warning("⚠️ No hay datos válidos para mostrar. Verifica tu archivo CSV.")
        return
    
    # Panel de diagnóstico (ocultable)
    with st.expander("🔍 Diagnóstico técnico (solo para administradores)"):
        st.write("📝 Columnas detectadas:", df.columns.tolist())
        st.write("📅 Rango de fechas:", df['Fecha'].min(), "a", df['Fecha'].max())
        st.write("👥 Total de jugadores:", len(df['Jugador'].unique()))
    
    # Filtros mejorados
    st.sidebar.header("⚙️ Filtros")
    
    jugadores = st.sidebar.multiselect(
        "Seleccionar Jugador",
        options=sorted(df['Jugador'].unique()),
        default=None,
        key='jugador_filter'
    )
    
    fechas = st.sidebar.multiselect(
        "Seleccionar Fecha",
        options=sorted(df['Fecha'].unique(), reverse=True),
        default=None,
        key='fecha_filter'
    )
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if jugadores:
        df_filtrado = df_filtrado[df_filtrado['Jugador'].isin(jugadores)]
    if fechas:
        df_filtrado = df_filtrado[df_filtrado['Fecha'].isin(fechas)]
    
    # Mostrar resultados
    st.subheader("📋 Resultados Filtrados")
    
    if df_filtrado.empty:
        st.warning("⚠️ No hay datos con los filtros seleccionados")
    else:
        # Aplicar iconos
        for col, umbral in UMBRALES.items():
            if col in df_filtrado.columns:
                df_filtrado[col] = df_filtrado[col].apply(lambda x: mostrar_icono(x, umbral))
        
        # Mostrar tabla con estilo
        st.dataframe(
            df_filtrado.style.applymap(
                lambda x: 'color: green' if x == "👍" else ('color: red' if x == "👎" else ''),
                subset=list(UMBRALES.keys())
            ),
            height=700,
            use_container_width=True,
            hide_index=True,
            column_order=["Jugador", "Fecha"] + list(UMBRALES.keys())
        )
    
    # Pie de página
    st.sidebar.markdown("---")
    st.sidebar.caption(f"🔄 Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

if __name__ == "__main__":
    main()
