import streamlit as st
import pandas as pd
import random
import uuid
import time
from datetime import datetime
import plotly.graph_objects as go

# Configuración técnica de la página
st.set_page_config(
    page_title="Dashboard Estación Meteorológica",
    layout="wide"
)

# Estilo CSS generalizado
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { 
        background-color: #161b22; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #30363d;
        min-height: 130px; 
    }
    .box-activo {
        background-color: #1f6e43;
        color: white;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
        font-weight: bold;
        border-left: 5px solid #2ea043;
    }
    .box-inactivo {
        background-color: #8c1d1d;
        color: white;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
        font-weight: bold;
        border-left: 5px solid #f85149;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE DATOS ---
def generar_lectura():
    temp_c = round(random.uniform(18.0, 28.0), 1)
    hum_p = round(random.uniform(40.0, 70.0), 1)
    luz_norm = round(random.uniform(0.0, 1.0), 2)
    lluvia_int = round(random.uniform(0.0, 1.0), 2)
    
    return {
        "reading_id": str(uuid.uuid4()),
        "station_id": "STATION_001",
        "timestamp": datetime.now().strftime("%H:%M:%S"), # Usamos formato de hora para el eje X
        "temperature": {"celsius": temp_c, "normalized": (temp_c + 20) / 70},
        "humidity": {"percent": hum_p, "normalized": hum_p / 100},
        "heat_index": round(temp_c + (hum_p * 0.02), 1),
        "light": {
            "normalized": luz_norm,
            "label": "BRILLANTE" if luz_norm > 0.7 else "MODERADO" if luz_norm > 0.3 else "TENUE"
        },
        "rain": {"is_raining": lluvia_int > 0.5, "intensity": lluvia_int},
        "actuators": {
            "fan": temp_c > 25,
            "led": luz_norm < 0.3,
            "buzzer": lluvia_int > 0.5
        },
        "sensor_status": {
            "dht11": random.choice(["ok", "error"]), # Simula desconexiones
            "ldr": "ok", 
            "fc37": "ok"
        }
    }

# Inicializar histórico para las gráficas (Ahora incluye la columna 'tiempo')
if 'historico' not in st.session_state:
    st.session_state.historico = pd.DataFrame(columns=['tiempo', 'temp', 'hum'])

# --- CONTROLES DE LA INTERFAZ ---
st.title("Sistema de Monitoreo Meteorológico")
st.caption("Análisis de datos en tiempo real - Estación Local")

st.sidebar.header("Configuración de Visualización")
tipo_grafica = st.sidebar.radio("Tipo de gráfico histórico:", ["Líneas", "Barras"])

# Generar nueva lectura
lectura = generar_lectura()

# Almacenar datos limitando estrictamente a las últimas 15 muestras
nuevo_dato = pd.DataFrame({
    'tiempo': [lectura['timestamp']],
    'temp': [lectura['temperature']['celsius']],
    'hum': [lectura['humidity']['percent']]
})
st.session_state.historico = pd.concat([st.session_state.historico, nuevo_dato]).tail(15)

# --- FILA 1: MÉTRICAS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Temperatura", f"{lectura['temperature']['celsius']} °C", f"Sensación: {lectura['heat_index']} °C")
col2.metric("Humedad", f"{lectura['humidity']['percent']} %", f"Normalizada: {lectura['humidity']['normalized']}")
col3.metric("Iluminación", lectura['light']['label'], f"Índice: {lectura['light']['normalized']}")
col4.metric("Lluvia", "Detectada" if lectura['rain']['is_raining'] else "Ninguna", f"Intensidad: {lectura['rain']['intensity']}")

st.write("---")

# --- FILA 2: GRÁFICAS (TIEMPO vs VALOR) ---
st.subheader("Análisis de Tendencias (Últimas 15 lecturas)")
hist_col1, hist_col2 = st.columns(2)

fig_temp = go.Figure()
fig_hum = go.Figure()
df = st.session_state.historico

# Trazado de gráficas dependiendo del tipo elegido
if tipo_grafica == "Barras":
    fig_temp.add_trace(go.Bar(x=df['tiempo'], y=df['temp'], marker_color='#ff4b4b', name="Temp"))
    fig_hum.add_trace(go.Bar(x=df['tiempo'], y=df['hum'], marker_color='#0068c9', name="Hum"))
else:
    fig_temp.add_trace(go.Scatter(x=df['tiempo'], y=df['temp'], mode='lines+markers', line=dict(color='#ff4b4b', width=3)))
    fig_hum.add_trace(go.Scatter(x=df['tiempo'], y=df['hum'], mode='lines+markers', line=dict(color='#0068c9', width=3)))

config_layout = dict(
    template="plotly_dark",
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    height=300,
    margin=dict(l=40, r=20, t=20, b=40),
    xaxis=dict(tickangle=0, title="Tiempo")
)

with hist_col1:
    st.write("**Temperatura vs Tiempo**")
    fig_temp.update_layout(**config_layout)
    fig_temp.update_yaxes(range=[-20, 50], title="Temperatura (°C)")
    # El uso de unique 'key' previene problemas de ID en Streamlit
    st.plotly_chart(fig_temp, use_container_width=True, key="graf_temp")

with hist_col2:
    st.write("**Humedad Relativa vs Tiempo**")
    fig_hum.update_layout(**config_layout)
    fig_hum.update_yaxes(range=[0, 100], title="Humedad (%)")
    st.plotly_chart(fig_hum, use_container_width=True, key="graf_hum")

st.write("---")

# --- FILA 3: BOXES DINÁMICOS DE ACTUADORES Y HARDWARE ---
status_col1, status_col2 = st.columns(2)

with status_col1:
    st.subheader("Estado de Actuadores")
    for act_name, act_status in lectura['actuators'].items():
        label_display = act_name.upper()
        if act_status:
            st.markdown(f'<div class="box-activo">{label_display}: ACTIVO</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="box-inactivo">{label_display}: INACTIVO</div>', unsafe_allow_html=True)

with status_col2:
    st.subheader("Salud del Hardware")
    for sensor, estado in lectura['sensor_status'].items():
        sensor_display = sensor.upper()
        if estado == "ok":
            st.markdown(f'<div class="box-activo">SENSOR {sensor_display}: CONECTADO</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="box-inactivo">SENSOR {sensor_display}: NO CONECTADO / ERROR</div>', unsafe_allow_html=True)

st.caption(f"ID Lectura: {lectura['reading_id']} | Timestamp Actual: {lectura['timestamp']}")

# --- CICLO DE ACTUALIZACIÓN LIMPIO ---
time.sleep(2.5) # Espera 2.5 segundos
st.rerun()      # Recarga la página suavemente