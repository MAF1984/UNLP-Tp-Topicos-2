## ADR 010: Autenticación y autorización

**Estado:** Propuesto · **Fecha:** 15/11/2026 · **Etapa:** I

**Drivers:** hay tres roles con permisos distintos (administradores, event owners y clientes); el enunciado incluye la autenticación en la Etapa I; el ADR 005 nombra JWT sin que exista una decisión previa; los servicios deben autorizar sin convertir a Identity en un cuello de botella en los picos.

**Contexto:** Identity emite las credenciales, pero cada servicio debe poder validarlas de forma local. Además hace falta una identidad para las llamadas entre servicios.

**Alternativas consideradas:**

- *Sesiones del lado del servidor con almacén compartido*: descartado; agrega estado compartido y acoplamiento con Identity en el camino crítico.
- *Tokens opacos con introspección en cada request*: descartado; una llamada síncrona por request.
- *JWT de larga duración*: descartado; la revocación es prácticamente imposible.
- *IdP externo (Keycloak, Auth0)*: válido y reemplazable. Para el TP, Identity implementa un flujo compatible con OIDC para poder migrar sin cambiar a los servicios.

**Decisión:**

1. **Tokens:** Identity emite un access token JWT firmado con clave asimétrica (ES256) y vida corta (supuesto: 15 min), con los claims `sub`, `role`, `iss`, `aud`, `exp`, `jti` y `kid`. El refresh token es opaco, rotativo y de un solo uso (supuesto: 7 días), se guarda hasheado en Identity, y su reutilización revoca toda la familia de tokens.
2. **Validación local** en el Gateway y en cada servicio, con las claves públicas (JWKS) cacheadas (ADR 004); no hay llamada a Identity por request. La revocación se apoya en la vida corta y, para casos críticos, en una lista de revocación propagada por el evento `identity.user.disabled.v1` con TTL igual a la vida del token.
3. **Credenciales:** contraseñas con Argon2id; rate limiting y bloqueo progresivo ante intentos fallidos; MFA (TOTP) para administradores.
4. **RBAC con ownership**, con denegación por defecto y aplicado en cada servicio, no solo en el Gateway (defensa en profundidad):

| Acción | ADMIN | EVENT_OWNER | CUSTOMER |
|---|---|---|---|
| Gestionar usuarios y roles | Sí | No | No |
| Crear, editar y publicar eventos | Cualquiera | Solo los propios | No |
| Cancelar un evento | Cualquiera | Solo los propios | No |
| Ver ventas y reportes | Todos | Solo de sus eventos | No |
| Comprar tickets | No | No | Sí |
| Solicitar una devolución | No | No | Sí (sus tickets) |
| Aprobar o rechazar devoluciones | Sí | No | No |
| Mantenimiento (reindex, DLQ, flags de cola) | Sí | No | No |

Cada usuario tiene un único rol; un owner que quiera comprar usa una cuenta de cliente.

5. **Servicio a servicio:** tokens de corta vida con credenciales de cliente (mTLS queda como evolución en Kubernetes). Cada servicio acepta solo su propia `aud`; los endpoints internos no se exponen fuera de la red de servicios. El token del usuario se propaga para auditar quién originó la acción.
6. **Claves y secretos:** gestionados por el orquestador, con rotación de claves de firma mediante `kid` y período de solapamiento.
7. Los tokens de admisión (ADR 003) y las claves de idempotencia (ADR 002) quedan ligados al `sub`.

**Implicancias:**

- Positivas: los servicios autorizan sin depender de Identity en cada request; los permisos son explícitos y verificables.
- Negativas / riesgos: un token robado es válido hasta su expiración (mitigado por la vida corta); la rotación de claves y la gestión de refresh tokens agregan complejidad; la revocación inmediata exige la lista de revocación.

**Criterio de verificación:** (1) un token expirado, con firma inválida o con `aud` incorrecta devuelve 401; (2) un CUSTOMER que intenta aprobar una devolución recibe 403; (3) un EVENT_OWNER que edita un evento ajeno recibe 403; (4) con Identity detenido, los requests con token válido siguen funcionando hasta su expiración; (5) reutilizar un refresh token revoca la familia; (6) un endpoint interno invocado sin token de servicio devuelve 401.
