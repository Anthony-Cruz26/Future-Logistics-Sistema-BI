#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
PROCESO ETL - TRANSPORTE
================================================================================
Autor: Anthony Cruz, Yexica Angulo
Fecha: Abril 2026
Base de Datos: FUTURE_LOGISTIC

DESCRIPCION:
    Script ETL para la carga de datos de TRANSPORTE desde archivos Excel
    generados por el simulador SAP hacia la base de datos SQL Server.
    
    El proceso realiza las siguientes operaciones:
        1. Busca archivos SAP_TRANSPORTE_*.xlsx en la carpeta REPORTES
        2. Valida la estructura de columnas del archivo Excel
        3. Inserta los registros en la tabla HECHOS_TRANSPORTE
        4. Registra la auditoria en AUDITORIA_ETL
        5. Mueve los archivos procesados a la carpeta PROCESADOS

ESTRUCTURA DE LA TABLA HECHOS_TRANSPORTE:
    - FECHA: date (NO NULL)
    - ORDEN_TRANSPORTE: varchar(20) (PK)
    - ID_PRODUCTO: varchar(20) (FK)
    - ID_BODEGA: int (FK)
    - CTD_TEORICA_DESDE: int
    - CTD_TEORICA_HACIA: int
    - RUMA_ALMACENAMIENTO: varchar(20)
    - UMA: varchar(10)
    - LOTE: varchar(10)
    - ESTADO: varchar(20)
================================================================================
"""

import os
import sys
import pandas as pd
import pyodbc
from datetime import datetime

BASE_DIR = "C:/Users/yaps2/OneDrive - Ormesby Primary/Escritorio/SistemaSAP_Prueba"


class Config:
    """Configuracion centralizada del proceso ETL"""
    SERVER = 'localhost\\SQLEXPRESS'
    DATABASE = 'FUTURE_LOGISTIC'
    CARPETA_REPORTES = f"{BASE_DIR}/REPORTES"
    CARPETA_PROCESADOS = f"{BASE_DIR}/REPORTES/PROCESADOS"
    PATRON_ARCHIVO = 'SAP_TRANSPORTE_'


def conectar_sql():
    """Establece conexion con SQL Server usando autenticacion de Windows"""
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
    """Obtiene la lista de archivos de transporte pendientes de procesar"""
    archivos = []
    
    if not os.path.exists(Config.CARPETA_REPORTES):
        return archivos
    
    for archivo in os.listdir(Config.CARPETA_REPORTES):
        if archivo.startswith(Config.PATRON_ARCHIVO) and archivo.endswith('.xlsx'):
            ruta_completa = os.path.join(Config.CARPETA_REPORTES, archivo)
            archivos.append((archivo, ruta_completa))
    
    return sorted(archivos, reverse=True)


def procesar_archivo(nombre_archivo, ruta_archivo):
    """
    Procesa un archivo de transporte e inserta sus datos en la base de datos.
    
    Parametros:
        nombre_archivo: str - Nombre del archivo a procesar
        ruta_archivo: str - Ruta completa del archivo
    
    Retorna:
        bool - True si el proceso fue exitoso, False en caso contrario
    """
    inicio = datetime.now()
    print(f'\nPROCESANDO: {nombre_archivo}')
    
    try:
        dataframe = pd.read_excel(ruta_archivo, sheet_name='TRANSPORTE')
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
    
    for indice, fila in dataframe.iterrows():
        try:
            # El ID_BODEGA en el Excel ya es 1-6 (PK de DIM_BODEGA)
            # Valores posibles: 1, 2, 3, 4, 5, 6
            id_bodega = int(fila['ID_BODEGA'])
            
            # Validar que ID_BODEGA esté en rango 1-6
            if id_bodega < 1 or id_bodega > 6:
                print(f'   ERROR: ID_BODEGA fuera de rango: {id_bodega}')
                registros_error += 1
                continue
            
            cursor.execute('''
                INSERT INTO HECHOS_TRANSPORTE (
                    FECHA, ORDEN_TRANSPORTE, ID_PRODUCTO, ID_BODEGA,
                    CTD_TEORICA_DESDE, CTD_TEORICA_HACIA,
                    RUMA_ALMACENAMIENTO, UMA, LOTE, ESTADO
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fila['FECHA'],
                str(fila['ORDEN_TRANSPORTE']).strip(),
                str(fila['ID_PRODUCTO']).strip(),
                id_bodega,
                int(fila['CTD_TEORICA_DESDE']),
                int(fila['CTD_TEORICA_HACIA']),
                str(fila.get('RUMA_ALMACENAMIENTO', '')).strip() if pd.notna(fila.get('RUMA_ALMACENAMIENTO')) else None,
                str(fila.get('UMA', '')).strip() if pd.notna(fila.get('UMA')) else None,
                str(fila.get('LOTE', '')).strip() if pd.notna(fila.get('LOTE')) else None,
                str(fila.get('ESTADO', 'COMPLETADO')).strip().upper()
            ))
            
            registros_exitosos += 1
            
            if registros_exitosos % 1000 == 0:
                conexion.commit()
                print(f'      ... {registros_exitosos} registros insertados')
                
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
            'TRANSPORTE', nombre_archivo, total_registros,
            registros_exitosos, registros_error,
            'EXITOSO' if registros_error == 0 else 'PARCIAL', duracion
        ))
        conexion.commit()
    except Exception as error:
        print(f'   ERROR: Registrando auditoria - {str(error)}')
    
    # Mover archivo procesado a carpeta PROCESADOS
    try:
        destino = os.path.join(Config.CARPETA_PROCESADOS, nombre_archivo)
        os.rename(ruta_archivo, destino)
        print(f'   Archivo movido a: PROCESADOS')
    except Exception as error:
        print(f'   ERROR: Moviendo archivo - {str(error)}')
    
    conexion.close()
    print(f'   Insertados: {registros_exitosos} | Errores: {registros_error} | Tiempo: {duracion}s')
    return registros_error == 0


def procesar_todos():
    """Procesa todos los archivos de transporte pendientes"""
    os.makedirs(Config.CARPETA_PROCESADOS, exist_ok=True)
    
    archivos = obtener_archivos()
    
    if not archivos:
        print('\nINFO: No hay archivos de TRANSPORTE para procesar')
        return True
    
    todos_exitosos = True
    for nombre, ruta in archivos:
        if not procesar_archivo(nombre, ruta):
            todos_exitosos = False
    
    return todos_exitosos


if __name__ == '__main__':
    print('=' * 70)
    print('PROCESO ETL - TRANSPORTE')
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