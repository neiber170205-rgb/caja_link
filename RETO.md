# FESC Legacy Challenge 2026

Hackathon del programa de Ingeniería de Software · Técnico · Tecnólogo · Profesional

---

## 1. Información general

| | |
|---|---|
| Duración | La anuncian los organizadores. La **hora límite** se publica en la plataforma del evento |
| Equipos | Parejas (2 estudiantes del mismo nivel) |
| Organización del tiempo | Libre. No hay hitos ni orden obligatorio. Todo el material está disponible desde el inicio |
| Inteligencia artificial | Permitida durante todo el reto (ver sección 3) |
| Entorno | Cada nivel descarga su propio kit (ZIP) desde la plataforma del evento. Ningún nivel depende del trabajo de otro |
| Calificación | Validador automático + entregables verificados por el sistema (ver `rubrica.md`). La única excepción es la mitad del pitch: el comité revisa el contenido del video |

### El escenario común

Una Caja de Compensación Familiar lleva años operando sobre un sistema legacy (IBM Informix / Genero) cuya base de datos se convirtió en el punto de integración de todo: afiliaciones, subsidios, educación, reportes. Cambiar una columna rompe varias aplicaciones, y validar afiliaciones con otras cajas sigue siendo manual.

Cada nivel resuelve una parte distinta del problema:

| Nivel | Reto | Pregunta |
|---|---|---|
| Técnico | **Terminal Rescue** | ¿Puedes diagnosticar y reparar un proceso crítico averiado desde la terminal? |
| Tecnólogo | **Legacy Escape** | ¿Puedes modernizar el sistema sin apagarlo ni romper las aplicaciones que dependen de él? |
| Profesional | **Caja Link** | ¿Puedes integrar varias cajas entre sí con seguridad, privacidad y tolerancia a fallas? |

---

## 2. Reglas comunes

1. **Entrega:** cada pareja descarga el kit de su nivel, lo sube a **su propio repositorio Git público** (GitHub, GitLab o Bitbucket) y registra el enlace en la plataforma del evento (**Mi equipo**) (cada integrante entra con su correo; la primera contraseña es su número de documento y la plataforma obliga a cambiarla). El enlace se puede cambiar hasta la fecha de cierre.
2. **Repositorio público:** la plataforma comprueba al registrar que el repositorio se pueda descargar sin usuario ni contraseña. Si al llegar la hora límite el repositorio no está registrado o no es público, el equipo **no se califica**.
3. **Hora límite:** se califica automáticamente el **último commit con fecha anterior a la hora límite**. Lo que se suba después se ignora. Si no hay ningún commit antes de la hora límite, el equipo no se califica.
4. **Commits:** los dos integrantes hacen commits con su propio nombre y correo. El sistema revisa que haya al menos 10 commits durante el evento, al menos 3 de cada integrante y mensajes que describan el cambio ("corrige host de la base en cierre-api", no "update").
5. El entorno debe quedar **levantable desde cero** con `docker compose up -d --build` (o con el `run.sh` que indique cada reto). La calificación es automática y corre en un servidor Linux: los scripts del equipo (`run.sh`, `reset.sh`, `rollback.sh`) se ejecutan con `bash` y solo pueden contar con `docker` / `docker compose`, `git`, `python3`, `curl`, `jq`, `psql` y las utilidades estándar (`grep`, `awk`, `sed`, `sort`…). Cualquier otra herramienta debe correr dentro de un contenedor (`docker compose exec` o `docker compose run`). Por seguridad del servidor, `docker-compose.yml` no puede usar `privileged`, `cap_add`, `devices`, `network_mode: host`, `pid: host` ni montar carpetas fuera del repositorio (por ejemplo, `/var/run/docker.sock`): si lo hace, el entorno no se levanta y las pruebas valen 0.
6. Los secretos van en `.env` (no se versiona). Se entrega `.env.example`. Ningún archivo del repositorio puede tener escrito el valor de un token, clave o contraseña: el código los lee de variables de entorno.
7. Se permite cualquier lenguaje y framework, salvo que el reto indique lo contrario. Los nombres de endpoints, archivos, carpetas, servicios y puertos de este documento son **obligatorios**: el sistema de calificación los usa.
8. Cada kit incluye:
   - `./validator check`: ejecuta las pruebas públicas del contrato. El validador oficial ejecuta además casos ocultos.
   - `./validator entregables`: revisa los documentos y el repositorio con **las mismas reglas y puntos** del calificador oficial.
   - `./reset.sh`: devuelve el kit al estado inicial si el equipo rompe el entorno.
9. Los documentos entregables tienen un **formato obligatorio** (títulos, campos y tablas) indicado en cada reto. El sistema los revisa de forma automática: si el formato no se respeta, el entregable no suma. Cada kit trae estos archivos como **plantillas** con los títulos, campos y tablas listos para llenar; una plantilla sin llenar no suma puntos.
10. **Formato de los documentos:** todos los documentos que se califican van en **Markdown (`.md`)** con el nombre y la ruta exactos que pide el reto (`openapi.yaml` y `config/cajas.yaml` van en YAML). No se aceptan Word (`.docx`), PDF ni otros formatos en su lugar: si el sistema encuentra, por ejemplo, `AI_USAGE.docx` en vez de `AI_USAGE.md`, el entregable vale 0 y el reporte lo indica. La única excepción es la carpeta `evidence/` del nivel Técnico, que acepta `.txt`, `.log`, `.md`, `.csv`, `.json`, `.pdf`, `.png`, `.jpg` y `.jpeg`. Ningún archivo de texto puede pesar más de 1 MB: los que lo superen no se revisan.

11. **Pitch de 1 minuto:** cada pareja graba un video de **60 segundos o menos** que presente su solución (el problema, qué construyeron y qué resultado lograron), lo sube a **Google Drive**, lo comparte como «Cualquier persona con el enlace» y registra ese enlace en **Mi equipo** antes de la hora límite. Vale 5 puntos de los entregables: la mitad la da el sistema si Drive confirma que es un video público de 60 segundos o menos, y la otra mitad el comité si el contenido es válido. Si el comité lo marca como **no válido**, el pitch vale 0. No modifiquen el archivo después de la hora límite: el sistema lo detecta y pierde la mitad automática.

12. **README: documentación del software (2 puntos):** el `README.md` del repositorio es la documentación del software de la pareja (la guía de los organizadores viene aparte, en `KIT.md`). Cada kit lo trae como plantilla con once secciones obligatorias: `## Descripción`, `## Integrantes`, `## Requisitos`, `## Instalación y ejecución`, `## Configuración`, `## Arquitectura`, `## Uso`, `## Pruebas`, `## Documentación`, `## Qué resolvimos` y `## Limitaciones y pendientes`. El sistema no solo revisa que estén llenas: las contrasta con el repositorio. Configuración debe explicar **cada variable de `.env.example`**; Arquitectura, nombrar **cada servicio de `docker-compose.yml`**; Uso, incluir las rutas del contrato (en el Técnico, la API y los archivos de `output/`); Documentación, enlazar los demás entregables del nivel; e Instalación y ejecución, los comandos para levantarlo. El detalle está en la rúbrica (TE08 / GE11 / PE11).

---

## 3. Uso de inteligencia artificial

Se permite usar cualquier herramienta durante el reto (ChatGPT, Claude, Gemini, Copilot, Cursor, agentes, modelos locales).

> Puedes usar IA para construir cualquier parte de la solución, pero ambos integrantes deben poder entender, ejecutar, depurar y modificar todo lo entregado. Documentar con honestidad cómo usaron la IA y qué corrigieron también suma puntos (`AI_USAGE.md`).

Cada equipo entrega `AI_USAGE.md` en la raíz con **al menos 3 usos relevantes**, cada uno con este formato exacto:

```markdown
## Uso 1
- Herramienta: ChatGPT
- Para qué se usó: diagnosticar el error de conexión de la API
- Prompt principal (resumido): "connection refused contra cierre-db en docker compose"
- Qué produjo: sugirió cambiar el host a localhost
- Qué modificó o corrigió el equipo: localhost no sirve entre contenedores; usamos el nombre del servicio cierre-db
```

Los cinco campos deben estar llenos y "Qué modificó o corrigió el equipo" debe explicar la corrección en **8 palabras o más**. Si `AI_USAGE.md` no existe o no tiene ningún uso completo, se aplica la penalización de −5 puntos.

---

## 6. Nivel Profesional — Caja Link: interoperabilidad entre cajas

### Contexto

Antes de otorgar una tarifa subsidiada o un subsidio, una caja debe verificar que la persona no tenga afiliación vigente en otra caja. Hoy se hace con archivos mensuales o servicios punto a punto: con 2 cajas es manejable, con 5 son 10 integraciones distintas, cada una con su formato, credenciales y fallas.

> ¿Cómo validan varias cajas una afiliación sin compartir bases de datos, sin exponer datos de más y sin dar una respuesta falsa cuando otra caja no responde?

### Kit entregado

| Caja simulada | Exposición | Dificultad |
|---|---|---|
| Caja Norte | REST JSON · `http://localhost:9001` | Lenta a ratos, a veces no responde |
| Caja Oriente | SOAP/XML · `http://localhost:9002` | Documentos con puntos y ceros a la izquierda |
| Caja Centro | Archivo plano diario en `caja-centro/` | Información del día anterior |
| Caja Sur | Especificación incluida; se activa con `docker compose --profile caja-sur up -d` · `http://localhost:9004` | Debe poder sumarse sin rehacer el sistema |

Además: datos sintéticos (incluye personas afiliadas en dos cajas con fechas que se cruzan), resumen de reglas de protección de datos (Ley 1581: finalidad y dato mínimo) y un endpoint `POST /__chaos` en cada caja simulada que usa el validador para provocar fallas.

### Misión

Construir el servicio de interoperabilidad. La arquitectura es libre (hub central, federado o híbrido), pero debe justificarse.

1. **Consulta en línea:** ¿este documento tiene afiliación vigente en otra caja?
2. **Cruce por lote:** dado un archivo de documentos, detectar dobles afiliaciones.
3. **Seguridad y privacidad:** autenticación entre cajas, finalidad obligatoria, dato mínimo, auditoría.
4. **Tolerancia a fallas:** si una caja no responde, nunca se responde "no afiliado".
5. **Evolución:** contrato versionado y una cuarta caja incorporable por configuración.

### Contrato obligatorio (lo que revisa el validador)

Servicio en `http://localhost:8083`. Cada caja consumidora se autentica con `Authorization: Bearer <token>` (`NORTE_TOKEN`, `ORIENTE_TOKEN`, `CENTRO_TOKEN`, `SUR_TOKEN`, `ADMIN_TOKEN` en `.env`).

**Consulta:** `GET /api/v1/affiliations/{document}?purpose=<finalidad>`

`purpose` ∈ `TARIFA_SUBSIDIADA`, `SUBSIDIO_MONETARIO`, `VALIDACION_AFILIACION`. Sin finalidad o con una inválida → `400`.

```json
{
  "requestId": "01J...",
  "result": "AFILIADO_OTRA_CAJA | NO_AFILIADO | INDETERMINADO",
  "matches": [
    { "caja": "NORTE", "validFrom": "2024-01-01", "validTo": null, "source": "ONLINE | FILE", "asOf": "2026-10-04" }
  ],
  "unavailable": ["ORIENTE"]
}
```

Reglas:

- Se excluye la caja que consulta. El documento se normaliza (puntos, espacios, ceros a la izquierda).
- Prohibido incluir: nombre, dirección, teléfono, correo, salario, beneficiarios.
- Si alguna caja no responde y no hay coincidencia en las demás → `INDETERMINADO`, con la caja en `unavailable`.
- Respuesta en menos de 5 segundos aunque una caja esté lenta.
- Sin token → `401`.

**Lote:**

- `POST /api/v1/batch-checks` (CSV con columna `document`, header `Idempotency-Key`) → `202` con `{ "jobId" }`. Repetir con la misma llave devuelve el mismo `jobId`.
- `GET /api/v1/batch-checks/{jobId}` → `{ "status": "PENDING|RUNNING|DONE", "results": [...] }`.
- 10.000 documentos en 5 minutos o menos.

**Versión 2:** `GET /api/v2/affiliations/{document}` agrega `affiliateType` (`DEPENDIENTE`, `INDEPENDIENTE`, `PENSIONADO`). La v1 no cambia.

**Auditoría:** `GET /api/v1/audit?limit=100` (solo `ADMIN_TOKEN`) → entradas con `timestamp`, `requestingCaja`, `purpose`, `result`, `documentMasked`.

**Cuarta caja:** las cajas se declaran en `config/cajas.yaml` (o `.yml` / `.json`): las cuatro deben aparecer y ningún archivo de `src/` puede tener escritas direcciones de cajas (`caja-norte`, `:9001`…). Con Caja Sur activa, sus afiliaciones aparecen en las respuestas tras reiniciar el servicio.

**Límite de acceso:** el servicio del equipo habla con las cajas solo por sus interfaces (REST, SOAP y el archivo publicado de Caja Centro). No puede montar la carpeta `mocks/` ni leer los datos internos de las cajas simuladas.

**Pruebas del equipo:** igual que en Tecnólogo, un servicio `tests` con `profiles: ["test"]` que deja un reporte JUnit XML en `./test-results/`.

### Entregables

```text
src/
tests/
config/cajas.yaml
docker-compose.yml     incluye el servicio tests
openapi.yaml           OpenAPI 3: v1, v2, lote, estado del lote y auditoría
README.md              documentación del software (regla 12)
AI_USAGE.md
docs/
├── architecture.md
├── adr/               3 a 5 decisiones de arquitectura
├── threat-model.md
└── load-test.md
```

**Formato obligatorio de cada ADR (`docs/adr/NNN-titulo.md`):** secciones `## Contexto`, `## Decisión` y `## Consecuencias` con al menos 10 palabras cada una, y `## Alternativas` con al menos 2 en lista.

**Formato obligatorio de `docs/threat-model.md`:** una fila por cada categoría (Autenticación, Finalidad, Dato mínimo, Secretos, Auditoría). La columna `Prueba` tiene el nombre de una prueba automatizada que demuestra la mitigación; el sistema verifica que esa prueba aparezca **aprobada** en el reporte JUnit.

```markdown
| Categoría | Amenaza | Mitigación | Prueba |
|---|---|---|---|
| Autenticación | Una caja sin token consulta afiliaciones | Token por caja validado en cada petición | test_consulta_sin_token_responde_401 |
```

**Formato obligatorio de `docs/load-test.md`:** estas cuatro líneas (además del texto que quieran agregar).

```text
herramienta: k6
documentos: 10000
duracion_segundos: 184
errores: 0
```

**Formato obligatorio de `docs/architecture.md`:** secciones `## Contexto`, `## Componentes`, `## Flujo de consulta`, `## Manejo de fallas` y `## Alternativas descartadas` (al menos 2 en lista). Cada sección cuenta solo si tiene al menos 20 palabras.

---

## 7. Premios

| Premio | Para |
|---|---|
| Technical Builder | Mayor nota final del nivel Técnico |
| Product Builder | Mayor nota final del nivel Tecnólogo |
| Engineering Award | Mayor nota final del nivel Profesional |
| AI Engineering Award | Entre los equipos calificados sin penalizaciones, el mejor `AI_USAGE.md` según el sistema |
| FESC Productization | Entre los tres primeros de cada nivel, la mayor nota de los que están listos para producción: sin penalizaciones, validador ≥ 80 % y entregables ≥ 80 % |

La calificación detallada está en `rubrica.md`.
