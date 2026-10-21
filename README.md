# Taxis NYC — Pronóstico y apoyo a la toma de decisiones

Proyecto académico desarrollado para el módulo **AIMLF1**, orientado al análisis de la demanda de taxis amarillos de Nueva York mediante técnicas de series de tiempo, aprendizaje no supervisado y una aplicación web interactiva.

La solución permite consultar pronósticos horarios con incertidumbre, explorar tipos de zonas, estimar cuántos taxis enviar según distintos costos operativos y revisar una ficha con el desempeño y las limitaciones del modelo.

## Enlaces del proyecto

- **Aplicación Streamlit:** https://taxis-nyc-7fazkrfw97w5hm4tmxwgnz.streamlit.app
- **API en Render:** https://taxis-nyc-0b27.onrender.com
- **Documentación de la API:** https://taxis-nyc-0b27.onrender.com/docs
- **Repositorio GitHub:** https://github.com/IsaiZepeda04/taxis-nyc

> La API utiliza una instancia gratuita de Render, por lo que puede tardar algunos segundos en responder después de un periodo de inactividad.

## Integrante

- **Leonardo Isai Zepeda Tolentino**

## Objetivo

Construir una herramienta de apoyo para la planificación de una flota de taxis, combinando:

- pronóstico horario de demanda;
- cuantificación de incertidumbre mediante cuantiles;
- segmentación de zonas con K-Means;
- visualización de los grupos mediante PCA;
- recomendación operativa basada en costos;
- comunicación del desempeño y las limitaciones del modelo.

## Datos utilizados

Se utilizaron datos públicos de **NYC Taxi & Limousine Commission (NYC TLC)** correspondientes a viajes de taxis amarillos de enero de 2024.

Fuentes:

- Yellow Taxi Trip Records — enero 2024  
  https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet
- Taxi Zone Lookup  
  https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv

La zona de cada viaje se define mediante `PULocationID`, correspondiente al punto de origen.

## Metodología

### Pronóstico

La demanda se transforma en una serie horaria por zona, completando con cero las horas sin viajes.

El modelo utiliza variables temporales y rezagos como:

- `lag_24`
- `lag_48`
- `lag_167`
- `lag_168`
- `lag_169`
- promedio del día anterior
- hora
- día de la semana
- indicador de feriado
- zona como variable categórica

La evaluación respeta el orden temporal:

- **Entrenamiento:** hasta el 24 de enero de 2024.
- **Prueba:** del 25 al 31 de enero de 2024.
- **Pronóstico futuro:** 1 de febrero de 2024.

No se utiliza `train_test_split`, porque el problema es de series de tiempo y se busca evitar fuga de información.

El modelo final utiliza **XGBoost con regresión por cuantiles**, generando predicciones desde `p10` hasta `p90`.

Como referencia se utiliza un baseline sencillo: asumir que la demanda será igual a la observada exactamente una semana antes (`lag_168`).

### Segmentación

Las zonas se agrupan mediante **K-Means** a partir de variables relacionadas con:

- volumen de viajes;
- distancia mediana;
- tarifa mediana;
- propina mediana;
- actividad en fin de semana;
- actividad por franjas horarias.

Las variables se estandarizan con `StandardScaler`.

El número de grupos se selecciona evaluando el coeficiente de silueta entre `k = 2` y `k = 7`.

Para facilitar la interpretación visual se aplica **PCA a dos componentes**.

## Resultados principales

En la evaluación final:

- **MAE baseline semanal:** 11.88 viajes por hora.
- **MAE XGBoost p50:** 11.89 viajes por hora.
- **RMSE baseline semanal:** 21.88.
- **RMSE XGBoost p50:** 22.45.
- **Cobertura observada p10–p90:** 89.98%.
- **Ancho medio del intervalo p10–p90:** 49.61 viajes por hora.

El pronóstico central queda prácticamente empatado con la regla semanal. El valor adicional del modelo está en ofrecer una distribución de cuantiles que permite representar la incertidumbre y utilizar distintos niveles de riesgo en la decisión operativa.

Para la segmentación se seleccionaron **4 grupos**, con un coeficiente de silueta de **0.4113**. Las dos componentes principales de PCA conservan aproximadamente **65.75%** de la variación total.

## Aplicación Streamlit

La aplicación contiene cuatro páginas principales:

### Pronóstico

Permite seleccionar una zona y una fecha para consultar:

- pronóstico horario;
- cuantiles p10 a p90;
- banda de incertidumbre;
- demanda real cuando está disponible;
- valor observado una semana antes.

### Segmentación de zonas

Permite explorar los grupos obtenidos con K-Means mediante:

- filtros por grupo;
- visualización PCA;
- selección interactiva de zonas;
- métricas de cada zona;
- perfil horario;
- justificación del número de clusters.

### Decisión

Calcula el cuantil operativo según dos costos:

- costo de enviar un taxi que queda sin pasajero;
- costo de perder un pasajero por falta de taxi.

La página convierte ese cuantil en una recomendación de taxis por hora y, para fechas con datos reales, compara el costo frente a otras estrategias.

También permite descargar el plan generado en formato CSV.

### Ficha del modelo

Resume:

- desempeño global;
- comparación contra el baseline;
- cobertura del intervalo;
- error por tipo de zona;
- metodología;
- limitaciones;
- usos no recomendados.

## Arquitectura

La solución separa el backend del frontend:

```text
Streamlit
    │
    │ HTTP
    ▼
FastAPI
    │
    ├── modelo XGBoost
    └── datos preparados
```

La aplicación de Streamlit no carga el modelo directamente. Los pronósticos se solicitan a la API mediante peticiones HTTP.

## Estructura del repositorio

```text
taxis-nyc/
│
├── preparacion.ipynb
│
├── api/
│   ├── main.py
│   ├── requirements.txt
│   ├── modelo_pronostico.ubj
│   ├── demanda.parquet
│   ├── info_modelo.json
│   └── info_zonas.csv
│
├── app/
│   ├── streamlit_app.py
│   ├── requirements.txt
│   │
│   ├── paginas/
│   │   ├── pronostico.py
│   │   ├── segmentacion.py
│   │   ├── decision.py
│   │   └── ficha_modelo.py
│   │
│   ├── data/
│   │   ├── zonas_segmentadas.csv
│   │   ├── perfiles_horarios.csv
│   │   ├── silueta_k.csv
│   │   ├── resumen_clusters.csv
│   │   ├── metricas_modelo_final.csv
│   │   └── metricas_por_segmento.csv
│   │
│   └── .streamlit/
│       └── config.toml
│
├── .gitignore
└── README.md
```

## API

La API está desarrollada con **FastAPI** y contiene los siguientes endpoints:

### `GET /`

Comprueba que el servicio está disponible.

### `GET /info`

Devuelve información general como:

- zonas disponibles;
- fechas disponibles;
- cuantiles utilizados.

### `GET /pronostico`

Recibe:

```text
zona_id
fecha
```

Ejemplo:

```text
https://taxis-nyc-0b27.onrender.com/pronostico?zona_id=132&fecha=2024-01-31
```

Devuelve las 24 horas del día con:

- valor real, si existe;
- demanda de hace una semana;
- cuantiles del modelo.

## Ejecución local

### 1. Clonar el repositorio

```bash
git clone https://github.com/IsaiZepeda04/taxis-nyc.git
cd taxis-nyc
```

### 2. Crear un entorno virtual

En Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instalar dependencias de la API

```bash
pip install -r api/requirements.txt
```

### 4. Ejecutar FastAPI

Desde la raíz del proyecto:

```bash
uvicorn api.main:app --reload
```

La documentación estará disponible en:

```text
http://127.0.0.1:8000/docs
```

### 5. Instalar dependencias de Streamlit

```bash
pip install -r app/requirements.txt
```

### 6. Ejecutar la aplicación

```bash
python -m streamlit run app/streamlit_app.py
```

La aplicación utilizará la API local cuando no exista un `API_URL` configurado en los secrets de Streamlit.

## Tecnologías utilizadas

- Python
- Pandas
- NumPy
- scikit-learn
- XGBoost
- FastAPI
- Uvicorn
- Streamlit
- Plotly
- PyArrow
- Git y GitHub
- Render
- Streamlit Community Cloud

## Limitaciones

Este proyecto fue desarrollado con fines académicos y los resultados deben interpretarse dentro de ese contexto.

Entre las principales limitaciones se encuentran:

- el modelo utiliza únicamente información de enero de 2024;
- no incorpora directamente clima, eventos, obras o cierres viales;
- las zonas con menor volumen de viajes pueden quedar fuera del pronóstico;
- el comportamiento del taxi amarillo no representa toda la movilidad de Nueva York;
- el desempeño varía entre distintos tipos de zona;
- los resultados no deben extrapolarse directamente a otros períodos o ciudades sin una nueva evaluación.

## Conclusión

El proyecto integra diferentes técnicas vistas durante el módulo en una solución completa: preparación de datos, series de tiempo, cuantiles, K-Means, PCA, FastAPI y Streamlit.

Uno de los principales aprendizajes fue comprobar que un modelo más complejo no necesariamente supera ampliamente una regla sencilla. En este caso, el baseline semanal resultó muy competitivo. Sin embargo, el modelo por cuantiles aporta información adicional sobre la incertidumbre, lo cual permite tomar decisiones operativas considerando distintos niveles de riesgo.

La aplicación busca presentar estos resultados de forma clara para que una persona pueda interpretar el pronóstico, comprender el tipo de zona y tomar una decisión sin necesidad de interactuar directamente con el notebook o con el modelo.
