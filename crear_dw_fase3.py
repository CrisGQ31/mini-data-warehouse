import mysql.connector

try:
    # Conexión a MySQL
    conexion = mysql.connector.connect(
        host="localhost",
        user="root",
        password="" 
    )
    cursor = conexion.cursor()

    print("Creando Data Warehouse 'vinateria_dw'...")
    cursor.execute("DROP DATABASE IF EXISTS vinateria_dw")
    cursor.execute("CREATE DATABASE vinateria_dw")
    cursor.execute("USE vinateria_dw")

    # Creación de Dimensiones y Tabla de Hechos (Esquema Estrella)
    tablas_dw = [
        """CREATE TABLE dim_producto (
            id_dim_producto INT AUTO_INCREMENT PRIMARY KEY,
            id_producto_tx INT,
            nombre VARCHAR(100),
            categoria VARCHAR(50),
            proveedor VARCHAR(100)
        )""",
        """CREATE TABLE dim_cliente (
            id_dim_cliente INT AUTO_INCREMENT PRIMARY KEY,
            id_cliente_tx INT,
            nombre VARCHAR(100),
            tipo_cliente VARCHAR(50)
        )""",
        """CREATE TABLE dim_empleado (
            id_dim_empleado INT AUTO_INCREMENT PRIMARY KEY,
            id_empleado_tx INT,
            nombre VARCHAR(100),
            sucursal VARCHAR(50)
        )""",
        """CREATE TABLE dim_tiempo (
            id_dim_tiempo INT AUTO_INCREMENT PRIMARY KEY,
            fecha DATE,
            anio INT,
            mes INT,
            dia INT,
            dia_semana VARCHAR(20)
        )""",
        """CREATE TABLE fact_ventas (
            id_fact_venta INT AUTO_INCREMENT PRIMARY KEY,
            id_venta_tx INT,
            id_dim_producto INT,
            id_dim_cliente INT,
            id_dim_empleado INT,
            id_dim_tiempo INT,
            cantidad INT,
            precio_unitario DECIMAL(10,2),
            ingreso_total DECIMAL(10,2),
            FOREIGN KEY (id_dim_producto) REFERENCES dim_producto(id_dim_producto),
            FOREIGN KEY (id_dim_cliente) REFERENCES dim_cliente(id_dim_cliente),
            FOREIGN KEY (id_dim_empleado) REFERENCES dim_empleado(id_dim_empleado),
            FOREIGN KEY (id_dim_tiempo) REFERENCES dim_tiempo(id_dim_tiempo)
        )"""
    ]

    for tabla in tablas_dw:
        cursor.execute(tabla)

    conexion.commit()
    print("¡Éxito! Esquema estrella creado correctamente en 'vinateria_dw'.")

except mysql.connector.Error as err:
    print(f"Error de MySQL: {err}")
finally:
    if 'conexion' in locals() and conexion.is_connected():
        cursor.close()
        conexion.close()