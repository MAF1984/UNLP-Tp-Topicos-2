## ADR 012: Requisitos no funcionales cuantificados

**Estado:** Propuesto · **Fecha:** 15/11/2026 · **Etapa:** I (declarar) y III (validar con el stress test)

**Drivers:** sin números, ningún ADR es verificable; el enunciado incluye un stress test en la Etapa III y varias decisiones (cola, caché, resiliencia) dependen de la escala.

**Contexto:** todos los valores son supuestos de partida para el TP, no mediciones. Se calibran al tamaño del entorno de prueba y se ajustan, con evidencia, después de la primera corrida.

**Decisión:** adoptar los siguientes objetivos y revisar los ADR con los resultados del stress test.

| Categoría | Requisito | Objetivo (supuesto) | ADR |
|---|---|---|---|
| Carga | Usuarios en sala de espera por evento masivo | 50.000 (escala productiva); 10.000 usuarios virtuales en el stress test local | 003 |
| Carga | Holds sostenidos por evento masivo | 100/s, con picos de 300/s | 002, 003 |
| Carga | Compras confirmadas sostenidas | 50/s | 009 |
| Carga | Lecturas de catálogo | 1.000 req/s con ≥ 90 % de hit ratio | 004 |
| Latencia p95 | Detalle de evento con caché | < 200 ms | 004 |
| Latencia p95 | Búsqueda | < 500 ms | 006 |
| Latencia p95 | Crear hold (p99 < 1 s) | < 400 ms | 002 |
| Latencia p95 | Iniciar pago (sin contar la pasarela) | < 800 ms | 009 |
| Latencia p95 | Overhead del middleware | < 2 ms | 005 |
| Disponibilidad | Catálogo | 99,9 % mensual | 001 |
| Disponibilidad | Compra, durante ventanas de venta | 99,5 % | 001 |
| Errores | 5xx durante una apertura | < 1 % | 003 |
| Integridad | Dobles ventas | 0 (invariante) | 002 |
| Integridad | Eventos perdidos | 0 (duplicados tolerados e idempotentes) | 009 |
| Consistencia | Visibilidad de cambios del catálogo | ≤ 5 s | 004 |
| Consistencia | Lag de indexación de búsqueda | < 5 s | 006 |
| Consistencia | Lag de consumidores, p95 | < 10 s | 009 |
| Recuperación | RPO / RTO | ≤ 5 min / ≤ 30 min (backups con WAL y PITR) | 001 |
| Seguridad | Vida del access token | 15 min | 010 |
| Retención | Logs operativos / auditoría | 30 días / 5 años | 005 |

**Plan del stress test (Etapa III):**

1. Apertura masiva con sala de espera.
2. Contención sobre un mismo asiento y una misma zona.
3. Lectura intensiva del catálogo con y sin caché.
4. Caos: caída de Redis, de Payments y del broker durante la carga.
5. Prueba de resistencia de 30 minutos.

Herramienta a elección del equipo (k6 o Locust). Criterio de éxito: cumplir la tabla y 0 dobles ventas, verificado con consultas SQL posteriores a cada corrida (no hay dos asignaciones activas por asiento y `capacity = available + held + sold` en cada zona).

**Implicancias:**

- Positivas: los ADR pasan a ser verificables y el stress test tiene un criterio de éxito explícito.
- Negativas / riesgos: los números son supuestos y un entorno local no reproduce producción; hay que trabajar con escalas relativas y extrapolar con cuidado.
