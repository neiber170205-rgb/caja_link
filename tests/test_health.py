# =============================================================================
# test_health.py — Prueba de montaje: comprueba que el contenedor de pruebas
# llega al servicio caja-link por la red interna de docker compose.
# =============================================================================


# Regla 5 del reto: el entorno queda levantable con docker compose y el servicio
# responde en el puerto del contrato (8083). /health no pide token.
def test_health_responde_200(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}
