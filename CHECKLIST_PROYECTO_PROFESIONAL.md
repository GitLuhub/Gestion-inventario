# Checklist de Estándares Profesionales para Proyectos de Software

> Basado en las lecciones aprendidas en SAPI y en los estándares de la industria.
> Aplicar desde el inicio de cualquier proyecto — corregir después es costoso.

---

## 1. Arquitectura y Diseño

### Antes de escribir la primera línea de código

- [ ] Definir y documentar los **requisitos funcionales** (qué hace el sistema) y **no funcionales** (qué tan bien lo hace: latencia, disponibilidad, volumen)
- [ ] Dibujar el **diagrama de arquitectura** con todos los componentes y sus relaciones antes de implementar
- [ ] Decidir el **patrón arquitectónico**: monolito modular, microservicios, serverless — justificar la elección según el tamaño del equipo y el volumen esperado
- [ ] Identificar los **límites del sistema**: qué procesa de forma síncrona vs asíncrona
- [ ] Definir las **entidades de dominio** y sus relaciones antes de crear modelos de BD
- [ ] Establecer la **convención de nombres** para rutas, tablas, variables y archivos desde el día 1

### Patrones de código

- [ ] Separar capas: **presentación → lógica de negocio → acceso a datos** (nunca mezclar SQL con lógica de UI)
- [ ] Usar **Repository Pattern** para el acceso a datos — facilita testing y cambio de BD
- [ ] No repetir lógica: si el mismo bloque aparece 3 veces, extraerlo a una función/clase
- [ ] Evitar "magic numbers": usar constantes con nombre (`MAX_FILE_SIZE = 10_MB`, no `10485760`)
- [ ] Diseñar para el presente, no para el futuro hipotético — evitar sobre-ingeniería prematura

---

## 2. Seguridad

### Autenticación y Autorización

- [ ] **Nunca** almacenar contraseñas en texto plano — usar bcrypt, Argon2 o scrypt con sal
- [ ] Implementar **JWT con access token de corta duración** (15–30 min) + refresh token (7 días)
- [ ] Guardar el refresh token en cookie **httponly + secure + samesite=lax** — nunca en localStorage
- [ ] Activar `secure=True` en cookies en producción (requiere HTTPS)
- [ ] Implementar **autorización granular por roles** desde el primer endpoint — no añadirla después
- [ ] Aplicar el principio de **mínimo privilegio**: cada rol solo accede a lo que necesita
- [ ] Proteger endpoints de admin con doble verificación (rol + `is_superuser`)

### Protección de la API

- [ ] **Rate limiting** en todos los endpoints de autenticación (login, registro, reset password)
- [ ] Rate limiting diferenciado por rol en operaciones costosas (uploads, exports)
- [ ] Validar **todos** los inputs del usuario en el servidor — nunca confiar solo en validación del frontend
- [ ] Sanitizar outputs para prevenir **XSS** — especialmente en campos que el usuario puede editar
- [ ] Proteger contra **SQL injection** usando ORM o queries parametrizadas — nunca concatenar strings
- [ ] Configurar **CORS** restrictivo: lista blanca de orígenes, no `*` en producción
- [ ] Añadir headers de seguridad HTTP: `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`

### Secretos y Configuración

- [ ] **Nunca** commitear `.env`, API keys, certificados ni contraseñas al repositorio
- [ ] Crear `.env.example` con todas las variables documentadas y sin valores reales desde el día 1
- [ ] Añadir `.gitignore` completo antes del primer commit
- [ ] Rotar `SECRET_KEY` y credenciales entre entornos (dev ≠ staging ≠ producción)
- [ ] Usar variables de entorno para toda configuración que cambia entre entornos

### Datos Sensibles

- [ ] Identificar qué datos son PII (Personally Identifiable Information) antes de diseñar el esquema
- [ ] Implementar cifrado en reposo para datos sensibles (pgcrypto, SSE-S3)
- [ ] Implementar cifrado en tránsito (HTTPS/TLS) — nunca HTTP en producción
- [ ] Añadir **AuditLog** desde el inicio: quién hizo qué, cuándo y desde qué IP
- [ ] Planificar **retención y borrado de datos** (GDPR: derecho al olvido, exportación)

---

## 3. Base de Datos

### Diseño del Esquema

- [ ] Usar **UUIDs** como primary keys — evitan colisiones en entornos distribuidos y no revelan volumen
- [ ] Añadir `created_at` y `updated_at` a **todas** las tablas
- [ ] Definir constraints en la BD, no solo en el ORM: `NOT NULL`, `UNIQUE`, `FOREIGN KEY`
- [ ] Diseñar las relaciones con **cascade** apropiado: qué pasa con los hijos cuando se borra el padre
- [ ] Usar **soft delete** (`is_deleted`, `deleted_at`) para entidades de negocio importantes — el borrado físico es irreversible
- [ ] Normalizar el esquema hasta 3NF como mínimo — desnormalizar solo cuando hay evidencia de necesidad de rendimiento

### Migraciones

- [ ] Usar una herramienta de migraciones desde el día 1 (**Alembic**, Flyway, Liquibase)
- [ ] **Nunca** modificar tablas en producción a mano — siempre mediante migración versionada
- [ ] Hacer migraciones **reversibles**: incluir `upgrade()` y `downgrade()`
- [ ] Probar las migraciones en staging antes de aplicar en producción

### Rendimiento

- [ ] Añadir **índices** en columnas de búsqueda frecuente (`user_id`, `created_at`, `status`, FKs)
- [ ] Añadir índices **compuestos** para queries con múltiples filtros comunes
- [ ] Detectar y eliminar **N+1 queries** — usar `joinedload` / `eager loading` en consultas de listas
- [ ] Configurar **connection pooling** adecuado al número de workers esperados
- [ ] Implementar **caché** (Redis) para datos que no cambian frecuentemente (catálogos, tipos, configuración)
- [ ] Planificar **backups automáticos** con retención definida desde el día 1

---

## 4. API / Backend

### Diseño de Endpoints

- [ ] Seguir convenciones **RESTful**: sustantivos en plural, verbos HTTP correctos (GET/POST/PUT/PATCH/DELETE)
- [ ] Versionar la API desde el inicio (`/api/v1/`) — facilita evolución sin romper clientes existentes
- [ ] Devolver **códigos HTTP semánticamente correctos**: 201 para creación, 202 para aceptado, 204 para sin contenido, 422 para validación
- [ ] Usar **paginación** en todos los endpoints que devuelven listas — nunca devolver todos los registros
- [ ] Estandarizar el formato de respuesta: siempre la misma estructura para éxito y para error
- [ ] Documentar la API automáticamente (Swagger/OpenAPI) — FastAPI lo hace gratis

### Procesamiento Asíncrono

- [ ] Identificar desde el diseño qué operaciones son **lentas o bloqueantes** (llamadas a APIs externas, procesamiento de archivos, envío de emails)
- [ ] Mover esas operaciones a **workers asíncronos** (Celery, RQ, BullMQ) — nunca bloquear la API
- [ ] Implementar **reintentos con backoff exponencial** para tareas que pueden fallar temporalmente
- [ ] Implementar **circuit breaker** para servicios externos — evita cascada de fallos
- [ ] Exponer el **estado de las tareas** al cliente (polling o WebSocket)

### Resiliencia

- [ ] Manejar explícitamente todos los errores esperados — no dejar que excepciones lleguen al cliente como 500
- [ ] Añadir **timeouts** en todas las llamadas a servicios externos
- [ ] Validar el tamaño y tipo de archivos en el servidor, no solo en el cliente
- [ ] Añadir **healthcheck** endpoint (`/health`) que verifique BD, caché y dependencias críticas

---

## 5. Frontend / UX

### Arquitectura Frontend

- [ ] Separar **lógica de negocio** de componentes UI — usar hooks o stores para el estado de datos
- [ ] Usar **React Query / SWR** para data fetching — maneja caché, estados de carga y errores automáticamente
- [ ] Implementar **estados de carga** en todas las operaciones asíncronas — nunca dejar al usuario sin feedback
- [ ] Implementar **estados de error** con mensajes útiles — no solo "Error 500"
- [ ] Usar **interceptores de Axios** para renovar tokens automáticamente — el usuario no debe notar la expiración

### Experiencia de Usuario

- [ ] Añadir **confirmación** antes de acciones destructivas (eliminar, sobrescribir)
- [ ] Deshabilitar botones mientras una operación está en progreso — evitar doble envío
- [ ] Mostrar el resultado de cada acción con **feedback inmediato** (toast, mensaje inline)
- [ ] Implementar **optimistic updates** donde sea apropiado — la UI responde antes de que el servidor confirme
- [ ] Diseñar pensando en **mobile first** — la mayoría del tráfico web es móvil
- [ ] Garantizar **accesibilidad básica**: contraste de colores, etiquetas en formularios, navegación por teclado

### Seguridad Frontend

- [ ] **Nunca** almacenar tokens de acceso en localStorage — usar memoria o cookies httponly
- [ ] Implementar **rutas protegidas** que redirijan a login si el usuario no está autenticado
- [ ] Validar inputs en el cliente para UX, pero **siempre revalidar en el servidor**
- [ ] No exponer información sensible en la URL (IDs de sesión, tokens)

---

## 6. Testing

### Estrategia de Tests

- [ ] Definir la **pirámide de testing**: muchos unitarios, algunos de integración, pocos E2E
- [ ] Establecer un **umbral mínimo de cobertura** desde el inicio (80% es un buen punto de partida)
- [ ] Escribir tests **antes o al mismo tiempo** que el código — no después como deuda técnica
- [ ] Los tests deben ser **independientes**: cada test puede ejecutarse solo, sin depender de otro

### Tests Unitarios

- [ ] Testear toda la **lógica de negocio** de forma aislada (sin BD, sin red)
- [ ] Mockear dependencias externas (APIs, BD, email) en tests unitarios
- [ ] Cubrir **casos límite**: valores vacíos, nulos, máximos, mínimos, caracteres especiales
- [ ] Cubrir **casos de error**: qué pasa cuando falla la BD, cuando la API externa está caída

### Tests de Integración

- [ ] Tener al menos un conjunto de tests que use la **BD real** (no solo SQLite in-memory)
- [ ] Testear el **flujo completo** de los casos de uso más críticos end-to-end
- [ ] Usar fixtures y factories para crear datos de prueba — no hardcodear IDs ni valores

### Tests de Carga

- [ ] Definir los **objetivos de rendimiento** como criterios de aceptación (P95 < 500ms, error rate < 1%)
- [ ] Ejecutar tests de carga antes de cada release importante (Locust, k6, Artillery)
- [ ] Identificar el **punto de quiebre** del sistema bajo carga creciente

---

## 7. Rendimiento

### Backend

- [ ] Medir **antes de optimizar** — no hacer optimizaciones prematuras sin evidencia
- [ ] Usar **async/await** correctamente — no bloquear el event loop con operaciones síncronas costosas
- [ ] Implementar **paginación del lado del servidor** — nunca cargar toda la tabla en memoria
- [ ] Comprimir respuestas HTTP grandes (gzip/brotli)
- [ ] Usar **streaming** para archivos grandes — no cargarlos completos en memoria

### Frontend

- [ ] Optimizar el **bundle size**: code splitting, lazy loading de rutas y componentes pesados
- [ ] Usar **memoización** (useMemo, useCallback) solo donde el profiler lo justifique
- [ ] Implementar **caché del navegador** apropiado para assets estáticos
- [ ] Optimizar imágenes: formato WebP, lazy loading, tamaños responsive

---

## 8. Observabilidad y Monitoreo

### Logging

- [ ] Usar **logs estructurados en JSON** desde el inicio — facilita búsqueda y análisis
- [ ] Incluir en cada log: timestamp, nivel, servicio, request_id, user_id (si aplica), mensaje
- [ ] Definir niveles de log correctamente: DEBUG (desarrollo), INFO (operaciones normales), WARNING (situaciones inesperadas recuperables), ERROR (fallos)
- [ ] **Nunca** loguear contraseñas, tokens ni PII

### Métricas

- [ ] Exponer métricas en formato **Prometheus** desde el inicio
- [ ] Medir al menos: latencia (P50/P95/P99), tasa de requests, tasa de errores, requests en vuelo
- [ ] Crear un **dashboard operativo** (Grafana) con las métricas más importantes
- [ ] Configurar **alertas** para: tasa de errores alta, latencia elevada, servicio caído

### Trazabilidad

- [ ] Añadir un **request_id** único a cada petición y propagarlo a todos los servicios
- [ ] Implementar **AuditLog** para todas las acciones importantes del usuario
- [ ] Correlacionar logs entre servicios con el mismo request_id

---

## 9. Infraestructura y DevOps

### Contenedores

- [ ] **Dockerizar** todos los servicios desde el día 1 — "funciona en mi máquina" no es válido
- [ ] Usar **multi-stage builds** en Dockerfiles: etapa de build separada de la imagen final
- [ ] No instalar dependencias en runtime (`pip install` en `CMD`) — hacerlo en el `Dockerfile`
- [ ] Añadir **healthchecks** en Docker Compose para todos los servicios críticos
- [ ] Definir **resource limits** (CPU, memoria) en los contenedores de producción

### Entornos

- [ ] Tener al menos **3 entornos**: development, staging, production
- [ ] Staging debe ser **idéntico a producción** en configuración — las diferencias causan sorpresas
- [ ] Nunca probar en producción — usar staging para validar antes de cada release

### CI/CD

- [ ] Configurar **integración continua** que ejecute tests en cada push (GitHub Actions, GitLab CI)
- [ ] La pipeline debe fallar si los tests fallan o la cobertura cae por debajo del umbral
- [ ] Automatizar el **build y push de imágenes Docker** en la pipeline
- [ ] Implementar **despliegue continuo** a staging automáticamente tras merge a main

### Backup y Recuperación

- [ ] Configurar **backups automáticos** de la BD con retención definida (mínimo 7 días)
- [ ] Probar la **restauración** de backups periódicamente — un backup que no se puede restaurar no vale nada
- [ ] Documentar el **RTO** (Recovery Time Objective) y **RPO** (Recovery Point Objective)

---

## 10. Control de Versiones

### Git

- [ ] Definir una **estrategia de branching** antes de empezar (GitFlow, trunk-based, etc.)
- [ ] Escribir **commit messages** descriptivos: `tipo(scope): descripción` — nunca "fix", "changes", "wip"
- [ ] Usar **ramas por feature/bugfix** — nunca trabajar directamente en main
- [ ] Configurar **protección de main**: requerir PR + revisión + tests en verde antes de merge
- [ ] Añadir `.gitignore` **antes del primer commit** — sacarlo después es complicado

### Lo que NUNCA va al repositorio

- [ ] Archivos `.env` con valores reales
- [ ] API keys, passwords, tokens, certificados privados
- [ ] Archivos de BD (`*.sqlite`, dumps, backups)
- [ ] Dependencias (`node_modules/`, `.venv/`)
- [ ] Artefactos de build (`dist/`, `build/`, `__pycache__/`)
- [ ] Archivos de configuración del IDE (`.idea/`, `.vscode/`)
- [ ] Archivos temporales y logs

---

## 11. Documentación

### Código

- [ ] El código debe ser **auto-documentado**: nombres descriptivos, funciones pequeñas y enfocadas
- [ ] Añadir comentarios solo donde la lógica **no es obvia** — no documentar lo que el código ya dice
- [ ] Documentar las **decisiones de diseño importantes** (por qué, no qué)

### API

- [ ] Mantener la **documentación de la API actualizada** y autogenerada si es posible (Swagger)
- [ ] Documentar los códigos de error y sus causas
- [ ] Incluir ejemplos de request/response

### README

- [ ] El README debe responder en 30 segundos: **qué hace**, **por qué existe**, **cómo arrancarlo**
- [ ] Incluir instrucciones de instalación que **realmente funcionen** (probarlas en una máquina limpia)
- [ ] Documentar todas las variables de entorno requeridas
- [ ] Incluir instrucciones para ejecutar los tests

---

## 12. Compliance y Legal

- [ ] Identificar si el sistema procesa **datos de ciudadanos de la UE** → aplica GDPR
- [ ] Si aplica GDPR: implementar **exportación de datos del usuario** y **derecho al olvido**
- [ ] Definir y documentar la **política de retención de datos**
- [ ] Si se almacenan datos médicos, financieros o sensibles: consultar regulaciones específicas (HIPAA, PCI-DSS)
- [ ] Incluir **términos de uso** y **política de privacidad** si el sistema es público

---

## 13. Presentación (Proyectos de Portafolio)

- [ ] Tener una **demo pública** funcional con datos de ejemplo pre-cargados
- [ ] README con **GIF o video** del flujo principal (60–90 segundos es suficiente)
- [ ] Sección de **decisiones técnicas** explicando el "por qué" de las elecciones de arquitectura
- [ ] **Badges** visibles: cobertura de tests, versión, estado del build
- [ ] Datos de acceso de prueba claramente visibles (`admin / admin123`)
- [ ] Sin TODO comments, código comentado ni debug logs en el código público

---

## Orden de Aplicación Recomendado

Al iniciar un proyecto nuevo, aplicar en este orden:

```
Semana 1: Arquitectura + BD + Seguridad base
          (esquema, migraciones, auth, .gitignore, Docker)

Semana 2: API core + Tests unitarios
          (endpoints principales, validaciones, cobertura >80%)

Semana 3: Frontend + UX
          (páginas principales, estados de carga/error, protección de rutas)

Semana 4: Observabilidad + Performance
          (logs JSON, métricas, índices BD, N+1 queries)

Semana 5: Hardening + CI/CD
          (rate limiting, HTTPS, backups, pipeline de tests)

Semana 6: Documentación + Demo
          (README, seed de datos, despliegue público)
```

---

## Señales de Alerta (Red Flags)

Si alguna de estas situaciones ocurre, detener y corregir antes de continuar:

- ❌ "Lo añadimos los tests al final" → los tests se escriben con el código, no después
- ❌ "En dev no necesitamos HTTPS" → normalizar las diferencias dev/prod causa errores en producción
- ❌ "Eso lo arreglamos cuando escale" → la seguridad y los índices no se añaden después sin dolor
- ❌ "El `.env` está en el repo pero solo temporalmente" → una vez expuesto, rotar todas las credenciales
- ❌ "Funciona en mi máquina" → si no está dockerizado y documentado, no está terminado
- ❌ "Solo somos dos, no necesitamos PRs" → los PRs son para el código, no para el equipo; sirven de registro

---

*Checklist elaborado en base al desarrollo de SAPI (2026) y estándares de la industria.*
*Actualizar con nuevas lecciones aprendidas en cada proyecto.*
