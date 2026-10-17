# ============================================================
# TAXIS NYC — API MÍNIMA CON FASTAPI
# ============================================================
# Esta primera versión de la API tiene dos objetivos:
#
# 1. Confirmar que el servicio está en línea mediante GET /
# 2. Entregar información general del proyecto mediante GET /info
#
# Todavía NO se carga el modelo de XGBoost.
# El endpoint /pronostico se agregará en una fase posterior.
# ============================================================

from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException


# ============================================================
# 1. CONFIGURACIÓN DE RUTAS
# ============================================================

# __file__ representa la ubicación de este archivo main.py.
# resolve().parent obtiene la carpeta absoluta donde se encuentra.
#
# Usar Path evita problemas de rutas cuando la API se publique
# en Render, ya que el servicio no siempre se ejecuta desde la
# misma carpeta de trabajo que usamos localmente.
BASE_DIR = Path(__file__).resolve().parent

# El archivo info_zonas.csv será generado por preparacion.ipynb
# y debe colocarse dentro de la misma carpeta api/.
RUTA_ZONAS = BASE_DIR / "info_zonas.csv"


# ============================================================
# 2. FUNCIÓN PARA CARGAR LAS ZONAS
# ============================================================

def cargar_zonas() -> pd.DataFrame:
    """
    Carga el archivo con las zonas pronosticables.

    Returns
    -------
    pd.DataFrame
        DataFrame con las zonas que cumplen el criterio mínimo
        de viajes establecido en la actividad.

    Raises
    ------
    FileNotFoundError
        Si el archivo info_zonas.csv no existe.
    ValueError
        Si faltan columnas obligatorias.
    """

    # Verificamos primero que el archivo exista.
    if not RUTA_ZONAS.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo requerido: {RUTA_ZONAS.name}"
        )

    # Cargamos el CSV generado por el notebook.
    df = pd.read_csv(RUTA_ZONAS)

    # Columnas que esperamos recibir desde preparacion.ipynb.
    columnas_requeridas = {
        "PULocationID",
        "nombre_zona",
        "distrito",
        "total_viajes",
    }

    # Calculamos si falta alguna columna.
    columnas_faltantes = columnas_requeridas.difference(df.columns)

    if columnas_faltantes:
        raise ValueError(
            "Faltan columnas requeridas en info_zonas.csv: "
            + ", ".join(sorted(columnas_faltantes))
        )

    return df


# ============================================================
# 3. CARGA INICIAL DE DATOS
# ============================================================

# Cargamos las zonas una sola vez cuando inicia la API.
#
# Esto es más eficiente que volver a leer el CSV cada vez que
# alguien consulta /info.
zonas = cargar_zonas()


# ============================================================
# 4. CREACIÓN DE LA APLICACIÓN FASTAPI
# ============================================================

app = FastAPI(
    title="Taxis NYC API",
    description=(
        "API para el sistema de pronóstico y planificación "
        "operativa de taxis amarillos de Nueva York."
    ),
    version="0.1.0",
)


# ============================================================
# 5. ENDPOINT PRINCIPAL
# ============================================================

@app.get("/")
def inicio():
    """
    Comprueba que la API está funcionando.

    Este endpoint es útil para:
    - verificar rápidamente el despliegue;
    - comprobar que Render despertó el servicio;
    - detectar si la API está disponible antes de llamar
      otros endpoints.
    """

    return {
        "estado": "ok",
        "mensaje": "Taxis NYC API está en línea",
        "version": "0.1.0",
    }


# ============================================================
# 6. ENDPOINT /info
# ============================================================

@app.get("/info")
def obtener_info():
    """
    Devuelve la información general necesaria para la aplicación.

    En esta primera versión incluye:
    - zonas pronosticables;
    - fechas oficiales de entrenamiento y prueba;
    - fecha futura que se pronosticará;
    - estado actual del modelo;
    - cuantiles disponibles actualmente.

    Más adelante este endpoint se actualizará cuando exista
    el modelo probabilístico definitivo.
    """

    # Si por alguna razón no existen zonas cargadas,
    # respondemos con un error HTTP claro.
    if zonas.empty:
        raise HTTPException(
            status_code=500,
            detail="No hay zonas pronosticables disponibles.",
        )

    #Convertimos cada fila del dataFrame en un diccionario para que FastAPI lo pueda serializar a JSON.
    # compatible con JSON

    lista_zonas = [
        {
            "id": int(fila["PULocationID"]),
            "nombre": str(fila["nombre_zona"]),
            "distrito": str(fila["distrito"]),
            "total_viajes": int(fila["total_viajes"]),
        }
        for _, fila in zonas.iterrows()
    ]

    return {
        "version": "0.1.0",
        "estado modelo": "modelo inicial de pronostico",
        "zonas_pronosticables": len(lista_zonas),
        "zonas": lista_zonas,
        "fechas": {
            "entrenamiento_hasta": "2024-01-24",
            "prueba_desde": "2024-01-25",
            "prueba_hasta": "2024-01-31",
            "pronostico_futuro": "2024-02-01",
        },
        # En esta primera fase todavía no existe el modelo.
        "cuantiles": [0.50],
    }