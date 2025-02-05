# Tracker de transmisiones en vivo en la red social X

Proyecto que monitorea en tiempo real el conteo de visitas de una o más transmisiones en vivo. La información se almacena en un Excel con la siguiente estructura:
- **Fecha:** Año-Mes-Día.
- **Time:** Hora:Minuto:Segundo.
- **Columna adicional:** Cada columna corresponde al conteo de visitas de la transmisión requerida.

## Instalación

1. Clona este repositorio:
```bash
git clone https://github.com/dcansinonews/tracker_x.git
```
2. Accede al directorio
```bash
cd ruta_repositorio/
```
3. Crea un entorno virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate #En Mac
```

4. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso
El programa se ejecuta pasando por pares los argumentos, por ejemplo: nombre_cuenta y url_transmisión.
```bash
python trackerv3.py nmas https://url_transmision milenio https://url_tranmision_milenio
```

---
**NOTE**

El código está configurado para ejecutar cada minuto sin excepción; sin embargo, es posible detener su ejecución al presionar las teclas "ctrl" + "c". De esta manera el programa terminará si ejecución y almacenará los resultados del trackeo de vistas en el archivo de tipo Excel.
---
