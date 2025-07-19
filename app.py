import pandas as pd
import streamlit as st
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# 1. CONFIGURACIÓN INICIAL DE LA APLICACIÓN
st.set_page_config(
    page_title="Resultados de Pruebas USMP",
    layout="wide",
    page_icon="⚽"
)

# 2. URLS DE RECURSOS
LOGO_URL = "https://i.ibb.co/5hKcnyZ3/logo-usmp.png"
DATA_URL = "https://drive.google.com/uc?export=download&id=1ydetYhuHUcUGQl3ImcK2eGR-fzGaADXi"

# 3. DEFINICIÓN DE UMBRALES PARA LAS PRUEBAS
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

# 4. FUNCIÓN PARA CARGAR EL LOGO
def cargar_logo():
    try:
        response = requests.get(LOGO_URL, timeout=10)
        logo = Image.open(BytesIO(response.content))
        return logo
    except Exception as e:
        st.sidebar.error(f"No se pudo cargar el logo: {str(e)}")
        return None

# 5. FUNCIÓN PARA CARGAR LOS DATOS
def cargar_datos():
    try:
        # Descargar el archivo CSV
        df = pd.read_csv(DATA_URL)
        
        # Verificar las columnas disponibles
        st.session_state.columnas_disponibles = df.columns.tolist()
        
        # Estandarizar nombres de columnas
        df = df.rename(columns={
            'JUGADOR': 'Jugador',
            'CATEGORIA': 'Categoría',
            'FECHA': 'Fecha'
        })
        
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
        st.error(f"Error crítico al cargar datos: {str(e)}")
        return pd.DataFrame()

# 6. FUNCIÓN PARA MOSTRAR RESULTADOS CON ICONOS
def evaluar_resultado(valor, umbral):
    try:
        if pd.isna(valor):
            return ("❓", "gray")
        if float(valor) >= umbral:
            return ("✅", "green")
        else:
            return ("❌", "red")
    except:
        return ("⚠️", "orange")

# 7. FUNCIÓN PRINCIPAL
def main():
    try:
        # Cargar logo
        logo = cargar_logo()
        if logo:
            st.sidebar.image(logo, width=150)
        
        st.title("📊 Resultados de Pruebas de Movilidad")
        st.markdown("---")
        
        # Cargar datos
        datos = cargar_datos()
        
        if datos.empty:
            st.warning("No se encontraron datos válidos en el archivo.")
            if hasattr(st.session_state, 'columnas_disponibles'):
                st.info(f"Columnas encontradas: {st.session_state.columnas_disponibles}")
            return
        
        # Mostrar información general
        st.sidebar.markdown(f"**Total de registros:** {len(datos)}")
        st.sidebar.markdown(f"**Período evaluado:** {datos['Fecha'].min()} al {datos['Fecha'].max()}")
        
        # FILTROS
        st.sidebar.header("🔍 Filtros")
        
        # 1. Filtro por jugador
        jugadores = st.sidebar.multiselect(
            "Seleccionar Jugador(es)",
            options=sorted(datos['Jugador'].unique())
        )
        
        # 2. Filtro por categoría
        categorias = st.sidebar.multiselect(
            "Seleccionar Categoría(s)",
            options=sorted(datos['Categoría'].unique())
        )
        
        # 3. Filtro por fecha
        fechas = st.sidebar.multiselect(
            "Seleccionar Fecha(s)",
            options=sorted(datos['Fecha'].unique(), reverse=True)
        )
        
        # Aplicar filtros
        if jugadores:
            datos = datos[datos['Jugador'].isin(jugadores)]
        if categorias:
            datos = datos[datos['Categoría'].isin(categorias)]
        if fechas:
            datos = datos[datos['Fecha'].isin(fechas)]
        
        # Mostrar resultados filtrados
        st.header("Resultados de las Pruebas")
        
        if datos.empty:
            st.warning("No hay registros con los filtros seleccionados")
        else:
            # Crear copia para mostrar
            datos_mostrar = datos.copy()
            
            # Aplicar iconos a cada prueba
            for prueba, config in PRUEBAS.items():
                if prueba in datos_mostrar.columns:
                    datos_mostrar[prueba] = datos_mostrar[prueba].apply(
                        lambda x: evaluar_resultado(x, config["umbral"])[0]
                    )
            
            # Seleccionar columnas a mostrar
            columnas_mostrar = ['Jugador', 'Categoría', 'Fecha'] + list(PRUEBAS.keys())
            columnas_mostrar = [c for c in columnas_mostrar if c in datos_mostrar.columns]
            
            # Mostrar tabla con estilo
            st.dataframe(
                datos_mostrar[columnas_mostrar].style.applymap(
                    lambda x: 'color: green' if x == "✅" else 
                            ('color: red' if x == "❌" else 'color: gray'),
                    subset=list(PRUEBAS.keys())
                ),
                height=600,
                use_container_width=True,
                hide_index=True
            )
            
            # Mostrar estadísticas
            st.subheader("📈 Estadísticas Generales")
            st.dataframe(
                datos[list(PRUEBAS.keys())].describe().round(1),
                use_container_width=True
            )
            
            # Botón para exportar datos
            st.download_button(
                label="📥 Descargar Datos Filtrados",
                data=datos.to_csv(index=False).encode('utf-8'),
                file_name=f"resultados_movilidad_{datetime.now().date()}.csv",
                mime="text/csv"
            )
            
    except Exception as e:
        st.error(f"Error inesperado: {str(e)}")

# 8. EJECUCIÓN DE LA APLICACIÓN
if __name__ == "__main__":
    main()
