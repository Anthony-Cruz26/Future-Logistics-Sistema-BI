# 👤 Guía de Usuario

## ¿Qué es Future Logistics-Sistema-BI?

Es un sistema automatizado que permite a Future Logistics S.A. gestionar y visualizar datos históricos de:

- **Transporte**: Ingreso de azúcar a bodegas
- **Despacho**: Salida de azúcar hacia clientes
- **Devoluciones**: Devoluciones de clientes

---

## Flujo de Trabajo

# 1. Iniciar el Robot

```bash
python src/robot/INICIAR.py --once
```

# 2. Selección Manual (30 segundos)
Durante 30 segundos puedes ajustar:

📅 Fechas: Rango histórico a consultar

🏭 Bodega: Filtrar por bodega específica

🍚 Tipo de Azúcar: BLANCA o MORENA

📋 Datos a exportar:

☑ TRANSPORTE

☑ DESPACHO

☑ DEVOLUCIONES

# 3. Ejecución Automática
El robot automáticamente:

Genera los datos históricos

Descarga los archivos Excel

Ejecuta los ETLs

Muestra resultados

# 4. Visualización en Power BI
Al finalizar, se abren automáticamente los dashboards:

📦 Dashboard TRANSPORTE

🚚 Dashboard DESPACHO

🔄 Dashboard DEVOLUCIONES

# KPIs Disponibles
📦 TRANSPORTE
KPI	Descripción
Kilos Recibidos	Total de kilos ingresados a bodegas
Total OT's	Número de órdenes de transporte
Kilos por OT	Promedio de kilos por orden
Bodegas Activas	Bodegas con movimiento

# 🚚 DESPACHO
KPI	Descripción
Kilos Despachados	Total de kilos enviados a clientes
Clientes Atendidos	Clientes únicos atendidos
Promedio por Despacho	Kilos promedio por despacho
Provincias Atendidas	Cobertura geográfica

# 🔄 DEVOLUCIONES
KPI	Descripción
Kilos Devueltos	Total de kilos devueltos
% Devolución	Porcentaje sobre despachos
Motivos	Distribución de causas
Tiempo de Procesamiento	Días hasta procesar

# Estructura de Archivos Generados
Archivos de Reporte

REPORTES/
├── SAP_TRANSPORTE_2026-06-30_1430.xlsx
├── SAP_DESPACHO_2026-06-30_1430.xlsx
└── SAP_DEVOLUCIONES_2026-06-30_1430.xlsx

Archivos Procesados
REPORTES/PROCESADOS/
├── SAP_TRANSPORTE_2026-06-30_1430_20260630_143500.xlsx
├── SAP_DESPACHO_2026-06-30_1430_20260630_143500.xlsx
└── SAP_DEVOLUCIONES_2026-06-30_1430_20260630_143500.xlsx

Comandos Útiles
# Ejecutar una sola vez
python src/robot/INICIAR.py --once

# Ejecutar en bucle (cada 2 horas)
python src/robot/INICIAR.py

# Mostrar ayuda
python src/robot/INICIAR.py --help

#Ejecutar ETL manualmente
python src/etl/PROCESO_ETL_TRANSPORTE.py
python src/etl/PROCESO_ETL_DESPACHO.py
python src/etl/PROCESO_ETL_DEVOLUCION.py

# Mensajes del Sistema

✅ Éxito
PROCESO COMPLETADO CON EXITO

Los datos han sido cargados en SQL Server.

Archivos generados:
  - TRANSPORTE
  - DESPACHO
  - DEVOLUCIONES
    
❌ Error
ERROR EN EL ETL - TRANSPORTE

Detalles:
[Error detallado]

Revise la consola para mas detalles.

# Preguntas Frecuentes
¿Cuánto tiempo tarda el proceso?
Simulación: 15-30 segundos

Descarga: 30-90 segundos

ETL: 30 segundos - 5 minutos

Total: ~2-7 minutos

# ¿Qué pasa si falla un ETL?
Los dashboards se abren de todas formas

El archivo se queda en REPORTES para reprocesar

Se registra el error en AUDITORIA_ETL

# ¿Puedo ejecutar solo un ETL?
Sí, ejecuta el script individualmente:
python src/etl/PROCESO_ETL_TRANSPORTE.py


#¿Dónde se guardan los logs?
Los logs se muestran en la consola en tiempo real.








