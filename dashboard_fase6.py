import streamlit as st
import pandas as pd
import mysql.connector
import warnings

warnings.filterwarnings('ignore')

# 1. Configuración de la página web
st.set_page_config(page_title="DSS Vinatería", page_icon="🍷", layout="wide")

st.title(" Dashboard Ejecutivo - Sistema de Soporte a Decisiones (DSS)")
st.markdown("Este panel interactivo consolida la información del Data Warehouse para respaldar la toma de decisiones estratégicas, como la próxima expansión de sucursales.")

# 2. Conexión y Extracción de Datos (Caché activado para mayor velocidad)
@st.cache_data
def cargar_datos():
    conexion = mysql.connector.connect(host="localhost", user="root", password="", database="vinateria_dw")
    query = """
        SELECT 
            dt.fecha, 
            dp.nombre AS producto, 
            dp.categoria, 
            de.sucursal, 
            fv.cantidad, 
            fv.ingreso_total
        FROM fact_ventas fv
        JOIN dim_tiempo dt ON fv.id_dim_tiempo = dt.id_dim_tiempo
        JOIN dim_producto dp ON fv.id_dim_producto = dp.id_dim_producto
        JOIN dim_empleado de ON fv.id_dim_empleado = de.id_dim_empleado
    """
    df = pd.read_sql(query, conexion)
    conexion.close()
    df['fecha'] = pd.to_datetime(df['fecha'])
    return df

try:
    df = cargar_datos()

    # 3. BARRA LATERAL (Filtros de control)
    st.sidebar.header("Filtros de Análisis")
    
    # Filtro por Categoría
    categorias = df['categoria'].unique().tolist()
    categoria_filtro = st.sidebar.multiselect("Filtrar por Categoría:", options=categorias, default=categorias)
    
    # Filtro por Sucursal
    sucursales = df['sucursal'].unique().tolist()
    sucursal_filtro = st.sidebar.multiselect("Filtrar por Sucursal:", options=sucursales, default=sucursales)

    # Aplicar los filtros cruzados al DataFrame
    df_filtrado = df[(df['categoria'].isin(categoria_filtro)) & (df['sucursal'].isin(sucursal_filtro))]

    # 4. KPIs PRINCIPALES (Indicadores Clave)
    st.subheader("Indicadores Clave de Rendimiento (KPIs)")
    col1, col2, col3 = st.columns(3)
    
    total_ingresos = df_filtrado['ingreso_total'].sum()
    total_tickets = len(df_filtrado)
    ticket_promedio = total_ingresos / total_tickets if total_tickets > 0 else 0

    col1.metric("Ingresos Acumulados", f"${total_ingresos:,.2f}")
    col2.metric("Volumen de Ventas (Tickets)", f"{total_tickets:,}")
    col3.metric("Ticket Promedio", f"${ticket_promedio:,.2f}")

    st.divider()

    # 5. GRÁFICAS INTERACTIVAS
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("📈 Tendencia de Ingresos")
        # Agrupar ventas por fecha para la línea de tiempo
        ventas_tiempo = df_filtrado.groupby('fecha')['ingreso_total'].sum().reset_index()
        ventas_tiempo.set_index('fecha', inplace=True)
        st.line_chart(ventas_tiempo)

    with col_graf2:
        st.subheader(" Desempeño por Producto (Ingresos)")
        # Agrupar ventas por producto para gráfica de barras
        top_productos = df_filtrado.groupby('producto')['ingreso_total'].sum().sort_values(ascending=False).head(8)
        st.bar_chart(top_productos)

except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}. Asegúrate de que XAMPP esté encendido.")