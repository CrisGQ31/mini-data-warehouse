import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
import matplotlib.ticker as ticker
import warnings

warnings.filterwarnings('ignore')

try:
    db_dw = mysql.connector.connect(host="localhost", user="root", password="", database="vinateria_dw")
    print("Iniciando generación de gráficas con formato ejecutivo...")

    # --- 1. PRODUCTOS MÁS RENTABLES (FORMATO EJECUTIVO) ---
    query_prod = """
        SELECT dp.nombre, SUM(fv.ingreso_total) as ingresos_totales
        FROM fact_ventas fv
        JOIN dim_producto dp ON fv.id_dim_producto = dp.id_dim_producto
        GROUP BY dp.nombre
        ORDER BY ingresos_totales DESC
        LIMIT 5
    """
    df_top_prod = pd.read_sql(query_prod, db_dw)
    
    plt.figure(figsize=(12, 6))
    sns.set_style("whitegrid")
    
    # Crear gráfica
    ax = sns.barplot(x='ingresos_totales', y='nombre', data=df_top_prod, palette='Blues_r')
    plt.title('Top 5 Licores con Mayor Impacto Financiero', fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('Ingresos Acumulados', fontsize=12)
    plt.ylabel('')
    
    # Formatear el eje X como moneda ($)
    formatter = ticker.FuncFormatter(lambda x, pos: f'${x:,.0f}')
    ax.xaxis.set_major_formatter(formatter)
    
    # Añadir las etiquetas de datos exactas en las barras
    for container in ax.containers:
        ax.bar_label(container, fmt='$%d', padding=5, fontsize=11)
        
    plt.tight_layout()
    plt.savefig('top_productos.png', dpi=300) # Alta resolución para presentaciones
    plt.close()

    # --- 2. SEGMENTACIÓN K-MEANS (TRADUCCIÓN A NEGOCIO) ---
    query_clientes = """
        SELECT dc.id_cliente_tx as id_cliente, 
               COUNT(DISTINCT fv.id_venta_tx) as frecuencia_compras, 
               SUM(fv.ingreso_total) as gasto_total
        FROM fact_ventas fv
        JOIN dim_cliente dc ON fv.id_dim_cliente = dc.id_dim_cliente
        GROUP BY dc.id_cliente_tx
    """
    df_clientes = pd.read_sql(query_clientes, db_dw)

    X = df_clientes[['frecuencia_compras', 'gasto_total']]
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df_clientes['cluster_id'] = kmeans.fit_predict(X)

    # Identificar automáticamente qué cluster es VIP, Regular y Casual basándose en el gasto promedio
    promedios = df_clientes.groupby('cluster_id')['gasto_total'].mean().sort_values()
    etiquetas_negocio = {
        promedios.index[0]: 'Casuales (Bajo consumo)',
        promedios.index[1]: 'Regulares (Consumo medio)',
        promedios.index[2]: 'VIP (Alta rentabilidad)'
    }
    df_clientes['Perfil de Cliente'] = df_clientes['cluster_id'].map(etiquetas_negocio)

    plt.figure(figsize=(12, 7))
    sns.set_style("whitegrid")
    
    # Gráfica con colores más distintivos
    sns.scatterplot(x='frecuencia_compras', y='gasto_total', hue='Perfil de Cliente', 
                    data=df_clientes, palette=['#FF6B6B', '#4ECDC4', '#FFE66D'], s=150, edgecolor='black')
    
    plt.title('Clasificación Automática de Clientes (IA)', fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('Número de Visitas a la Sucursal', fontsize=12)
    plt.ylabel('Gasto Acumulado en el Semestre', fontsize=12)
    
    # Formato moneda en el eje Y
    ax2 = plt.gca()
    ax2.yaxis.set_major_formatter(formatter)
    
    plt.tight_layout()
    plt.savefig('segmentacion_clientes.png', dpi=300)
    plt.close()

    print("¡Listo! Imágenes actualizadas con diseño profesional.")

except Exception as e:
    print(f"Ocurrió un error: {e}")
finally:
    if 'db_dw' in locals() and db_dw.is_connected():
        db_dw.close()