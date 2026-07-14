# FUTURE LOGISTIC - Base de Datos

## Descripción
Base de datos del sistema de inteligencia de negocios para Future Logistics S.A.

## Modelo de datos
- **Modelo:** Copo de nieve (Snowflake)
- **Base de datos:** SQL Server
- **Tecnologías:** SQL Server + Power BI + Python ETL

## Tablas

### Tablas de Hechos
| Tabla | Descripción | Registros aprox. |
|-------|-------------|------------------|
| `HECHOS_TRANSPORTE` | Ingreso de azúcar a bodegas | 107,949 |
| `HECHOS_DESPACHOS` | Salida de azúcar a clientes | 227,569 |
| `HECHOS_DEVOLUCIONES` | Devoluciones de clientes | 17,461 |

### Tablas de Dimensiones
| Tabla | Descripción |
|-------|-------------|
| `DIM_BODEGA` | Catálogo de bodegas (6 en Durán) |
| `DIM_CLIENTE` | Catálogo de clientes (15) |
| `DIM_DESTINO` | Ciudades de destino |
| `DIM_PRODUCTO` | Catálogo de productos (23) |
| `DIM_PROVINCIA` | Provincias del Ecuador |
| `DIM_TRANSACCION` | Tabla puente (transacciones) |

## Índices
Todos los índices están optimizados para consultas de Power BI.

## Relaciones
- `HECHOS_DESPACHOS` → `DIM_TRANSACCION` (FK)
- `HECHOS_DEVOLUCIONES` → `DIM_TRANSACCION` (FK)
- `DIM_DESTINO` → `DIM_PROVINCIA` (FK)

## Uso en el proyecto
Esta BD recibe datos del robot `INICIAR.py` y alimenta los dashboards de Power BI.

---

**Autor:** Anthony Cruz / Yexica Angulo  
**Fecha:** Julio 2026  
**Proyecto:** Tesis Future Logistics S.A.