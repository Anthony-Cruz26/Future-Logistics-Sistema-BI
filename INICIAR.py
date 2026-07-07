#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
SISTEMA DE INTELIGENCIA DE NEGOCIOS - FUTURE LOGISTICS S.A.
================================================================================

MODULO: INICIAR.py
FECHA: Junio 2026

DESCRIPCION:
    Robot automatizado que gestiona el flujo completo de extraccion,
    transformacion y carga de datos desde el simulador SAP hacia
    la base de datos SQL Server.

FUNCIONALIDADES:
    1. Abre navegador y accede al simulador SAP
    2. Espera 30 segundos en pantalla de filtros para seleccion manual
    3. Genera datos de TRANSPORTE, DESPACHO y DEVOLUCIONES
    4. Descarga archivos Excel usando exportarSegunSeleccion()
    5. Ejecuta procesos ETL con pausas controladas
    6. Muestra MessageBox con resultado de cada ETL
    7. Abre dashboards de Power BI en navegador predeterminado
    8. El navegador se queda abierto en la pantalla de resultados

================================================================================
"""

import os
import sys
import time
import shutil
import subprocess
import ctypes
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


# ============================================================================
# CONFIGURACION DE CONSOLA (WINDOWS)
# ============================================================================
if sys.platform == "win32":
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 6)
    except:
        pass


# ============================================================================
# CONFIGURACION DEL SISTEMA
# ============================================================================
class Config:

    USUARIO = "supervisor"
    CONTRASENA = "distribucion2026"

    RUTA_HTML = "C:/Users/yaps2/OneDrive - Ormesby Primary/Escritorio/SistemaSAP_Prueba/SIMULACIÓN_SAP.html"
    URL_SAP = Path(RUTA_HTML).as_uri()

    CARPETA_REPORTES = "C:/Users/yaps2/OneDrive - Ormesby Primary/Escritorio/SistemaSAP_Prueba/REPORTES"
    CARPETA_PROCESADOS = os.path.join(CARPETA_REPORTES, "PROCESADOS")
    CARPETA_DESCARGAS = os.path.join(os.path.expanduser("~"), "Downloads")

    ESPERA_CARGA = 5
    ESPERA_DESCARGA = 30
    ESPERA_BOTON = 20
    ESPERA_REPORTE = 15
    ESPERA_POST_LOGIN = 5
    ESPERA_SELECCION_MANUAL = 30
    INTERVALO_EJECUCION = 7200
    PAUSA_ENTRE_ETL = 5

    TIMEOUT_ETL_TRANSPORTE = 1800
    TIMEOUT_ETL_DESPACHO = 1800
    TIMEOUT_ETL_DEVOLUCION = 1800

    SELECTORES = {
        'logon_row': "div#logon-row",
        'btn_acceder': "span#lg-acceder",
        'usuario': "input#loginUser",
        'contrasena': "input#loginPass",
        'btn_login': "button#btnLogin",
        'cmd_input': "input#cmdInp",
        'btn_ejecutar_reporte': "button.btn-success"
    }

    RUTA_ETL_TRANSPORTE = "C:/Users/yaps2/OneDrive - Ormesby Primary/Escritorio/SistemaSAP_Prueba/PROCESO_ETL_TRANSPORTE.py"
    RUTA_ETL_DESPACHO = "C:/Users/yaps2/OneDrive - Ormesby Primary/Escritorio/SistemaSAP_Prueba/PROCESO_ETL_DESPACHO.py"
    RUTA_ETL_DEVOLUCION = "C:/Users/yaps2/OneDrive - Ormesby Primary/Escritorio/SistemaSAP_Prueba/PROCESO_ETL_DEVOLUCION.py"


# ============================================================================
# FUNCIONES DE GESTION DE CARPETAS
# ============================================================================
def crear_carpetas():
    os.makedirs(Config.CARPETA_REPORTES, exist_ok=True)
    os.makedirs(Config.CARPETA_PROCESADOS, exist_ok=True)
    return True


# ============================================================================
# FUNCIONES DE LOGGING
# ============================================================================
def guardar_log(paso, mensaje):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f'[{timestamp}] {paso}: {mensaje}')


def mostrar_mensaje_exito():
    try:
        ctypes.windll.user32.MessageBoxW(
            0,
            "PROCESO COMPLETADO CON EXITO\n\n"
            "Los datos han sido cargados en SQL Server.\n\n"
            "Archivos generados:\n"
            "  - TRANSPORTE\n"
            "  - DESPACHO\n"
            "  - DEVOLUCIONES\n\n"
            "El navegador permanece abierto en la pantalla de resultados.\n"
            "Los dashboards se abriran en tu navegador predeterminado.",
            "Future Logistics S.A. - Robot SAP",
            0x40 | 0x0
        )
    except:
        pass


def mostrar_mensaje_error_etl(nombre_etl, error_detalle=""):
    try:
        mensaje = f"ERROR EN EL ETL - {nombre_etl}\n\n"
        if error_detalle:
            mensaje += f"Detalles:\n{error_detalle}\n\n"
        mensaje += "Revise la consola para mas detalles.\n\n"
        mensaje += "Los dashboards se abriran de todas formas."
        
        ctypes.windll.user32.MessageBoxW(
            0,
            mensaje,
            "Future Logistics S.A. - Error ETL",
            0x10 | 0x0
        )
    except:
        pass

    
def mostrar_mensaje_error_general(error=""):
    try:
        mensaje = "ERROR EN EL PROCESO GENERAL\n\n"
        if error:
            mensaje += f"Detalles:\n{error}\n\n"
        mensaje += "Revise la consola.\n\n"
        mensaje += "Los dashboards se abriran de todas formas."
        
        ctypes.windll.user32.MessageBoxW(
            0,
            mensaje,
            "Future Logistics S.A. - Error General",
            0x10 | 0x0
        )
    except:
        pass


def mostrar_mensaje_info_dashboards():
    try:
        ctypes.windll.user32.MessageBoxW(
            0,
            "ABRIENDO DASHBOARDS\n\n"
            "Se abriran los dashboards de Power BI en tu navegador predeterminado.\n\n"
            "TRANSPORTE\n"
            "DESPACHO\n"
            "DEVOLUCIONES\n\n"
            "Si no se abren, verifica que tengas sesion iniciada en Power BI.",
            "Future Logistics S.A. - Dashboards",
            0x40 | 0x0
        )
    except:
        pass


# ============================================================================
# FUNCIONES DE NAVEGACION Y AUTOMATIZACION
# ============================================================================
def iniciar_navegador():
    try:
        opciones = Options()
        opciones.add_argument("--start-maximized")
        opciones.add_argument("--disable-notifications")

        prefs = {
            "download.default_directory": Config.CARPETA_DESCARGAS,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_setting_values.automatic_downloads": 1,
        }
        opciones.add_experimental_option("prefs", prefs)

        opciones.add_argument("--disable-web-security")
        opciones.add_argument("--allow-running-insecure-content")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=opciones
        )
        guardar_log('NAVEGADOR', 'Navegador iniciado')
        return driver
    except Exception as e:
        guardar_log('ERROR_NAVEGADOR', str(e))
        return None


def verificar_html():
    existe = os.path.exists(Config.RUTA_HTML)
    if existe:
        guardar_log('ARCHIVO', 'HTML encontrado')
    return existe


def navegar(driver):
    try:
        driver.get(Config.URL_SAP)
        time.sleep(Config.ESPERA_CARGA)
        guardar_log('NAVEGACION', 'Pagina cargada')
        return True
    except Exception as e:
        guardar_log('ERROR_NAV', str(e))
        return False


def acceder_desde_logon(driver):
    try:
        guardar_log('LOGON', 'Accediendo al sistema desde pantalla LOGON...')

        WebDriverWait(driver, Config.ESPERA_BOTON).until(
            EC.presence_of_element_located((By.ID, "s-logon"))
        )
        time.sleep(1)

        try:
            fila_sistema = WebDriverWait(driver, Config.ESPERA_BOTON).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, Config.SELECTORES['logon_row']))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", fila_sistema)
            time.sleep(0.5)

            acciones = ActionChains(driver)
            acciones.double_click(fila_sistema).perform()
            guardar_log('LOGON', 'Doble clic en sistema ejecutado')
            time.sleep(2)
            return True

        except Exception as e:
            guardar_log('LOGON', f'Error en doble clic: {str(e)}')

            try:
                boton_acceder = WebDriverWait(driver, Config.ESPERA_BOTON).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, Config.SELECTORES['btn_acceder']))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", boton_acceder)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", boton_acceder)
                guardar_log('LOGON', 'Click en Acceder al sistema ejecutado')
                time.sleep(2)
                return True
            except Exception as e2:
                guardar_log('LOGON', f'Error en click: {str(e2)}')
                return False

    except Exception as e:
        guardar_log('ERROR_LOGON', str(e))
        return False


def login(driver):
    try:
        guardar_log('LOGIN', 'Esperando pantalla de login...')

        WebDriverWait(driver, Config.ESPERA_BOTON).until(
            EC.visibility_of_element_located((By.ID, "s-login"))
        )
        time.sleep(2)

        campo_usuario = WebDriverWait(driver, Config.ESPERA_BOTON).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, Config.SELECTORES['usuario']))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", campo_usuario)
        time.sleep(0.5)
        campo_usuario.clear()
        campo_usuario.send_keys(Config.USUARIO)
        guardar_log('LOGIN', 'Usuario ingresado')

        campo_pass = WebDriverWait(driver, Config.ESPERA_BOTON).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, Config.SELECTORES['contrasena']))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", campo_pass)
        time.sleep(0.5)
        campo_pass.clear()
        campo_pass.send_keys(Config.CONTRASENA)
        guardar_log('LOGIN', 'Contrasena ingresada')

        boton_login = WebDriverWait(driver, Config.ESPERA_BOTON).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, Config.SELECTORES['btn_login']))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_login)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", boton_login)
        guardar_log('LOGIN', 'Click en ACCEDER ejecutado')

        time.sleep(Config.ESPERA_POST_LOGIN)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "s-ea"))
            )
            guardar_log('LOGIN', 'Easy Access cargado correctamente')
        except:
            guardar_log('LOGIN', 'No se detecto Easy Access, continuando...')

        guardar_log('LOGIN', 'Sesion iniciada correctamente')
        return True

    except Exception as e:
        guardar_log('ERROR_LOGIN', str(e))
        try:
            driver.save_screenshot("error_login.png")
            guardar_log('ERROR_LOGIN', 'Screenshot guardado')
        except:
            pass
        return False


def ejecutar_comando_lx02(driver):
    try:
        guardar_log('COMANDO', 'Ejecutando comando Lx02...')

        WebDriverWait(driver, Config.ESPERA_BOTON).until(
            EC.visibility_of_element_located((By.ID, "s-ea"))
        )
        time.sleep(2)

        cmd_input = WebDriverWait(driver, Config.ESPERA_BOTON).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, Config.SELECTORES['cmd_input']))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", cmd_input)
        time.sleep(0.5)

        cmd_input.clear()
        cmd_input.send_keys("Lx02")
        time.sleep(0.5)

        cmd_input.send_keys(Keys.ENTER)
        guardar_log('COMANDO', 'Comando Lx02 ejecutado')

        try:
            WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.ID, "s-filter"))
            )
            guardar_log('COMANDO', 'Pantalla de filtros cargada')
        except:
            guardar_log('COMANDO', 'No se detecto pantalla de filtros')

        time.sleep(2)
        return True
    except Exception as e:
        guardar_log('ERROR_COMANDO', str(e))
        return False


def ejecutar_reporte(driver):
    try:
        guardar_log('REPORTE', 'Pantalla de filtros cargada')

        guardar_log('MANUAL', '=' * 50)
        guardar_log('MANUAL', 'TIEMPO PARA SELECCION MANUAL')
        guardar_log('MANUAL', '=' * 50)
        guardar_log('MANUAL', f'Tienes {Config.ESPERA_SELECCION_MANUAL} segundos para:')
        guardar_log('MANUAL', '  - Cambiar las fechas de consulta')
        guardar_log('MANUAL', '  - Seleccionar una bodega especifica')
        guardar_log('MANUAL', '  - Filtrar por tipo de azucar')
        guardar_log('MANUAL', '  - Seleccionar que datos exportar')
        guardar_log('MANUAL', '')
        guardar_log('MANUAL', f'Esperando {Config.ESPERA_SELECCION_MANUAL} segundos...')
        guardar_log('MANUAL', '')

        for i in range(Config.ESPERA_SELECCION_MANUAL, 0, -1):
            print(f'  [MANUAL] Segundos restantes para seleccion: {i:2d}', end='\r')
            time.sleep(1)
        print('')

        guardar_log('MANUAL', 'Tiempo de seleccion finalizado. Continuando con ejecucion automatica...')
        guardar_log('MANUAL', '=' * 50)

        boton = None
        estrategias = [
            (By.XPATH, "//button[contains(text(), 'EJECUTAR REPORTE')]"),
            (By.CLASS_NAME, "btn-success"),
            (By.XPATH, "//button[contains(text(), 'EJECUTAR')]"),
            (By.CSS_SELECTOR, "button.btn.btn-success"),
            (By.XPATH, "//button[@onclick='ejecutarReporte()']")
        ]

        for by, selector in estrategias:
            try:
                boton = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((by, selector))
                )
                guardar_log('REPORTE', f'Boton encontrado con selector: {selector}')
                break
            except:
                continue

        if not boton:
            guardar_log('REPORTE', 'No se pudo encontrar el boton EJECUTAR REPORTE')
            driver.save_screenshot("error_boton_reporte.png")
            return False

        driver.execute_script("arguments[0].scrollIntoView(true);", boton)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", boton)
        guardar_log('REPORTE', 'Click en EJECUTAR REPORTE')

        guardar_log('REPORTE', f'Generando datos... esperando {Config.ESPERA_REPORTE} segundos')

        for i in range(1, Config.ESPERA_REPORTE // 5 + 1):
            time.sleep(5)
            if i % 2 == 0:
                guardar_log('REPORTE', f'Generando datos... {i * 5}/{Config.ESPERA_REPORTE} segundos')

        try:
            cantidad = driver.execute_script("return datosTransporte ? datosTransporte.length : 0;")
            guardar_log('REPORTE', f'Datos generados: {cantidad:,} transportes')
            if cantidad == 0:
                guardar_log('REPORTE', 'No se generaron datos, reintentando...')
                driver.execute_script("arguments[0].click();", boton)
                time.sleep(Config.ESPERA_REPORTE)
        except Exception as e:
            guardar_log('REPORTE', f'No se pudo verificar datos: {str(e)}')

        return True
    except Exception as e:
        guardar_log('ERROR_REPORTE', str(e))
        return False


def descargar_archivos(driver):
    try:
        guardar_log('DESCARGA', 'Iniciando descarga de archivos...')
        
        archivos_antes = set()
        if os.path.exists(Config.CARPETA_DESCARGAS):
            for f in os.listdir(Config.CARPETA_DESCARGAS):
                if f.startswith('SAP_') and f.endswith('.xlsx'):
                    archivos_antes.add(f)
        guardar_log('DESCARGA', f'Archivos previos en Downloads: {len(archivos_antes)}')

        try:
            cantidad = driver.execute_script("return datosTransporte ? datosTransporte.length : 0;")
            if cantidad == 0:
                guardar_log('DESCARGA', 'No hay datos para exportar. Abortando descarga.')
                return False
            guardar_log('DESCARGA', f'Datos listos para exportar: {cantidad:,} registros')
        except Exception as e:
            guardar_log('DESCARGA', f'No se pudo verificar datos: {str(e)}')

        guardar_log('DESCARGA', 'Ejecutando exportarSegunSeleccion()...')
        driver.execute_script("exportarSegunSeleccion();")

        tiempo_espera = 0
        archivos_descargados = set()

        guardar_log('DESCARGA', f'Esperando descarga (max {Config.ESPERA_DESCARGA}s)...')

        while tiempo_espera < Config.ESPERA_DESCARGA:
            time.sleep(3)
            tiempo_espera += 3

            archivos_ahora = set()
            if os.path.exists(Config.CARPETA_DESCARGAS):
                for f in os.listdir(Config.CARPETA_DESCARGAS):
                    if (f.startswith('SAP_') and f.endswith('.xlsx') and
                        not f.endswith('.tmp') and not f.endswith('.crdownload')):
                        archivos_ahora.add(f)

            nuevos = archivos_ahora - archivos_antes
            if nuevos:
                archivos_descargados.update(nuevos)
                guardar_log('DESCARGA', f'Detectados: {nuevos}')

            if len(archivos_descargados) >= 3:
                guardar_log('DESCARGA', f'3 archivos descargados exitosamente en {tiempo_espera}s')
                return True

            if tiempo_espera % 9 == 0:
                guardar_log('DESCARGA', f'Esperando... {tiempo_espera}/{Config.ESPERA_DESCARGA}s - Encontrados: {len(archivos_descargados)}/3')

        if archivos_descargados:
            guardar_log('DESCARGA', f'Solo {len(archivos_descargados)} archivo(s): {archivos_descargados}')
            return True
        else:
            guardar_log('DESCARGA', 'No se descargo ningun archivo')
            driver.save_screenshot("error_descarga.png")
            guardar_log('DESCARGA', 'Screenshot guardado: error_descarga.png')
            return False

    except Exception as e:
        guardar_log('ERROR_DESCARGA', str(e))
        return False


def mover_archivos_descargados():
    archivos_movidos = []

    guardar_log('MOVIMIENTO', 'Buscando archivos en Downloads...')

    if not os.path.exists(Config.CARPETA_DESCARGAS):
        guardar_log('ERROR', 'Carpeta Downloads no existe')
        return archivos_movidos

    archivos_encontrados = []
    for archivo in os.listdir(Config.CARPETA_DESCARGAS):
        if archivo.startswith('SAP_') and archivo.endswith('.xlsx'):
            archivos_encontrados.append(archivo)

    guardar_log('MOVIMIENTO', f'Archivos encontrados: {len(archivos_encontrados)}')

    for archivo in archivos_encontrados:
        origen = os.path.join(Config.CARPETA_DESCARGAS, archivo)

        if not os.path.exists(origen):
            continue

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_base, ext = os.path.splitext(archivo)
            nombre_final = f"{nombre_base}_{timestamp}{ext}"
            destino = os.path.join(Config.CARPETA_REPORTES, nombre_final)

            shutil.move(origen, destino)
            guardar_log('MOVIMIENTO', f'Movido: {archivo}')
            archivos_movidos.append(destino)

        except Exception as e:
            guardar_log('ERROR_MOVER', f'Error moviendo {archivo}: {str(e)}')

    guardar_log('MOVIMIENTO', f'Total movidos: {len(archivos_movidos)}')
    return archivos_movidos


# ============================================================================
# FUNCIONES DE PROCESAMIENTO ETL
# ============================================================================
def ejecutar_etl(script, nombre, timeout):
    try:
        guardar_log('ETL', f'Iniciando {nombre}...')

        if not os.path.exists(script):
            guardar_log('ETL', f'Script no encontrado: {script}')
            return False

        inicio = time.time()
        resultado = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        duracion = time.time() - inicio

        if resultado.returncode == 0:
            guardar_log('ETL', f'{nombre} exitoso (duracion: {duracion:.1f}s)')
            return True
        else:
            guardar_log('ETL', f'{nombre} fallo (duracion: {duracion:.1f}s)')
            if resultado.stderr:
                print(resultado.stderr)
            return False
    except subprocess.TimeoutExpired:
        guardar_log('ETL', f'{nombre} TIMEOUT (supero {timeout}s)')
        return False
    except Exception as e:
        guardar_log('ETL', f'Error en {nombre}: {str(e)}')
        return False


# ============================================================================
# FUNCION PARA ABRIR DASHBOARDS
# ============================================================================
def abrir_dashboards():
    """Abre los dashboards de Power BI en el navegador predeterminado"""
    try:
        dashboards = [
            ("TRANSPORTE", "https://app.powerbi.com/groups/3e8074f0-cf7e-4e30-8de4-ecb856988343/reports/be71aa82-25c5-4aca-ac7d-05a5763d34f7/5963a551ab45ea61da82?experience=power-bi"),
            ("DESPACHO", "https://app.powerbi.com/groups/3e8074f0-cf7e-4e30-8de4-ecb856988343/reports/be71aa82-25c5-4aca-ac7d-05a5763d34f7/624939736adb5216190c?experience=power-bi"),
            ("DEVOLUCIONES", "https://app.powerbi.com/groups/3e8074f0-cf7e-4e30-8de4-ecb856988343/reports/be71aa82-25c5-4aca-ac7d-05a5763d34f7/f51c9d6120667dded1d3?experience=power-bi")
        ]
        
        guardar_log('DASHBOARD', 'Abriendo dashboards de Power BI...')
        
        for nombre, url in dashboards:
            # Usar start en Windows para abrir en navegador predeterminado
            os.system(f'start {url}')
            guardar_log('DASHBOARD', f'Dashboard {nombre} abierto')
            time.sleep(2)
        
        return True
        
    except Exception as e:
        guardar_log('DASHBOARD', f'Error abriendo dashboards: {str(e)}')
        return False


# ============================================================================
# FUNCION PRINCIPAL
# ============================================================================
def proceso_completo():
    guardar_log('INICIO', '=' * 60)
    guardar_log('INICIO', f'INICIANDO ROBOT - {datetime.now().strftime("%H:%M:%S")}')
    guardar_log('INICIO', '=' * 60)

    driver = None
    resultados_etl = {"TRANSPORTE": False, "DESPACHO": False, "DEVOLUCION": False}

    try:
        if not verificar_html():
            mostrar_mensaje_error_general('HTML no encontrado')
            return False

        driver = iniciar_navegador()
        if not driver:
            return False

        if not navegar(driver):
            driver.quit()
            return False

        if not acceder_desde_logon(driver):
            driver.quit()
            return False

        if not login(driver):
            driver.quit()
            return False

        if not ejecutar_comando_lx02(driver):
            driver.quit()
            return False

        if not ejecutar_reporte(driver):
            driver.quit()
            return False

        if not descargar_archivos(driver):
            driver.quit()
            return False

        # El navegador se queda abierto - NO LO CERRAMOS
        guardar_log('NAVEGADOR', 'DESCARGA COMPLETADA - El navegador permanece abierto')
        guardar_log('NAVEGADOR', 'Puede ver los resultados en la pantalla 5 del simulador')
        guardar_log('NAVEGADOR', 'Cierre el navegador manualmente cuando desee finalizar')
        
        print('\n' + '=' * 70)
        print('DESCARGA COMPLETADA EXITOSAMENTE')
        print('=' * 70)
        print('EL NAVEGADOR PERMANECE ABIERTO en la pantalla de resultados')
        print('Cierre el navegador MANUALMENTE cuando desee terminar')
        print('=' * 70 + '\n')

        time.sleep(3)
        archivos_movidos = mover_archivos_descargados()

        if len(archivos_movidos) < 3:
            guardar_log('ADVERTENCIA', f'Solo se movieron {len(archivos_movidos)} archivos (se esperaban 3)')
        else:
            guardar_log('EXITO', f'Se movieron {len(archivos_movidos)} archivos')

        # Ejecutar ETLs y guardar resultados
        guardar_log('ETL', 'Ejecutando procesos ETL...')
        
        resultados_etl["TRANSPORTE"] = ejecutar_etl(Config.RUTA_ETL_TRANSPORTE, 'TRANSPORTE', Config.TIMEOUT_ETL_TRANSPORTE)
        if not resultados_etl["TRANSPORTE"]:
            mostrar_mensaje_error_etl('TRANSPORTE', 'El proceso ETL de transporte fallo')
        
        guardar_log('ESPERA', f'Pausa de {Config.PAUSA_ENTRE_ETL} segundos...')
        time.sleep(Config.PAUSA_ENTRE_ETL)

        resultados_etl["DESPACHO"] = ejecutar_etl(Config.RUTA_ETL_DESPACHO, 'DESPACHO', Config.TIMEOUT_ETL_DESPACHO)
        if not resultados_etl["DESPACHO"]:
            mostrar_mensaje_error_etl('DESPACHO', 'El proceso ETL de despacho fallo')
        
        guardar_log('ESPERA', f'Pausa de {Config.PAUSA_ENTRE_ETL} segundos...')
        time.sleep(Config.PAUSA_ENTRE_ETL)

        resultados_etl["DEVOLUCION"] = ejecutar_etl(Config.RUTA_ETL_DEVOLUCION, 'DEVOLUCION', Config.TIMEOUT_ETL_DEVOLUCION)
        if not resultados_etl["DEVOLUCION"]:
            mostrar_mensaje_error_etl('DEVOLUCION', 'El proceso ETL de devoluciones fallo')

        # Mostrar resumen de ETLs
        todos_exitosos = all(resultados_etl.values())
        
        if todos_exitosos:
            guardar_log('EXITO', 'PROCESO COMPLETADO EXITOSAMENTE')
            mostrar_mensaje_exito()
        else:
            fallaron = [nombre for nombre, ok in resultados_etl.items() if not ok]
            guardar_log('ERROR', f'Fallaron los siguientes ETLs: {", ".join(fallaron)}')
            mostrar_mensaje_error_general(f'Fallaron los ETLs: {", ".join(fallaron)}')

        # ============================================================
        # ABRIR DASHBOARDS SIEMPRE (tengan exito o no los ETLs)
        # ============================================================
        guardar_log('DASHBOARD', 'Preparando apertura de dashboards...')
        time.sleep(2)
        
        mostrar_mensaje_info_dashboards()
        
        dashboards_abiertos = abrir_dashboards()
        
        if dashboards_abiertos:
            guardar_log('DASHBOARD', 'Dashboards abiertos correctamente')
        else:
            guardar_log('DASHBOARD', 'Hubo problemas al abrir algunos dashboards')
        
        return todos_exitosos

    except Exception as e:
        guardar_log('ERROR_GENERAL', str(e))
        mostrar_mensaje_error_general(str(e))
        
        # Aun si hay error, intentar abrir dashboards
        try:
            guardar_log('DASHBOARD', 'Intentando abrir dashboards a pesar del error...')
            abrir_dashboards()
        except:
            pass
            
        if driver:
            driver.quit()
        return False


def ejecutar_loop():
    print('=' * 60)
    print('ROBOT SAP INICIADO')
    print('=' * 60)
    print(f'Ejecucion cada {Config.INTERVALO_EJECUCION} segundos')
    print(f'Timeout ETL: 30 minutos por proceso')
    print(f'Pausa entre ETLs: {Config.PAUSA_ENTRE_ETL} segundos')
    print(f'Tiempo para seleccion manual: {Config.ESPERA_SELECCION_MANUAL} segundos')
    print('')
    print('NOTAS:')
    print('  - Durante los primeros segundos, podra ajustar filtros manualmente')
    print('  - El navegador se quedara abierto en la pantalla de resultados')
    print('  - Los dashboards se abriran automaticamente al final')
    print('  - Los dashboards se abren en tu navegador predeterminado')
    print('=' * 60)

    try:
        while True:
            print(f'\nEjecutando: {datetime.now().strftime("%H:%M:%S")}')
            inicio_ejecucion = time.time()
            proceso_completo()
            tiempo_total = time.time() - inicio_ejecucion
            print(f'Tiempo total de ejecucion: {tiempo_total:.1f} segundos')
            print(f'Proxima ejecucion en {Config.INTERVALO_EJECUCION} segundos...\n')
            time.sleep(Config.INTERVALO_EJECUCION)
    except KeyboardInterrupt:
        print('\nRobot detenido manualmente')
        sys.exit(0)


# ============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# ============================================================================
if __name__ == '__main__':
    crear_carpetas()

    if '--help' in sys.argv:
        print('''
================================================================================
INICIAR.py - Robot Automatizador SAP
================================================================================

Uso: python INICIAR.py [opciones]

Opciones:
  --once       Ejecutar una sola vez
  --help       Mostrar ayuda

Descripcion:
    Robot que automatiza la extraccion de datos del simulador SAP,
    descarga los archivos Excel (TRANSPORTE, DESPACHO, DEVOLUCIONES)
    y ejecuta los procesos ETL.

Configuracion de tiempos:
    - Tiempo para seleccion manual: 30 segundos
    - Timeout ETL TRANSPORTE: 30 minutos
    - Timeout ETL DESPACHO: 30 minutos
    - Timeout ETL DEVOLUCION: 30 minutos
    - Pausa entre ETLs: 5 segundos
    - Intervalo entre ejecuciones completas: 2 horas

Dashboards:
    - Se abren automaticamente al final del proceso
    - Se abren en tu navegador predeterminado (Chrome/Edge/Firefox)
    - Se abren incluso si algun ETL falla

Comportamiento del navegador:
    - El navegador NO se cierra automaticamente
    - Permanece abierto en la pantalla de resultados
    - Cierre el navegador manualmente cuando desee finalizar

Estructura de carpetas:
    REPORTES/              -> Archivos Excel descargados
    REPORTES/PROCESADOS/   -> Archivos ya procesados por ETL

================================================================================
        ''')
        sys.exit(0)

    if '--once' in sys.argv:
        sys.exit(0 if proceso_completo() else 1)
    else:
        ejecutar_loop()