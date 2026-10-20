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

from datetime import date
from pathlib import Path
import json

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from xgboost import XGBRegressor


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

app = FastAPI(
    title="API Taxis NYC",
    description="API de pronóstico de demanda de taxis amarillos de Nueva York.",
    version="1.0.0",
)

BASE_DIR = Path(__file__).resolve().parent

RUTA_MODELO = BASE_DIR / "modelo_pronostico.ubj"
RUTA_DEMANDA = BASE_DIR / "demanda.parquet"
RUTA_INFO_MODELO = BASE_DIR / "info_modelo.json"
RUTA_ZONAS = BASE_DIR / "info_zonas.csv"


# ============================================================
# 2. CARGAR INFORMACIÓN DEL MODELO
# ============================================================

with open(
    RUTA_INFO_MODELO,
    "r",
    encoding="utf-8",
) as archivo:
    INFO_MODELO = json.load(archivo)


VARIABLES = INFO_MODELO["variables"]
CUANTILES = INFO_MODELO["cuantiles"]
NOMBRES_CUANTILES = INFO_MODELO["nombres_cuantiles"]
CATEGORIAS_ZONAS = INFO_MODELO["categorias_zonas"]


# ============================================================
# 3. CARGAR EL MODELO
# ============================================================

modelo = XGBRegressor()

modelo.load_model(
    RUTA_MODELO
)


# ============================================================
# 4. CARGAR LA DEMANDA PREPARADA
# ============================================================

demanda = pd.read_parquet(
    RUTA_DEMANDA
)

demanda["hora"] = pd.to_datetime(
    demanda["hora"]
)

# Reconstruimos la categoría exactamente como en entrenamiento.
demanda["zona"] = pd.Categorical(
    demanda["zona"].astype(int),
    categories=CATEGORIAS_ZONAS,
)


# ============================================================
# 5. CARGAR CATÁLOGO DE ZONAS
# ============================================================

zonas_original = pd.read_csv(
    RUTA_ZONAS
)


def preparar_catalogo_zonas(df):
    """
    Estandariza los nombres de las columnas del catálogo
    utilizado anteriormente en el proyecto.
    """

    candidatos_id = [
        "PULocationID",
        "zona_id",
        "LocationID",
        "id",
    ]

    candidatos_nombre = [
        "nombre_zona",
        "zona",
        "Zone",
        "nombre",
    ]

    candidatos_distrito = [
        "distrito",
        "Borough",
        "borough",
    ]

    columna_id = next(
        (
            columna
            for columna in candidatos_id
            if columna in df.columns
        ),
        None,
    )

    columna_nombre = next(
        (
            columna
            for columna in candidatos_nombre
            if columna in df.columns
        ),
        None,
    )

    columna_distrito = next(
        (
            columna
            for columna in candidatos_distrito
            if columna in df.columns
        ),
        None,
    )

    if (
        columna_id is None
        or columna_nombre is None
        or columna_distrito is None
    ):
        raise RuntimeError(
            "info_zonas.csv no contiene las columnas esperadas."
        )

    catalogo = df[
        [
            columna_id,
            columna_nombre,
            columna_distrito,
        ]
    ].copy()

    catalogo.columns = [
        "zona_id",
        "nombre",
        "distrito",
    ]

    catalogo["zona_id"] = (
        catalogo["zona_id"]
        .astype(int)
    )

    # Solo dejamos zonas que el modelo realmente puede pronosticar.
    catalogo = catalogo[
        catalogo["zona_id"].isin(
            CATEGORIAS_ZONAS
        )
    ]

    return catalogo


zonas = preparar_catalogo_zonas(
    zonas_original
)


# ============================================================
# 6. ENDPOINT PRINCIPAL
# ============================================================

@app.get("/")
def inicio():

    return {
        "mensaje": "API Taxis NYC en línea",
        "modelo": "XGBoost por cuantiles",
        "estado": "ok",
    }


# ============================================================
# 7. INFORMACIÓN GENERAL
# ============================================================

@app.get("/info")
def obtener_info():

    fechas = sorted(
        demanda["hora"]
        .dt.strftime("%Y-%m-%d")
        .unique()
        .tolist()
    )

    lista_zonas = []

    for _, fila in zonas.sort_values(
        "nombre"
    ).iterrows():

        lista_zonas.append(
            {
                "id": int(
                    fila["zona_id"]
                ),
                "nombre": fila["nombre"],
                "distrito": fila["distrito"],
            }
        )

    return {
        "modelo": "XGBoost por cuantiles",
        "zonas": lista_zonas,
        "fechas": fechas,
        "cuantiles": CUANTILES,
        "nombres_cuantiles": NOMBRES_CUANTILES,
        "periodo": {
            "inicio_prueba": INFO_MODELO[
                "fecha_inicio_prueba"
            ],
            "fin_prueba": INFO_MODELO[
                "fecha_fin_prueba"
            ],
            "fecha_futura": INFO_MODELO[
                "fecha_futura"
            ],
        },
    }


# ============================================================
# 8. ENDPOINT DE PRONÓSTICO
# ============================================================

@app.get("/pronostico")
def obtener_pronostico(
    zona_id: int,
    fecha: date,
):

    # Validar que la zona exista.
    if zona_id not in CATEGORIAS_ZONAS:

        raise HTTPException(
            status_code=404,
            detail="La zona solicitada no está disponible para pronóstico.",
        )

    filas = demanda[
        (
            demanda["PULocationID"]
            == zona_id
        )
        & (
            demanda["hora"].dt.date
            == fecha
        )
    ].copy()

    if filas.empty:

        raise HTTPException(
            status_code=404,
            detail="No hay datos para esa zona o fecha.",
        )

    filas = filas.sort_values(
        "hora"
    )

    if len(filas) != 24:

        raise HTTPException(
            status_code=500,
            detail="El día seleccionado no contiene las 24 horas esperadas.",
        )

    # Reconstruimos la categoría antes de predecir.
    filas["zona"] = pd.Categorical(
        filas["zona"].astype(int),
        categories=CATEGORIAS_ZONAS,
    )

    X = filas[
        VARIABLES
    ]

    # Predicción de cuantiles.
    predicciones = modelo.predict(
        X
    )

    predicciones = np.asarray(
        predicciones
    )

    if predicciones.ndim == 1:

        predicciones = (
            predicciones.reshape(
                -1,
                1,
            )
        )

    # Evitar cuantiles cruzados.
    predicciones = np.sort(
        predicciones,
        axis=1,
    )

    # La cantidad de viajes no puede ser negativa.
    predicciones = np.maximum(
        predicciones,
        0,
    )

    if (
        predicciones.shape[1]
        != len(NOMBRES_CUANTILES)
    ):

        raise HTTPException(
            status_code=500,
            detail="El modelo no devolvió la cantidad esperada de cuantiles.",
        )

    # Información de la zona.
    zona_info = zonas[
        zonas["zona_id"]
        == zona_id
    ].iloc[0]

    horas_respuesta = []

    for posicion, (_, fila) in enumerate(
        filas.iterrows()
    ):

        cuantiles_hora = {}

        for indice, nombre in enumerate(
            NOMBRES_CUANTILES
        ):

            cuantiles_hora[nombre] = round(
                float(
                    predicciones[
                        posicion,
                        indice,
                    ]
                ),
                2,
            )

        valor_real = fila["viajes"]

        if pd.isna(valor_real):
            valor_real = None
        else:
            valor_real = int(
                round(
                    float(valor_real)
                )
            )

        hace_semana = fila[
            "lag_168"
        ]

        if pd.isna(hace_semana):
            hace_semana = None
        else:
            hace_semana = int(
                round(
                    float(hace_semana)
                )
            )

        horas_respuesta.append(
            {
                "hora": int(
                    fila["hora"].hour
                ),
                "real": valor_real,
                "hace_una_semana": hace_semana,
                "cuantiles": cuantiles_hora,
            }
        )

    return {
        "zona": {
            "id": int(
                zona_info["zona_id"]
            ),
            "nombre": zona_info["nombre"],
            "distrito": zona_info["distrito"],
        },
        "fecha": str(fecha),
        "horas": horas_respuesta,
    }