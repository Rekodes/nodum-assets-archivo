# Una imagen por algoritmo, todas desde este Dockerfile: `--build-arg ALGORITHM=line-count`.
# Solo la biblioteca estándar de Python: nada que descargar al construir, imágenes pequeñas y el
# mismo resultado en cualquier máquina. ocean-node las ejecuta sin red, como 1000:1000 y sin
# capacidades (CapDrop ALL), con las entradas en /data/inputs y las salidas en /data/outputs.
FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1

ARG ALGORITHM
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 ALGORITHM=${ALGORITHM}

WORKDIR /app
COPY common.py /app/common.py
COPY ${ALGORITHM}/ /app/${ALGORITHM}/
RUN test -n "${ALGORITHM}" && ln -s /app/${ALGORITHM}/$(echo ${ALGORITHM} | tr - _).py /app/main.py

USER 1000:1000
ENTRYPOINT ["python", "/app/main.py"]
