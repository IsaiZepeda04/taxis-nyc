from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


RUTA_DATA = Path(__file__).resolve().parent.parent / "data"


@st.cache_data
def cargar_metricas():
    """Carga las métricas globales y las métricas por tipo de zona."""

    ruta_global = RUTA_DATA / "metricas_modelo_final.csv"
    ruta_segmentos = RUTA_DATA / "metricas_por_segmento.csv"

    metricas_globales = pd.read_csv(ruta_global)
    metricas_segmentos = pd.read_csv(ruta_segmentos)

    return metricas_globales, metricas_segmentos


def obtener_valor(tabla, nombre):
    """Obtiene una métrica por su nombre."""

    fila = tabla.loc[
        tabla["metrica"] == nombre,
        "valor"
    ]

    if fila.empty:
        return None

    return float(fila.iloc[0])


def formato_numero(valor, decimales=2):
    """Formatea valores numéricos."""

    if valor is None:
        return "N/D"

    return f"{valor:.{decimales}f}"


def formato_porcentaje(valor, decimales=2):
    """Convierte una proporción decimal a porcentaje."""

    if valor is None:
        return "N/D"

    return f"{valor * 100:.{decimales}f}%"


# ============================================================
# ENCABEZADO
# ============================================================

st.title("Ficha del modelo")

st.caption(
    "Resumen del desempeño, la incertidumbre, los errores por tipo de zona "
    "y las condiciones de uso del modelo de pronóstico."
)


# ============================================================
# CARGA DE DATOS
# ============================================================

try:
    metricas, segmentos = cargar_metricas()

except FileNotFoundError:
    st.error(
        "No se encontraron los archivos de métricas necesarios "
        "para mostrar la ficha del modelo."
    )

    st.caption(
        "Verifica que metricas_modelo_final.csv y "
        "metricas_por_segmento.csv estén dentro de app/data/."
    )

    st.stop()

except Exception as error:
    st.error(
        "Ocurrió un problema al cargar las métricas "
        "de la ficha del modelo."
    )

    st.caption(str(error))

    st.stop()


# ============================================================
# MÉTRICAS GLOBALES
# ============================================================

mae_baseline = obtener_valor(
    metricas,
    "mae_baseline_semanal"
)

rmse_baseline = obtener_valor(
    metricas,
    "rmse_baseline_semanal"
)

mae_modelo = obtener_valor(
    metricas,
    "mae_xgboost_p50"
)

rmse_modelo = obtener_valor(
    metricas,
    "rmse_xgboost_p50"
)

cobertura = obtener_valor(
    metricas,
    "cobertura_p10_p90"
)

ancho_intervalo = obtener_valor(
    metricas,
    "ancho_medio_p10_p90"
)


# ============================================================
# RESUMEN EJECUTIVO
# ============================================================

st.subheader("Resumen ejecutivo")

with st.container(border=True):

    st.write(
        "El modelo estima la demanda horaria de taxis amarillos "
        "por zona mediante XGBoost y cuantiles del 10% al 90%. "
        "Su objetivo es apoyar la planificación operativa mostrando "
        "un pronóstico central y un rango explícito de incertidumbre."
    )

    if mae_modelo is not None and mae_baseline is not None:

        diferencia_mae = mae_modelo - mae_baseline

        if diferencia_mae < 0:

            st.badge(
                "XGBoost mejora el MAE del baseline semanal",
                color="green"
            )

        elif diferencia_mae > 0:

            st.badge(
                "El baseline semanal obtiene un MAE ligeramente menor",
                color="orange"
            )

        else:

            st.badge(
                "XGBoost y el baseline obtienen el mismo MAE",
                color="blue"
            )


    if cobertura is not None:

        if cobertura >= 0.80:

            st.badge(
                "El intervalo p10–p90 alcanza al menos "
                "la cobertura nominal",
                color="green"
            )

        else:

            st.badge(
                "La cobertura p10–p90 queda por debajo "
                "del 80% nominal",
                color="red"
            )


# ============================================================
# DESEMPEÑO GLOBAL
# ============================================================

st.subheader("Desempeño global")

col1, col2, col3, col4 = st.columns(4)


with col1:

    delta_mae = None

    if mae_modelo is not None and mae_baseline is not None:

        delta_mae = (
            f"{mae_modelo - mae_baseline:+.2f} "
            "vs baseline"
        )

    st.metric(
        "MAE XGBoost p50",
        formato_numero(mae_modelo),
        delta=delta_mae,
        delta_color="inverse",
        border=True
    )


with col2:

    st.metric(
        "MAE baseline semanal",
        formato_numero(mae_baseline),
        border=True
    )


with col3:

    delta_cobertura = None

    if cobertura is not None:

        delta_cobertura = (
            f"{(cobertura - 0.80) * 100:+.2f} pp vs 80%"
        )

    st.metric(
        "Cobertura p10–p90",
        formato_porcentaje(cobertura),
        delta=delta_cobertura,
        border=True
    )


with col4:

    st.metric(
        "Ancho medio p10–p90",
        formato_numero(ancho_intervalo),
        help=(
            "Amplitud promedio del intervalo de "
            "incertidumbre en viajes por hora."
        ),
        border=True
    )


# ============================================================
# INTERPRETACIÓN GLOBAL
# ============================================================

if mae_modelo is not None and mae_baseline is not None:

    if mae_modelo > mae_baseline:

        st.info(
            "El pronóstico central p50 queda prácticamente "
            "empatado con la regla de usar la demanda de hace "
            "una semana. El valor adicional del modelo está en "
            "proporcionar cuantiles y un rango de incertidumbre "
            "que el baseline no ofrece."
        )

    else:

        st.success(
            "El pronóstico central p50 mejora el MAE de la regla "
            "semanal y, además, ofrece una distribución de cuantiles "
            "para representar la incertidumbre."
        )


# ============================================================
# DESEMPEÑO POR TIPO DE ZONA
# ============================================================

st.subheader("Desempeño por tipo de zona")

segmentos = segmentos.copy()

segmentos["mejora_modelo"] = (
    segmentos["mae_xgboost_p50"]
    < segmentos["mae_baseline_semanal"]
)

cantidad_mejoras = int(
    segmentos["mejora_modelo"].sum()
)

cantidad_segmentos = len(segmentos)


peor_segmento = segmentos.loc[
    segmentos["mae_xgboost_p50"].idxmax()
]

mejor_segmento = segmentos.loc[
    segmentos["mae_xgboost_p50"].idxmin()
]


col_a, col_b, col_c = st.columns(3)


with col_a:

    st.metric(
        "Perfiles donde mejora XGBoost",
        f"{cantidad_mejoras} de {cantidad_segmentos}",
        border=True
    )


with col_b:

    st.metric(
        "Mayor MAE",
        formato_numero(
            float(
                peor_segmento["mae_xgboost_p50"]
            )
        ),
        help=str(
            peor_segmento["tipo_zona"]
        ),
        border=True
    )


with col_c:

    st.metric(
        "Menor MAE",
        formato_numero(
            float(
                mejor_segmento["mae_xgboost_p50"]
            )
        ),
        help=str(
            mejor_segmento["tipo_zona"]
        ),
        border=True
    )


# ============================================================
# PESTAÑAS DE GRÁFICOS
# ============================================================

tab_error, tab_cobertura = st.tabs(
    [
        "Error por tipo de zona",
        "Cobertura del intervalo"
    ]
)


# ============================================================
# GRÁFICO DE ERROR
# ============================================================

with tab_error:

    datos_error = segmentos[
        [
            "tipo_zona",
            "mae_xgboost_p50",
            "mae_baseline_semanal"
        ]
    ].copy()


    datos_error = datos_error.rename(
        columns={
            "tipo_zona": "Tipo de zona",
            "mae_xgboost_p50": "XGBoost p50",
            "mae_baseline_semanal": "Baseline semanal"
        }
    )


    datos_error_largo = datos_error.melt(
        id_vars="Tipo de zona",
        var_name="Método",
        value_name="MAE"
    )


    figura_error = px.bar(
        datos_error_largo,
        x="Tipo de zona",
        y="MAE",
        color="Método",
        barmode="group",
        labels={
            "MAE": "MAE (viajes por hora)"
        },
        title=(
            "MAE de XGBoost frente al baseline semanal"
        )
    )


    figura_error.update_layout(
        xaxis_title="Tipo de zona",
        yaxis_title="MAE (viajes por hora)",
        legend_title="Método",
        hovermode="x unified"
    )


    st.plotly_chart(
        figura_error,
        width="stretch"
    )


    st.caption(
        "Un MAE menor representa un mejor desempeño. "
        "La comparación por grupo permite identificar perfiles "
        "donde la regla semanal sigue siendo difícil de superar."
    )


# ============================================================
# GRÁFICO DE COBERTURA
# ============================================================

with tab_cobertura:

    datos_cobertura = segmentos[
        [
            "tipo_zona",
            "cobertura_p10_p90"
        ]
    ].copy()


    datos_cobertura["Cobertura"] = (
        datos_cobertura[
            "cobertura_p10_p90"
        ] * 100
    )


    figura_cobertura = px.bar(
        datos_cobertura,
        x="tipo_zona",
        y="Cobertura",
        labels={
            "tipo_zona": "Tipo de zona",
            "Cobertura": "Cobertura (%)"
        },
        title=(
            "Cobertura observada del intervalo p10–p90"
        )
    )


    figura_cobertura.add_hline(
        y=80,
        line_dash="dash",
        annotation_text="Objetivo nominal: 80%",
        annotation_position="top left"
    )


    figura_cobertura.update_layout(
        xaxis_title="Tipo de zona",
        yaxis_title="Cobertura (%)"
    )


    st.plotly_chart(
        figura_cobertura,
        width="stretch"
    )


    st.caption(
        "El intervalo p10–p90 tiene un objetivo nominal del 80%. "
        "Una cobertura claramente superior indica un intervalo "
        "más conservador."
    )


# ============================================================
# INTERPRETACIÓN POR SEGMENTO
# ============================================================

st.subheader("Lectura de los resultados")


with st.container(border=True):

    st.markdown(
        f"""
**Mayor dificultad.** El perfil **{peor_segmento["tipo_zona"]}**
presenta el MAE más alto del modelo, con
**{peor_segmento["mae_xgboost_p50"]:.2f} viajes por hora**.

**Menor dificultad.** El perfil **{mejor_segmento["tipo_zona"]}**
presenta el MAE más bajo, con
**{mejor_segmento["mae_xgboost_p50"]:.2f} viajes por hora**.

En conjunto, XGBoost obtiene un MAE menor que el baseline en
**{cantidad_mejoras} de {cantidad_segmentos} tipos de zona**.

Esto muestra que el desempeño depende del perfil operativo
y que no debe suponerse una mejora uniforme en todas las zonas.
"""
    )


# ============================================================
# TABLA DETALLADA
# ============================================================

with st.expander(
    "Ver métricas detalladas por tipo de zona"
):

    tabla = segmentos[
        [
            "tipo_zona",
            "horas_evaluadas",
            "mae_xgboost_p50",
            "mae_baseline_semanal",
            "rmse_xgboost_p50",
            "cobertura_p10_p90"
        ]
    ].copy()


    tabla["cobertura_p10_p90"] = (
        tabla["cobertura_p10_p90"] * 100
    )


    tabla = tabla.rename(
        columns={
            "tipo_zona": "Tipo de zona",
            "horas_evaluadas": "Horas evaluadas",
            "mae_xgboost_p50": "MAE XGBoost",
            "mae_baseline_semanal": "MAE baseline",
            "rmse_xgboost_p50": "RMSE XGBoost",
            "cobertura_p10_p90": "Cobertura (%)"
        }
    )


    st.dataframe(
        tabla,
        width="stretch",
        hide_index=True,
        column_config={
            "MAE XGBoost":
                st.column_config.NumberColumn(
                    format="%.2f"
                ),

            "MAE baseline":
                st.column_config.NumberColumn(
                    format="%.2f"
                ),

            "RMSE XGBoost":
                st.column_config.NumberColumn(
                    format="%.2f"
                ),

            "Cobertura (%)":
                st.column_config.NumberColumn(
                    format="%.1f%%"
                )
        }
    )


# ============================================================
# DATOS Y METODOLOGÍA
# ============================================================

st.subheader("Datos y metodología")


with st.expander(
    "Cómo se entrenó y evaluó el modelo",
    expanded=False
):

    st.markdown(
        """
- **Datos:** viajes de taxis amarillos de Nueva York de enero de 2024.
- **Zona:** `PULocationID`, correspondiente a la zona de origen.
- **Entrenamiento:** hasta el 24 de enero de 2024 inclusive.
- **Prueba:** del 25 al 31 de enero de 2024.
- **Pronóstico futuro:** 1 de febrero de 2024.
- **Modelo:** XGBoost con objetivo de regresión por cuantiles.
- **Cuantiles:** p10, p20, p30, p40, p50, p60, p70, p80 y p90.
- **Baseline:** demanda observada exactamente una semana antes (`lag_168`).
- **Evaluación:** separación temporal, sin `train_test_split`.
"""
    )


    if (
        rmse_modelo is not None
        and rmse_baseline is not None
    ):

        st.write(
            f"RMSE XGBoost p50: **{rmse_modelo:.2f}** · "
            f"RMSE baseline semanal: **{rmse_baseline:.2f}**"
        )


# ============================================================
# LIMITACIONES Y USO RESPONSABLE
# ============================================================

st.subheader(
    "Limitaciones y uso responsable"
)


col_lim, col_uso = st.columns(2)


with col_lim:

    with st.container(border=True):

        st.markdown(
            "#### Limitaciones"
        )

        st.markdown(
            """
- El modelo fue construido únicamente con datos de **enero de 2024**.
- Solo se pronostican zonas con al menos **3,000 viajes** en el mes.
- No incorpora directamente clima, eventos, cierres viales u otros sucesos extraordinarios.
- El comportamiento observado en taxis amarillos no representa toda la movilidad de una zona.
- La precisión cambia según el tipo de zona, por lo que el error global no describe todos los casos por igual.
"""
        )


with col_uso:

    with st.container(border=True):

        st.markdown(
            "#### Usos no recomendados"
        )

        st.markdown(
            """
- No utilizarlo como única fuente para **recortar servicio** en zonas de baja actividad histórica.
- No interpretar el pronóstico como una garantía exacta de demanda.
- No usarlo para decisiones de seguridad, emergencias o asignación de recursos críticos.
- No extrapolar automáticamente los resultados a otros meses, años, ciudades o tipos de transporte sin una nueva evaluación.
"""
        )


st.warning(
    "Una mala decisión basada únicamente en el modelo puede "
    "afectar a conductores por exceso de taxis sin pasajeros "
    "y a usuarios por falta de disponibilidad. Las zonas de "
    "menor volumen requieren especial cuidado porque algunas "
    "quedan fuera del pronóstico."
)


# ============================================================
# RETROALIMENTACIÓN
# ============================================================

st.divider()


st.caption(
    "Esta ficha resume las métricas generadas "
    "por el notebook de preparación."
)


valoracion = st.feedback(
    "stars",
    key="valoracion_ficha_modelo"
)


if valoracion is not None:

    st.toast(
        "Gracias por valorar la claridad "
        "de la ficha del modelo."
    )