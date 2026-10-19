# PB Conecta · Guía de despliegue

Cómo pasar del prototipo local a un entorno donde otras personas puedan entrar y recibir correos reales. Es una guía para tener en cuenta a futuro: **nada de esto está aplicado todavía**.

---

## 1. Opciones según el objetivo

| Objetivo | Opción | Costo |
|---|---|---|
| Mostrarlo un rato (presentación, pruebas con compañeros) | Túnel desde un equipo propio | Gratis |
| Dejarlo funcionando todo el tiempo | Servidor en la nube (VPS) con Docker | Gratis con créditos de estudiante, o 5–6 USD/mes |
| Uso institucional real | Servidores de la universidad, con su aval | Lo asume la institución |

---

## 2. Demo temporal desde un equipo propio (túnel)

No hace falta abrir puertos en el router. Un túnel crea una dirección pública que llega al `http://localhost:8080` del equipo.

| Herramienta | Notas |
|---|---|
| **Cloudflare Tunnel** (`cloudflared`) | Gratis y estable. Sin dominio propio da una dirección temporal tipo `algo.trycloudflare.com` |
| **ngrok** | Muy fácil de usar; el plan gratis tiene límites |
| **Tailscale Funnel** | Gratis |

Ejemplo con Cloudflare, con el proyecto ya levantado:

```bash
cloudflared tunnel --url http://localhost:8080
```

**Tener en cuenta:**

- Solo funciona mientras el equipo esté prendido, con Docker abierto y conectado a internet.
- **No hacerlo desde un equipo ni una red corporativa** (por ejemplo, el portátil del trabajo). Exponer servicios desde equipos de una empresa normalmente va contra sus políticas de TI. Usar un equipo personal.
- Agregar el dominio del túnel en `DJANGO_ALLOWED_HOSTS` y en `FRONTEND_URL` del `.env`, o Django rechazará las peticiones.
- Es para demos, no para dejarlo en producción.

---

## 3. Despliegue real en un servidor (VPS)

### 3.1 Dónde alojarlo

| Opción | Costo aproximado |
|---|---|
| **GitHub Student Developer Pack** (con el correo `@pascualbravo.edu.co`) | Gratis: créditos en DigitalOcean o Azure y, según la temporada, un dominio gratis por un año. **Empezar por aquí** |
| Oracle Cloud "Always Free" | Gratis; el registro a veces es complicado |
| Hetzner, DigitalOcean, Contabo | 5–6 USD al mes |
| Servidores de la universidad | Lo ideal si la institución adopta la plataforma |

Un servidor con **2 GB de RAM y 1–2 CPU** alcanza para el prototipo.

### 3.2 Pasos

1. **Dominio:** crear un registro DNS tipo `A` que apunte a la IP del servidor, por ejemplo `pbconecta.midominio.com`.
2. **Servidor:** instalar Docker y Docker Compose, y clonar el repositorio:
   ```bash
   git clone https://github.com/JuanCa-Restrepo/Pb_Conecta.git
   ```
3. **Archivo `.env` de producción:** copiar `.env.example` y cambiar como mínimo:

   | Variable | Valor en producción |
   |---|---|
   | `DJANGO_DEBUG` | `0` |
   | `DJANGO_SECRET_KEY` | Una clave nueva, larga y aleatoria (nunca la de desarrollo) |
   | `DJANGO_ALLOWED_HOSTS` | `pbconecta.midominio.com,backend` |
   | `FRONTEND_URL` | `https://pbconecta.midominio.com` (también define `CSRF_TRUSTED_ORIGINS`) |
   | `POSTGRES_PASSWORD` | Una clave fuerte nueva |
   | `CARGAR_DEMO` | `0` (ver el punto 6) |
   | `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_REMITENTE` | Los del proveedor de correo (sección 4) |

4. **Levantar en modo demo:** usa gunicorn y el frontend compilado en vez de los servidores de desarrollo:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.demo.yml up -d --build
   ```
   > ⚠️ El modo demo está preparado (`docker-compose.demo.yml`, `nginx/demo.conf`, `nginx/Dockerfile.demo`) pero **nunca se ha probado de punta a punta**. Lo primero es probarlo en local.
5. **HTTPS (candado):**
   - Opción A: poner el dominio detrás de **Cloudflare** (proxy activado). Da HTTPS automático y gratis.
   - Opción B: certificado gratuito de **Let's Encrypt** (certbot) en el Nginx del servidor.
6. **Datos iniciales:** no cargar los datos de demostración: sus usuarios tienen una contraseña conocida y publicada en el README. Crear solo el superadministrador:
   ```bash
   docker compose exec backend python manage.py createsuperuser
   ```
   y desde `/admin` crear las cuentas de la oficina, los programas académicos reales, el periodo y los parámetros.
7. **Respaldos:** el proyecto ya trae los scripts. Programar `backup.sh` a diario, por ejemplo con `cron`, y respaldar también el volumen `media` (hojas de vida, convenios, logos):
   ```bash
   sh scripts/backup.sh
   ```
   Para restaurar: `sh scripts/restore.sh backups/<archivo>.dump`, que **reemplaza** los datos actuales. Guardar los respaldos fuera del servidor.
8. **Actualizar** cuando haya cambios en el repositorio:
   ```bash
   git pull
   docker compose -f docker-compose.yml -f docker-compose.demo.yml up -d --build
   ```

### 3.3 Ajustes de código pendientes antes de producción

Revisados en `backend/config/settings.py`; hoy no existen:

- **Correo con autenticación:** solo se leen `EMAIL_HOST`, `EMAIL_PORT` y `EMAIL_REMITENTE`. Un proveedor real exige además `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` y `EMAIL_USE_TLS`. Hay que agregarlos a `settings.py` (leyéndolos del `.env`) y a `.env.example`.
- **Ajustes de HTTPS:** agregar cuando `DEBUG` esté apagado:
  - `SECURE_PROXY_SSL_HEADER`;
  - `SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE`;
  - `SECURE_HSTS_SECONDS`.
- **Revisión general:** ejecutar `python manage.py check --deploy` y atender sus avisos.

---

## 4. Correos reales

En desarrollo los correos llegan a **Mailpit** (http://localhost:8025), que los atrapa y no los envía a nadie. En producción se cambian las variables SMTP del `.env` por las de un proveedor, después de agregar los ajustes de la sección 3.3.

| Proveedor | Plan gratis | Notas |
|---|---|---|
| **Brevo** | 300 correos/día | Recomendado para empezar |
| **Resend** | 3.000 correos/mes | Fácil de configurar |
| **Amazon SES** | Casi gratis por volumen | Más técnico |
| Gmail con "contraseña de aplicación" | Límite diario bajo | Solo para pruebas; puede caer en spam |

Ejemplo de variables (Brevo):

```env
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=<usuario SMTP que da Brevo>
EMAIL_HOST_PASSWORD=<clave SMTP que da Brevo>
EMAIL_USE_TLS=1
EMAIL_REMITENTE=PB Conecta <no-responder@midominio.com>
```

**Para que no lleguen a spam:** en el DNS del dominio, configurar los registros **SPF, DKIM y DMARC**. El proveedor da los valores exactos para copiar.

**Remitente:** el remitente por defecto usa el dominio `pascualbravo.edu.co`. Solo se puede usar ese dominio si la universidad lo autoriza y configura su DNS. Mientras tanto, usar un dominio propio.

---

## 5. Datos personales (si se usa con estudiantes reales)

- En Colombia aplica la **Ley 1581 de 2012 (Habeas Data)** y el Decreto 1377 de 2013. La plataforma maneja hojas de vida, correos y teléfonos, así que necesita:
  - una política de tratamiento de datos publicada;
  - la autorización explícita de cada usuario al registrarse.
- Lo recomendable es que la **universidad aloje o avale** la plataforma, porque sería la responsable del tratamiento de esos datos.
- Las hojas de vida y los convenios ya se entregan solo a usuarios autorizados (archivos protegidos con `X-Accel-Redirect`). Aun así, el servidor debe tener acceso restringido y respaldos cifrados.

---

## 6. Ruta recomendada

1. Pedir el **GitHub Student Developer Pack**.
2. Probar el **modo demo en local**.
3. Hacer los **ajustes de código** de la sección 3.3.
4. Crear un **VPS pequeño** con los créditos y apuntar un **dominio**.
5. Activar **HTTPS**.
6. Conectar **Brevo** para el correo y configurar SPF, DKIM y DMARC.
7. Programar los **respaldos**.
8. Antes de abrirlo a estudiantes reales: **política de datos** y aval de la universidad.
