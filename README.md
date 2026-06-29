🚛 Future Logistics S.A. - Sistema de Inteligencia de Negocios

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![SQL Server](https://img.shields.io/badge/SQL%20Server-2022-red)](https://www.microsoft.com/es-es/sql-server/)
[![Power BI](https://img.shields.io/badge/Power%20BI-Desktop-yellow)](https://powerbi.microsoft.com/)
[![Selenium](https://img.shields.io/badge/Selenium-4.0-green)](https://www.selenium.dev/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

📋 Descripción del Proyecto

Sistema automatizado de **Inteligencia de Negocios** para **FutureLogistic S.A.**, empresa de logística y distribución de azúcar en Ecuador.

El sistema simula, extrae, transforma y carga datos desde un sistema SAT (Sistema de Almacenamiento y Transporte) hacia un **Data Warehouse en SQL Server** con modelo estrella, para posteriormente visualizar KPIs logísticos en **Power BI**.

🎯 Objetivos del Proyecto

1. **Gestionar** los indicadores de desempeño (KPIs) cruciales para el proceso operativo logístico
2. **Construir** la arquitectura técnica del sistema ETL-BI
3. **Automatizar** la extracción programada de datos desde SAP hacia SQL Server
4. **Diseñar** dashboards interactivos en Power BI

---

# Arquitectura del Sistema
┌─────────────────────────────────────────────────────────────────────┐
│ ARQUITECTURA DEL SISTEMA │
├─────────────────────────────────────────────────────────────────────┤
│ │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│ │ SIMULADOR │ │ ROBOT │ │ SQL SERVER │ │
│ │ SAP │ ──▶│ (Python) │ ──▶│ Database │ │
│ │ (HTML/JS) │ │ │ │ │ │
│ └──────────────┘ └──────────────┘ └──────────────┘ │
│ │ │ │ │
│ ▼ ▼ ▼ │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│ │ Archivos │ │ ETLs │ │ POWER BI │ │
│ │ Excel │ │ (Python) │ │ Dashboard │ │
│ └──────────────┘ └──────────────┘ └──────────────┘ │
│ │
└─────────────────────────────────────────────────────────────────────┘

**Componentes Principales**

| Componente | Tecnología | Propósito |
|------------|------------|-----------|
| **Simulador SAP** | HTML, CSS, JavaScript, XLSX | Genera datos históricos realistas |
| **Robot Automatizador** | Python + Selenium | Navega, extrae y descarga archivos |
| **ETL** | Python + Pandas + PyODBC | Transforma y carga datos en SQL Server |
| **Data Warehouse** | SQL Server (Modelo Estrella) | Almacena datos históricos |
| **Dashboards** | Power BI | Visualización de KPIs |

# 📊 Modelo de Datos

# Modelo Estrella
┌─────────────────────┐
│ DIM_FECHA │
│ (Calendario) │
└──────────┬──────────┘
│
┌──────────────────────┼──────────────────────┐
│ │ │
▼ ▼ ▼
┌───────────────┐ ┌─────────────────┐ ┌───────────────┐
│ DIM_BODEGA │ │ HECHOS_ │ │ DIM_CLIENTE │
│ │ │ TRANSPORTE │ │ │
└───────────────┘ └─────────────────┘ └───────────────┘
│
┌─────────────────────┼─────────────────────┐
│ │ │
▼ ▼ ▼
┌───────────────┐ ┌─────────────────┐ ┌───────────────┐
│ DIM_PRODUCTO │ │ HECHOS_ │ │ DIM_DESTINO │
│ │ │ DESPACHOS │ │ │
└───────────────┘ └─────────────────┘ └───────────────┘
│
▼
┌─────────────────┐
│ HECHOS_ │
│ DEVOLUCIONES │
└─────────────────┘


### Tablas Principales

| Tabla | PK | Propósito |
|-------|-----|-----------|
| `HECHOS_TRANSPORTE` | `ORDEN_TRANSPORTE` | Ingreso de azúcar a bodegas |
| `HECHOS_DESPACHOS` | `ORDEN_DESPACHO` | Salida de azúcar a clientes |
| `HECHOS_DEVOLUCIONES` | `ORDEN_DEVOLUCION` | Devoluciones de clientes |

---

## 🚀 Instalación Rápida

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/FutureLogistic-Sistema-BI.git
cd FutureLogistic-Sistema-BI
```

# 2. Instalar dependencias
pip install -r requirements.txt

#3. Configurar base de datos
Abrir SQL Server Management Studio

Ejecutar database/FUTURE_LOGISTIC.sql

Verificar la creación de tablas


