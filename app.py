import pandas as pd
import streamlit as st
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
import base64

# Configuración del dashboard
st.set_page_config(
    page_title="Resultados de Pruebas USMP",
    layout="wide",
    page_icon="⚽"
)

# URLs de recursos
LOGO_URL = "https://i.ibb.co/5hKcnyZ3/logo-usmp.png"
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

# Umbrales para las pruebas
PRUEBAS = {
    "THOMAS PSOAS D": {"umbral": 10, "aprobado": "👍", "reprobado": "👎"},
    "THOMAS PSOAS I": {"umbral": 10, "aprobado": "👍", "reprobado": "👎"},
    "THOMAS CUADRICEPS D": {"umbral": 50, "aprobado": "👍", "reprobado": "👎"},
    "THOMAS CUADRICEPS I": {"umbral": 50, "aprobado": "👍", "reprobado": "👎"},
    "THOMAS SARTORIO D": {"umbral": 80, "aprobado": "👍", "reprobado": "👎"},
    "THOMAS SARTORIO I": {"umbral": 80, "aprobado": "👍", "reprobado": "👎"},
    "JURDAN D": {"umbral": 75, "aprobado": "👍", "reprobado": "👎"},
    "JURDAN I": {"umbral": 75, "aprobado": "👍", "reprobado": "👎"}
}

# Función mejorada para cargar el logo
def cargar_logo():
    try:
        response = requests.get(LOGO_URL, timeout=10)
        img = Image.open(BytesIO(response.content))
        
        # Convertir a base64 para mayor compatibilidad
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Mostrar usando HTML para evitar problemas de caché
        logo_html = f"""
        <div style="display: flex; justify-content: center;">
            <img src="data:image/png;base64,{img_str}" width="200">
        </div>
        """
        return logo_html
    except Exception as e:
        st.sidebar.warning(f"No se pudo cargar el logo: {str(e)}")
        return None

# Función para cargar datos
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

# Función para mostrar iconos con formato HTML
def formato_icono(valor, prueba):
    if pd.isna(valor):
        return "<span style='color:gray'>❓</span>"
    elif valor >= PRUEBAS[prueba]["umbral"]:
        return "<span style='color:green;font-size:18px'>👍</span>"
    else:
        return "<span style='color:red;font-size:18px'>👎</span>"

def main():
    # Mostrar logo usando HTML
    logo_html = cargar_logo()
    if logo_html:
        st.sidebar.markdown(logo_html, unsafe_allow_html=True)
    
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
        
        # Aplicar formato a las pruebas disponibles
        pruebas_disponibles = [p for p in PRUEBAS if p in df_mostrar.columns]
        
        # Crear HTML para la tabla
        html = """
        <style>
            table {width:100%; border-collapse:collapse;}
            th {background-color:#f0f2f6; text-align:left; padding:8px;}
            td {padding:8px; border-bottom:1px solid #ddd;}
        </style>
        <table>
            <tr>
                <th>Jugador</th>
                <th>Categoría</th>
                <th>Fecha</th>
        """
        
        # Agregar encabezados de pruebas
        for prueba in pruebas_disponibles:
            html += f"<th>{prueba}</th>"
        html += "</tr>"
        
        # Agregar filas de datos
        for _, row in df_mostrar.iterrows():
            html += "<tr>"
            html += f"<td>{row['JUGADOR']}</td>"
            html += f"<td>{row.get('CATEGORIA', '')}</td>"
            html += f"<td>{row['FECHA']}</td>"
            
            for prueba in pruebas_disponibles:
                valor = row[prueba]
                html += f"<td>{formato_icono(valor, prueba)}</td>"
            
            html += "</tr>"
        
        html += "</table>"
        
        # Mostrar tabla HTML
        st.markdown(html, unsafe_allow_html=True)
        
        # Mostrar estadísticas
        if pruebas_disponibles:
            st.subheader("📈 Estadísticas")
            st.dataframe(
                datos[pruebas_disponibles].describe().round(1),
                use_container_width=True
            )

if __name__ == "__main__":
    main()
