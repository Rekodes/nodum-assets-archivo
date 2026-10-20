"""Regresión logística que predice el estrés hídrico del maíz con los sensores de cada finca.

Aprende de lo que es barato medir (el tiempo y la temperatura de la cubierta) y se enseña con la
sonda de humedad del suelo, que no entra como variable. Solo usa las horas de sol: de noche la
planta no transpira y su cubierta no delata la sed (el índice de estrés de la cubierta se mide a
mediodía). La prueba es el último 20 % de horas de cada finca. Es el entrenamiento local del
aprendizaje federado: salen los pesos y las métricas, no las lecturas.
"""

from __future__ import annotations

import logging

from logistic import (
    LogisticRegression,
    Standardiser,
    coefficients_svg,
    evaluate,
    feature,
    label,
    model_document,
    split_by_time,
)
from ocean_app import Algorithm, AlgorithmError, Job, Parameter, Record, main, read_records

log = logging.getLogger(__name__)

FEATURES = ("air_temp_c", "relative_humidity_pct", "solar_radiation_w_m2", "wind_speed_m_s", "canopy_temp_c")
TARGET = "water_stress"
TEST_SHARE = 0.2


class WaterStressModel(Algorithm):
    parameters = (
        Parameter("epochs", "number", "Épocas", "Pasadas del descenso de gradiente.", default=300),
        Parameter("learning_rate", "number", "Tasa de aprendizaje", "Tamaño del paso.", default=0.5),
        Parameter("l2", "number", "Regularización L2", "Penaliza los pesos grandes.", default=0.001),
        Parameter("min_radiation", "number", "Radiación mínima (W/m²)",
                  "Solo entran las horas con al menos esta radiación; 0 para usarlas todas.", default=300),
    )

    def run(self, job: Job) -> None:
        train_rows: list[Record] = []
        test_rows: list[Record] = []
        sources = []
        min_radiation = job.parameters.number("min_radiation")
        for path in job.inputs:
            rows = [
                r for r in read_records(path)
                if TARGET in r and all(f in r for f in FEATURES) and feature(r, "solar_radiation_w_m2") >= min_radiation
            ]
            if not rows:
                log.info("%s: no tiene las variables de las fincas de maíz, se ignora", path.name)
                continue
            train, test = split_by_time(rows, TEST_SHARE)
            train_rows += train
            test_rows += test
            sources.append({"file": path.name, "rows": len(rows)})
        if not train_rows or not test_rows:
            raise AlgorithmError("No hay datos de fincas con los que entrenar")

        scaler = Standardiser.fit(FEATURES, train_rows)
        model = LogisticRegression(
            len(FEATURES),
            job.parameters.integer("epochs"),
            job.parameters.number("learning_rate"),
            job.parameters.number("l2"),
        )
        model.fit(scaler.transform(train_rows), [label(r, TARGET) for r in train_rows])
        metrics = evaluate(model, scaler.transform(test_rows), [label(r, TARGET) for r in test_rows])

        job.outputs.write_json("model.json", model_document(TARGET, scaler, model))
        job.outputs.write_json("metrics.json", {
            "test": metrics, "train_samples": len(train_rows), "min_radiation_w_m2": min_radiation, "sources": sources,
        })
        job.outputs.write_text(
            "coefficients.svg", coefficients_svg(FEATURES, model.weights, "Coeficientes del modelo de estrés hídrico")
        )
        log.info("Entrenado con %d horas de %d fincas; prueba con %d", len(train_rows), len(sources), len(test_rows))
        log.info("Exactitud %s, F1 %s, AUC %s", metrics["accuracy"], metrics["f1"], metrics["auc"])


if __name__ == "__main__":
    main(WaterStressModel())
