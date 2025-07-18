import pandas as pd
import streamlit as st
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# Configuración del dashboard
st.set_page_config(
    page_title="Dashboard de Pruebas de Movilidad USMP",
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
        logo = Image.open(BytesIO(response.content))
        return logo
    except Exception as e:
        st.sidebar.warning(f"No se pudo cargar el logo: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def cargar_datos():
    try:
        # Descargar y leer los datos
        df = pd.read_csv(DATA_URL)
        
        # Verificar estructura de datos
        st.session_state.columnas_originales = df.columns.tolist()
        
        # Estandarizar nombres de columnas
        mapeo_columnas = {
            'JUGADOR': 'Jugador',
            'CATEGORIA': 'Categoría',
            'FECHA': 'Fecha'
        }
        
        # Renombrar columnas
        df = df.rename(columns=mapeo_columnas)
        
        # Limpieza básica de datos
        df = df.dropna(subset=['Jugador', 'Fecha'])
        
        # Convertir fechas
        try:
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True).dt.date
        except:
            df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        
        # Limpieza de categorías
        df['Categoría'] = df['Categoría'].fillna('Sin categoría').str.strip()
        
        # Procesar valores numéricos
        for prueba in UMBRALES:
            if prueba in df.columns:
                df[prueba] = pd.to_numeric(
                    df[prueba].astype(str)
                    .str.replace(',', '.')
                    .str.replace(r'[^\d.]', '', regex=True),
                    errors='coerce'
                )
        
        return df, None
    
    except Exception as e:
        return None, f"Error al cargar datos: {str(e)}"

def mostrar_icono(valor, umbral):
    try:
        if pd.isna(valor):
            return "❓"
        return "👍" if float(valor) >= umbral else "👎"
    except:
        return "❓"

def aplicar_filtros(df, jugadores, categorias, fechas):
    try:
        mask = pd.Series(True, index=df.index)
        
        if jugadores:
            mask &= df['Jugador'].isin(jugadores)
        if categorias:
            mask &= df['Categoría'].isin(categorias)
        if fechas:
            mask &= df['Fecha'].isin(fechas)
        
        return df[mask]
    except Exception as e:
        st.error(f"Error al aplicar filtros: {str(e)}")
        return df

def main():
    try:
        # Cargar logo
        logo = cargar_logo()
        if logo:
            st.sidebar.image(logo, width=150)
        
        st.title("⚽ Dashboard de Pruebas de Movilidad USMP")
        st.markdown("---")
        
        # Cargar datos con manejo de errores
        df, error = cargar_datos()
        
        if error or df is None:
            st.error(error)
            if hasattr(st.session_state, 'columnas_originales'):
                st.warning(f"Columnas encontradas en el archivo: {st.session_state.columnas_originales}")
            return
        
        if df.empty:
            st.warning("El archivo no contiene datos válidos.")
            return
        
        # Mostrar resumen inicial
        st.sidebar.markdown(f"**Total de registros:** {len(df)}")
        st.sidebar.markdown(f"**Período:** {df['Fecha'].min()} al {df['Fecha'].max()}")
        
        # Filtros en sidebar
        st.sidebar.header("Filtros")
        
        jugadores = st.sidebar.multiselect(
            "Seleccionar Jugador(es)",
            options=sorted(df['Jugador'].unique()),
            default=None
        )
        
        categorias = st.sidebar.multiselect(
            "Seleccionar Categoría(s)",
            options=sorted(df['Categoría'].unique()),
            default=None
        )
        
        fechas = st.sidebar.multiselect(
            "Seleccionar Fecha(s)",
            options=sorted(df['Fecha'].unique(), reverse=True),
            default=None
        )
        
        # Aplicar filtros
        df_filtrado = aplicar_filtros(df, jugadores, categorias, fechas)
        
        # Mostrar resultados
        st.header("Resultados de Pruebas")
        
        if df_filtrado.empty:
            st.warning("No hay registros con los filtros seleccionados")
        else:
            # Preparar datos para visualización
            df_mostrar = df_filtrado.copy()
            
            # Aplicar iconos
            for prueba in UMBRALES:
                if prueba in df_mostrar.columns:
                    df_mostrar[prueba] = df_mostrar[prueba].apply(
                        lambda x: mostrar_icono(x, UMBRALES[prueba])
            
            # Seleccionar columnas a mostrar
            columnas_mostrar = ['Jugador', 'Categoría', 'Fecha'] + list(UMBRALES.keys())
            columnas_mostrar = [c for c in columnas_mostrar if c in df_mostrar.columns]
            
            # Mostrar tabla con estilo
            st.dataframe(
                df_mostrar[columnas_mostrar].style.applymap(
                    lambda x: 'color: green' if x == "👍" else 
                             ('color: red' if x == "👎" else 'color: gray'),
                    subset=list(UMBRALES.keys())
                ),
                height=600,
                use_container_width=True,
                hide_index=True
            )
            
            # Mostrar estadísticas
            st.subheader("Estadísticas")
            st.dataframe(
                df_filtrado[list(UMBRALES.keys())].describe().round(1),
                use_container_width=True
            )
            
            # Exportar datos
            st.download_button(
                label="Descargar datos filtrados",
                data=df_filtrado.to_csv(index=False).encode('utf-8'),
                file_name=f"resultados_movilidad_{datetime.now().date()}.csv",
                mime="text/csv"
            )
            
    except Exception as e:
        st.error(f"Error inesperado: {str(e)}")

if __name__ == "__main__":
    main()
