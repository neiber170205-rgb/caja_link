# Imagen del contenedor de pruebas de Caja Link.
# Prueba el servicio en funcionamiento por la red interna de docker compose y
# deja el reporte JUnit XML en /results (montado como ./test-results).
FROM python:3.12-slim

# PYTHONUNBUFFERED: los mensajes de pytest salen de inmediato.
# PYTHONDONTWRITEBYTECODE: no deja archivos .pyc en la carpeta de pruebas.
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /tests

# Primero las librerías: esta capa se reutiliza mientras requirements.txt no cambie.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# -p no:cacheprovider: no escribe .pytest_cache dentro del contenedor.
# --junitxml: el reporte que revisa el calificador (modelo de amenazas y PE03).
CMD ["pytest", "-v", "-p", "no:cacheprovider", "-o", "junit_family=xunit2", "--junitxml=/results/junit.xml"]
