import pandas as pd
import streamlit as st
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# 1. Configuración inicial
st.set_page_config(
    page_title="Dashboard de Pruebas USMP",
    layout="wide",
    page_icon="⚽"
)

# 2. URLs de recursos
LOGO_URL = "https://i.ibb.co/5hKcnyZ3/logo-usmp.png"
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

# 3. Configuración de pruebas
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

# 4. Función para normalizar nombres de columnas
def normalizar_nombre(col):
    return (col.strip().upper()
            .replace("Á", "A").replace("É", "E").replace("Í", "I")
            .replace("Ó", "O").replace("Ú", "U"))

# 5. Función para cargar datos con manejo robusto
def cargar_datos():
    try:
        # Descargar datos
        df = pd.read_csv(DATA_URL)
        
        # Normalizar nombres de columnas
        df.columns = [normalizar_nombre(col) for col in df.columns]
        
        # Mapeo de columnas alternativas
        columnas_requeridas = {
            'JUGADOR': ['JUGADOR', 'NOMBRE', 'ATLETA'],
            'CATEGORIA': ['CATEGORIA', 'CATEGORÍA', 'GRUPO', 'EQUIPO'],
            'FECHA': ['FECHA', 'FECHA PRUEBA', 'FECHAEVALUACION']
        }
        
        # Verificar columnas
        columnas_encontradas = {}
        for tipo, alternativas in columnas_requeridas.items():
            for alt in alternativas:
                if alt in df.columns:
                    columnas_encontradas[tipo] = alt
                    break
            else:
                st.error(f"No se encontró columna para: {tipo}")
                return None
        
        # Renombrar columnas
        df = df.rename(columns={
            columnas_encontradas['JUGADOR']: 'Jugador',
            columnas_encontradas['CATEGORIA']: 'Categoria',
            columnas_encontradas['FECHA']: 'Fecha'
        })
        
        # Limpieza de datos
        df = df.dropna(subset=['Jugador', 'Fecha'])
        
        # Convertir fechas
        try:
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True).dt.date
        except:
            df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        
        # Limpieza de categorías
        df['Categoria'] = df['Categoria'].fillna('Sin categoría').str.strip()
        
        # Procesar valores numéricos
        for prueba in PRUEBAS:
            col_normalizada = normalizar_nombre(prueba)
            if col_normalizada in df.columns:
                df[prueba] = pd.to_numeric(
                    df[col_normalizada].astype(str)
                    .str.replace(',', '.')
                    .str.replace(r'[^\d.]', '', regex=True),
                    errors='coerce'
                )
        
        return df
    
    except Exception as e:
        st.error(f"Error al procesar datos: {str(e)}")
        return None

# 6. Función principal
def main():
    # Cargar logo
    try:
        response = requests.get(LOGO_URL, timeout=10)
        logo = Image.open(BytesIO(response.content))
        st.sidebar.image(logo, width=150)
    except:
        st.sidebar.warning("Logo no disponible")

    st.title("⚽ Dashboard de Pruebas de Movilidad")
    st.markdown("---")
    
    # Cargar datos
    datos = cargar_datos()
    
    if datos is None or datos.empty:
        st.error("No se pudieron cargar datos válidos. Verifica el archivo fuente.")
        return
    
    # Filtros
    st.sidebar.header("Filtros")
    
    jugadores = st.sidebar.multiselect(
        "Jugadores",
        options=sorted(datos['Jugador'].unique())
    )
    
    categorias = st.sidebar.multiselect(
        "Categorías",
        options=sorted(datos['Categoria'].unique())
    )
    
    fechas = st.sidebar.multiselect(
        "Fechas",
        options=sorted(datos['Fecha'].unique(), reverse=True)
    )
    
    # Aplicar filtros
    if jugadores:
        datos = datos[datos['Jugador'].isin(jugadores)]
    if categorias:
        datos = datos[datos['Categoria'].isin(categorias)]
    if fechas:
        datos = datos[datos['Fecha'].isin(fechas)]
    
    # Mostrar resultados
    if datos.empty:
        st.warning("No hay datos con los filtros seleccionados")
    else:
        # Preparar datos para visualización
        df_mostrar = datos.copy()
        
        # Evaluar resultados
        for prueba, config in PRUEBAS.items():
            if prueba in df_mostrar.columns:
                df_mostrar[prueba] = df_mostrar[prueba].apply(
                    lambda x: "✅" if not pd.isna(x) and x >= config["umbral"] else "❌" if not pd.isna(x) else "❓"
                )
        
        # Mostrar tabla
        columnas_mostrar = ['Jugador', 'Categoria', 'Fecha'] + list(PRUEBAS.keys())
        columnas_mostrar = [c for c in columnas_mostrar if c in df_mostrar.columns]
        
        st.dataframe(
            df_mostrar[columnas_mostrar].style.applymap(
                lambda x: 'color: green' if x == "✅" else 
                         'color: red' if x == "❌" else 'color: gray',
                subset=list(PRUEBAS.keys())
            ),
            height=600,
            use_container_width=True
        )
        
        # Mostrar estadísticas
        st.subheader("Estadísticas")
        st.dataframe(
            datos[list(PRUEBAS.keys())].describe().round(1),
            use_container_width=True
        )

if __name__ == "__main__":
    main()
