## ADR 003: Sala de espera virtual para eventos masivos

**Estado:** Aceptado (rev. 2) · **Fecha:** 15/11/2026 · **Etapa:** III (la API de compra de la Etapa I ya acepta un admission token opcional)

**Drivers:** el enunciado pide encolar solicitudes, notificar la posición, procesar en orden, aplicar backpressure y notificar en tiempo real; hay que proteger a Ticketing y a PostgreSQL de los picos de apertura de ventas.

**Contexto:** la apertura de un evento masivo genera una demanda muy superior a la capacidad sostenida de Ticketing y su base de datos (ver ADR 012). Procesar cada solicitud en el momento provoca fallas en cascada.

**Alternativas consideradas:**

- *Rate limiting duro con error 503*: descartado como mecanismo principal por la experiencia de usuario. Se mantiene como defensa complementaria en el borde (por IP y usuario) contra abuso.
- *Autoscaling reactivo*: insuficiente por sí solo; la base de datos no escala en segundos. Se usa como complemento en servicios stateless.
- *Message broker como cola de espera*: descartado. Un broker procesa trabajo asíncrono, pero no entrega la posición en la fila, no controla la admisión y no permite expulsar usuarios abandonados. El broker se usa para eventos y sagas (ADR 009).

**Decisión:** un servicio aislado, **Waiting Room**, desplegado separado de los nodos de frontend.

1. **Una cola por evento** (bulkhead), activada por el flag `requires_queue` del evento (decisión del administrador o umbral de capacidad configurable). Un evento masivo no degrada a los demás.
2. **Posición:** ZSET por evento en una instancia Redis dedicada (ADR 004). El usuario recibe un `queue_token` firmado (evento, usuario, id de cola, exp).
3. **Equidad y anti-bots:** quienes llegan antes de la hora de apertura se ordenan aleatoriamente al abrir; luego rige FIFO. Un usuario autenticado tiene una sola posición por evento. Rate limiting por IP y usuario, y CAPTCHA opcional al ingresar.
4. **Admission controller:** cada segundo admite hasta N usuarios, con N = mínimo entre un tope configurado y una capacidad dinámica derivada de señales de salud (p95 de Ticketing, ocupación del pool de conexiones, consumer lag). Además limita la cantidad de compradores simultáneos en checkout (K tokens activos); el slot se libera al completar, cancelar o expirar la compra. Es backpressure adaptativo.
5. **Admission token** firmado (evento, usuario, expiración de 10 min (supuesto)), obligatorio en los endpoints de compra de los eventos con cola. Ticketing lo valida localmente (firma y exp) sin llamar al Waiting Room, así que no hay acoplamiento síncrono. Sin token válido: 403 `ADMISSION_REQUIRED`.
6. **Heartbeat:** el cliente confirma presencia cada 20 s (supuesto), implícito en la conexión SSE. Sin señal durante 60 s se libera la posición, para que la cola no se trabe con usuarios abandonados.
7. **Notificaciones:** SSE (más simple que WebSockets y suficiente para tráfico unidireccional), servido por el propio Waiting Room y no por los nodos de frontend. La posición se emite agrupada cada 3–5 s, no por cada cambio, para evitar un fan-out O(n) por tick. Fallback: polling con jitter. Una reconexión retoma la posición con el `queue_token`.
8. **Fallas:** si Redis del Waiting Room cae, los eventos con cola pausan la venta (*fail closed*); los demás no se ven afectados. No hay riesgo de doble venta, porque la corrección vive en PostgreSQL (ADR 002).
9. **Objetivo medible:** se reemplaza “100 % de uptime” (no verificable) por un SLO. Durante una apertura, Ticketing mantiene p95 < 400 ms en la creación de holds y errores 5xx < 1 %, y la sala de espera acepta ≥ 99,9 % de los ingresos válidos (supuestos, ver ADR 012).

**Implicancias:**

- Positivas: Ticketing y PostgreSQL operan siempre dentro de sus límites; la experiencia de espera es predecible y justa.
- Negativas / riesgos: un servicio y una instancia Redis más; las conexiones SSE abiertas consumen memoria y deben dimensionarse; los bots no se eliminan por completo; los tokens firmados exigen gestión de claves y tolerancia al desfase de relojes.

**Criterio de verificación:** (1) con 10.000 usuarios virtuales en una apertura simulada, las admisiones hacia Ticketing no superan la tasa configurada y el pool de PostgreSQL no se satura; (2) un usuario sin heartbeat durante 60 s libera su posición; (3) una compra sin admission token válido devuelve 403 `ADMISSION_REQUIRED`; (4) mientras un evento masivo está en cola, la latencia de otro evento no se degrada; (5) una reconexión recupera la posición original.
