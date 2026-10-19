import DescriptionIcon from "@mui/icons-material/Description";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import {
  Alert, Box, Button, Card, CardContent, CardHeader, Chip, FormControlLabel, LinearProgress, MenuItem, Stack, Switch,
  TextField, Typography,
} from "@mui/material";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

import { api, leerErrores } from "../../api/cliente";
import { abrirArchivoProtegido } from "../../api/descargas";
import { JORNADAS, MODALIDADES, NIVELES_IDIOMA, TIPOS_ENLACE } from "../../api/opciones";
import type { Certificacion, Enlace, Experiencia, Idioma, ItemCatalogo, PerfilPropio, Proyecto } from "../../api/tipos";
import { useAuth } from "../../auth/AuthContext";
import { useAviso } from "../../components/Avisos";
import { EstadoChip } from "../../components/EstadoChip";
import { EditorHabilidades } from "../../components/perfil/EditorHabilidades";
import { SeccionLista } from "../../components/perfil/SeccionLista";
import { fecha } from "../../utilidades/formato";

const CLAVE = ["estudiante", "perfil"];

function Dato({ etiqueta, children }: { etiqueta: string; children: ReactNode }) {
  return (
    <Box sx={{ minWidth: 160, flex: "1 1 160px" }}>
      <Typography variant="caption" color="text.secondary">{etiqueta}</Typography>
      <Typography variant="body2">{children || "—"}</Typography>
    </Box>
  );
}

function DatosBasicos({ perfil, onGuardado }: { perfil: PerfilPropio; onGuardado: () => void }) {
  const { data: ciudades = [] } = useQuery({ queryKey: ["catalogos", "ciudades"], queryFn: async () => (await api.get<ItemCatalogo[]>("/catalogos/ciudades/")).data });
  const [editando, setEditando] = useState(false);
  const [form, setForm] = useState<Record<string, string | boolean>>({});
  const [errores, setErrores] = useState<{ general: string; campos: Record<string, string> }>({ general: "", campos: {} });

  function editar() {
    setForm({
      nombres: perfil.nombres, apellidos: perfil.apellidos, telefono: perfil.telefono, documento: perfil.documento ?? "",
      semestre: perfil.semestre ? String(perfil.semestre) : "", ciudad: perfil.ciudad ? String(perfil.ciudad) : "",
      titular: perfil.titular, acerca_de: perfil.acerca_de, fecha_disponible: perfil.fecha_disponible ?? "",
      jornada: perfil.jornada ?? "", modalidad_preferida: perfil.modalidad_preferida ?? "", abierto_oportunidades: perfil.abierto_oportunidades,
    });
    setErrores({ general: "", campos: {} });
    setEditando(true);
  }

  const campo = (nombre: string) => ({
    value: form[nombre] as string,
    onChange: (e: { target: { value: string } }) => setForm({ ...form, [nombre]: e.target.value }),
    error: Boolean(errores.campos[nombre]),
    helperText: errores.campos[nombre],
    fullWidth: true,
  });

  async function guardar() {
    const vacioANull = (v: string | boolean) => (v === "" ? null : v);
    try {
      await api.patch("/estudiantes/yo/", {
        ...form,
        semestre: form.semestre ? Number(form.semestre) : null,
        ciudad: form.ciudad ? Number(form.ciudad) : null,
        fecha_disponible: vacioANull(form.fecha_disponible),
        jornada: vacioANull(form.jornada),
        modalidad_preferida: vacioANull(form.modalidad_preferida),
      });
      setEditando(false);
      onGuardado();
    } catch (e) {
      setErrores(leerErrores(e));
    }
  }

  return (
    <Card>
      <CardHeader
        title="Datos y disponibilidad"
        slotProps={{ title: { variant: "h6" } }}
        action={!editando && <Button onClick={editar}>Editar</Button>}
      />
      <CardContent sx={{ pt: 0 }}>
        {!editando ? (
          <Stack spacing={2}>
            {perfil.titular && <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>{perfil.titular}</Typography>}
            {perfil.acerca_de && <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>{perfil.acerca_de}</Typography>}
            <Stack direction="row" useFlexGap spacing={2} sx={{ flexWrap: "wrap" }}>
              <Dato etiqueta="Correo">{perfil.email}</Dato>
              <Dato etiqueta="Teléfono">{perfil.telefono}</Dato>
              <Dato etiqueta="Semestre">{perfil.semestre}</Dato>
              <Dato etiqueta="Ciudad">{perfil.ciudad_nombre}</Dato>
              <Dato etiqueta="Disponible desde">{perfil.fecha_disponible ? fecha(perfil.fecha_disponible) : ""}</Dato>
              <Dato etiqueta="Jornada">{perfil.jornada_nombre}</Dato>
              <Dato etiqueta="Modalidad preferida">{perfil.modalidad_preferida_nombre}</Dato>
              <Dato etiqueta="Abierto a oportunidades">{perfil.abierto_oportunidades ? "Sí" : "No"}</Dato>
            </Stack>
          </Stack>
        ) : (
          <Stack spacing={2}>
            {errores.general && <Alert severity="error">{errores.general}</Alert>}
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField label="Nombres" required {...campo("nombres")} />
              <TextField label="Apellidos" required {...campo("apellidos")} />
            </Stack>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField label="Teléfono" {...campo("telefono")} />
              <TextField label="Semestre" type="number" slotProps={{ htmlInput: { min: 1, max: 12 } }} {...campo("semestre")} />
              <TextField label="Documento" {...campo("documento")} helperText={errores.campos.documento ?? "No se muestra a las empresas."} />
            </Stack>
            <TextField label="Titular profesional" placeholder="Estudiante de Software · React y Django" {...campo("titular")} />
            <TextField label="Acerca de mí" multiline minRows={3} {...campo("acerca_de")} />
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField select label="Ciudad" {...campo("ciudad")}>
                <MenuItem value="">Sin especificar</MenuItem>
                {ciudades.map((c) => <MenuItem key={c.id} value={String(c.id)}>{c.nombre}</MenuItem>)}
              </TextField>
              <TextField label="Disponible desde" type="date" slotProps={{ inputLabel: { shrink: true } }} {...campo("fecha_disponible")} />
            </Stack>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField select label="Jornada" {...campo("jornada")}>
                <MenuItem value="">Sin especificar</MenuItem>
                {JORNADAS.map((o) => <MenuItem key={o.valor} value={o.valor}>{o.etiqueta}</MenuItem>)}
              </TextField>
              <TextField select label="Modalidad preferida" {...campo("modalidad_preferida")}>
                <MenuItem value="">Sin especificar</MenuItem>
                {MODALIDADES.map((o) => <MenuItem key={o.valor} value={o.valor}>{o.etiqueta}</MenuItem>)}
              </TextField>
            </Stack>
            <FormControlLabel
              control={<Switch checked={Boolean(form.abierto_oportunidades)} onChange={(e) => setForm({ ...form, abierto_oportunidades: e.target.checked })} />}
              label="Abierto a oportunidades: las empresas aliadas pueden encontrarme en la búsqueda de talento"
            />
            <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end" }}>
              <Button onClick={() => setEditando(false)}>Cancelar</Button>
              <Button variant="contained" onClick={guardar}>Guardar</Button>
            </Stack>
          </Stack>
        )}
      </CardContent>
    </Card>
  );
}

function HojaVida({ perfil, onGuardado }: { perfil: PerfilPropio; onGuardado: () => void }) {
  const avisar = useAviso();
  const [enviando, setEnviando] = useState(false);

  async function subir(archivo: File | undefined) {
    if (!archivo) return;
    const datos = new FormData();
    datos.append("archivo", archivo);
    setEnviando(true);
    try {
      await api.post("/estudiantes/yo/hoja-vida/", datos);
      avisar("Hoja de vida actualizada.");
      onGuardado();
    } catch (e) {
      const { general, campos } = leerErrores(e);
      avisar(campos.archivo ?? general, "error");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Card>
      <CardHeader title="Hoja de vida" slotProps={{ title: { variant: "h6" } }} />
      <CardContent sx={{ pt: 0 }}>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ alignItems: { sm: "center" } }}>
          <Stack direction="row" spacing={1} sx={{ alignItems: "center", flex: 1 }}>
            <DescriptionIcon color={perfil.tiene_hoja_vida ? "primary" : "disabled"} />
            <Typography variant="body2">
              {perfil.tiene_hoja_vida ? "Tu hoja de vida está cargada. Se envía una copia con cada postulación." : "Aún no has subido tu hoja de vida (PDF, máximo 5 MB)."}
            </Typography>
          </Stack>
          {perfil.tiene_hoja_vida && (
            <Button onClick={() => abrirArchivoProtegido("/estudiantes/yo/hoja-vida/").catch((e) => avisar(leerErrores(e).general, "error"))}>Ver</Button>
          )}
          <Button component="label" variant={perfil.tiene_hoja_vida ? "outlined" : "contained"} startIcon={<UploadFileIcon />} disabled={enviando}>
            {perfil.tiene_hoja_vida ? "Reemplazar" : "Subir PDF"}
            <input hidden type="file" accept="application/pdf,.pdf" onChange={(e) => { subir(e.target.files?.[0]); e.target.value = ""; }} />
          </Button>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default function MiPerfil() {
  const cliente = useQueryClient();
  const { recargarUsuario } = useAuth();
  const [editandoHabilidades, setEditandoHabilidades] = useState(false);
  const { data: perfil } = useQuery({ queryKey: CLAVE, queryFn: async () => (await api.get<PerfilPropio>("/estudiantes/yo/")).data });

  function refrescar() {
    cliente.invalidateQueries({ queryKey: CLAVE });
    cliente.invalidateQueries({ queryKey: ["convocatorias"] }); // La afinidad depende del perfil
    recargarUsuario();
  }

  if (!perfil) return null;
  const { completitud } = perfil;

  return (
    <Stack spacing={2}>
      <Card>
        <CardContent>
          <Stack direction={{ xs: "column", md: "row" }} spacing={3}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h5" component="h1">{perfil.nombre}</Typography>
              <Stack direction="row" spacing={1} useFlexGap sx={{ mt: 1, flexWrap: "wrap" }}>
                <Chip size="small" color="primary" variant="outlined" label={`${perfil.programa_nombre} · ${perfil.nivel_programa}`} />
                <EstadoChip estado={perfil.estado} etiqueta={perfil.estado_nombre} />
              </Stack>
            </Box>
            <Box sx={{ minWidth: { md: 320 } }}>
              <Stack direction="row" sx={{ justifyContent: "space-between", mb: 0.5 }}>
                <Typography variant="subtitle2">Perfil completo</Typography>
                <Typography variant="subtitle2">{completitud.porcentaje} %</Typography>
              </Stack>
              <LinearProgress variant="determinate" value={completitud.porcentaje} sx={{ height: 8, borderRadius: 4 }} />
              {completitud.faltantes.length > 0 && (
                <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 1 }}>
                  Siguiente paso: {completitud.faltantes[0].texto.toLowerCase()}.
                </Typography>
              )}
            </Box>
          </Stack>
        </CardContent>
      </Card>

      {perfil.faltantes_para_postular.length > 0 && (
        <Alert severity="warning">Para poder postularte te falta registrar: {perfil.faltantes_para_postular.join(", ")}.</Alert>
      )}

      <DatosBasicos perfil={perfil} onGuardado={refrescar} />
      <HojaVida perfil={perfil} onGuardado={refrescar} />

      <Card>
        <CardHeader title="Habilidades" slotProps={{ title: { variant: "h6" } }} action={<Button onClick={() => setEditandoHabilidades(true)}>Editar</Button>} />
        <CardContent sx={{ pt: 0 }}>
          {perfil.habilidades.length === 0 ? (
            <Typography variant="body2" color="text.secondary">Agrega tus habilidades: se usan para calcular tu afinidad con cada convocatoria.</Typography>
          ) : (
            <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
              {perfil.habilidades.map((h) => <Chip key={h.id} label={`${h.nombre} · ${h.nivel_nombre}`} />)}
            </Stack>
          )}
        </CardContent>
      </Card>
      <EditorHabilidades
        abierto={editandoHabilidades}
        actuales={perfil.habilidades}
        onCerrar={() => setEditandoHabilidades(false)}
        onGuardado={() => { setEditandoHabilidades(false); refrescar(); }}
      />

      <SeccionLista<Experiencia>
        titulo="Experiencia"
        ruta="/estudiantes/yo/experiencias/"
        items={perfil.experiencias}
        vacio="Agrega trabajos, voluntariados o monitorías."
        campos={[
          { nombre: "cargo", etiqueta: "Cargo", requerido: true },
          { nombre: "organizacion", etiqueta: "Organización", requerido: true },
          { nombre: "fecha_inicio", etiqueta: "Inicio", tipo: "fecha", requerido: true },
          { nombre: "fecha_fin", etiqueta: "Fin", tipo: "fecha", ayuda: "Déjalo vacío si es tu trabajo actual." },
          { nombre: "descripcion", etiqueta: "Descripción", tipo: "multilinea" },
        ]}
        primario={(e) => `${e.cargo} · ${e.organizacion}`}
        secundario={(e) => `${fecha(e.fecha_inicio)} – ${e.fecha_fin ? fecha(e.fecha_fin) : "actual"}`}
        onCambio={refrescar}
      />
      <SeccionLista<Proyecto>
        titulo="Proyectos"
        ruta="/estudiantes/yo/proyectos/"
        items={perfil.proyectos}
        vacio="Agrega proyectos académicos o personales."
        campos={[
          { nombre: "titulo", etiqueta: "Título", requerido: true },
          { nombre: "descripcion", etiqueta: "Descripción", tipo: "multilinea" },
          { nombre: "url", etiqueta: "Enlace", tipo: "url" },
        ]}
        primario={(p) => p.titulo}
        secundario={(p) => p.url || p.descripcion}
        onCambio={refrescar}
      />
      <SeccionLista<Idioma>
        titulo="Idiomas"
        ruta="/estudiantes/yo/idiomas/"
        items={perfil.idiomas}
        vacio="Agrega los idiomas que manejas."
        campos={[
          { nombre: "idioma", etiqueta: "Idioma", requerido: true },
          { nombre: "nivel", etiqueta: "Nivel", tipo: "select", opciones: NIVELES_IDIOMA },
        ]}
        primario={(i) => `${i.idioma} · ${i.nivel}`}
        onCambio={refrescar}
      />
      <SeccionLista<Certificacion>
        titulo="Certificaciones"
        ruta="/estudiantes/yo/certificaciones/"
        items={perfil.certificaciones}
        vacio="Agrega cursos o certificaciones."
        campos={[
          { nombre: "nombre", etiqueta: "Nombre", requerido: true },
          { nombre: "entidad", etiqueta: "Entidad", requerido: true },
          { nombre: "fecha", etiqueta: "Fecha", tipo: "fecha" },
          { nombre: "url", etiqueta: "Enlace", tipo: "url" },
        ]}
        primario={(c) => `${c.nombre} · ${c.entidad}`}
        secundario={(c) => (c.fecha ? fecha(c.fecha) : "")}
        onCambio={refrescar}
      />
      <SeccionLista<Enlace>
        titulo="Enlaces"
        ruta="/estudiantes/yo/enlaces/"
        items={perfil.enlaces}
        vacio="Agrega tu LinkedIn, GitHub o portafolio."
        campos={[
          { nombre: "tipo", etiqueta: "Tipo", tipo: "select", opciones: TIPOS_ENLACE },
          { nombre: "url", etiqueta: "URL", tipo: "url", requerido: true },
        ]}
        primario={(e) => e.tipo_nombre}
        secundario={(e) => e.url}
        onCambio={refrescar}
      />
    </Stack>
  );
}
