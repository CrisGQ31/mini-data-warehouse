import mysql.connector
import pandas as pd
import warnings

# Ignorar advertencias de pandas sobre SQLAlchemy para mantener la consola limpia
warnings.filterwarnings('ignore')

try:
    # Conexiones a ambas bases de datos
    db_tx = mysql.connector.connect(host="localhost", user="root", password="", database="vinateria_tx")
    db_dw = mysql.connector.connect(host="localhost", user="root", password="", database="vinateria_dw")
    cursor_dw = db_dw.cursor()

    print("Iniciando proceso ETL...")

    # --- 1. EXTRACCIÓN Y TRANSFORMACIÓN (DIMENSIONES) ---
    
    print("Cargando dim_producto (Cruzando datos con proveedores)...")
    query_prod = """
        SELECT p.id_producto, p.nombre, p.categoria, pr.nombre as proveedor 
        FROM productos p JOIN proveedores pr ON p.id_proveedor = pr.id_proveedor
    """
    df_prod = pd.read_sql(query_prod, db_tx)
    for _, row in df_prod.iterrows():
        cursor_dw.execute("INSERT INTO dim_producto (id_producto_tx, nombre, categoria, proveedor) VALUES (%s, %s, %s, %s)", 
                          (row['id_producto'], row['nombre'], row['categoria'], row['proveedor']))

    print("Cargando dim_cliente...")
    df_clientes = pd.read_sql("SELECT id_cliente, nombre, tipo_cliente FROM clientes", db_tx)
    for _, row in df_clientes.iterrows():
        cursor_dw.execute("INSERT INTO dim_cliente (id_cliente_tx, nombre, tipo_cliente) VALUES (%s, %s, %s)", 
                          (row['id_cliente'], row['nombre'], row['tipo_cliente']))

    print("Cargando dim_empleado...")
    df_empleados = pd.read_sql("SELECT id_empleado, nombre, sucursal FROM empleados", db_tx)
    for _, row in df_empleados.iterrows():
        cursor_dw.execute("INSERT INTO dim_empleado (id_empleado_tx, nombre, sucursal) VALUES (%s, %s, %s)", 
                          (row['id_empleado'], row['nombre'], row['sucursal']))

    # --- 2. EXTRACCIÓN Y TRANSFORMACIÓN (TIEMPO Y HECHOS) ---
    print("Extrayendo histórico de ventas y detalles...")
    query_ventas = """
        SELECT v.id_venta, v.fecha, v.id_cliente, v.id_empleado, 
               dv.id_producto, dv.cantidad, dv.precio_unitario, dv.subtotal
        FROM ventas v
        JOIN detalle_ventas dv ON v.id_venta = dv.id_venta
    """
    df_ventas = pd.read_sql(query_ventas, db_tx)

    # Crear la dimensión tiempo separando año, mes, día y calculando el día de la semana
    df_tiempo = df_ventas[['fecha']].copy()
    df_tiempo['fecha_corta'] = df_tiempo['fecha'].dt.date
    df_tiempo = df_tiempo.drop_duplicates(subset=['fecha_corta'])

    dias_es = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}

    print("Cargando dim_tiempo...")
    mapa_tiempo = {} # Diccionario para conectar la fecha exacta con su nuevo ID en el Data Warehouse
    for _, row in df_tiempo.iterrows():
        f = row['fecha']
        f_corta = row['fecha_corta']
        dia_semana = dias_es[f.weekday()]
        
        cursor_dw.execute("INSERT INTO dim_tiempo (fecha, anio, mes, dia, dia_semana) VALUES (%s, %s, %s, %s, %s)", 
                          (f_corta, f.year, f.month, f.day, dia_semana))
        mapa_tiempo[f_corta] = cursor_dw.lastrowid

    # --- 3. CARGA (LOAD) TABLA DE HECHOS ---
    print("Transformando y cargando fact_ventas (Tabla central)...")
    
    # Mapeo rápido de IDs
    mapa_prod = {row['id_producto']: i+1 for i, row in df_prod.iterrows()}
    mapa_cli = {row['id_cliente']: i+1 for i, row in df_clientes.iterrows()}
    mapa_emp = {row['id_empleado']: i+1 for i, row in df_empleados.iterrows()}

    fact_data = []
    for _, row in df_ventas.iterrows():
        id_venta_tx = row['id_venta']
        id_dim_prod = mapa_prod[row['id_producto']]
        id_dim_cli = mapa_cli[row['id_cliente']]
        id_dim_emp = mapa_emp[row['id_empleado']]
        id_dim_tiempo = mapa_tiempo[row['fecha'].date()]
        
        fact_data.append((id_venta_tx, id_dim_prod, id_dim_cli, id_dim_emp, id_dim_tiempo, 
                          row['cantidad'], row['precio_unitario'], row['subtotal']))

    # Inserción masiva
    cursor_dw.executemany("""
        INSERT INTO fact_ventas (id_venta_tx, id_dim_producto, id_dim_cliente, id_dim_empleado, id_dim_tiempo, cantidad, precio_unitario, ingreso_total) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, fact_data)

    db_dw.commit()
    print("¡Proceso ETL completado con éxito! Tu Data Warehouse está listo.")

except mysql.connector.Error as err:
    print(f"Error de MySQL: {err}")
except Exception as e:
    print(f"Error en el procesamiento de Pandas: {e}")
finally:
    if 'db_tx' in locals() and db_tx.is_connected():
        db_tx.close()
    if 'db_dw' in locals() and db_dw.is_connected():
        cursor_dw.close()
        db_dw.close()