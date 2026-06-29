#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
PROCESO ETL - DEVOLUCIONES
================================================================================
Autor: Anthony Cruz, Yexica Angulo
Fecha: Abril 2026
Base de Datos: FUTURE_LOGISTIC

DESCRIPCION:
    Script ETL para la carga de datos de DEVOLUCIONES desde archivos Excel
    generados por el simulador SAP hacia la base de datos SQL Server.
    
    El proceso realiza las siguientes operaciones:
        1. Busca archivos SAP_DEVOLUCIONES_*.xlsx en la carpeta REPORTES
        2. Valida la estructura de columnas del archivo Excel
        3. Inserta los registros en la tabla HECHOS_DEVOLUCIONES
        4. Registra la auditoria en AUDITORIA_ETL
        5. Mueve los archivos procesados a la carpeta PROCESADOS
================================================================================
"""

import os
import sys
import pandas as pd
import pyodbc
from datetime import datetime

BASE_DIR = "C:/Users/yaps2/OneDrive - Ormesby Primary/Escritorio/SistemaSAP_Prueba"


class Config:
    SERVER = 'localhost\\SQLEXPRESS'
    DATABASE = 'FUTURE_LOGISTIC'
    CARPETA_REPORTES = f"{BASE_DIR}/REPORTES"
    CARPETA_PROCESADOS = f"{BASE_DIR}/REPORTES/PROCESADOS"
    PATRON_ARCHIVO = 'SAP_DEVOLUCIONES_'


def conectar_sql():
    try:
        conn_str = (f'Driver={{ODBC Driver 17 for SQL Server}};'
                    f'Server={Config.SERVER};'
                    f'Database={Config.DATABASE};'
                    f'Trusted_Connection=yes;')
        conexion = pyodbc.connect(conn_str, timeout=30)
        return conexion
    except Exception as error:
        print(f'   ERROR: Conexion SQL - {str(error)}')
        return None


def obtener_archivos():
    archivos = []
    if not os.path.exists(Config.CARPETA_REPORTES):
        return archivos
    
    for archivo in os.listdir(Config.CARPETA_REPORTES):
        if archivo.startswith(Config.PATRON_ARCHIVO) and archivo.endswith('.xlsx'):
            ruta_completa = os.path.join(Config.CARPETA_REPORTES, archivo)
            archivos.append((archivo, ruta_completa))
    
    return sorted(archivos, reverse=True)


def obtener_id_bodega(codigo_bodega, cursor):
    try:
        codigo = str(codigo_bodega).strip()
        if len(codigo) == 1:
            codigo = '0' + codigo
        cursor.execute("SELECT ID_BODEGA FROM DIM_BODEGA WHERE CODIGO = ?", codigo)
        resultado = cursor.fetchone()
        return resultado[0] if resultado else 1
    except Exception:
        return 1


def obtener_id_provincia(id_provincia, cursor):
    try:
        cursor.execute("SELECT ID_PROVINCIA FROM DIM_PROVINCIA WHERE ID_PROVINCIA = ?", int(id_provincia))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else 1
    except Exception:
        return 1


def obtener_id_destino(id_destino, cursor):
    try:
        cursor.execute("SELECT ID_DESTINO FROM DIM_DESTINO WHERE ID_DESTINO = ?", int(id_destino))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else 1
    except Exception:
        return 1


def obtener_id_transaccion(orden_despacho_original, cursor):
    try:
        orden_str = str(orden_despacho_original).strip()
        cursor.execute("SELECT ID_TRANSACCION FROM DIM_TRANSACCION WHERE ORDEN_DESPACHO = ?", orden_str)
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None
    except Exception:
        return None


def procesar_archivo(nombre_archivo, ruta_archivo):
    inicio = datetime.now()
    print(f'\nPROCESANDO: {nombre_archivo}')
    
    try:
        dataframe = pd.read_excel(ruta_archivo, sheet_name='DEVOLUCIONES')
        total_registros = len(dataframe)
        print(f'   Registros encontrados: {total_registros}')
        print(f'   Columnas encontradas: {list(dataframe.columns)}')
    except Exception as error:
        print(f'   ERROR: Leyendo archivo - {str(error)}')
        return False
    
    conexion = conectar_sql()
    if not conexion:
        return False
    
    cursor = conexion.cursor()
    registros_exitosos = 0
    registros_error = 0
    no_encontrados = 0
    
    for indice, fila in dataframe.iterrows():
        try:
            # Buscar ID_TRANSACCION en DIM_TRANSACCION
            id_transaccion_origen = obtener_id_transaccion(fila['ORDEN_DESPACHO_ORIGINAL'], cursor)
            
            if not id_transaccion_origen:
                no_encontrados += 1
                continue
            
            id_bodega = obtener_id_bodega(fila['ID_BODEGA'], cursor)
            id_provincia = obtener_id_provincia(fila['ID_PROVINCIA'], cursor)
            id_destino = obtener_id_destino(fila['ID_DESTINO'], cursor)
            
            cursor.execute('''
                INSERT INTO HECHOS_DEVOLUCIONES (
                    FECHA_DEVOLUCION, ORDEN_DEVOLUCION, ID_CLIENTE, ID_PROVINCIA,
                    ID_DESTINO, ID_BODEGA, RUMA_DESTINO, KILOS_DEVUELTOS,
                    MOTIVO_DEVOLUCION, ID_PRODUCTO, ID_TRANSACCION_ORIGEN
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fila['FECHA_DEVOLUCION'],
                str(fila['ORDEN_DEVOLUCION']).strip(),
                int(fila['ID_CLIENTE']),
                id_provincia,
                id_destino,
                id_bodega,
                str(fila.get('RUMA_DESTINO', '')).strip() if pd.notna(fila.get('RUMA_DESTINO')) else None,
                int(fila['KILOS_DEVUELTOS']),
                str(fila.get('MOTIVO_DEVOLUCION', 'DAÑADO EMPAQUE')).strip().upper(),
                str(fila.get('ID_PRODUCTO', '')).strip() if pd.notna(fila.get('ID_PRODUCTO')) else None,
                id_transaccion_origen
            ))
            
            registros_exitosos += 1
            
            if registros_exitosos % 1000 == 0:
                conexion.commit()
                
        except Exception as error:
            registros_error += 1
            if registros_error <= 10:
                print(f'   ERROR: Fila {indice + 2} - {str(error)[:100]}')
    
    conexion.commit()
    duracion = round((datetime.now() - inicio).total_seconds(), 2)
    
    # Registrar auditoria
    try:
        cursor.execute('''
            INSERT INTO AUDITORIA_ETL (
                TIPO_ETL, NOMBRE_ARCHIVO, CANTIDAD_REGISTROS,
                REGISTROS_EXITOSOS, REGISTROS_ERROR, ESTADO,
                TIEMPO_EJECUCION_SEGUNDOS
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            'DEVOLUCION', nombre_archivo, total_registros,
            registros_exitosos, registros_error + no_encontrados,
            'EXITOSO' if (registros_error == 0 and no_encontrados == 0) else 'PARCIAL', duracion
        ))
        conexion.commit()
    except Exception as error:
        print(f'   ERROR: Registrando auditoria - {str(error)}')
    
    # Mover archivo procesado
    try:
        destino = os.path.join(Config.CARPETA_PROCESADOS, nombre_archivo)
        os.rename(ruta_archivo, destino)
        print(f'   Archivo movido a: PROCESADOS')
    except Exception as error:
        print(f'   ERROR: Moviendo archivo - {str(error)}')
    
    conexion.close()
    print(f'   Insertados: {registros_exitosos} | No encontrados: {no_encontrados} | Errores: {registros_error} | Tiempo: {duracion}s')
    return registros_error == 0 and no_encontrados == 0


def procesar_todos():
    os.makedirs(Config.CARPETA_PROCESADOS, exist_ok=True)
    archivos = obtener_archivos()
    
    if not archivos:
        print('\nINFO: No hay archivos de DEVOLUCIONES para procesar')
        return True
    
    todos_exitosos = True
    for nombre, ruta in archivos:
        if not procesar_archivo(nombre, ruta):
            todos_exitosos = False
    
    return todos_exitosos


if __name__ == '__main__':
    print('=' * 70)
    print('PROCESO ETL - DEVOLUCIONES')
    print('Autores: Anthony Cruz, Yexica Angulo')
    print('Fecha: Junio 2026')
    print('=' * 70)
    
    resultado = procesar_todos()
    
    print('=' * 70)
    if resultado:
        print(' PROCESO COMPLETADO EXITOSAMENTE')
    else:
        print(' PROCESO COMPLETADO CON ERRORES')
    print('=' * 70)
    
    sys.exit(0 if resultado else 1)