# PB Conecta

Plataforma de networking para prácticas profesionales de la **Institución Universitaria Pascual Bravo**. Conecta a estudiantes, empresas aliadas y la oficina de prácticas.

Proyecto académico del curso Pensamiento Creativo. Prototipo construido solo con herramientas libres y gratuitas: Docker, PostgreSQL, Django y React.

---

## Cómo levantar el proyecto

**Requisito:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y abierto.

1. Abre una terminal en esta carpeta.
2. Si no existe el archivo `.env`, cópialo desde la plantilla y cambia los valores marcados con `CAMBIAR`:
   ```bash
   cp .env.example .env
   ```
3. Levanta todo:
   ```bash
   docker compose up --build
   ```

La primera vez tarda varios minutos, porque descarga imágenes e instala dependencias. Al terminar:

| Qué | Dirección |
|---|---|
| **Aplicación** | http://localhost:8080 |
| Documentación de la API (Swagger) | http://localhost:8080/api/docs/ |
| Panel del superadministrador (Django admin) | http://localhost:8080/admin/ |
| Bandeja de correos de prueba (Mailpit) | http://localhost:8025 |
| PostgreSQL (DBeaver, pgAdmin) | `localhost:5433`, con el usuario y la contraseña del `.env` |

### Usarlo desde Docker Desktop

Después del primer `docker compose up`, el proyecto aparece en Docker Desktop, en **Containers**, como el grupo **`pbconecta`**. Tiene 6 contenedores: `nginx`, `frontend`, `backend`, `scheduler`, `db` y `mailpit`. Desde ahí puedes:

- **Iniciar o detener** todo el proyecto con los botones ▶ / ■ del grupo.
- **Ver los logs** de cada contenedor haciendo clic en su nombre. Los de `backend` son los más útiles cuando algo falla.
- **Abrir la aplicación** con el enlace del puerto `8080:80` del contenedor `nginx`.
- **Abrir una terminal** dentro de un contenedor (pestaña *Exec*), por ejemplo para ejecutar comandos de Django en `backend`.

---

## Usuarios de demostración

Se crean automáticamente la primera vez que se levanta el proyecto con la base de datos vacía. **Todos usan la contraseña `PbConecta2026*`.**

| Rol | Correo | Para probar |
|---|---|---|
| Superadministrador | `admin@pascualbravo.edu.co` | Panel `/admin`: catálogos, parámetros y cuentas de la oficina |
| Oficina de prácticas | `practicas@pascualbravo.edu.co` | Gestión del proceso |
| Estudiante **habilitado** | `estudiante@pascualbravo.edu.co` | Tecnología en Desarrollo de Software; perfil completo con hoja de vida de ejemplo, puede postularse |
| Estudiante **no habilitado** | `estudiante2@pascualbravo.edu.co` | Diseño Gráfico; solo puede explorar |
| Empresa **aliada** | `talento@techandina.example` | Tech Andina S.A.S., con convenio vigente |
| Empresa **pendiente** | `rrhh@solarnorte.example` | Solicitud esperando la aprobación de la oficina |

También se cargan: 12 programas académicos (hay que **verificarlos contra la oferta oficial** del Pascual Bravo), habilidades, sectores, ciudades del Valle de Aburrá, el periodo 2026-2, 4 convocatorias (3 publicadas y 1 en revisión) y publicaciones de ejemplo en el muro.

---

## Estado del prototipo

| Módulo | Estado |
|---|---|
| Infraestructura (Docker, Nginx, PostgreSQL, Mailpit, scheduler) | ✅ Funcionando |
| Modelo de datos completo (38 tablas, restricciones e índices) | ✅ Migraciones aplicadas |
| M1 Acceso: registro de estudiante y de empresa, verificación de correo, inicio de sesión con JWT, roles, recuperar y cambiar contraseña | ✅ Funcionando |
| M9 Notificaciones: campana, correo por Mailpit | ✅ Base funcionando |
| Tareas programadas: cierre de convocatorias, vencimiento de convenios, inicio de prácticas, aviso diario de alertas | ✅ Funcionando |
| Pantallas de inicio por rol, con el estado de habilitación del estudiante | ✅ Funcionando |
| M3 Empresas (oficina): aprobar, rechazar, suspender, reactivar, convenios con PDF protegido, registrar empresa | ✅ Funcionando |
| M7 Habilitación de estudiantes: individual, varios a la vez, historial | ✅ Funcionando |
| M4 Convocatorias: crear, editar, enviar a revisión, devolver, aprobar, publicar en el muro, cerrar, duplicar | ✅ Funcionando |
| M2 Perfil del estudiante: datos, hoja de vida PDF protegida, habilidades, experiencia, proyectos, idiomas, certificaciones, enlaces, completitud | ✅ Funcionando |
| M5 Convocatorias para el estudiante: «Mi programa» / todas / guardadas, búsqueda de texto completo, filtros, índice de afinidad, recomendadas | ✅ Funcionando |
| M6 Postulaciones: postularse, estados con historial, entrevistas, bitácora de seguimiento, notas internas, postulantes por convocatoria, vista global de la oficina | ✅ Funcionando |
| M7 Oficina: verificación de requisitos, legalización (cierra las demás postulaciones y la convocatoria al completar cupos), prácticas por iniciar / en curso / finalizadas / canceladas, alertas de seguimiento, notas de asesoría | ✅ Funcionando |
| M3 Directorio público de empresas aliadas, página de cada empresa, seguir empresas, perfil y logo de la empresa | ✅ Funcionando |
| M5 Búsqueda de talento para empresas (estudiantes «Abiertos a oportunidades») e invitación a postularse | ✅ Funcionando |
| M8 Tablero de indicadores (ubicación, embudo, tendencia, por programa), filtros por periodo y programa, exportación a CSV, resumen por convocatoria para la empresa | ✅ Funcionando |
| M10 Muro: convocatorias automáticas, ofertas externas, eventos, noticias y comunicados; publicaciones dirigidas por programa; «Me interesa», comentarios, guardados y moderación | ✅ Funcionando |
| Opcionales no incluidos: varios reclutadores por empresa (RF-08), preguntas de filtro (RF-36), publicaciones de estudiantes y reportes en el muro (RF-108) | ⏸️ Fuera del prototipo |

El detalle de cada requerimiento está en [`docs/01-requerimientos.md`](docs/01-requerimientos.md).

---

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/01-requerimientos.md`](docs/01-requerimientos.md) | Análisis, actores, requerimientos funcionales y no funcionales, reglas de negocio, decisiones |
| [`docs/02-arquitectura.md`](docs/02-arquitectura.md) | Contenedores, capas, seguridad, búsqueda, afinidad, API, estructura del repositorio |
| [`docs/03-modelo-datos.md`](docs/03-modelo-datos.md) | Diagramas entidad-relación, diccionario de datos y cómo se garantiza cada regla |
| [`docs/04-despliegue.md`](docs/04-despliegue.md) | Cómo publicarlo: túnel para demos, servidor en la nube, HTTPS, correos reales, respaldos y datos personales |
| [`docs/05-manual-de-uso.md`](docs/05-manual-de-uso.md) | Manual de uso por rol: estudiante, empresa, oficina de prácticas y superadministrador |

---

## Estructura

```
pb-conecta/
├── docker-compose.yml          # Entorno de desarrollo
├── docker-compose.demo.yml     # Modo demo (frontend compilado + Gunicorn)
├── .env.example                # Plantilla de variables de entorno
├── db/init/                    # Extensiones de PostgreSQL
├── nginx/                      # Configuración del proxy (desarrollo y demo)
├── backend/                    # Django + Django REST Framework
│   ├── config/                 # settings, urls
│   ├── apps/                   # cuentas, catalogos, estudiantes, empresas, convocatorias,
│   │                           # postulaciones, muro, notificaciones, reportes, comun
│   └── templates/correos/      # Plantillas HTML de los correos
├── frontend/                   # React + Vite + TypeScript + MUI
│   └── src/                    # api, auth, layouts, pages, components
├── scripts/                    # Copia de seguridad y restauración
└── docs/                       # Requerimientos, arquitectura, modelo de datos, despliegue, manual
```

---

## Pruebas automatizadas

```bash
docker compose exec backend python manage.py test apps
```

Cubren las reglas de negocio y los permisos: registro, inicio de sesión, aprobación de empresas y convenios, habilitación, perfil y hoja de vida, flujo de convocatorias, afinidad, búsqueda, postulaciones (RN-04 a RN-13), verificación y legalización (RN-07 a RN-09), prácticas, alertas, bitácora, muro y moderación, directorio, búsqueda de talento, indicadores, exportaciones, contraseñas y aislamiento entre empresas. Son 109 pruebas.

---

## Comandos útiles

```bash
# Levantar en segundo plano / detener
docker compose up -d
docker compose down

# Ver los logs del backend
docker compose logs -f backend

# Crear migraciones después de cambiar un modelo
docker compose exec backend python manage.py makemigrations

# Ejecutar a mano las tareas programadas
docker compose exec backend python manage.py cerrar_convocatorias
docker compose exec backend python manage.py revisar_convenios
docker compose exec backend python manage.py iniciar_practicas
docker compose exec backend python manage.py generar_alertas

# Empezar de cero (BORRA la base de datos y los archivos subidos)
docker compose down -v

# Modo demo para la sustentación
docker compose -f docker-compose.yml -f docker-compose.demo.yml up --build

# Copia de seguridad y restauración
sh scripts/backup.sh
sh scripts/restore.sh backups/<archivo>.dump
```

---

## Repositorio

Por ahora el proyecto **no está en ningún repositorio remoto**. Cuando lo quieras subir con una cuenta personal de GitHub o GitLab, el `.gitignore` ya excluye el archivo `.env` (que tiene las contraseñas), `node_modules`, los archivos subidos y las copias de seguridad.
