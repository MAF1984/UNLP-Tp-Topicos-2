# Guía de Contribución - Ticketera Virtual (Tópicos de Ingeniería de Software II)

¡Bienvenido/a al repositorio del proyecto! Este documento establece las reglas, la metodología, la política de uso de Inteligencia Artificial y el flujo de trabajo obligatorios para contribuir al desarrollo de la plataforma de venta de tickets.

---

## 📌 1. Metodología de Desarrollo

Este proyecto utiliza **Spec-Driven Development (SDD)** guiado por el framework [OpenSpec](https://openspec.dev/) y agentes de Inteligencia Artificial.

El desarrollo está organizado en 3 etapas incrementales:
* **Etapa I - Core del Negocio:** Backend, APIs REST contract-first, autenticación JWT/RBAC, catálogo de eventos (numerados y por zonas), compra transaccional con locks e `Idempotency-Key`, saga compensatoria de pagos mockeados y bitácora HTTP estructurada.
* **Etapa II - Cache e Inteligencia:** Cache Look-Aside en Redis con invalidación reactiva por eventos y motor de recomendaciones basado en historial y preferencias.
* **Etapa III - Escalabilidad y Resiliencia:** Sala de espera virtual FIFO con tokens de admisión y backpressure, devoluciones con saga y aprobación de administrador, búsqueda multicriterio con PostgreSQL FTS y validación bajo stress test (k6 / Locust).

### Ciclo de vida de un Cambio (OpenSpec)
Cada nueva funcionalidad, ajuste de infraestructura o etapa se gestiona como un *change* en OpenSpec:
1. **Explore:** Análisis de ventajas/desventajas arquitectónicas y consulta obligatoria de `docs/adr/`.
2. **Proposal (`proposal.md`):** Justificación del "por qué" y declaración de capabilities nuevas o modificadas.
3. **Specs (`specs/`):** Definición de requerimientos y criterios de aceptación en sintaxis **EARS** y escenarios **Given-When-Then** con códigos HTTP explícitos.
4. **Design (`design.md`):** Diseño técnico detallado respetando **Arquitectura Hexagonal**, sin dependencias cruzadas entre esquemas lógicos y con diagramas de secuencia Mermaid.
5. **Tasks (`tasks.md`):** Desglose de tareas atómicas aplicando estrictamente **TDD** (tests en rojo antes de código).
6. **Apply:** Implementación del código y verificación dentro de contenedores Docker.
7. **Archive:** Cierre y archivado del cambio una vez superados todos los tests y actualizados los ADRs.

---

## 🤖 2. Política de Uso de IA y Mitigación de Bus Factor

* **La IA como herramienta, la autoría en el equipo:** Los agentes de IA proponen código y diseño, pero los integrantes del equipo son los únicos responsables de su corrección, seguridad y mantenibilidad.
* **Comprensión obligatoria del diff:** Ningún Pull Request será aprobado si el desarrollador no comprende en su totalidad cada línea introducida por el agente. *Si no puedes defender y explicar el diff en el coloquio de la materia, el código no se mergea*.
* **Revisión cruzada humana:** Para mitigar el *Bus Factor*, todo PR debe ser revisado y aprobado por otro miembro del equipo, verificando que no existan soluciones mágicas, dependencias ocultas o violaciones a los ADRs.

---

## 🌿 3. Flujo de Ramas y Sistema de Carriles (Lanes)

### Ramas Principales
* `main`: Código estable y validado de entregas finales. Protegida contra push directo.
* `Development`: Rama de integración continua. Protegida contra push directo; todas las contribuciones entran vía PR.

### Nomenclatura de Ramas de Trabajo
Toda contribución parte desde `Development` bajo la convención:
* `E{Número de Etapa}-feature/<nombre-descriptivo>` (ej. `E0-feature/bootstrap`, `E1-feature/auth-gateway`, `E1-feature/checkout-concurrency`).
* `E{Número de Etapa}-fix/<nombre-descriptivo>` para correcciones de bugs.

### Sistema de Carriles (Lanes)

| Carril | Tipo de Contribución | Requisitos Previos | Flujo de Aprobación |
| :--- | :--- | :--- | :--- |
| **Lane Docs / ADR** | Cambios exclusivos en `docs/`, `openspec/` o archivos `.md`. | No requiere Issue previo. | Revisión ágil y verificación de consistencia. |
| **Lane Code / Feat / Fix** | Código fuente backend, frontend, bases de datos o pipelines. | **Issue previo obligatorio en GitHub** vinculado en la descripción del PR. | CI en verde (tests + linters) + 2 aprobaciones obligatorias (Bot IA + Humano). |

---

## 💬 4. Estándar de Mensajes de Commit (Conventional Commits)

Todos los commits deben cumplir con el estándar [Conventional Commits](https://www.conventionalcommits.org/):
```
<tipo>(<alcance opcional>): <descripción concisa en imperativo>

[cuerpo opcional detallando el motivo del cambio]

[referencia a issues, ej. Closes #12]
```

**Tipos válidos:**
* `feat`: Nueva funcionalidad para el usuario/sistema.
* `fix`: Corrección de un bug.
* `docs`: Modificaciones exclusivas de documentación o ADRs.
* `test`: Adición o refactorización de pruebas automatizadas.
* `refactor`: Cambio de código que no altera la funcionalidad externa.
* `chore`: Mantenimiento de configuración, dependencias o herramientas de CI.

---

## 🚀 5. Proceso de Pull Requests y Quality Gates

Para mergear a `Development`, se deben satisfacer todos los Quality Gates:
1. **Target:** Siempre apuntar a `Development`.
2. **Revisiones Requeridas (Exactamente 2):**
   * Un agente/bot de IA para code review estático.
   * Un revisor humano del equipo con rol de administrador/par.
3. **Integración Continua (CI):** Ejecución exitosa de `pytest` y linters dentro del entorno Docker.
4. **Análisis de Calidad (SonarCloud):** Superar el Quality Gate sin vulnerabilidades de seguridad ni deuda técnica crítica.

---

## 🐳 6. Entorno de Desarrollo Local (Docker-Only)

Para garantizar la reproducibilidad entre Windows, Linux y macOS:
* **Prohibido instalar dependencias de desarrollo localmente con pip global.**
* Toda la ejecución y pruebas se orquestan mediante **Docker Compose**:
  ```bash
  # Levantar el entorno completo en segundo plano
  docker compose up -d

  # Ver estado de los contenedores
  docker compose ps

  # Ejecutar la suite de tests dentro del contenedor
  docker compose exec gateway pytest
  ```
* Todo microservicio nuevo debe respetar la estrategia **Database-per-Service** (esquemas lógicos aislados sin JOINs cruzados) y la **Arquitectura Hexagonal**.
