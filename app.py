import streamlit as st
import pandas as pd
import plotly.express as px
import glob

# 1. Configuración de la página (Una sola pantalla ejecutiva)
st.set_page_config(
    page_title="Dashboard Ejecutivo DOT - Análisis de Retrasos",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ Dashboard Ejecutivo: Operaciones y Puntualidad Aérea (DOT)")
st.markdown("Análisis estratégico de impuntualidad, factores causales y desempeño por aerolínea.")

# 2. Carga optimizada concatenando los 6 archivos .parquet desde GitHub
@st.cache_data
def cargar_datos():
    # Busca todos los archivos Parquet de muestra en la raíz o en subcarpetas
    archivos = glob.glob('datos_limpios_muestra_*.parquet')
    if not archivos:
        archivos = glob.glob('**/datos_limpios_muestra_*.parquet', recursive=True)
    
    # Lee y concatena todos los archivos encontrados
    lista_df = [pd.read_parquet(f) for f in sorted(archivos)]
    df_cargado = pd.concat(lista_df, ignore_index=True)
    return df_cargado

df = cargar_datos()

# ------------------------------------------------------------------------------
# 3. FILTROS INTERACTIVOS (Requisito: 2 filtros)
# ------------------------------------------------------------------------------
st.sidebar.header("🔍 Filtros de Operación")

# Filtro 1: Selección de Aerolínea
aerolineas_disponibles = ['Todas'] + sorted(df['NOMBRE_AEROLINEA'].dropna().unique().tolist())
aerolinea_sel = st.sidebar.selectbox("Seleccionar Aerolínea:", aerolineas_disponibles)

# Filtro 2: Categoría de Retraso
categorias_disponibles = ['Todas'] + sorted(df['CATEGORIA_RETRASO'].dropna().unique().tolist())
categoria_sel = st.sidebar.selectbox("Filtrar por Categoría de Retraso:", categoria_sel if 'categoria_sel' in locals() else categorias_disponibles)

# Aplicar filtros
df_filtrado = df.copy()
if aerolinea_sel != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['NOMBRE_AEROLINEA'] == aerolinea_sel]
if categoria_sel != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['CATEGORIA_RETRASO'] == categoria_sel]

st.sidebar.markdown("---")
st.sidebar.info(f"Mostrando **{len(df_filtrado):,}** registros de un total de **{len(df):,}**.")

# ------------------------------------------------------------------------------
# 4. KPIs EJECUTIVOS (Requisito: 4–6 KPIs)
# ------------------------------------------------------------------------------
total_vuelos = len(df_filtrado)
vuelos_a_tiempo = (df_filtrado['ARRIVAL_DELAY'] <= 15).sum()
tasa_puntualidad = (vuelos_a_tiempo / total_vuelos * 100) if total_vuelos > 0 else 0
prom_retraso_llegada = df_filtrado['ARRIVAL_DELAY'].mean() if total_vuelos > 0 else 0
prom_retraso_salida = df_filtrado['DEPARTURE_DELAY'].mean() if total_vuelos > 0 else 0
total_cancelados = df_filtrado['CANCELLED'].sum() if 'CANCELLED' in df_filtrado.columns else 0
tasa_cancelacion = (total_cancelados / total_vuelos * 100) if total_vuelos > 0 else 0

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Total de Vuelos", f"{total_vuelos:,}")
kpi2.metric("Tasa de Puntualidad", f"{tasa_puntualidad:.1f}%")
kpi3.metric("Prom. Retraso Llegada", f"{prom_retraso_llegada:.1f} min")
kpi4.metric("Prom. Retraso Salida", f"{prom_retraso_salida:.1f} min")
kpi5.metric("Tasa Cancelación", f"{tasa_cancelacion:.2f}%")

st.markdown("---")

# ------------------------------------------------------------------------------
# 5. GRÁFICOS INTERACTIVOS (Requisito: 3–4 gráficos)
# ------------------------------------------------------------------------------
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("1. Distribución de Estado de Vuelos")
    fig1 = px.pie(
        df_filtrado, 
        names='CATEGORIA_RETRASO', 
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig1.update_layout(margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig1, use_container_width=True)

with col_g2:
    st.subheader("2. Top Aerolíneas con Mayor Retraso en Llegada")
    top_aerolineas = df_filtrado.groupby('NOMBRE_AEROLINEA')['ARRIVAL_DELAY'].mean().reset_index()
    top_aerolineas = top_aerolineas.sort_values(by='ARRIVAL_DELAY', ascending=True).tail(8)
    fig2 = px.bar(
        top_aerolineas, 
        x='ARRIVAL_DELAY', 
        y='NOMBRE_AEROLINEA', 
        orientation='h',
        labels={'ARRIVAL_DELAY': 'Minutos Promedio', 'NOMBRE_AEROLINEA': 'Aerolínea'},
        color='ARRIVAL_DELAY',
        color_continuous_scale='Reds'
    )
    fig2.update_layout(margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig2, use_container_width=True)

col_g3, col_g4 = st.columns(2)

with col_g3:
    st.subheader("3. Desglose de Causas Principales de Retraso")
    causas = {
        'Sistema Aéreo (NAS)': df_filtrado['AIRSYSTEM_DELAY'].sum() if 'AIRSYSTEM_DELAY' in df_filtrado.columns else 0,
        'Seguridad': df_filtrado['SECURITY_DELAY'].sum() if 'SECURITY_DELAY' in df_filtrado.columns else 0,
        'Aerolínea': df_filtrado['AIRLINE_DELAY'].sum() if 'AIRLINE_DELAY' in df_filtrado.columns else 0,
        'Avión Tardío': df_filtrado['LATE_AIRCRAFT_DELAY'].sum() if 'LATE_AIRCRAFT_DELAY' in df_filtrado.columns else 0,
        'Clima': df_filtrado['WEATHER_DELAY'].sum() if 'WEATHER_DELAY' in df_filtrado.columns else 0
    }
    df_causas = pd.DataFrame(list(causas.items()), columns=['Causa', 'Minutos Totales'])
    fig3 = px.bar(
        df_causas, 
        x='Causa', 
        y='Minutos Totales',
        color='Causa',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig3.update_layout(margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig3, use_container_width=True)

with col_g4:
    st.subheader("4. Retraso Promedio por Día de la Semana")
    dias_map = {1: 'Lun', 2: 'Mar', 3: 'Mié', 4: 'Jue', 5: 'Vie', 6: 'Sáb', 7: 'Dom'}
    df_dias = df_filtrado.copy()
    df_dias['DIA_NOMBRE'] = df_dias['DAY_OF_WEEK'].map(dias_map)
    retraso_dia = df_dias.groupby(['DAY_OF_WEEK', 'DIA_NOMBRE'])['ARRIVAL_DELAY'].mean().reset_index()
    fig4 = px.line(
        retraso_dia, 
        x='DIA_NOMBRE', 
        y='ARRIVAL_DELAY', 
        markers=True,
        labels={'ARRIVAL_DELAY': 'Minutos Promedio', 'DIA_NOMBRE': 'Día'}
    )
    fig4.update_layout(margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ------------------------------------------------------------------------------
# 6. HALLAZGOS Y RECOMENDACIONES (Requisito: 3 hallazgos, 2 recomendaciones)
# ------------------------------------------------------------------------------
col_h, col_r = st.columns(2)

with col_h:
    st.markdown("### 💡 3 Hallazgos Clave")
    st.markdown("""
    1. **Efecto Cascada por Avión Tardío:** La causa principal de minutos acumulados de retraso corresponde a *Late Aircraft*, demostrando un efecto dominó en los itinerarios diarios.
    2. **Concentración Semanal:** Los días jueves y viernes registran los promedios más altos de retrasos en llegada debido al volumen pico de tráfico.
    3. **Heterogeneidad entre Operadores:** Se identifica una brecha superior a 15 minutos de diferencia en el promedio de puntualidad entre las aerolíneas con mejor y peor desempeño.
    """)

with col_r:
    st.markdown("### 📌 2 Recomendaciones Operativas")
    st.markdown("""
    1. **Reorganización de Tiempos de Giro (Turnaround):** Aumentar el margen programado en tierra para aeronaves con rutas de alta frecuencia para absorber retrasos sin propagarlos.
    2. **Protocolos Preventivos en Horas Pico:** Implementar asignaciones dinámicas de puertas y cuadrillas de tierra durante las ventanas críticas de jueves y viernes tarde.
    """)
