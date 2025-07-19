import pandas as pd
import streamlit as st
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# Configuración esencial para mostrar emojis
st.set_page_config(
    page_title="Resultados USMP",
    layout="wide",
    page_icon="⚽"
)

# URLs de recursos
LOGO_URL = "https://i.ibb.co/5hKcnyZ3/logo-usmp.png"
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

# Umbrales para las pruebas (con emojis directos)
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
        return None

def cargar_datos():
    try:
        df = pd.read_csv(DATA_URL)
        
        # Normalizar nombres de columnas
        df.columns = [col.strip().upper() for col in df.columns]
        
        # Mapeo flexible de columnas
        columnas_requeridas = {
            'JUGADOR': ['JUGADOR', 'NOMBRE', 'ATLETA'],
            'CATEGORIA': ['CATEGORIA', 'CATEGORÍA', 'GRUPO'],
            'FECHA': ['FECHA', 'FECHA PRUEBA']
        }
        
        # Buscar coincidencias
        mapeo = {}
        for estandar, alternativas in columnas_requeridas.items():
            for alt in alternativas:
                if alt in df.columns:
                    mapeo[alt] = estandar
                    break
        
        # Renombrar columnas
        df = df.rename(columns=mapeo)
        
        # Limpieza básica
        df = df.dropna(subset=['JUGADOR', 'FECHA'])
        
        # Convertir fechas
        df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce').dt.date
        
        # Procesar valores numéricos
        for prueba in PRUEBAS:
            if prueba.upper() in df.columns:
                df[prueba] = pd.to_numeric(
                    df[prueba.upper()].astype(str)
                    .str.replace(',', '.')
                    .str.replace(r'[^\d.]', '', regex=True),
                    errors='coerce'
                )
        
        return df
    
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return None

def main():
    # Configurar encoding para emojis
    import sys
    import codecs
    if sys.stdout.encoding != 'UTF-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    
    # Cargar logo
    logo = cargar_logo()
    if logo:
        st.sidebar.image(logo, width=150)
    
    st.title("📊 Resultados de Pruebas de Movilidad")
    
    # Cargar datos
    datos = cargar_datos()
    
    if datos is None:
        st.error("No se pudieron cargar los datos. Verifica el archivo.")
        return
    
    if datos.empty:
        st.warning("No hay datos disponibles")
        return
    
    # Filtros
    st.sidebar.header("🔍 Filtros")
    
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
        # Preparar datos para mostrar
        df_mostrar = datos.copy()
        
        # Aplicar iconos solo a columnas existentes
        pruebas_disponibles = [p for p in PRUEBAS if p in df_mostrar.columns]
        
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
        
        # Mostrar tabla con emojis
        st.dataframe(
            df_mostrar[columnas_mostrar].style.applymap(
                lambda x: 'color: green' if x == PRUEBAS[next(iter(PRUEBAS))]["icono_ok"] else 
                         'color: red' if x == PRUEBAS[next(iter(PRUEBAS))]["icono_fail"] else 
                         'color: gray',
                subset=pruebas_disponibles
            ),
            height=600,
            use_container_width=True
        )
        
        # Mostrar estadísticas
        if pruebas_disponibles:
            st.subheader("📈 Estadísticas")
            st.dataframe(
                datos[pruebas_disponibles].describe().round(1),
                use_container_width=True
            )

if __name__ == "__main__":
    main()
