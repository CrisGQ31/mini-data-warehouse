import mysql.connector
from faker import Faker
import random
from datetime import datetime, timedelta

# Configurar Faker con datos de México
fake = Faker('es_MX')

# 1. Conexión inicial a MySQL (para crear la base de datos)
try:
    conexion = mysql.connector.connect(
        host="localhost",
        user="root",
        password="", # <-- PON TU CONTRASEÑA DE MYSQL AQUÍ SI TIENES UNA
    )
    cursor = conexion.cursor()
    
    print("Creando base de datos 'vinateria_tx'...")
    cursor.execute("DROP DATABASE IF EXISTS vinateria_tx")
    cursor.execute("CREATE DATABASE vinateria_tx")
    cursor.execute("USE vinateria_tx")

    # 2. Creación de Tablas (Esquema Transaccional)
    tablas = [
        """CREATE TABLE proveedores (
            id_proveedor INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100),
            telefono VARCHAR(20)
        )""",
        """CREATE TABLE empleados (
            id_empleado INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100),
            sucursal VARCHAR(50)
        )""",
        """CREATE TABLE clientes (
            id_cliente INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100),
            tipo_cliente VARCHAR(50)
        )""",
        """CREATE TABLE productos (
            id_producto INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100),
            categoria VARCHAR(50),
            precio_venta DECIMAL(10,2),
            id_proveedor INT,
            FOREIGN KEY (id_proveedor) REFERENCES proveedores(id_proveedor)
        )""",
        """CREATE TABLE ventas (
            id_venta INT AUTO_INCREMENT PRIMARY KEY,
            fecha DATETIME,
            id_cliente INT,
            id_empleado INT,
            total DECIMAL(10,2),
            FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
            FOREIGN KEY (id_empleado) REFERENCES empleados(id_empleado)
        )""",
        """CREATE TABLE detalle_ventas (
            id_detalle INT AUTO_INCREMENT PRIMARY KEY,
            id_venta INT,
            id_producto INT,
            cantidad INT,
            precio_unitario DECIMAL(10,2),
            subtotal DECIMAL(10,2),
            FOREIGN KEY (id_venta) REFERENCES ventas(id_venta),
            FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
        )"""
    ]

    for tabla in tablas:
        cursor.execute(tabla)
    
    print("Tablas creadas con éxito. Generando datos ficticios...")

    # 3. Insertar Catálogos Base (Proveedores, Empleados, Clientes, Productos)
    
    # Proveedores
    proveedores = [('Casa Madero',), ('Cuervo',), ('Bacardi y Cía',), ('Diageo México',), ('Pernod Ricard',)]
    cursor.executemany("INSERT INTO proveedores (nombre) VALUES (%s)", proveedores)
    
    # Empleados
    empleados = [(fake.name(), 'Matriz') for _ in range(4)]
    cursor.executemany("INSERT INTO empleados (nombre, sucursal) VALUES (%s, %s)", empleados)
    
    # Clientes (100 clientes frecuentes/casuales)
    clientes = [(fake.name(), random.choice(['Frecuente', 'Casual', 'Mayorista'])) for _ in range(100)]
    cursor.executemany("INSERT INTO clientes (nombre, tipo_cliente) VALUES (%s, %s)", clientes)

    # Productos de Vinatería
    productos_base = [
        ('Vino Tinto Shiraz', 'Vinos', 450.00, 1), ('Vino Blanco Chardonnay', 'Vinos', 380.00, 1),
        ('Tequila Reposado', 'Destilados', 650.00, 2), ('Tequila Añejo', 'Destilados', 950.00, 2),
        ('Ron Blanco', 'Destilados', 220.00, 3), ('Ron Añejo', 'Destilados', 340.00, 3),
        ('Whisky 12 Años', 'Destilados', 850.00, 4), ('Vodka Clásico', 'Destilados', 290.00, 4),
        ('Mezcal Joven', 'Destilados', 580.00, 5), ('Ginebra Premium', 'Destilados', 720.00, 5)
    ]
    cursor.executemany("INSERT INTO productos (nombre, categoria, precio_venta, id_proveedor) VALUES (%s, %s, %s, %s)", productos_base)
    conexion.commit()

    # 4. Generar Ventas (Simulación de 6 meses - 5000 transacciones)
    print("Generando 5,000 ventas (esto puede tomar unos segundos)...")
    
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=180) # 6 meses atrás
    
    ventas_data = []
    detalle_data = []
    
    for i in range(1, 5001):
        # Datos de la cabecera de venta
        fecha_venta = fake.date_time_between(start_date=fecha_inicio, end_date=fecha_fin)
        id_cliente = random.randint(1, 100)
        id_empleado = random.randint(1, 4)
        
        # Generar entre 1 y 4 productos por ticket de venta
        num_productos_ticket = random.randint(1, 4)
        total_venta = 0
        detalles_ticket = []
        
        for _ in range(num_productos_ticket):
            producto = random.choice(productos_base)
            id_prod = productos_base.index(producto) + 1
            precio_u = producto[2]
            cantidad = random.randint(1, 3)
            subtotal = precio_u * cantidad
            total_venta += subtotal
            
            detalles_ticket.append((i, id_prod, cantidad, precio_u, subtotal))
            
        ventas_data.append((fecha_venta, id_cliente, id_empleado, total_venta))
        detalle_data.extend(detalles_ticket)

    # Insertar en base de datos en lotes para mayor velocidad
    cursor.executemany("INSERT INTO ventas (fecha, id_cliente, id_empleado, total) VALUES (%s, %s, %s, %s)", ventas_data)
    cursor.executemany("INSERT INTO detalle_ventas (id_venta, id_producto, cantidad, precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s)", detalle_data)
    
    conexion.commit()
    print("¡Éxito! Base de datos 'vinateria_tx' creada y poblada con 5,000 transacciones.")

except mysql.connector.Error as err:
    print(f"Error de MySQL: {err}")
finally:
    if 'conexion' in locals() and conexion.is_connected():
        cursor.close()
        conexion.close()