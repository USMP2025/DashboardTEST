import pandas as pd
import streamlit as st
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# Configuración del dashboard
st.set_page_config(
    page_title="Dashboard de Pruebas USMP",
    layout="wide",
    page_icon="⚽"
)

# URLs de recursos
LOGO_URL = "https://i.ibb.co/5hKcnyZ3/logo-usmp.png"
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

# Umbrales para las pruebas
PRUEBAS = {
    "THOMAS PSOAS D": {"umbral": 10, "unidad": "grados"},
    "THOMAS PSOAS I": {"umbral": 10, "unidad": "grados"},
    "THOMAS CUADRICEPS D": {"umbral": 50, "unidad": "grados"},
    "THOMAS CUADRICEPS I": {"umbral": 50, "unidad": "grados"},
    "THOMAS SARTORIO D": {"umbral": 80, "unidad": "grados"},
    "THOMAS SARTORIO I": {"umbral": 80, "unidad": "grados"},
    "JURDAN D": {"umbral": 75, "unidad": "cm"},
    "JURDAN I": {"umbral": 75, "unidad": "cm"}
}

def cargar_logo():
    try:
        response = requests.get(LOGO_URL, timeout=10)
        return Image.open(BytesIO(response.content))
    except:
        return None

def cargar_datos():
    try:
        # Cargar datos y mostrar columnas disponibles para diagnóstico
        df = pd.read_csv(DATA_URL)
        st.session_state.columnas_disponibles = df.columns.tolist()
        
        # Normalizar nombres de columnas
        df.columns = [col.strip().upper() for col in df.columns]
        
        # Mapeo flexible de columnas
        mapeo_columnas = {
            'JUGADOR': ['JUGADOR', 'NOMBRE', 'ATLETA'],
            'CATEGORIA': ['CATEGORIA', 'CATEGORÍA', 'GRUPO'],
            'FECHA': ['FECHA', 'FECHA PRUEBA']
        }
        
        # Encontrar columnas reales
        columnas_renombradas = {}
        for nombre_estandar, alternativas in mapeo_columnas.items():
            for alt in alternativas:
                if alt in df.columns:
                    columnas_renombradas[alt] = nombre_estandar
                    break
        
        # Verificar que tenemos todas las columnas necesarias
        if len(columnas_renombradas) < 3:
            st.error(f"No se encontraron todas las columnas necesarias. Columnas disponibles: {df.columns.tolist()}")
            return None
        
        # Renombrar columnas
        df = df.rename(columns=columnas_renombradas)
        
        # Limpieza básica
        df = df.dropna(subset=['JUGADOR', 'FECHA'])
        
        # Convertir fechas
        try:
            df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True).dt.date
        except:
            df['FECHA'] = pd.to_datetime(df['FECHA']).dt.date
        
        # Procesar valores numéricos
        for prueba in PRUEBAS:
            prueba_norm = prueba.upper()
            if prueba_norm in df.columns:
                df[prueba] = pd.to_numeric(
                    df[prueba_norm].astype(str)
                    .str.replace(',', '.')
                    .str.replace(r'[^\d.]', '', regex=True),
                    errors='coerce'
                )
        
        return df
    
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return None

def main():
    logo = cargar_logo()
    if logo:
        st.sidebar.image(logo, width=150)
    
    st.title("Dashboard de Pruebas de Movilidad")
    
    # Cargar datos con manejo de errores
    datos = cargar_datos()
    
    if datos is None:
        if hasattr(st.session_state, 'columnas_disponibles'):
            st.error(f"Columnas disponibles en el archivo: {st.session_state.columnas_disponibles}")
        return
    
    if datos.empty:
        st.warning("El archivo no contiene datos válidos")
        return
    
    # Mostrar información general
    st.sidebar.markdown(f"**Total registros:** {len(datos)}")
    st.sidebar.markdown(f"**Rango fechas:** {datos['FECHA'].min()} a {datos['FECHA'].max()}")
    
    # Filtros
    st.sidebar.header("Filtros")
    
    jugadores = st.sidebar.multiselect(
        "Jugadores",
        options=sorted(datos['JUGADOR'].unique())
    )
    
    categorias = st.sidebar.multiselect(
        "Categorías",
        options=sorted(datos['CATEGORIA'].unique()) if 'CATEGORIA' in datos.columns else []
    )
    
    fechas = st.sidebar.multiselect(
        "Fechas",
        options=sorted(datos['FECHA'].unique(), reverse=True)
    )
    
    # Aplicar filtros
    if jugadores:
        datos = datos[datos['JUGADOR'].isin(jugadores)]
    if categorias and 'CATEGORIA' in datos.columns:
        datos = datos[datos['CATEGORIA'].isin(categorias)]
    if fechas:
        datos = datos[datos['FECHA'].isin(fechas)]
    
    # Mostrar resultados
    if datos.empty:
        st.warning("No hay datos con los filtros seleccionados")
    else:
        # Preparar datos para visualización
        df_mostrar = datos.copy()
        
        # Aplicar evaluación solo a columnas existentes
        pruebas_disponibles = [p for p in PRUEBAS if p in df_mostrar.columns]
        
        for prueba in pruebas_disponibles:
            df_mostrar[prueba] = df_mostrar[prueba].apply(
                lambda x: "✅" if not pd.isna(x) and x >= PRUEBAS[prueba]["umbral"] else "❌" if not pd.isna(x) else "❓"
            )
        
        # Columnas a mostrar (solo las disponibles)
        columnas_base = ['JUGADOR', 'CATEGORIA', 'FECHA'] if 'CATEGORIA' in df_mostrar.columns else ['JUGADOR', 'FECHA']
        columnas_mostrar = [c for c in columnas_base + pruebas_disponibles if c in df_mostrar.columns]
        
        # Mostrar tabla
        st.dataframe(
            df_mostrar[columnas_mostrar].style.applymap(
                lambda x: 'color: green' if x == "✅" else 'color: red' if x == "❌" else 'color: gray',
                subset=pruebas_disponibles
            ),
            height=600,
            use_container_width=True
        )
        
        # Mostrar estadísticas
        if pruebas_disponibles:
            st.subheader("Estadísticas")
            st.dataframe(
                datos[pruebas_disponibles].describe().round(1),
                use_container_width=True
            )

if __name__ == "__main__":
    main()
