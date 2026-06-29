#  Arquitectura del Sistema

# Visión General

El sistema está compuesto por 4 capas principales que trabajan en conjunto para automatizar el flujo de datos desde la simulación hasta la visualización.

┌─────────────────────────────────────────────────────────────────────────┐
│ CAPA DE VISUALIZACIÓN │
│ (Power BI Dashboards) │
├─────────────────────────────────────────────────────────────────────────┤
│ CAPA DE ALMACENAMIENTO │
│ (SQL Server - Modelo Estrella) │
├─────────────────────────────────────────────────────────────────────────┤
│ CAPA DE PROCESAMIENTO │
│ (ETL - Python + Pandas) │
├─────────────────────────────────────────────────────────────────────────┤
│ CAPA DE EXTRACCIÓN │
│ (Robot - Python + Selenium) │
├─────────────────────────────────────────────────────────────────────────┤
│ CAPA DE SIMULACIÓN │
│ (HTML + JavaScript + XLSX) │
└─────────────────────────────────────────────────────────────────────────┘

## Detalle de Componentes

### 1. Simulador SAP (`SIMULACIÓN_SAP.html`)

**Tecnologías**: HTML5, CSS3, JavaScript, XLSX (SheetJS)

**Funcionalidad**:
- Interfaz tipo SAP con 5 pantallas (LOGON, LOGIN, Easy Access, Filtros, Resultados)
- Datos históricos (2024-2025)
- Exportación a Excel de 3 tipos de datos:
  - TRANSPORTE
  - DESPACHO
  - DEVOLUCIONES

- **Transporte**: 80-240 registros/día (según temporada)
- **Despacho**: 1-3 despachos por transporte
- **Devoluciones**: ~3% del volumen despachado

### 2. Robot Automatizador (`INICIAR.py`)

**Tecnologías**: Python, Selenium, WebDriver

**Funcionalidad**:
- Navegación automática por el simulador SAP
- Login automático (usuario: supervisor)
- Ejecución de comandos SAP (Lx02)
- Espera manual de 30 segundos para ajustar filtros
- Descarga de archivos Excel
- Ejecución de ETLs en secuencia
- Apertura automática de dashboards Power BI

### 3. Procesos ETL

#### ETL TRANSPORTE
- Lee archivos `SAP_TRANSPORTE_*.xlsx`
- Inserta en `HECHOS_TRANSPORTE`
- Valida bodegas y productos

#### ETL DESPACHO
- Lee archivos `SAP_DESPACHO_*.xlsx`
- Inserta en `DIM_TRANSACCION` y `HECHOS_DESPACHOS`
- Relaciona con dimensiones (cliente, destino, bodega)

#### ETL DEVOLUCION
- Lee archivos `SAP_DEVOLUCIONES_*.xlsx`
- Inserta en `HECHOS_DEVOLUCIONES`
- Relaciona con despacho original via `ID_TRANSACCION`

### 4. Base de Datos (SQL Server)

**Modelo Estrella**:

| Tabla | Tipo | PK |
|-------|------|-----|
| `DIM_BODEGA` | Dimensión | ID_BODEGA |
| `DIM_CLIENTE` | Dimensión | ID_CLIENTE |
| `DIM_DESTINO` | Dimensión | ID_DESTINO |
| `DIM_PRODUCTO` | Dimensión | ID_PRODUCTO |
| `DIM_PROVINCIA` | Dimensión | ID_PROVINCIA |
| `DIM_FECHA` | Dimensión | ID_FECHA |
| `HECHOS_TRANSPORTE` | Hechos | ORDEN_TRANSPORTE |
| `HECHOS_DESPACHOS` | Hechos | ORDEN_DESPACHO |
| `HECHOS_DEVOLUCIONES` | Hechos | ORDEN_DEVOLUCION |
| `AUDITORIA_ETL` | Auditoría | ID_AUDITORIA |

### 5. Dashboards Power BI

- **Transporte**: KPI de recepción de azúcar
- **Despacho**: KPI de distribución a clientes
- **Devoluciones**: KPI de calidad y servicio

## Flujo de Datos

1. Usuario ejecuta INICIAR.py
2. Robot abre navegador → SIMULACIÓN_SAP.html
3.Login automático → pantalla de filtros
4. Espera 30s para ajustes manuales
5. Ejecuta reporte → genera datos en memoria
6. Exporta archivos Excel (3 archivos)
7. Mueve archivos a REPORTES/
8. Ejecuta ETL TRANSPORTE
9. Ejecuta ETL DESPACHO
10. Ejecuta ETL DEVOLUCION
11. Abre dashboards Power BI

## Diagrama ER

```sql
-- Relaciones principales
DIM_BODEGA (ID_BODEGA) ←→ HECHOS_TRANSPORTE (ID_BODEGA)
DIM_PRODUCTO (ID_PRODUCTO) ←→ HECHOS_TRANSPORTE (ID_PRODUCTO)

DIM_CLIENTE (ID_CLIENTE) ←→ HECHOS_DESPACHOS (ID_CLIENTE)
DIM_BODEGA (ID_BODEGA) ←→ HECHOS_DESPACHOS (ID_BODEGA)
DIM_DESTINO (ID_DESTINO) ←→ HECHOS_DESPACHOS (ID_DESTINO)
DIM_PRODUCTO (ID_PRODUCTO) ←→ HECHOS_DESPACHOS (ID_PRODUCTO)
DIM_PROVINCIA (ID_PROVINCIA) ←→ HECHOS_DESPACHOS (ID_PROVINCIA)

DIM_CLIENTE (ID_CLIENTE) ←→ HECHOS_DEVOLUCIONES (ID_CLIENTE)
DIM_BODEGA (ID_BODEGA) ←→ HECHOS_DEVOLUCIONES (ID_BODEGA)
DIM_DESTINO (ID_DESTINO) ←→ HECHOS_DEVOLUCIONES (ID_DESTINO)
DIM_PROVINCIA (ID_PROVINCIA) ←→ HECHOS_DEVOLUCIONES (ID_PROVINCIA)
```


# Seguridad y Auditoría

AUDITORIA_ETL: Registra cada ejecución de ETL

Logs en consola: Seguimiento en tiempo real

Validaciones: Verificación de integridad de datos
