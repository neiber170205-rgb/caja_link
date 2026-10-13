# FESC Legacy Challenge 2026 — Lo esperado y rúbrica de calificación

Este documento complementa `RETO.md`. Define qué se espera de cada reto, cómo se califica y cómo se calcula la nota final.

**Principio:** toda la nota es verificable. La única parte que decide una persona es la mitad del pitch (5 puntos), donde el comité revisa el contenido del video:

- El **sistema de calificación** ejecuta las pruebas del validador, revisa los entregables con reglas fijas y detecta las penalizaciones.
- El **comité** verifica cada resultado antes de publicarlo, revisa el contenido del pitch (válido o no válido) y registra la copia entre equipos si la confirma.
- El **jurado** consulta en la plataforma el resultado de cada pareja en lenguaje sencillo. No asigna puntos ni necesita leer código.

Los identificadores (`T01`, `GE03`, `PE02`…) son los mismos que aparecen en los reportes. Cada equipo puede revisar su avance con `./validator check` (pruebas) y `./validator entregables` (documentos), que usan las mismas reglas del calificador oficial.

---

## 1. Fórmula general

Nota final sobre 100 puntos:

| Componente | Técnico | Tecnólogo | Profesional | Quién lo califica |
|---|---:|---:|---:|---|
| Validador automático | 80 | 70 | 70 | Sistema: pruebas sobre el entorno entregado |
| Entregables verificables | 20 | 30 | 30 | Sistema: revisa documentos, código y Git con las reglas de esta rúbrica. Pitch: mitad el sistema (duración) y mitad el comité (contenido) |

```text
nota_validador = (puntos_obtenidos / puntos_posibles) × peso_validador
nota_final     = nota_validador + entregables − penalizaciones      (entre 0 y 100)
```

- Las pruebas y entregables con resultado parcial otorgan puntos proporcionales. Por ejemplo, 7 de 10 incidentes completos dan el 70 % de los puntos de TE01.
- Los puntos de los entregables están directamente en la escala de la nota final: TE01 vale 8 puntos de los 100.
- Los documentos se revisan solo en **Markdown (`.md`)** con la ruta exacta del reto (`openapi.yaml` y `config/cajas.yaml` en YAML). Un documento entregado en Word, PDF u otro formato cuenta como no entregado (el reporte dice qué archivo se encontró). La evidencia del nivel Técnico acepta además `.txt`, `.log`, `.csv`, `.json`, `.pdf`, `.png` y `.jpg`. Los archivos de texto de más de 1 MB no se revisan.

---

## 2. Alcance por nivel (plan de estudios FESC)

Lo que se pide en cada reto corresponde a lo que el estudiante ya cursó en su ciclo propedéutico ([plan de estudios](https://www.ingsoftwarefesc.com/)). Nada de lo exigido requiere materias de un ciclo posterior.

| Nivel | Semestres | Materias en las que se apoya | Se exige | No se exige |
|---|---|---|---|---|
| Técnico | I a III | Sistemas Operativos, Virtualización, Docker, Base de Datos Relacionales, Programación Estructurada y Orientada a Objetos, Modelos y Documentación del Software | Diagnosticar desde la terminal, reparar Docker Compose, consultas SQL, scripts en Bash o Python, documentar incidentes con evidencia, usar Git | Diseñar arquitectura, construir APIs nuevas, seguridad, pruebas automatizadas |
| Tecnólogo | IV a VI | Arquitectura y Diseño del Software, Desarrollo Básico y Avanzado de Aplicaciones en Red, Arquitectura Cliente-Servidor, Codificación y Pruebas del Software, Seguridad Informática | Construir una API REST con adapter, autenticación por token, pruebas automatizadas, contrato OpenAPI, plan de migración con rollback | ADR formales, modelo de amenazas, pruebas de carga, sistemas distribuidos |
| Profesional | VII a IX | Gestión de Proyectos de Software, Calidad y Seguridad del Software, Tecnologías Emergentes, Prototipado y Validación (y todo lo anterior) | Integración de sistemas heterogéneos, tolerancia a fallas, protección de datos (Ley 1581), ADR, modelo de amenazas demostrado con pruebas, prueba de carga, versionado y extensión por configuración | — |

---

## 5. Nivel Profesional — Caja Link

### Lo que se espera

Un servicio de interoperabilidad que responde correctamente consultas en línea y por lote entre cajas heterogéneas, protege los datos personales, nunca da un falso "no afiliado" ante fallas y puede crecer (versión 2 y cuarta caja) sin rehacerse. Las decisiones de arquitectura y de seguridad están documentadas y las mitigaciones se demuestran con pruebas automatizadas.

### Validador (500 puntos → 70)

| ID | Prueba | Cómo se verifica | Pts |
|---|---|---|---:|
| P01 | Autenticación | Sin token → 401; auditoría solo con `ADMIN_TOKEN` | 30 |
| P02 | Finalidad | Sin `purpose` o inválido → 400 | 30 |
| P03 | Resultados correctos | Muestra oculta de casos `AFILIADO_OTRA_CAJA` y `NO_AFILIADO`, incluidas dobles afiliaciones | 70 |
| P04 | Normalización | Documentos con puntos, espacios o ceros a la izquierda dan el mismo resultado | 20 |
| P05 | Exclusión de la caja consultante | La caja que pregunta no aparece en `matches` | 20 |
| P06 | Dato mínimo | Ninguna respuesta contiene campos prohibidos | 40 |
| P07 | Caja caída | Con una caja apagada vía `/__chaos`: `INDETERMINADO` y la caja en `unavailable` (nunca `NO_AFILIADO`) | 60 |
| P08 | Caja lenta | Respuesta en menos de 5 s con una caja lenta | 30 |
| P09 | Fuente por archivo | Coincidencias de Caja Centro con `source: FILE` y `asOf` | 30 |
| P10 | Lote | 10.000 documentos, resultados correctos en 5 min o menos | 60 |
| P11 | Idempotencia del lote | Misma `Idempotency-Key` → mismo `jobId` | 20 |
| P12 | Versionado | v2 incluye `affiliateType`; v1 idéntica a antes | 30 |
| P13 | Auditoría | Entradas con los campos exigidos y documento enmascarado | 20 |
| P14 | Cuarta caja | Con Caja Sur activa y reinicio del servicio, sus afiliaciones aparecen | 40 |

### Entregables verificables (30 puntos)

Los formatos obligatorios están en `RETO.md` §6.

| ID | Entregable | Qué revisa el sistema | Pts |
|---|---|---|---:|
| PE01 | Decisiones de arquitectura (ADR) | `docs/adr/` tiene al menos 3 ADR, cada uno con las secciones Contexto, Decisión y Consecuencias (al menos 10 palabras cada una) y Alternativas (al menos 2) | 4 |
| PE02 | Modelo de amenazas demostrado | `docs/threat-model.md` tiene una fila por Autenticación, Finalidad, Dato mínimo, Secretos y Auditoría. Por categoría: la mitad si la amenaza y la mitigación están descritas, la otra mitad si la prueba citada aparece **aprobada** en el reporte JUnit del equipo | 5 |
| PE03 | Pruebas automatizadas | Igual que GE05, con al menos 15 pruebas aprobadas | 3 |
| PE04 | Prueba de carga documentada | `docs/load-test.md` tiene las líneas `herramienta:`, `documentos:` (10 000 o más), `duracion_segundos:` (300 o menos) y `errores:` | 2 |
| PE05 | Cajas por configuración | `config/cajas.yaml` (o .yml/.json) declara las 4 cajas y ningún archivo de `src/` tiene direcciones de cajas escritas en el código (caja-norte, :9001, :9002, :9004…) | 3 |
| PE06 | Contrato OpenAPI v1 y v2 | `openapi.yaml` es OpenAPI 3 y declara las 5 rutas del contrato (v1, v2, lote, estado del lote y auditoría) | 2 |
| PE07 | Documento de arquitectura | `docs/architecture.md` tiene las secciones Contexto, Componentes, Flujo de consulta, Manejo de fallas y Alternativas descartadas (con al menos 2), cada una con al menos 20 palabras | 1 |
| PE08 | Historial Git | Igual que TE05 | 1 |
| PE09 | Uso de IA documentado | Igual que TE06 | 2 |
| PE10 | Pitch de 1 minuto | En **Mi equipo** está registrado el enlace público de Google Drive de un video de **60 segundos o menos** que presenta la solución. Mitad automática: el sistema consulta en Drive que el archivo sea un video público, su duración y que no se haya modificado después de la hora límite. Mitad del comité: contenido válido. Si el comité lo marca **no válido**, el entregable vale 0 | 5 |
| PE11 | README: documentación del software | Igual que TE08, con las 5 rutas del contrato en Uso, `docker compose --profile test run --rm tests` en Pruebas y enlaces a `docs/architecture.md`, `docs/adr/`, `docs/threat-model.md`, `docs/load-test.md`, `openapi.yaml`, `config/cajas.yaml` y `AI_USAGE.md` | 2 |

---

## 6. Penalizaciones

Todas se detectan automáticamente, salvo la copia. El reporte de cada equipo muestra la evidencia de cada penalización.

| Situación | Efecto | Cómo se detecta |
|---|---|---|
| Repositorio no registrado o no público | No se califica | Al llegar la hora límite, la plataforma intenta descargar el repositorio registrado sin usuario ni contraseña. Si no hay enlace registrado o la descarga falla, el equipo queda NO CALIFICADO. La plataforma ya avisa al registrar el enlace si no es público |
| Entrega tardía | Ver regla | Se califica el **último commit anterior a la hora límite**; lo posterior se ignora. Si no hay ningún commit antes de la hora límite, el equipo queda NO CALIFICADO |
| Sin `AI_USAGE.md` o sin usos | −5 puntos | No existe `AI_USAGE.md` en la raíz del repositorio, o no tiene ninguna sección `## Uso N` completa (la plantilla vacía del kit no cuenta) |
| Secretos versionados | −5 puntos | `.env` está o estuvo en el historial de Git, o el valor de un token, clave o contraseña de `.env`/`.env.example` aparece escrito en otro archivo del equipo (se ignoran los valores de ejemplo como `cambiar-...`) |
| Acceso directo a la base (Tecnólogo) o a los datos internos de otra caja (Profesional) | −10 puntos y 0 en GE01 / PE05 | Tecnólogo: un servicio nuevo que no se llama `gateway…`, `adapter…` ni `tests` se conecta a `legacy-db` (registro de conexiones de PostgreSQL) o depende de ella en `docker-compose.yml`. Profesional: un servicio del equipo monta la carpeta `mocks/` o su código lee los archivos de datos de las cajas simuladas |
| El entorno no levanta desde cero | El validador corre con lo que levante; las pruebas que fallen valen 0 | `docker compose up -d --build` termina con error, o `docker-compose.yml` usa opciones que dan acceso al servidor (`privileged`, `cap_add`, `devices`, red o procesos del host, montajes fuera del repositorio) y por eso no se levanta (se anota en el reporte) |
| Copia entre equipos | Descalificación de los equipos involucrados | El reporte de similitud marca dos entregas del mismo nivel con 60 % o más de líneas de código propias en común (sin contar el código del kit). El comité revisa el caso y la registra en la plataforma |

Si una detección automática resulta ser un falso positivo, el comité la anula en la plataforma con el motivo. La anulación queda visible en los reportes.

## 7. Desempate

1. Mayor puntaje del validador.
2. Mayor puntaje en entregables.
3. Último commit más temprano.

## 8. Premios

| Premio | Regla |
|---|---|
| Technical Builder | Mayor nota final del nivel Técnico |
| Product Builder | Mayor nota final del nivel Tecnólogo |
| Engineering Award | Mayor nota final del nivel Profesional |
| AI Engineering Award | Entre los equipos calificados **sin penalizaciones**, el de mayor puntaje en el entregable de uso de IA (TE06 / GE09 / PE09). Desempate por nota final |
| FESC Productization | Entre los tres primeros de cada nivel, los que están **listos para producción**: sin penalizaciones, validador ≥ 80 % y entregables ≥ 80 %. Gana la mayor nota final; desempate por porcentaje del validador |

Si ningún equipo cumple la regla, el premio se declara desierto.

## 9. Calificación automatizada

Todo el proceso corre en la plataforma del evento. Las personas solo verifican y consultan:

1. **Material:** cada nivel descarga su kit (ZIP con el kit, el reto y la rúbrica de su ciclo).
2. **Registro:** cada pareja registra el enlace público de su repositorio en **Mi equipo** (cada integrante entra con su correo; la primera contraseña es su número de documento y la plataforma obliga a cambiarla); la plataforma comprueba en ese momento que se pueda descargar. En el mismo lugar registra el enlace de Drive del **pitch**, y la plataforma verifica al momento que sea un video público de 60 segundos o menos.
3. **Cierre:** al llegar la hora límite, la plataforma descarga cada repositorio, lo deja en el último commit anterior a la hora límite, levanta el entorno desde cero en un servidor aislado, ejecuta el validador oficial (con casos ocultos), revisa los entregables, ejecuta las pruebas del equipo y el rollback, y detecta las penalizaciones. Los equipos se califican uno por uno.
4. **Verificación:** el comité mira cada pitch y lo marca válido o no válido, y luego revisa cada resultado (no se puede verificar un resultado con el pitch pendiente). Solo entonces la pareja lo ve en **Mi equipo** y el jurado lo consulta en una ficha sencilla: nota, puesto en el nivel y cómo le fue en cada parte.
5. **Veredicto:** la plataforma combina todo y produce:
   - **Matriz Excel:** ranking por nivel con fórmulas, detalle de cada prueba y entregable con su evidencia, penalizaciones (origen y estado), rúbrica y calculadora de la fórmula.
   - **PDF:** reporte por equipo (cada prueba, cada entregable y penalizaciones con su evidencia, nota final) y consolidado con ranking y premios.
   - **Reporte de similitud** entre equipos del mismo nivel, para que el comité revise posibles copias.
6. **Publicación:** el comité publica la tabla de resultados cuando termina la verificación.
