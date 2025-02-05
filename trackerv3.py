import re
import time
import signal
import sys
import datetime
import argparse
import os
import pandas as pd
from selenium import webdriver
from PIL import Image
import easyocr

reader = easyocr.Reader(["es", "en"], gpu=False)
drivers = {}

def manejar_salida(signal_recibida, frame):
    """Maneja la señal de salida (Ctrl+C).

    Argumentos:
        signal_recibida: La señal recibida (por ejemplo, SIGINT).
        frame: El frame en el que se recibió la señal.
    Cierra todas las instancias de webdriver y finaliza el programa.
    """
    print("\nSaliendo del script...")
    for driver in drivers.values():
        driver.quit()
    sys.exit(0)

def recortar_region_vistas(path_captura, path_salida):
    """Recorta la región de la imagen donde se muestran las vistas.

    Argumentos:
        path_captura: Ruta del archivo de imagen original (captura de pantalla).
        path_salida: Ruta del archivo donde se guardará la imagen recortada.
    Realiza un recorte fijo (ajusta los valores de la tupla según sea necesario).
    """
    with Image.open(path_captura) as img:
        region = img.crop((490, 720, 800, 750))
        region.save(path_salida)

def obtener_conteo_vistas_por_ocr(driver, stream_name, captura_temp=None):
    """Obtiene el conteo de vistas mediante OCR en la captura de pantalla de la transmisión.

    Argumentos:
        driver: Instancia del webdriver que muestra la transmisión.
        stream_name: Nombre identificador de la transmisión (se usa para nombrar archivos temporales).
        captura_temp: (Opcional) Nombre del archivo temporal para la captura; si no se especifica se genera automáticamente.
    Retorna:
        Una tupla (texto_crudo, conteo) donde 'texto_crudo' es el texto detectado y 'conteo' es el número de vistas (entero).
    """
    if not captura_temp:
        captura_temp = f"captura_temp_{stream_name}.png"
    region_temp = f"region_vistas_{stream_name}.png"
    driver.save_screenshot(captura_temp)
    recortar_region_vistas(captura_temp, region_temp)
    try:
        result_texts = reader.readtext(region_temp, detail=0)
        texto_crudo = " ".join(result_texts).strip().lower()
        matches = re.findall(r'([\d\.,]+)(?:\s*(mil))?', texto_crudo)
        if matches:
            numero_detectado, indicador_mil = matches[0]
            numero_normalizado = numero_detectado.replace(",", ".")
            numero_normalizado = re.sub(r'\.(?=\d{3}(?:\s|$))', '', numero_normalizado)
            if "." in numero_normalizado:
                conteo = float(numero_normalizado)
            else:
                conteo = int(numero_normalizado)
            if indicador_mil == "mil":
                conteo *= 1000
            return texto_crudo, int(conteo)
        return texto_crudo, -1
    except Exception as e:
        print(f"Error en OCR para {stream_name}: {e}")
        return "Error en OCR", -1

def escribir_en_excel(fila, nombre_archivo, columnas):
    """Escribe una fila de datos en un archivo Excel, creando el archivo si no existe.

    Argumentos:
        fila: Lista de valores a escribir en una sola fila, siguiendo el orden de 'columnas'.
        nombre_archivo: Ruta del archivo Excel donde se guardarán los datos.
        columnas: Lista de nombres de columna que definen la estructura del reporte.
    """
    datos = pd.DataFrame([fila], columns=columnas)
    if os.path.exists(nombre_archivo):
        with pd.ExcelWriter(nombre_archivo, mode='a', if_sheet_exists='overlay', engine='openpyxl') as writer:
            sheet = writer.sheets.get("Sheet1")
            startrow = sheet.max_row if sheet else 0
            datos.to_excel(writer, index=False, header=False, startrow=startrow)
    else:
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            datos.to_excel(writer, index=False)

def main():
    """Inicializa el monitoreo de una o varias transmisiones en vivo y registra los datos en un Excel.

    Los argumentos se deben pasar en pares (nombre URL). Por ejemplo:
        python tracker.py canal1 https://url1 canal2 https://url2
    """
    signal.signal(signal.SIGINT, manejar_salida)
    parser = argparse.ArgumentParser(description="Monitorear vistas de transmisiones en vivo usando OCR.")
    parser.add_argument("streams", nargs="+", help="Pares de nombre y URL para cada transmisión (e.g. canal1 url1 canal2 url2 ...)")
    args = parser.parse_args()
    if len(args.streams) % 2 != 0:
        print("Error: Debe proporcionar pares de nombre y URL para cada transmisión.")
        sys.exit(1)
    stream_names = []
    streams = {}
    for i in range(0, len(args.streams), 2):
        name = args.streams[i]
        url = args.streams[i+1]
        stream_names.append(name)
        streams[name] = url
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    for name, url in streams.items():
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        drivers[name] = driver
        time.sleep(60)
    nombre_archivo = f"analisis_del_live_en_X_{datetime.datetime.now().strftime('%Y-%m-%d')}.xlsx"
    columnas = ["Fecha", "Time"] + stream_names
    print("Monitoreando transmisiones. Presiona Ctrl+C para salir.\n")
    while True:
        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
        hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
        conteos = {}
        for name, driver in drivers.items():
            texto, vistas = obtener_conteo_vistas_por_ocr(driver, name)
            conteos[name] = vistas
            print(f"[{fecha_actual} {hora_actual}] - {name}: Texto detectado: {texto} - Vistas: {vistas}")
        fila = [fecha_actual, hora_actual] + [conteos[name] for name in stream_names]
        escribir_en_excel(fila, nombre_archivo, columnas)
        time.sleep(6)

if __name__ == "__main__":
    main()