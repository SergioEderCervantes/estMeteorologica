import streamlit as st
import pandas as pd
import time
import requests # <--- Importamos requests para conectarnos a la API
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Dashboard Estación Meteorológica", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; min-height: 130px; }
    .box-activo { background-color: #1f6e43; color: white; padding: 12px; border-radius: 8px; margin-bottom: 10px; font-weight: bold; border-left: 5px solid #2ea043; }
    .box-inactivo { background-color: #8c1d1d; color: white; padding: 12px; border-radius: 8px; margin-bottom: 10px; font-weight: bold; border-left: 5px solid #f85149; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A LA API ---
# URL de tu API (asumiendo que FastAPI corre en el puerto 8000)
API_URL = "http://127.0.0.1:8000/readings/latest"

def obtener_lectura_api():
    """Hace una petición GET a la API para obtener la última lectura real."""
    try:
        # Hacemos la petición con un timeout de 2 segundos para no trabar la página
        respuesta = requests.get(API_URL, timeout=2)
        
        if respuesta.status_code == 200:
            return respuesta.json() # Retorna el JSON de la API
        elif respuesta.status_code == 404:
            return "Vacio" # La API funciona, pero no hay lecturas guardadas aún
        else:
            return None
    except requests.exceptions.RequestException:
        return None # La API está apagada o inaccesible

# --- INICIALIZAR HISTÓRICO ---
if 'historico' not in st.session_state:
    st.session_state.historico = pd.DataFrame(columns=['tiempo', 'temp', 'hum'])

# --- INTERFAZ ---
st.title("Sistema de Monitoreo Meteorológico")
st.caption("Consumiendo datos en tiempo real de FastAPI")

st.sidebar.header("Configuración de Visualización")
tipo_grafica = st.sidebar.radio("Tipo de gráfico histórico:", ["Líneas", "Barras"])

# Intentamos obtener la lectura real
lectura = obtener_lectura_api()

# Si la API está conectada y mandó datos...
if isinstance(lectura, dict):
    
    # Procesar fecha/hora (para el eje X de la gráfica)
    try:
        # Extraer solo la hora si viene en formato largo ISO 8601
        hora_str = lectura['timestamp'].split('T')[1][:8] 
    except:
        hora_str = lectura['timestamp']

    # Guardar en el histórico (máximo 15)
    nuevo_dato = pd.DataFrame({
        'tiempo': [hora_str],
        'temp': [lectura['temperature']['celsius']],
        'hum': [lectura['humidity']['percent']]
    })
    st.session_state.historico = pd.concat([st.session_state.historico, nuevo_dato]).tail(15)

    # --- FILA 1: MÉTRICAS ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Temperatura", f"{lectura['temperature']['celsius']} °C", f"Sensación: {lectura.get('heat_index', '--')} °C")
    col2.metric("Humedad", f"{lectura['humidity']['percent']} %", f"Normalizada: {lectura['humidity']['normalized']}")
    col3.metric("Iluminación", lectura['light']['label'], f"Índice: {lectura['light']['normalized']}")
    col4.metric("Lluvia", "Detectada" if lectura['rain']['is_raining'] else "Ninguna", f"Intensidad: {lectura['rain']['intensity']}")

    st.write("---")

    # --- FILA 2: GRÁFICAS ---
    st.subheader("Análisis de Tendencias (Últimas 15 lecturas)")
    hist_col1, hist_col2 = st.columns(2)

    fig_temp = go.Figure()
    fig_hum = go.Figure()
    df = st.session_state.historico

    if tipo_grafica == "Barras":
        fig_temp.add_trace(go.Bar(x=df['tiempo'], y=df['temp'], marker_color='#ff4b4b', name="Temp"))
        fig_hum.add_trace(go.Bar(x=df['tiempo'], y=df['hum'], marker_color='#0068c9', name="Hum"))
    else:
        fig_temp.add_trace(go.Scatter(x=df['tiempo'], y=df['temp'], mode='lines+markers', line=dict(color='#ff4b4b', width=3)))
        fig_hum.add_trace(go.Scatter(x=df['tiempo'], y=df['hum'], mode='lines+markers', line=dict(color='#0068c9', width=3)))

    config_layout = dict(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(l=40, r=20, t=20, b=40), xaxis=dict(tickangle=0, title="Tiempo"))

    with hist_col1:
        st.write("**Temperatura vs Tiempo**")
        fig_temp.update_layout(**config_layout)
        fig_temp.update_yaxes(range=[-20, 50], title="Temperatura (°C)")
        st.plotly_chart(fig_temp, use_container_width=True, key="graf_temp")

    with hist_col2:
        st.write("**Humedad Relativa vs Tiempo**")
        fig_hum.update_layout(**config_layout)
        fig_hum.update_yaxes(range=[0, 100], title="Humedad (%)")
        st.plotly_chart(fig_hum, use_container_width=True, key="graf_hum")

    st.write("---")

    # --- FILA 3: ACTUADORES Y HARDWARE ---
    status_col1, status_col2 = st.columns(2)

    with status_col1:
        st.subheader("Estado de Actuadores")
        for act_name, act_status in lectura['actuators'].items():
            if act_status:
                st.markdown(f'<div class="box-activo">{act_name.upper()}: ACTIVO</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="box-inactivo">{act_name.upper()}: INACTIVO</div>', unsafe_allow_html=True)

    with status_col2:
        st.subheader("Salud del Hardware")
        for sensor, estado in lectura['sensor_status'].items():
            if estado == "ok":
                st.markdown(f'<div class="box-activo">SENSOR {sensor.upper()}: CONECTADO</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="box-inactivo">SENSOR {sensor.upper()}: NO CONECTADO / ERROR</div>', unsafe_allow_html=True)

    st.caption(f"ID Lectura: {lectura['reading_id']} | Timestamp Actual: {lectura['timestamp']} | Estación: {lectura['station_id']}")

elif lectura == "Vacio":
    st.warning("La API está conectada, pero aún no hay ninguna lectura guardada en la base de datos (Error 404). Esperando datos del Arduino...")
    
else:
    st.error("🔌 Error: No se pudo conectar con la API en `http://127.0.0.1:8000/readings/latest`. Asegúrate de que el backend de FastAPI esté corriendo.")

# --- CICLO DE ACTUALIZACIÓN ---
time.sleep(3) 
st.rerun()