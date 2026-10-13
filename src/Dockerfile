# Imagen del servicio Caja Link.
# Parte de la misma imagen base que usan las cajas simuladas del kit.
FROM python:3.12-slim

# PYTHONUNBUFFERED: los mensajes salen de inmediato en "docker compose logs".
# PYTHONDONTWRITEBYTECODE: no deja archivos .pyc dentro del contenedor.
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Primero las librerías: esta capa se reutiliza mientras requirements.txt no cambie.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# El servicio corre con un usuario sin privilegios, no como root.
RUN useradd --system --uid 10001 --no-create-home servicio
USER servicio

EXPOSE 8083

# Un solo proceso: la auditoría y los lotes viven en memoria y deben ser los mismos
# para todas las peticiones. --no-access-log evita que la URL (que lleva el documento)
# quede escrita en los registros.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8083", "--no-access-log"]
