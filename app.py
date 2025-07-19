import pandas as pd
import streamlit as st
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# Configuración del dashboard
st.set_page_config(
    page_title="Resultados de Pruebas USMP",
    layout="wide",
    page_icon="⚽"
)

# URLs de recursos
LOGO_URL = "https://i.ibb.co/5hKcnyZ3/logo-usmp.png"
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

# Umbrales para las pruebas con emojis directos
PRUEBAS = {
    "THOMAS PSOAS D": {"umbral": 10, "icono_ok": "👍", "icono_fail": "👎"},
    "THOMAS PSOAS I": {"umbral": 10, "icono_ok": "👍", "icono_fail": "👎"},
    "THOMAS CUADRICEPS D": {"umbral": 50, "icono_ok": "👍", "icono_fail": "👎"},
    "THOMAS CUADRICEPS I": {"umbral": 50, "icono_ok": "👍", "icono_fail": "👎"},
    "THOMAS SARTORIO D": {"umbral": 80, "icono_ok": "👍", "icono_fail": "👎"},
    "THOMAS SARTORIO I": {"umbral": 80, "icono_ok": "👍", "icono_fail": "👎"},
    "JURDAN D": {"umbral": 75, "icono_ok": "👍", "icono_fail": "👎"},
    "JURDAN I": {"umbral": 75, "icono_ok": "👍", "icono_fail": "👎"}
}

def cargar_logo():
    try:
        response = requests.get(LOGO_URL, timeout=10)
        return Image.open(BytesIO(response.content))
    except:
        st.sidebar.warning("No se pudo cargar el logo")
        return None

def cargar_datos():
    try:
        # Cargar el archivo CSV
        df = pd.read_csv(DATA_URL)
        
        # Normalizar nombres de columnas
        df.columns = [col.strip().upper() for col in df.columns]
        
        # Mapeo flexible de columnas
        mapeo_columnas = {
            'JUGADOR': ['JUGADOR', 'NOMBRE', 'ATLETA'],
            'CATEGORIA': ['CATEGORIA', 'CATEGORÍA', 'GRUPO'],
            'FECHA': ['FECHA', 'FECHA PRUEBA']
        }
        
        # Buscar coincidencias para cada columna requerida
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
        
        # Limpieza básica de datos
        df = df.dropna(subset=['JUGADOR', 'FECHA'])
        
        # Convertir fechas
        df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce').dt.date
        
        # Procesar valores numéricos para cada prueba
        for prueba in PRUEBAS:
            if prueba in df.columns:
                df[prueba] = pd.to_numeric(
                    df[prueba].astype(str)
                    .str.replace(',', '.')
                    .str.replace(r'[^\d.]', '', regex=True),
                    errors='coerce'
                )
        
        return df
    
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return None

def main():
    # Cargar logo
    logo = cargar_logo()
    if logo:
        st.sidebar.image(logo, width=150)
    
    st.title("⚽ Resultados de Pruebas de Movilidad")
    
    # Cargar datos
    datos = cargar_datos()
    
    if datos is None:
        st.error("No se pudieron cargar los datos. Verifica el archivo.")
        return
    
    if datos.empty:
        st.warning("No hay datos disponibles")
        return
    
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
        
        # Identificar qué pruebas están disponibles en los datos
        pruebas_disponibles = [p for p in PRUEBAS if p in df_mostrar.columns]
        
        # Aplicar iconos a cada prueba disponible
        for prueba in pruebas_disponibles:
            df_mostrar[prueba] = df_mostrar[prueba].apply(
                lambda x: (
                    PRUEBAS[prueba]["icono_ok"] if not pd.isna(x) and x >= PRUEBAS[prueba]["umbral"]
                    else PRUEBAS[prueba]["icono_fail"] if not pd.isna(x)
                    else "❓"
                )
            )
        
        # Seleccionar columnas a mostrar
        columnas_base = ['JUGADOR', 'CATEGORIA', 'FECHA'] if 'CATEGORIA' in df_mostrar.columns else ['JUGADOR', 'FECHA']
        columnas_mostrar = [c for c in columnas_base + pruebas_disponibles if c in df_mostrar.columns]
        
        # Mostrar tabla con los iconos de pulgares
        st.dataframe(
            df_mostrar[columnas_mostrar].style.applymap(
                lambda x: 'color: green' if x == "👍" else 
                         'color: red' if x == "👎" else 
                         'color: gray',
                subset=pruebas_disponibles
            ),
            height=600,
            use_container_width=True,
            hide_index=True
        )
        
        # Mostrar estadísticas si hay pruebas disponibles
        if pruebas_disponibles:
            st.subheader("Estadísticas")
            st.dataframe(
                datos[pruebas_disponibles].describe().round(1),
                use_container_width=True
            )

if __name__ == "__main__":
    main()
