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

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        # Leer CSV directamente desde Google Drive
        df = pd.read_csv(DATA_URL, encoding='utf-8')
        
        # Verificar las columnas disponibles
        st.write("Columnas encontradas en el CSV:", df.columns.tolist())
        
        # Mapeo de columnas (ajustado según el CSV real)
        column_map = {
            'JUGADOR': 'Jugador',
            'CATEGORIA': 'Categoría',  # Nota: En tu CSV es CATEGORIA sin acento
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
        
        # Renombrar columnas
        df = df.rename(columns=column_map)
        
        # Limpieza y conversión de datos
        df = df.dropna(subset=['Jugador', 'Fecha'])
        
        # Convertir fecha (manejar diferentes formatos)
        try:
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True).dt.date
        except:
            df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
            
        df['Categoría'] = df['Categoría'].fillna('Sin categoría').str.strip()
        
        # Procesar valores numéricos
        for col in UMBRALES.keys():
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str)
                    .str.replace(',', '.')
                    .str.replace(r'[^\d.]', '', regex=True),
                    errors='coerce'
                )
        
        return df

    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return pd.DataFrame()

def mostrar_icono(valor, umbral):
    if pd.isna(valor):
        return "❓"
    try:
        return "👍" if float(valor) >= umbral else "👎"
    except:
        return "❓"

# Interfaz principal
def main():
    # Logo
    logo = cargar_logo()
    if logo:
        st.sidebar.image(logo, width=200)
    
    st.title("Dashboard de Resultados de Pruebas de Movilidad")
    
    # Cargar datos
    df = cargar_datos()
    
    if df.empty:
        st.warning("No se pudieron cargar datos. Verifica la conexión y el formato del archivo.")
        return
    
    # Mostrar vista previa de los datos
    with st.expander("Ver datos crudos"):
        st.dataframe(df.head())
    
    # Filtros en sidebar
    st.sidebar.header("Filtros")
    
    # Obtener opciones únicas
    opciones_jugador = sorted(df['Jugador'].unique())
    opciones_categoria = sorted(df['Categoría'].unique())
    opciones_fecha = sorted(df['Fecha'].unique(), reverse=True)
    
    # Widgets de filtro
    jugador_seleccionado = st.sidebar.multiselect(
        "Seleccionar Jugador(es)",
        options=opciones_jugador
    )
    
    categoria_seleccionada = st.sidebar.multiselect(
        "Seleccionar Categoría(s)",
        options=opciones_categoria
    )
    
    fecha_seleccionada = st.sidebar.multiselect(
        "Seleccionar Fecha(s)",
        options=opciones_fecha
    )
    
    # Aplicar filtros
    filtro_aplicado = False
    df_filtrado = df.copy()
    
    if jugador_seleccionado:
        df_filtrado = df_filtrado[df_filtrado['Jugador'].isin(jugador_seleccionado)]
        filtro_aplicado = True
    
    if categoria_seleccionada:
        df_filtrado = df_filtrado[df_filtrado['Categoría'].isin(categoria_seleccionada)]
        filtro_aplicado = True
    
    if fecha_seleccionada:
        df_filtrado = df_filtrado[df_filtrado['Fecha'].isin(fecha_seleccionada)]
        filtro_aplicado = True
    
    # Mostrar resultados
    st.subheader("Resultados de Pruebas")
    
    if not filtro_aplicado:
        st.info("Usa los filtros en la barra lateral para explorar los datos")
    elif df_filtrado.empty:
        st.warning("No hay resultados con los filtros seleccionados")
    else:
        # Crear copia para mostrar con iconos
        df_mostrar = df_filtrado.copy()
        
        # Aplicar iconos a las columnas de pruebas
        for prueba, umbral in UMBRALES.items():
            if prueba in df_mostrar.columns:
                df_mostrar[prueba] = df_mostrar[prueba].apply(lambda x: mostrar_icono(x, umbral))
        
        # Seleccionar columnas a mostrar
        columnas_mostrar = ["Jugador", "Categoría", "Fecha"] + list(UMBRALES.keys())
        columnas_mostrar = [col for col in columnas_mostrar if col in df_mostrar.columns]
        
        # Mostrar tabla con estilo
        st.dataframe(
            df_mostrar[columnas_mostrar].style.applymap(
                lambda x: 'color: green' if x == "👍" else ('color: red' if x == "👎" else 'color: gray'),
                subset=list(UMBRALES.keys())
            ),
            height=700,
            use_container_width=True,
            hide_index=True
        )
        
        # Mostrar resumen estadístico
        st.subheader("Resumen Estadístico")
        st.dataframe(
            df_filtrado[list(UMBRALES.keys())].describe().round(2),
            use_container_width=True
        )

if __name__ == "__main__":
    main()
