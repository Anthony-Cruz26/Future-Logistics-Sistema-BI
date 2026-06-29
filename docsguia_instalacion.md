# 🔧 Guía de Instalación

## Requisitos Previos

### Software Requerido

| Software | Versión | Descarga |
|----------|---------|----------|
| Python | 3.8+ | [python.org](https://www.python.org/) |
| SQL Server | 2017+ | [microsoft.com](https://www.microsoft.com/sql-server) |
| SQL Server Management Studio | 18+ | [microsoft.com](https://docs.microsoft.com/ssms) |
| Power BI Desktop | Última | [microsoft.com](https://powerbi.microsoft.com) |
| Chrome Browser | Última | [google.com/chrome](https://www.google.com/chrome) |
| Git | Última | [git-scm.com](https://git-scm.com/) |

---

## Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/Future Logistics-Sistema-BI.git
cd Future Logistics-Sistema-BI
```

## Paso 2: Crear Entorno Virtual

Windows
python -m venv venv
venv\Scripts\activate

Linux/Mac
python3 -m venv venv
source venv/bin/activate

## Paso 3: Instalar Dependencias
pip install -r requirements.txt

## Paso 4: Configurar Base de Datos
4.1 Abrir SQL Server Management Studio
4.2 Ejecutar el script de creación

-- Abrir el archivo database/FUTURE_LOGISTIC.sql
-- Ejecutarlo completamente (F5)

4.3 Verificar la creación
USE FUTURE_LOGISTIC;
SELECT * FROM INFORMATION_SCHEMA.TABLES;

## Paso 5: Configurar Rutas
5.1 Verificar rutas en INICIAR.py
Abrir src/robot/INICIAR.py y verificar:

class Config:
    RUTA_HTML = "C:/Users/tu_usuario/.../SIMULACIÓN_SAP.html"
    CARPETA_REPORTES = "C:/Users/tu_usuario/.../REPORTES"
    RUTA_ETL_TRANSPORTE = "C:/Users/tu_usuario/.../PROCESO_ETL_TRANSPORTE.py"
    RUTA_ETL_DESPACHO = "C:/Users/tu_usuario/.../PROCESO_ETL_DESPACHO.py"
    RUTA_ETL_DEVOLUCION = "C:/Users/tu_usuario/.../PROCESO_ETL_DEVOLUCION.py"

5.2 Ajustar según tu sistema
Reemplaza tu_usuario con tu nombre de usuario real.

## Paso 6: Configurar Power BI
6.1 Abrir Power BI Desktop
6.2 Conectar a SQL Server
Obtener datos → SQL Server

Servidor: localhost\SQLEXPRESS

Base de datos: FUTURE_LOGISTIC

Seleccionar tablas:

DIM_BODEGA

DIM_CLIENTE

DIM_DESTINO

DIM_PRODUCTO

DIM_PROVINCIA

HECHOS_TRANSPORTE

HECHOS_DESPACHOS

HECHOS_DEVOLUCIONES

6.3 Crear Relaciones
Tabla 1	Tabla 2	Relación
DIM_BODEGA.ID_BODEGA	HECHOS_TRANSPORTE.ID_BODEGA	1:N
DIM_PRODUCTO.ID_PRODUCTO	HECHOS_TRANSPORTE.ID_PRODUCTO	1:N
DIM_CLIENTE.ID_CLIENTE	HECHOS_DESPACHOS.ID_CLIENTE	1:N
DIM_DESTINO.ID_DESTINO	HECHOS_DESPACHOS.ID_DESTINO	1:N
DIM_PROVINCIA.ID_PROVINCIA	HECHOS_DESPACHOS.ID_PROVINCIA	1:N

## Paso 7: Ejecutar el Sistema
7.1 Ejecución única
bash
python src/robot/INICIAR.py --once
7.2 Ejecución en bucle
bash
python src/robot/INICIAR.py

## Paso 8: Verificar Resultados
8.1 Verificar archivos descargados
bash
ls src/reportes/REPORTES/
8.2 Verificar datos en SQL Server
sql
USE FUTURE_LOGISTIC;

-- Contar registros
SELECT 'TRANSPORTE' AS Tabla, COUNT(*) FROM HECHOS_TRANSPORTE
UNION ALL
SELECT 'DESPACHO', COUNT(*) FROM HECHOS_DESPACHOS
UNION ALL
SELECT 'DEVOLUCION', COUNT(*) FROM HECHOS_DEVOLUCIONES;

-- Ver auditoría
SELECT * FROM AUDITORIA_ETL ORDER BY ID_AUDITORIA DESC;
Solución de Problemas
Error: "No se encuentra el módulo pyodbc"
bash
pip install pyodbc
Error: "ChromeDriver no encontrado"
bash
pip install --upgrade webdriver-manager
Error: "No se puede conectar a SQL Server"
Verificar que SQL Server esté corriendo

Verificar que el nombre del servidor sea correcto

Verificar autenticación de Windows

Error: "HTML no encontrado"
Verificar que la ruta en INICIAR.py apunte correctamente al archivo HTML

