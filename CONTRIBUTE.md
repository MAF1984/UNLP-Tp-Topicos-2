# Guía de Contribución - Ticketera Virtual (Tópicos de Ingeniería de Software II)

¡Bienvenido/a al repositorio del proyecto! Este documento establece las reglas, la metodología y el flujo de trabajo obligatorios para contribuir al desarrollo de la plataforma de venta de tickets.

## 📌 1. Metodología de Desarrollo

Este proyecto utiliza **Spec-Driven Development** guiado por el framework [OpenSpec](https://openspec.dev/) y agentes de Inteligencia Artificial. 
El desarrollo está dividido en 3 etapas incrementales:
* **Etapa I - Core:** Backend, APIs, autenticación, compra de tickets, mockups.
* **Etapa II - Integración:** Sistema de recomendación y estrategias de caché.
* **Etapa III - Escalabilidad:** Colas de venta, devoluciones, búsqueda avanzada y stress test.

### Ciclo de vida de un Cambio (OpenSpec)
Cada nueva funcionalidad o etapa se gestiona como un *change* en OpenSpec, siguiendo estrictamente este flujo:
1. **Explore:** Análisis de ventajas/desventajas arquitectónicas (sin código).
2. **Proposal:** Propuesta funcional y técnica consolidada (`/opsx:propose`).
3. **Specs:** Definición de especificaciones detalladas de la API y el sistema.
4. **Design:** Diseño técnico y arquitectónico.
5. **Tasks:** División del trabajo en tareas ejecutables.
6. **Implement:** Desarrollo del código cumpliendo con los tests y el stack definido.
7. **Archive:** Cierre y archivado del cambio una vez finalizado y documentado.

## 🌿 2. Flujo de Ramas (Git Workflow)

* **Ramas Principales:** `main` (código en producción/versiones estables) y `Development` (integración continua).
* **Restricción:** **NUNCA** se permite hacer *commit* o *push* directo a las ramas principales.
* **Ramas de Funcionalidad (Feature Branches):** Toda contribución debe hacerse en una rama nueva partiendo de `Development`.
  * La nomenclatura obligatoria es: `E{Número de Etapa}-feature/<nombre-descriptivo>`.
  * *Ejemplo:* Para desarrollar la concurrencia de tickets en la Etapa 1, la rama debe llamarse `E1-feature/control-concurrencia`.

## 🚀 3. Proceso de Pull Requests (PR)

Una vez finalizada la implementación de una funcionalidad en la rama correspondiente, se debe abrir un PR cumpliendo los siguientes requisitos obligatorios (Quality Gates):

1. **Target Branch:** Todo PR debe apuntar a la rama `Development`.
2. **Revisiones (Aprobaciones):** Se requieren exactamente **2 aprobaciones** para habilitar el *merge*:
   * Un agente de IA dedicado a la revisión de código (bot).
   * Un desarrollador/usuario humano con permisos de administrador en el repositorio.
3. **Integración Continua (CI):** Todos los tests unitarios y de integración (`pytest`) deben ejecutarse a través de GitHub Actions y pasar exitosamente.
4. **Análisis Estático (SonarCloud):** Todo el código introducido debe superar el escaneo de SonarCloud. Si el código no alcanza el umbral de calidad preestablecido (ej. cobertura, bugs, code smells), el PR quedará bloqueado automáticamente.

## 🐳 4. Entorno Local y Stack Tecnológico

Asegúrate de respetar las tecnologías base del proyecto:
* **Backend:** Python (FastAPI, Pydantic v2, SQLAlchemy 2, Alembic).
* **Frontend:** Flask 3 (Jinja2, HTMX - renderizado del lado del servidor). Aplicación separada del backend.
* **Persistencia:** PostgreSQL.
* **Infraestructura:** Priorizar siempre la **Dockerización**. Base de datos, backend y frontend deben poder levantarse mediante contenedores (`docker-compose`) para garantizar la reproducibilidad del entorno de desarrollo local.

## 📝 5. Estilo de Código y Tests

* Escribe código limpio y tipado (type hints en Python).
* Asegúrate de incluir tests unitarios relevantes para cada nueva regla de negocio antes de marcar una tarea como completada.
* Si agregas nuevas variables de entorno, asegúrate de documentarlas en un archivo `.env.example`.

---
*Gracias por contribuir a mantener la calidad y el orden arquitectónico de este proyecto.*