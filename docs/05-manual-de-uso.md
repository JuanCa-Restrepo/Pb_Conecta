# PB Conecta · Manual de uso

Guía para usar la plataforma según el rol: estudiante, empresa aliada, oficina de prácticas y superadministrador.

---

## 1. Acceso

### 1.1 Direcciones (entorno local)

| Qué | Dirección |
|---|---|
| Aplicación | http://localhost:8080 |
| Panel del superadministrador | http://localhost:8080/admin/ |
| Bandeja de correos de prueba (Mailpit) | http://localhost:8025 |
| Documentación de la API | http://localhost:8080/api/docs/ |

Para levantar el proyecto, ver el [README](../README.md#cómo-levantar-el-proyecto). Los usuarios de demostración están en la sección [Usuarios de demostración](../README.md#usuarios-de-demostración) del README.

### 1.2 Crear una cuenta

- **Estudiante:** en *Registrarse como estudiante*.
  - Usa el correo institucional **@pascualbravo.edu.co**; otros dominios no se aceptan.
  - Elige tu programa.
  - Llega un correo con un enlace para **verificar la cuenta**. En local ese correo aparece en Mailpit.
- **Empresa:** en *Registrarse como empresa*, con los datos de la empresa y del contacto.
  - La cuenta queda **pendiente** hasta que la oficina de prácticas la apruebe.
  - Solo publica convocatorias cuando es **aliada con convenio vigente**.
- **Oficina de prácticas:** no se registra. El superadministrador crea sus cuentas desde `/admin`.

### 1.3 Contraseña

- **¿Olvidaste tu contraseña?** En *Iniciar sesión*. Llega un enlace al correo, válido por 2 horas.
- **Cambiar contraseña:** con la sesión iniciada, desde el avatar arriba a la derecha → *Cambiar contraseña*.
- Por seguridad, después de 5 intentos fallidos en un minuto el inicio de sesión se bloquea un momento.

### 1.4 Elementos comunes

- **Campana:** notificaciones dentro de la plataforma. Las más importantes también llegan por correo.
- **Menú lateral:** cambia según el rol. En el celular se abre con el botón ☰.
- **Avatar:** datos de la cuenta, cambio de contraseña y cierre de sesión.
- **Directorio de empresas aliadas:** es público, se ve incluso sin iniciar sesión.

---

## 2. Estudiante

Menú: **Inicio · Muro · Convocatorias · Mis postulaciones · Empresas · Mi perfil**.

### 2.1 Estado de habilitación

En **Inicio** siempre aparece el estado del estudiante frente a las prácticas:

| Estado | Qué significa |
|---|---|
| No habilitado | Puedes ver todo, pero aún no postularte. La oficina te habilita cuando cumples los requisitos académicos |
| Habilitado | Ya puedes postularte a las convocatorias de tu programa |
| Ubicado | Tienes una práctica legalizada que aún no inicia. No puedes postularte a otras |
| En práctica | Tu práctica está en curso |
| Práctica finalizada | Terminaste tu práctica |

### 2.2 Mi perfil

Es tu hoja de vida dentro de la plataforma, y la ven las empresas a las que te postulas. Incluye:
- datos personales y académicos;
- **hoja de vida en PDF**;
- habilidades con nivel;
- experiencia, proyectos, idiomas, certificaciones y enlaces (LinkedIn, GitHub, portafolio).

Una barra muestra qué tan **completo** está el perfil.

**Mínimo para poder postularte:**
- estar habilitado;
- hoja de vida en PDF;
- semestre;
- teléfono;
- al menos una habilidad.

**«Abierto a oportunidades»:** si lo activas, las empresas aliadas te pueden encontrar en su búsqueda de talento e invitarte a postularte. Tu correo y tu teléfono no se muestran en esa búsqueda.

### 2.3 Convocatorias

- **Pestañas:** *Mi programa*, *Todas* y *Guardadas*. Puedes ver todas las convocatorias, pero **solo te postulas a las que incluyen tu programa**.
- **Búsqueda y filtros:** por texto, modalidad, ciudad y otros criterios.
- **Afinidad (0–100):** indica qué tanto encaja la convocatoria contigo. Pesa:
  - el programa (50);
  - las habilidades (35);
  - la modalidad (10);
  - la disponibilidad (5).
- **Recomendadas:** aparecen en Inicio, ordenadas por afinidad.
- **Guardar:** marca una convocatoria para revisarla después.
- **Postularme:** si algo lo impide, el botón explica por qué. Por ejemplo, perfil incompleto, otro programa o convocatoria cerrada. No hay límite de postulaciones.

### 2.4 Mis postulaciones

Cada postulación muestra su estado y una **bitácora de seguimiento**:

```
Postulado → En revisión → Preseleccionado → Entrevista → Seleccionado → Legalizado
                    (en cualquier punto: No seleccionado)
```

- **Desde «Preseleccionado»** ves los datos de contacto de la empresa. El contacto también puede darse por fuera de la plataforma.
- **Entrevista:** la empresa la programa con fecha, modalidad y lugar o enlace. Te llega una notificación.
- **Bitácora:** puedes escribir mensajes o registrar un contacto que ocurrió por fuera (llamada, correo, WhatsApp…).
- **Retirarme:** puedes retirar una postulación mientras siga activa.
- **Cerrado por sistema:** cuando legalizas una práctica, tus demás postulaciones activas se cierran solas.

### 2.5 Empresas y muro

- **Empresas:** directorio de empresas aliadas, con la página de cada una y sus convocatorias. Puedes **seguir** una empresa para recibir aviso cuando publique.
- **Muro:** convocatorias, ofertas externas y bolsas de empleo, eventos, noticias y comunicados de la oficina. Puedes marcar **«Me interesa»**, comentar y guardar publicaciones.

---

## 3. Empresa aliada

Menú: **Inicio · Muro · Mis convocatorias · Buscar talento · Perfil de la empresa**.

### 3.1 Perfil de la empresa

Datos, descripción, sector, sitio web y **logo**. Esto es lo que se ve en el directorio público y en la página de la empresa.

### 3.2 Mis convocatorias

```
Borrador → En revisión → Publicada → Cerrada
               ↓
           Devuelta (con observaciones de la oficina) → se corrige y se reenvía
```

1. **Crear:** cargo, descripción, programas afines (al menos uno), habilidades, modalidad, ciudad, cupos, fecha de cierre y demás datos.
2. **Enviar a revisión.** La oficina la aprueba y se publica, o la devuelve con observaciones.
3. **Al publicarse:**
   - aparece en el muro;
   - se avisa a los estudiantes habilitados de los programas afines y a los seguidores de la empresa.
4. **Editar una publicada:** vuelve a revisión.
5. **Cerrar:** se cierra a mano o sola, cuando llega la fecha de cierre o cuando se completan los cupos legalizados.
6. **Duplicar:** crea un borrador nuevo a partir de una existente.

Solo se puede publicar si la empresa es **aliada con convenio vigente**.

### 3.3 Postulantes

Dentro de cada convocatoria está la lista de postulantes. Cada uno muestra su perfil, su hoja de vida y su afinidad.

| Acción | Cuándo |
|---|---|
| Pasar a *En revisión* | Desde *Postulado* |
| *Preseleccionar* | Desde *En revisión* |
| **Programar entrevista** | Desde *Preseleccionado* (pasa a *Entrevista*) |
| *Seleccionar* | Desde *Entrevista* |
| *No seleccionado* | En cualquier punto antes de *Seleccionado* |

La bitácora permite mensajes y el registro de contactos externos. Cuando seleccionas a alguien, **la oficina de prácticas** verifica sus requisitos con el estudiante y **legaliza** la práctica.

### 3.4 Buscar talento

Búsqueda de estudiantes que activaron **«Abierto a oportunidades»**, con filtros por programa, habilidades y otros criterios. Con **Invitar** el estudiante recibe una notificación para postularse a una de tus convocatorias.

### 3.5 Inicio

Resumen por convocatoria: postulantes por etapa y estado de cada proceso.

---

## 4. Oficina de prácticas

Menú: **Indicadores · Alertas de seguimiento · Estudiantes y habilitación · Empresas y convenios · Convocatorias · Postulaciones · Prácticas · Muro**.

### 4.1 Indicadores

Tablero con:
- ubicación de estudiantes;
- embudo de postulaciones;
- tendencia en el tiempo;
- resultados por programa.

Se filtra por **periodo** y **programa**, y se **exporta a CSV** para abrirlo en Excel.

### 4.2 Alertas de seguimiento

Casos que necesitan atención. Se calculan al momento:
- seleccionados pendientes de verificación y legalización;
- estudiantes habilitados que no se han postulado;
- postulaciones sin respuesta de la empresa;
- estudiantes sin ubicar después de un tiempo;
- convocatorias publicadas sin postulantes;
- convenios próximos a vencer.

Los días de cada alerta se ajustan en `/admin` → *Parámetros*. Una tarea diaria también envía el resumen de alertas.

### 4.3 Estudiantes y habilitación

- Busca y filtra estudiantes por programa y estado.
- **Habilitar**, uno por uno o **varios a la vez**, con observación opcional. El estudiante recibe la notificación y ve su nuevo estado en Inicio.
- **Deshabilitar**, con motivo obligatorio.
- **Seguimiento:** historial de habilitaciones y **notas de asesoría** de cada estudiante.

### 4.4 Empresas y convenios

- **Solicitudes de empresas:** **aprobar** o **rechazar** con motivo. **Suspender** o **reactivar** empresas aliadas.
- **Registrar convenio:** fechas de inicio y fin, y el PDF del convenio, que es un archivo protegido.
- **Registrar empresa** directamente desde la oficina.
- Cuando un convenio vence, la empresa pasa a *Convenio vencido* y deja de poder publicar. Una tarea diaria lo revisa.

### 4.5 Convocatorias

- **En revisión:** **aprobar** (se publica) o **devolver** con observaciones.
- Puede crear convocatorias propias y publicarlas directamente.
- Si edita una convocatoria publicada, se vuelve a publicar sin pasar por revisión.

### 4.6 Postulaciones y legalización

La oficina **no revisa cada postulación**. Ve todas las postulaciones y actúa cuando la empresa **selecciona** a un estudiante:

1. **Verificar requisitos:** habla con el estudiante y registra **Cumple** o **No cumple**, con observación.
2. **Legalizar:** solo si *Cumple*. Registra:
   - fechas de inicio y fin;
   - tipo de vinculación;
   - asesor;
   - tutor de la empresa;
   - documento de soporte (opcional).

Al legalizar:
- el estudiante pasa a *Ubicado*;
- sus demás postulaciones se cierran;
- si se completan los cupos, la convocatoria se cierra.

En la bitácora la oficina también puede escribir **notas internas**, que el estudiante y la empresa no ven.

### 4.7 Prácticas

Pestañas **Por iniciar · En curso · Finalizadas · Canceladas**.

- La práctica pasa a **En curso** sola en su fecha de inicio, por una tarea diaria.
- **Finalizar:** con observación. El estudiante pasa a *Práctica finalizada*.
- **Cancelar:** con motivo. El estudiante vuelve a quedar habilitado para buscar otra práctica.

### 4.8 Muro

Publica **ofertas externas o bolsas de empleo, eventos, noticias y comunicados**. Puede dirigirlos a programas específicos. También **modera**: oculta o vuelve a mostrar publicaciones de otros.

---

## 5. Superadministrador

Entra por http://localhost:8080/admin/ (panel de Django). Ahí gestiona:

- **Cuentas:** crea los usuarios de la oficina de prácticas y administra cualquier cuenta.
- **Catálogos:**
  - programas académicos (verificarlos contra la oferta oficial);
  - habilidades, sectores, ciudades;
  - periodos académicos.
- **Parámetros:** días de cada alerta y avisos de vencimiento de convenios.

El superadministrador también puede entrar a la aplicación, donde ve el menú de la oficina.

---

## 6. Tareas automáticas

El contenedor `scheduler` ejecuta estas tareas cada día:

| Tarea | Qué hace |
|---|---|
| Cierre de convocatorias | Cierra las que llegaron a su fecha de cierre |
| Revisión de convenios | Marca convenios vencidos y avisa de los que están por vencer |
| Inicio de prácticas | Pasa a *En curso* las prácticas legalizadas al llegar su fecha de inicio |
| Alertas | Envía a la oficina el resumen diario de alertas |

---

## 7. Preguntas frecuentes

**No me llega el correo de verificación.** En local los correos no salen a internet: revisa http://localhost:8025. En producción, revisa la carpeta de spam.

**No puedo postularme.** El botón explica el motivo. Los más comunes:
- no estás habilitado;
- falta la hoja de vida, el semestre, el teléfono o alguna habilidad;
- la convocatoria no es de tu programa;
- ya tienes una práctica legalizada.

**La empresa no puede publicar.** Debe estar aprobada como aliada y tener un convenio vigente registrado por la oficina.

**`/admin` no abre.** Escribe la dirección completa con la barra final: `http://localhost:8080/admin/`. Si el navegador guardó una redirección vieja, prueba en una ventana de incógnito.

**Quiero empezar de cero con los datos de demostración.** Esto borra todo lo que se haya creado:
```bash
docker compose down -v
docker compose up -d
```
