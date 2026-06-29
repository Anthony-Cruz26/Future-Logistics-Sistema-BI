#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
PROCESO ETL - DESPACHO 
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
    PATRON_ARCHIVO = 'SAP_DESPACHO_'


def conectar_sql():
    try:
        conn_str = (f'Driver={{ODBC Driver 17 for SQL Server}};'
                    f'Server={Config.SERVER};'
                    f'Database={Config.DATABASE};'
                    f'Trusted_Connection=yes;')
        conexion = pyodbc.connect(conn_str, timeout=120)
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


def obtener_caches(cursor):
    """Cargar dimensiones en memoria"""
    
    bodegas = {}
    cursor.execute("SELECT CODIGO, ID_BODEGA FROM DIM_BODEGA")
    for row in cursor.fetchall():
        bodegas[row[0].strip()] = row[1]
    
    provincias = set()
    cursor.execute("SELECT ID_PROVINCIA FROM DIM_PROVINCIA")
    for row in cursor.fetchall():
        provincias.add(row[0])
    
    destinos = set()
    cursor.execute("SELECT ID_DESTINO FROM DIM_DESTINO")
    for row in cursor.fetchall():
        destinos.add(row[0])
    
    return bodegas, provincias, destinos


def procesar_archivo(nombre_archivo, ruta_archivo):
    inicio = datetime.now()
    print(f'\nPROCESANDO: {nombre_archivo}')

    try:
        dataframe = pd.read_excel(ruta_archivo, sheet_name='DESPACHOS')
        total_registros = len(dataframe)
        print(f'   Registros encontrados: {total_registros:,}')
    except Exception as error:
        print(f'   ERROR: Leyendo archivo - {str(error)}')
        return False

    conexion = conectar_sql()
    if not conexion:
        return False

    cursor = conexion.cursor()
    
    # Cargar caches
    bodegas_cache, provincias_cache, destinos_cache = obtener_caches(cursor)
    
    # Preparar datos para inserción masiva
    datos_dim = []
    datos_hechos = []
    
    registros_error = 0
    
    print('   Procesando filas...')
    
    for indice, fila in dataframe.iterrows():
        try:
            # ID_BODEGA
            codigo_bodega = str(fila['ID_BODEGA']).strip()
            if len(codigo_bodega) == 1:
                codigo_bodega = '0' + codigo_bodega
            id_bodega = bodegas_cache.get(codigo_bodega, 1)
            
            # ID_PROVINCIA e ID_DESTINO
            id_provincia = int(fila['ID_PROVINCIA'])
            id_destino = int(fila['ID_DESTINO'])
            
            if id_provincia not in provincias_cache:
                id_provincia = 1
            if id_destino not in destinos_cache:
                id_destino = 1
            
            # Datos comunes
            orden_despacho = str(fila['ORDEN_DESPACHO']).strip()
            fecha = fila['FECHA']
            id_cliente = int(fila['ID_CLIENTE'])
            id_producto = str(fila['ID_PRODUCTO']).strip()
            kilos = int(fila['KILOS_DESPACHADOS_CLIENTE'])
            uma = str(fila.get('UMA', '')).strip() if pd.notna(fila.get('UMA')) else None
            lote = str(fila.get('LOTE', '')).strip() if pd.notna(fila.get('LOTE')) else None
            ruma = str(fila.get('RUMA_DESPACHO', '')).strip() if pd.notna(fila.get('RUMA_DESPACHO')) else None
            estado = str(fila.get('ESTADO', 'DESPACHADO')).strip().upper()
            
            # Datos para DIM_TRANSACCION
            datos_dim.append((
                orden_despacho, fecha, id_cliente, id_producto,
                id_destino, id_bodega, kilos, uma, lote, ruma
            ))
            
            # Datos para HECHOS_DESPACHOS
            datos_hechos.append((
                fecha, orden_despacho, id_cliente, id_bodega, id_producto,
                ruma, uma, lote, id_provincia, id_destino, kilos, estado
            ))
            
        except Exception as error:
            registros_error += 1
            if registros_error <= 10:
                print(f'   ERROR: Fila {indice + 2} - {str(error)[:100]}')
    
    if not datos_dim:
        print('   No hay datos válidos para insertar')
        conexion.close()
        return False
    
    print(f'   Preparando inserción de {len(datos_dim):,} registros...')
    
    try:
        # Activar inserción rápida
        cursor.fast_executemany = True
        
        # Limpiar tablas antes de insertar (opcional - si quieres empezar fresco)
        # cursor.execute("DELETE FROM HECHOS_DESPACHOS")
        # cursor.execute("DELETE FROM DIM_TRANSACCION")
        # conexion.commit()
        # print('   Tablas limpiadas')
        
        # PASO 1: Insertar en DIM_TRANSACCION
        print('   Insertando en DIM_TRANSACCION...')
        
        # Insertar en lotes de 10000
        batch_size = 10000
        for i in range(0, len(datos_dim), batch_size):
            batch = datos_dim[i:i+batch_size]
            cursor.executemany('''
                INSERT INTO DIM_TRANSACCION (
                    ORDEN_DESPACHO, FECHA_DESPACHO, ID_CLIENTE, ID_PRODUCTO,
                    ID_DESTINO, ID_BODEGA, KILOS_DESPACHADOS, UMA, LOTE, RUMA_DESPACHO
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', batch)
            conexion.commit()
            print(f'       ... {min(i+batch_size, len(datos_dim)):,} de {len(datos_dim):,} registros en DIM_TRANSACCION')
        
        print(f'        {len(datos_dim):,} registros insertados en DIM_TRANSACCION')
        
        # PASO 2: Obtener IDs de transacción
        print('   Obteniendo IDs de transacción...')
        
        # Crear tabla temporal
        cursor.execute("CREATE TABLE #tmp_ordenes (ORDEN_DESPACHO varchar(20))")
        
        # Insertar órdenes únicas
        ordenes_unicas = list(set([d[0] for d in datos_dim]))
        for orden in ordenes_unicas:
            cursor.execute("INSERT INTO #tmp_ordenes (ORDEN_DESPACHO) VALUES (?)", (orden,))
        
        # Obtener IDs
        cursor.execute('''
            SELECT t.ORDEN_DESPACHO, d.ID_TRANSACCION 
            FROM #tmp_ordenes t
            INNER JOIN DIM_TRANSACCION d ON t.ORDEN_DESPACHO = d.ORDEN_DESPACHO
        ''')
        
        id_transaccion_map = {}
        for row in cursor.fetchall():
            id_transaccion_map[row[0]] = row[1]
        
        cursor.execute("DROP TABLE #tmp_ordenes")
        
        # PASO 3: Preparar datos de hechos con ID_TRANSACCION
        datos_hechos_con_id = []
        for i, d in enumerate(datos_hechos):
            orden = datos_dim[i][0]
            id_transaccion = id_transaccion_map.get(orden)
            if id_transaccion:
                datos_hechos_con_id.append(d + (id_transaccion,))
        
        # PASO 4: Insertar en HECHOS_DESPACHOS
        if datos_hechos_con_id:
            print('   Insertando en HECHOS_DESPACHOS...')
            
            for i in range(0, len(datos_hechos_con_id), batch_size):
                batch = datos_hechos_con_id[i:i+batch_size]
                cursor.executemany('''
                    INSERT INTO HECHOS_DESPACHOS (
                        FECHA, ORDEN_DESPACHO, ID_CLIENTE, ID_BODEGA, ID_PRODUCTO,
                        RUMA_DESPACHO, UMA, LOTE, ID_PROVINCIA, ID_DESTINO,
                        KILOS_DESPACHADOS_CLIENTE, ESTADO, ID_TRANSACCION
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', batch)
                conexion.commit()
                print(f'       ... {min(i+batch_size, len(datos_hechos_con_id)):,} de {len(datos_hechos_con_id):,} registros en HECHOS_DESPACHOS')
            
            print(f'        {len(datos_hechos_con_id):,} registros insertados en HECHOS_DESPACHOS')
        
    except Exception as error:
        print(f'   ERROR en inserción: {str(error)}')
        conexion.rollback()
        conexion.close()
        return False
    
    duracion = round((datetime.now() - inicio).total_seconds(), 2)
    
    # Auditoria
    try:
        cursor.execute('''
            INSERT INTO AUDITORIA_ETL (
                TIPO_ETL, NOMBRE_ARCHIVO, CANTIDAD_REGISTROS,
                REGISTROS_EXITOSOS, REGISTROS_ERROR, ESTADO,
                TIEMPO_EJECUCION_SEGUNDOS
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            'DESPACHO', nombre_archivo, total_registros,
            len(datos_hechos), registros_error,
            'EXITOSO' if registros_error == 0 else 'PARCIAL', duracion
        ))
        conexion.commit()
    except Exception as error:
        print(f'   ERROR: Registrando auditoria - {str(error)}')
    
    # Mover archivo
    try:
        destino = os.path.join(Config.CARPETA_PROCESADOS, nombre_archivo)
        os.rename(ruta_archivo, destino)
        print(f'   Archivo movido a: PROCESADOS')
    except Exception as error:
        print(f'   ERROR: Moviendo archivo - {str(error)}')
    
    conexion.close()
    
    print(f'    RESULTADO: {len(datos_hechos):,} despachos insertados | Errores: {registros_error} | Tiempo: {duracion:.2f}s')
    return registros_error == 0


def procesar_todos():
    os.makedirs(Config.CARPETA_PROCESADOS, exist_ok=True)
    archivos = obtener_archivos()
    
    if not archivos:
        print('\nINFO: No hay archivos de DESPACHO para procesar')
        return True
    
    todos_exitosos = True
    for nombre, ruta in archivos:
        if not procesar_archivo(nombre, ruta):
            todos_exitosos = False
    
    return todos_exitosos


if __name__ == '__main__':
    print('=' * 70)
    print('PROCESO ETL - DESPACHO')
    print('=' * 70)
    
    resultado = procesar_todos()
    
    print('=' * 70)
    if resultado:
        print(' PROCESO COMPLETADO EXITOSAMENTE')
    else:
        print(' PROCESO COMPLETADO CON ERRORES')
    print('=' * 70)
    
    sys.exit(0 if resultado else 1)