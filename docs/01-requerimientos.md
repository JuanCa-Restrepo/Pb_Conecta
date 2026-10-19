# PB Conecta — Especificación de Requerimientos

| | |
|---|---|
| **Proyecto** | PB Conecta — plataforma de networking para prácticas profesionales |
| **Institución** | Institución Universitaria Pascual Bravo |
| **Versión** | 0.4 (incluye las decisiones D1–D7 y la habilitación desde la oficina) |
| **Fecha** | 16 de octubre de 2026 |
| **Fase** | 5.3.4 Prototipado |

**Cambios frente a la v0.1:** solo publican convocatorias las empresas con convenio vigente; el estudiante se postula solo a convocatorias de su programa y sin límite; la oficina **habilita a cada estudiante dentro de la plataforma** (sin CSV) y el estudiante ve siempre su estado de habilitación; el estudiante no habilitado puede explorar todo, pero no postularse; la oficina no revisa las postulaciones y solo vuelve a intervenir después de las entrevistas, para verificar y legalizar; cada postulación tiene una bitácora de seguimiento; el dominio institucional es `@pascualbravo.edu.co`; se agrega el **muro de publicaciones** (módulo M10).

---

## 1. Análisis del contexto

### 1.1 Problema identificado (según el documento del proyecto)

| # | Hallazgo | Fuente en el documento |
|---|---|---|
| P1 | Las convocatorias están **dispersas** entre bolsas de empleo, webs de empresas, redes y canales institucionales. | Planteamiento del problema |
| P2 | Hay **poca oferta de vacantes** frente a un número creciente de estudiantes. | Introducción, sombrero blanco |
| P3 | Falta **asesoramiento continuo** durante la búsqueda. | Introducción, Morales Balaguera (2025) |
| P4 | Muchos dependen de **contactos personales**, lo que genera inequidad y procesos poco transparentes. | Introducción, Ybarra Mora (2025) |
| P5 | Las prácticas no siempre son **afines al programa** del estudiante. | Chamorro (2025), Jiménez-Martínez et al. (2026) |
| P6 | Hay **trámites manuales** y tiempos de aprobación largos, con cuello de botella en la oficina de prácticas. | Sombreros blanco y negro |
| P7 | Las etapas del proceso están **desarticuladas** y no hay seguimiento integral. | Ramírez y Cortés (2023), Cortés Gómez (2022) |

### 1.2 Respuesta de la plataforma a cada problema

| Problema | Capacidad de PB Conecta | Módulo |
|---|---|---|
| P1 Dispersión | Convocatorias de empresas aliadas en un solo lugar, y un **muro** donde la oficina también publica ofertas de bolsas de empleo y convocatorias externas | M4, M5, M10 |
| P2 Poca oferta | Directorio de aliadas, publicación de la oficina en nombre de las empresas y difusión de ofertas externas en el muro | M3, M4, M10 |
| P3 Sin asesoramiento | **Bitácora de seguimiento** en cada postulación, alertas de estudiantes estancados y notas de asesoría | M6, M7 |
| P4 Inequidad / opacidad | Cualquier estudiante puede postularse, los estados son visibles y el motivo de no selección es obligatorio | M6 |
| P5 Falta de afinidad | Programas afines obligatorios en cada convocatoria; el estudiante solo se postula a las de su programa | M4, M5 |
| P6 Trámites manuales | Aprobaciones digitales, notificaciones automáticas y cierre automático de convocatorias | M7, M9 |
| P7 Desarticulación | Un solo ciclo de vida: postulación → selección → verificación de requisitos → legalización → práctica → cierre | M6, M7 |

### 1.3 Objetivo del prototipo

Construir un **prototipo funcional** con herramientas libres y gratuitas, desplegable con Docker, en el que:

- la **oficina de prácticas** gestione empresas aliadas, convenios, convocatorias y el proceso estudiante–empresa;
- las **empresas aliadas** publiquen convocatorias y gestionen a sus postulantes;
- los **estudiantes** creen un perfil profesional, exploren empresas y convocatorias de su programa, y se postulen;
- todos compartan un **muro de publicaciones** con convocatorias, ofertas de bolsas de empleo, eventos y noticias.

---

## 2. Actores y roles

| Rol | Quién es | Qué hace principalmente |
|---|---|---|
| **Estudiante** | Estudiante del Pascual Bravo con correo `@pascualbravo.edu.co` | Crea su perfil profesional, explora convocatorias y el muro, se postula y hace seguimiento a sus postulaciones |
| **Empresa aliada** | Usuario reclutador de una organización con **convenio vigente** | Mantiene el perfil de la empresa, publica convocatorias y noticias, y evalúa postulantes |
| **Oficina de prácticas** (administrativo) | Funcionario de la oficina de prácticas, con correo `@pascualbravo.edu.co` | Habilita estudiantes para prácticas; aprueba empresas, convenios y convocatorias; acompaña cada proceso; verifica requisitos con el estudiante en persona; legaliza prácticas; publica y modera el muro; consulta indicadores |
| **Superadministrador** | Responsable técnico de la plataforma | Crea cuentas de la oficina, gestiona catálogos y configura la plataforma |
| **Visitante** | Cualquier persona sin sesión iniciada | Ve la página de inicio, el directorio público de empresas aliadas y los formularios de registro |

> **Rol futuro (fuera del prototipo):** Docente asesor de práctica. En el prototipo, el asesor se registra como un dato de la práctica legalizada.

---

## 3. Alcance

### 3.1 Dentro del prototipo

- Registro, inicio de sesión y control de acceso por roles.
- Perfil profesional del estudiante, al estilo LinkedIn.
- Perfil de empresa, convenios y directorio de empresas aliadas.
- Ciclo completo de una convocatoria: creación, aprobación, publicación y cierre.
- Búsqueda centrada en el programa del estudiante, con filtros y recomendación por afinidad.
- Postulaciones con estados, bitácora de seguimiento y entrevistas.
- Panel de la oficina: aprobaciones, verificación de requisitos, legalización de prácticas y seguimiento.
- Muro de publicaciones con convocatorias, ofertas externas, eventos y noticias.
- Indicadores básicos y exportación a CSV.
- Notificaciones dentro de la plataforma y por correo (capturado localmente con Mailpit).
- Datos de demostración precargados.

### 3.2 Fuera del alcance (fases posteriores)

- Integración con el sistema académico de la universidad. La oficina verifica los requisitos académicos en persona y solo registra en la plataforma que lo hizo.
- Firma digital de convenios y actas.
- Seguimiento detallado durante la práctica: bitácoras semanales, visitas y evaluaciones formales.
- Chat en tiempo real (WebSockets), aplicación móvil nativa y emparejamiento con IA.
- Inicio de sesión único con cuentas institucionales (Google o Microsoft).
- Despliegue en producción con alta disponibilidad.

---

## 4. Ciclo de vida del proceso

### 4.1 Flujo principal

```
EMPRESA                     OFICINA DE PRÁCTICAS             ESTUDIANTE
───────                     ────────────────────             ──────────
Solicita registro ───────►  Aprueba la empresa
                            y registra el convenio
                            Habilita al estudiante ───────►  Ve su estado "Habilitado"
                            en la plataforma                 (antes ve "No habilitado" y
                                                             solo puede explorar)
Crea una convocatoria ───►  Aprueba la convocatoria ──────►  La ve en "Mi programa"
                            (se publica también en el muro)  y en el muro
                                                             Se postula (solo si es afín)
Revisa a los postulantes ◄────────────────────────────────── (la postulación llega directo
                                                             a la empresa; la oficina no
                                                             revisa cada postulación)
         │                                                   
         └──── Bitácora de seguimiento compartida (empresa · oficina · estudiante) ────┘
               mensajes + registro de contactos hechos por fuera (llamada, correo, reunión)

Preselecciona y agenda ───────────────────────────────────►  Recibe la notificación
la entrevista
Selecciona ──────────────►  El estudiante habla con la
                            oficina: se verifican en persona
                            la habilitación y los requisitos
                            Legaliza la práctica ─────────►  Queda "En práctica"
                            (fechas, asesor, documento)
                            Cierra la práctica ───────────►  "Práctica finalizada"
```

### 4.2 Estados de la postulación

| Estado | Quién lo asigna | Siguiente estado posible |
|---|---|---|
| Postulado | Estudiante (al postularse) | En revisión, No seleccionado, Retirado |
| En revisión | Empresa u oficina | Preseleccionado, No seleccionado, Retirado |
| Preseleccionado | Empresa u oficina | Entrevista (al programarla), No seleccionado, Retirado |
| Entrevista | Empresa (al agendar) | Seleccionado, No seleccionado, Retirado |
| Seleccionado | Empresa | Legalizado, Retirado |
| No seleccionado | Empresa u oficina (con motivo obligatorio) | — (final) |
| Retirado | Estudiante | — (final) |
| Legalizado | Oficina (exige la verificación de requisitos) | — (final; crea una **Práctica**) |
| Cerrado por sistema | Sistema (el estudiante ya fue ubicado en otra empresa o la convocatoria se canceló) | — (final) |

### 4.3 Estados de los demás objetos

| Objeto | Estados |
|---|---|
| **Empresa** | Pendiente de aprobación → Aliada (convenio vigente) / Rechazada → Convenio vencido → Suspendida |
| **Convocatoria** | Borrador → En revisión → Publicada / Devuelta con observaciones → Cerrada (por fecha, por cupos o manualmente) / Cancelada |
| **Estudiante** | Registrado (No habilitado) → Habilitado (por la oficina) → En búsqueda (tiene postulaciones activas) → Ubicado (práctica legalizada) → En práctica → Práctica finalizada |
| **Práctica** | Legalizada → En curso → Finalizada / Cancelada |
| **Publicación del muro** | Publicada → Oculta (moderada por la oficina) / Eliminada por su autor |

---

## 5. Requerimientos funcionales

Prioridad: **E** = Esencial (obligatorio en el prototipo) · **D** = Deseable · **O** = Opcional

### M1. Acceso y cuentas

| ID | Requerimiento | Actor | Prior. |
|---|---|---|---|
| RF-01 | El estudiante se registra con su correo **`@pascualbravo.edu.co`** y lo verifica con un enlace enviado por correo. | Estudiante | E |
| RF-02 | La empresa envía una **solicitud de registro** con razón social, NIT, sector, contacto y datos del usuario reclutador. La cuenta queda *Pendiente de aprobación*. | Empresa | E |
| RF-03 | El superadministrador crea las cuentas de la oficina de prácticas. Este rol no tiene autorregistro. | Superadmin | E |
| RF-04 | Todos los usuarios inician sesión con correo y contraseña. La sesión se maneja con tokens que expiran. | Todos | E |
| RF-05 | Los usuarios pueden recuperar la contraseña por correo y cambiarla desde su cuenta. | Todos | E |
| RF-06 | En el registro se debe **aceptar la política de tratamiento de datos** (Ley 1581 de 2012). Se guarda la fecha y la versión aceptada. | Estudiante, Empresa | E |
| RF-07 | Cada pantalla y cada endpoint verifican el **rol** y la **pertenencia** del recurso. Por ejemplo, una empresa solo ve sus propias convocatorias y postulantes. | Sistema | E |
| RF-08 | Una empresa puede tener **varios usuarios reclutadores**. | Empresa | O |

### M2. Perfil profesional del estudiante

| ID | Requerimiento | Prior. |
|---|---|---|
| RF-10 | El perfil incluye datos básicos: foto, nombre, programa académico, nivel (técnico, tecnológico o profesional), semestre, ciudad, teléfono, titular profesional y sección "Acerca de mí". | E |
| RF-11 | El estudiante registra **habilidades**, elegidas de un catálogo o agregadas libremente, e **idiomas** con su nivel. | E |
| RF-12 | El estudiante registra experiencia, proyectos académicos, certificaciones y enlaces (LinkedIn, GitHub, portafolio). | E |
| RF-13 | El estudiante carga su **hoja de vida en PDF** (máximo 5 MB). | E |
| RF-14 | El estudiante indica su **disponibilidad**: fecha posible de inicio, jornada y modalidad preferida (presencial, remota o híbrida). | E |
| RF-15 | El perfil muestra un **indicador de completitud** con sugerencias para completarlo. | D |
| RF-16 | Las empresas ven una **vista profesional** del perfil, sin datos sensibles como el número de documento. | E |
| RF-17 | El estudiante puede activar o desactivar la opción **"Abierto a oportunidades"** para aparecer en la búsqueda de talento de las empresas. | D |
| RF-18 | El estudiante ve siempre su **estado de habilitación** (*No habilitado* o *Habilitado*, con el periodo académico y la fecha) en su perfil y en el menú principal. Si no está habilitado, puede explorar convocatorias, empresas y el muro, pero el botón de postularse aparece deshabilitado con el mensaje "Aún no estás habilitado para prácticas. Acércate a la oficina de prácticas". | E |

### M3. Empresas aliadas y convenios

| ID | Requerimiento | Prior. |
|---|---|---|
| RF-20 | El perfil de empresa incluye logo, razón social, NIT, sector, tamaño, descripción, sitio web, ciudad o sede y datos de contacto. | E |
| RF-21 | Existe un **directorio de empresas aliadas** con filtros por sector y ciudad, y con el número de convocatorias activas de cada empresa. | E |
| RF-22 | Cada empresa tiene una **página** que muestra su información, sus convocatorias abiertas y sus publicaciones en el muro. | E |
| RF-23 | El estudiante puede **seguir** una empresa y recibir avisos cuando publique nuevas convocatorias. | D |
| RF-24 | La oficina puede **crear una empresa directamente**, aunque la empresa no tenga cuenta, para publicar convocatorias que llegaron por otros canales. | E |
| RF-25 | La oficina registra el **convenio** de cada empresa: número, fecha de inicio, fecha de vencimiento y documento PDF. Sin un convenio vigente, la empresa no puede publicar convocatorias. | E |
| RF-26 | La plataforma alerta a la oficina cuando un convenio vence en los próximos 30 días y cambia la empresa a *Convenio vencido* al llegar la fecha. | D |

### M4. Convocatorias

| ID | Requerimiento | Prior. |
|---|---|---|
| RF-30 | La empresa crea una convocatoria con estos campos: título, descripción, funciones, **programas afines** (al menos uno), nivel de formación, habilidades requeridas, modalidad, ciudad, tipo de vinculación (contrato de aprendizaje, práctica, pasantía o vínculo laboral), apoyo económico, número de cupos, fecha de inicio, duración y fecha de cierre. | E |
| RF-31 | La oficina puede crear convocatorias **en nombre de** cualquier empresa aliada. | E |
| RF-32 | Las convocatorias de las empresas pasan por **aprobación** de la oficina, que puede publicarlas o devolverlas con observaciones. | E |
| RF-33 | La empresa puede editar (con nueva revisión si ya estaba publicada), cerrar manualmente o duplicar una convocatoria. | E |
| RF-34 | La convocatoria se **cierra automáticamente** cuando llega la fecha de cierre o se cubren todos los cupos. | E |
| RF-35 | Al publicarse, la convocatoria **aparece automáticamente en el muro** (ver M10). | E |
| RF-36 | La empresa puede agregar **preguntas de filtro** que el estudiante responde al postularse. | O |

### M5. Exploración, búsqueda y recomendación

| ID | Requerimiento | Prior. |
|---|---|---|
| RF-40 | El listado de convocatorias abre por defecto **filtrado por el programa del estudiante** ("Mi programa"). Con la opción **"Ver todas"** el estudiante puede explorar las de otros programas. | E |
| RF-41 | Hay **búsqueda por texto** y **filtros** por programa, nivel, modalidad, ciudad, empresa, tipo de vinculación, si tiene apoyo económico y fecha de publicación. El listado es paginado. | E |
| RF-42 | La sección **"Recomendadas para ti"** ordena las convocatorias de su programa por un **índice de afinidad** calculado con las habilidades, la modalidad y la disponibilidad del estudiante. | E |
| RF-43 | En las convocatorias de otros programas, el botón de postularse aparece deshabilitado con el mensaje "Esta convocatoria no incluye tu programa". | E |
| RF-44 | El estudiante puede **guardar** convocatorias para verlas después. | D |
| RF-45 | La empresa puede **buscar talento** entre los estudiantes "Abiertos a oportunidades", filtrando por programa y habilidades, e **invitarlos** a postularse. | D |

### M6. Postulaciones y seguimiento

| ID | Requerimiento | Prior. |
|---|---|---|
| RF-50 | El estudiante se **postula** con su hoja de vida y un mensaje de presentación opcional. Antes de aceptar la postulación se validan las reglas RN-04 a RN-06. No hay límite de postulaciones. | E |
| RF-51 | En **"Mis postulaciones"** el estudiante ve el estado de cada postulación y una línea de tiempo con su historial. | E |
| RF-52 | El estudiante puede **retirar** una postulación mientras no esté legalizada. | E |
| RF-53 | La empresa ve los **postulantes de cada convocatoria**, con su índice de afinidad, el perfil completo y la hoja de vida descargable. | E |
| RF-54 | La empresa **cambia el estado** de cada postulación y puede agregar un comentario. Al marcar *No seleccionado*, el **motivo es obligatorio** y el estudiante lo puede ver. | E |
| RF-55 | La empresa **programa entrevistas** indicando fecha, hora, modalidad y lugar o enlace. El estudiante recibe una notificación. | E |
| RF-56 | Cada cambio de estado queda en un **historial auditable** con quién lo hizo, cuándo y el comentario. | E |
| RF-57 | Cada postulación tiene una **bitácora de seguimiento** compartida por la empresa, el estudiante y la oficina. En ella se pueden escribir **mensajes** y registrar **contactos hechos por fuera** de la plataforma (llamada, correo, WhatsApp, reunión presencial) con fecha y una nota. | E |
| RF-58 | La empresa ve el correo y el teléfono de sus postulantes. Desde *Preseleccionado*, el estudiante ve los datos de contacto de la empresa. Así pueden comunicarse también por fuera de la plataforma. | E |
| RF-59 | La oficina puede escribir **notas internas** en la bitácora, visibles solo para la oficina. | D |

### M7. Gestión administrativa (oficina de prácticas)

| ID | Requerimiento | Prior. |
|---|---|---|
| RF-60 | La oficina **aprueba, rechaza o suspende** empresas. | E |
| RF-61 | La oficina tiene una **bandeja de convocatorias por revisar** donde las aprueba o las devuelve con observaciones. | E |
| RF-62 | La oficina **habilita estudiantes en la plataforma**. Los busca por nombre, correo o programa, y al marcarlos como *Habilitado* indica el periodo académico y una observación opcional. También puede **deshabilitarlos** indicando el motivo. Cada cambio queda en el historial y le llega una notificación al estudiante. | E |
| RF-62a | Cuando la empresa selecciona a un estudiante, este habla con la oficina. La oficina registra la **verificación de requisitos**: fecha, funcionario que la hizo, resultado (cumple / no cumple) y observación. Esta verificación es obligatoria para legalizar. La oficina **no revisa cada postulación**, solo interviene en este punto o cuando lo considere necesario (RF-63). | E |
| RF-63 | Existe una **vista global de postulaciones** con filtros por programa, empresa, estado y periodo. Desde ella la oficina puede intervenir en cualquier proceso y escribir en su bitácora. | E |
| RF-64 | La oficina **legaliza la práctica** de una postulación seleccionada registrando fechas de inicio y fin, tipo de vinculación, asesor, tutor de la empresa y documento soporte. Al hacerlo, el estudiante queda como *Ubicado* y sus demás postulaciones activas se cierran. | E |
| RF-65 | La oficina **finaliza la práctica** con una observación de cierre. | E |
| RF-66 | La oficina ve **alertas de seguimiento**: estudiantes habilitados sin postulaciones en X días, postulaciones sin respuesta de la empresa en X días, estudiantes sin ubicar Y días después de su primera postulación y convocatorias sin postulantes. Los valores de X y Y son configurables. | E |
| RF-67 | La oficina registra **notas de asesoría** en el perfil de cada estudiante. | D |
| RF-68 | El superadministrador gestiona los **catálogos**: facultades, programas, habilidades, sectores, ciudades y periodos académicos. | E |
| RF-69 | Se pueden **gestionar usuarios**: buscarlos, activarlos o desactivarlos y restablecer su acceso. | E |
| RF-70 | La oficina puede **habilitar a varios estudiantes a la vez**, seleccionándolos en una lista filtrada por programa. | D |

### M8. Indicadores y reportes

| ID | Requerimiento | Prior. |
|---|---|---|
| RF-80 | La oficina tiene un **tablero de indicadores** con: estudiantes registrados, habilitados, en búsqueda y ubicados, y % de ubicación de los habilitados; tiempo promedio desde la habilitación hasta la ubicación; convocatorias activas; cupos ofertados frente a postulantes; empresas aliadas con convenio vigente. Se puede ver por programa y por periodo. | E |
| RF-81 | Los listados y reportes se pueden **exportar a CSV**. | E |
| RF-82 | La empresa tiene un **resumen** de sus convocatorias con el número de postulantes en cada estado. | D |

### M9. Notificaciones

| ID | Requerimiento | Prior. |
|---|---|---|
| RF-90 | Hay **notificaciones dentro de la plataforma** (campana) que se marcan como leídas o no leídas. | E |
| RF-91 | Los eventos clave también se notifican **por correo**. En el prototipo, los correos se capturan localmente con Mailpit. | E |

**Eventos que generan notificación:**

| Evento | Quién recibe la notificación |
|---|---|
| Nueva empresa solicita registro | Oficina |
| Empresa aprobada o rechazada | Empresa |
| Convenio próximo a vencer | Oficina |
| Convocatoria enviada a revisión | Oficina |
| Convocatoria publicada o devuelta | Empresa |
| Estudiante habilitado o deshabilitado | Estudiante |
| Nueva convocatoria de su programa o de una empresa seguida | Estudiante |
| Nueva postulación | Empresa |
| Cambio de estado de la postulación o entrevista agendada | Estudiante |
| Nuevo mensaje o registro en la bitácora de seguimiento | Los demás participantes de la postulación |
| Postulante seleccionado | Oficina |
| Práctica legalizada | Estudiante y empresa |
| Convocatoria cerrada | Empresa |
| Publicación del muro dirigida a su programa | Estudiante (solo dentro de la plataforma) |

### M10. Muro de publicaciones

| ID | Requerimiento | Prior. |
|---|---|---|
| RF-100 | Todos los usuarios con sesión ven un **muro** de publicaciones en orden cronológico, con filtros por tipo y por programa. Por defecto, el estudiante ve primero lo dirigido a su programa. | E |
| RF-101 | Hay cinco **tipos de publicación**: **Convocatoria** (se crea sola al publicarse una convocatoria y lleva a postularse), **Oferta externa / bolsa de empleo** (oferta de una empresa que no necesariamente es aliada o de otra bolsa de empleo, con enlace a la fuente original), **Evento** (ferias, charlas, talleres, con fecha y lugar), **Noticia** y **Comunicado de la oficina**. | E |
| RF-102 | **Quién publica:** la oficina publica cualquier tipo; las empresas aliadas publican noticias y eventos. | E |
| RF-103 | Cada publicación tiene texto, una imagen y un enlace opcionales, y los **programas destinatarios** (todos o algunos). | E |
| RF-104 | Las ofertas externas se marcan claramente como **externas**: la postulación se hace en la fuente original y no dentro de PB Conecta. | E |
| RF-105 | La oficina **modera** el muro: puede ocultar publicaciones y comentarios. | E |
| RF-106 | Los usuarios pueden marcar **"Me interesa"** y **comentar** las publicaciones. | D |
| RF-107 | Los usuarios pueden **guardar** publicaciones. | D |
| RF-108 | Los estudiantes pueden publicar logros o proyectos, y cualquier usuario puede **reportar** una publicación inapropiada. | O |

---

## 6. Reglas de negocio

| ID | Regla |
|---|---|
| RN-01 | Los estudiantes y la oficina solo pueden registrarse con correos **`@pascualbravo.edu.co`**. El dominio es configurable. |
| RN-02 | Una empresa solo puede publicar convocatorias y ver perfiles de estudiantes cuando está *Aliada*, es decir, aprobada y **con convenio vigente**. Si el convenio vence, las convocatorias ya publicadas siguen abiertas hasta su fecha de cierre, pero la empresa no puede crear nuevas. |
| RN-03 | Toda convocatoria creada por una empresa requiere aprobación de la oficina antes de publicarse. Las que crea la oficina se publican directamente. |
| RN-04 | Para postularse, el estudiante debe estar **habilitado por la oficina** (RF-62), tener su hoja de vida cargada y el perfil mínimo completo (programa, semestre, teléfono y al menos una habilidad). |
| RN-05 | El estudiante **solo puede postularse a convocatorias que incluyan su programa** entre los programas afines. Puede ver todas las demás. |
| RN-06 | Un estudiante no puede postularse dos veces a la misma convocatoria. **No hay límite** de postulaciones activas. |
| RN-07 | Para legalizar una práctica, la oficina debe haber registrado una **verificación de requisitos** con resultado *Cumple*. |
| RN-08 | Al legalizar una práctica, las demás postulaciones activas del estudiante pasan a *Cerrado por sistema* y el estudiante no puede postularse de nuevo hasta finalizar o cancelar esa práctica. |
| RN-09 | Una convocatoria se cierra automáticamente al llegar a su fecha de cierre o al cubrirse todos sus cupos legalizados. |
| RN-10 | La empresa solo ve a los postulantes de sus propias convocatorias y a los estudiantes "Abiertos a oportunidades". La hoja de vida solo la ven la empresa de la postulación y la oficina. |
| RN-11 | El motivo es obligatorio para marcar a alguien como *No seleccionado*, para devolver una convocatoria, para rechazar una empresa y para ocultar una publicación. |
| RN-12 | Todo cambio de estado y todo registro en la bitácora de seguimiento queda guardado con el usuario, la fecha y hora y el texto, y no se puede editar ni borrar. |
| RN-13 | Las transiciones de estado solo pueden seguir el orden definido en la sección 4.2. |
| RN-14 | Las ofertas externas del muro no generan postulaciones dentro de la plataforma ni entran en los indicadores de ubicación. |
| RN-15 | Solo la oficina puede cambiar el estado de habilitación de un estudiante. Si deshabilita a un estudiante, sus postulaciones activas no se cierran automáticamente, pero no puede crear nuevas. |

---

## 7. Requerimientos no funcionales

| ID | Categoría | Requerimiento | Criterio de aceptación |
|---|---|---|---|
| RNF-01 | Licenciamiento | Todo el stack es **libre y gratuito**. | No se usan licencias de pago ni servicios en la nube pagos. |
| RNF-02 | Portabilidad | Todo el entorno se levanta con **Docker Compose**. | `docker compose up` deja la aplicación funcionando con datos de demostración. La configuración va en un archivo `.env`. |
| RNF-03 | Seguridad | Las contraseñas se guardan con hash (PBKDF2 o Argon2) y deben cumplir una política mínima. | Mínimo 8 caracteres y validadores de Django. |
| RNF-04 | Seguridad | La autenticación usa JWT con un token de acceso de corta duración y un token de renovación. | Acceso: 30 min. Renovación: 7 días. |
| RNF-05 | Seguridad | Se aplica **autorización por objeto** en toda la API. | Hay pruebas que verifican que la empresa A no puede leer datos de la empresa B. |
| RNF-06 | Seguridad | Los archivos se validan por tipo y tamaño, se guardan con nombres aleatorios y la hoja de vida se sirve solo después de comprobar permisos. | Solo PDF, JPG y PNG. Máximo 5 MB. |
| RNF-07 | Seguridad | Se cubren los controles básicos de OWASP: ORM para evitar inyección SQL, escapado contra XSS, CORS restringido y límite de intentos de inicio de sesión. | Máximo 5 intentos fallidos por minuto. |
| RNF-08 | Legal | Se cumple la **Ley 1581 de 2012** (Habeas Data). | Hay consentimiento explícito y el usuario puede actualizar sus datos o solicitar la eliminación de su cuenta. |
| RNF-09 | Rendimiento | Los listados y el muro son paginados y la base de datos tiene índices. | Respuesta de la API menor a 1,5 s (p95) con 50 usuarios simultáneos y 20 elementos por página. |
| RNF-10 | Usabilidad | La interfaz es **responsive**, está en español y muestra mensajes de error claros. | Funciona desde 360 px de ancho. El estudiante se postula en 3 clics o menos desde la oferta. |
| RNF-11 | Accesibilidad | Se cumplen los criterios básicos de WCAG 2.1 AA. | Contraste AA, navegación con teclado y campos con etiqueta. |
| RNF-12 | Identidad | La interfaz usa los colores y el logo institucionales del Pascual Bravo. | Paleta definida en un solo archivo de tema. |
| RNF-13 | Mantenibilidad | La API REST está documentada con **OpenAPI/Swagger** y el código está organizado por módulos. | Swagger disponible en `/api/docs`. |
| RNF-14 | Calidad | Hay pruebas automatizadas de las reglas de negocio y de los permisos. | Las pruebas cubren RN-02 a RN-14 y RNF-05. |
| RNF-15 | Demostración | Hay un **script de datos de ejemplo** con programas reales, empresas con convenio, convocatorias, publicaciones del muro y estudiantes ficticios. | Un usuario de prueba por rol. |
| RNF-16 | Respaldo | Hay un script de copia de seguridad y restauración de PostgreSQL. | Usa `pg_dump` y `pg_restore`. |
| RNF-17 | Localización | La zona horaria es America/Bogota, el idioma es-CO y las fechas usan formato dd/mm/aaaa. | — |
| RNF-18 | Compatibilidad | Funciona en Chrome, Edge y Firefox. | Últimas 2 versiones de cada navegador. |

---

## 8. Restricciones y stack tecnológico propuesto

| Capa | Tecnología | Justificación |
|---|---|---|
| Frontend | **React 19 + Vite + TypeScript**, React Router, TanStack Query, MUI | Ecosistema maduro y gratuito. MUI ofrece componentes accesibles y un tema fácil de personalizar. |
| Backend | **Python 3.12 + Django 5.2 LTS + Django REST Framework** | El admin de Django, el ORM y las migraciones aceleran el prototipo. Al ser LTS tiene soporte largo. |
| Autenticación | djangorestframework-simplejwt | Implementa JWT de forma estándar. |
| Documentación de la API | drf-spectacular | Genera OpenAPI y Swagger automáticamente. |
| Base de datos | **PostgreSQL 17** | Es relacional y robusta, y trae **búsqueda de texto completo en español** nativa para buscar convocatorias y publicaciones sin otro motor. |
| Archivos | Volumen de Docker servido a través de Django y Nginx | Guarda hojas de vida, logos, convenios e imágenes del muro sin servicios externos. |
| Correo (desarrollo) | **Mailpit** | Captura todos los correos en una bandeja web local, sin enviar nada real. |
| Proxy web | **Nginx** | Sirve el frontend compilado y redirige `/api` al backend. |
| Tareas programadas | Contenedor ligero que ejecuta comandos de Django periódicamente | Se encarga del cierre automático, el vencimiento de convenios y las alertas de seguimiento sin añadir Celery ni Redis al prototipo. |
| Orquestación | **Docker + Docker Compose** | El entorno es reproducible en cualquier equipo del equipo con un solo comando. |
| Control de versiones | Git + GitHub o GitLab (gratuito) | Permite el trabajo colaborativo de los 5 integrantes. |

---

## 9. Modelo de dominio preliminar

Estas son las entidades principales. Su detalle se definirá en el diseño de la base de datos.

- **Usuario** (correo, rol, estado) → **ConsentimientoDatos**
- **Facultad** → **Programa** (nivel de formación)
- **PeriodoAcademico**
- **PerfilEstudiante** (usuario, programa, semestre, estado, disponibilidad, HV) → **Habilidad** (N:M), **Idioma**, **Experiencia**, **Proyecto**, **Enlace**
- **Habilitacion** (estudiante, periodo, estado habilitado / deshabilitado, funcionario, fecha, observación o motivo); se guarda el historial completo
- **VerificacionRequisitos** (estudiante, funcionario, fecha, resultado, observación)
- **Empresa** (NIT, sector, estado) → **UsuarioEmpresa**, **Convenio** (vigencia, documento)
- **Convocatoria** (empresa, estado, cupos, fechas) → **Programa** (N:M, programas afines), **Habilidad** (N:M)
- **Postulacion** (estudiante, convocatoria, estado, afinidad) → **HistorialEstado**, **Entrevista**, **EntradaSeguimiento** (tipo: mensaje / contacto externo / nota interna; canal; autor; fecha)
- **Practica** (postulación legalizada, fechas, asesor, tutor, documento, estado)
- **NotaAsesoria** (estudiante, autor de la oficina)
- **Publicacion** (tipo, autor, texto, imagen, enlace, programas destinatarios, estado, convocatoria opcional) → **Comentario**, **Reaccion**
- **Notificacion**, **ConvocatoriaGuardada**, **PublicacionGuardada**, **EmpresaSeguida**

---

## 10. Escenarios de aceptación del prototipo

El prototipo se considera **funcional** si se pueden demostrar de principio a fin los siguientes escenarios.

1. **Alta de una empresa aliada:** una empresa solicita su registro → la oficina recibe la notificación, la aprueba y registra su convenio vigente → la empresa inicia sesión y completa su perfil.
2. **Publicación de una convocatoria:** la empresa crea una convocatoria para "Tecnología en Desarrollo de Software" → la oficina la devuelve con una observación → la empresa la corrige → la oficina la aprueba → la convocatoria aparece publicada y en el muro.
3. **Habilitación y postulación por programa:** un estudiante de Software se registra con su correo `@pascualbravo.edu.co` → ve su estado *No habilitado*: puede explorar convocatorias y el muro, pero no postularse → la oficina lo habilita y le llega la notificación → completa su perfil y carga su HV → ve la convocatoria en "Mi programa" y en "Recomendadas para ti" → se postula. Si intenta postularse a una convocatoria solo de Diseño, la plataforma no lo permite.
4. **Selección con seguimiento:** la empresa revisa al postulante → lo preselecciona y registra en la bitácora "Llamada telefónica: se acordó entrevista" → agenda la entrevista (el correo llega a Mailpit) → lo selecciona. Otro postulante queda como *No seleccionado* con un motivo que él puede ver.
5. **Verificación y legalización:** el estudiante seleccionado habla con la oficina, que confirma sus requisitos, registra la verificación (*Cumple*) y legaliza la práctica → las demás postulaciones del estudiante se cierran → el tablero muestra un estudiante más ubicado → la oficina finaliza la práctica.
6. **Muro:** la oficina publica una oferta externa de una bolsa de empleo dirigida a Software → el estudiante la ve primero en su muro, marca "Me interesa" y el enlace lo lleva a la fuente original.
7. **Seguridad:** la empresa B intenta abrir la postulación de la empresa A por la URL o la API y recibe un error 403 o 404. Una empresa con convenio vencido no puede crear convocatorias.

---

## 11. Registro de decisiones

| # | Pregunta | Decisión |
|---|---|---|
| D1 | ¿Las convocatorias de las empresas requieren aprobación? | **Sí.** Además, solo publican las empresas aliadas con convenio vigente (RN-02, RN-03). |
| D2 | ¿El estudiante puede postularse a convocatorias de otros programas? | **Puede verlas todas, pero solo se postula a las de su programa.** La vista por defecto es "Mi programa" (RF-40, RF-43, RN-05). |
| D3 | ¿Hay límite de postulaciones activas? | **No.** El estudiante se postula a las que quiera (RN-06). |
| D4 | ¿Cómo se habilita al estudiante? | **La oficina lo habilita dentro de la plataforma, estudiante por estudiante y sin CSV.** El estudiante siempre ve su estado: si no está habilitado puede explorar, pero no postularse. Una vez habilitado, aplica libremente y las postulaciones llegan directo a la empresa, porque **la oficina no revisa cada postulación**. Cuando pasa las entrevistas y es seleccionado, habla con la oficina, que verifica en persona y legaliza (RF-18, RF-62, RF-62a, RN-04, RN-07, RN-15). |
| D5 | ¿Cómo es el contacto entre empresa y estudiante? | **Bitácora de seguimiento dentro de cada postulación**, y también se permite el contacto por fuera; esos contactos se pueden registrar en la bitácora (RF-57, RF-58). |
| D6 | ¿Cuál es el dominio institucional? | **`@pascualbravo.edu.co`** (RN-01). |
| D7 | ¿Se incluye un muro de publicaciones? | **Sí.** Incluye convocatorias, ofertas externas y de bolsas de empleo, eventos, noticias y comunicados (M10). |

---

## 12. Próximos pasos

1. Validar esta versión del documento.
2. Diseñar la **arquitectura** (diagrama de contenedores) y el **modelo entidad-relación** en PostgreSQL.
3. Definir los **endpoints de la API** y el **mapa de pantallas** por rol.
4. Montar el repositorio: `docker-compose.yml`, backend Django, frontend React, Nginx y Mailpit.
5. Implementar por módulos en este orden: M1 → M3 → M4 → M2 → M5 → M6 → M7 → M10 → M9 → M8.
6. Cargar los datos de demostración y verificar los escenarios de la sección 10.
