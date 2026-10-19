import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { Alert, Autocomplete, Button, Card, CardContent, Divider, InputAdornment, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type FormEvent } from "react";
import { Link as RouterLink, useNavigate, useParams } from "react-router-dom";

import { api, leerErrores } from "../../api/cliente";
import { MODALIDADES, NIVELES_FORMACION, TIPOS_VINCULACION } from "../../api/opciones";
import type { Convocatoria, EmpresaOficina, ItemCatalogo, Paginado, Programa } from "../../api/tipos";
import { useAuth } from "../../auth/AuthContext";
import { useAviso } from "../../components/Avisos";
import { enDiasISO } from "../../utilidades/formato";

interface Formulario {
  empresa: string;
  titulo: string;
  descripcion: string;
  funciones: string;
  nivel_formacion: string;
  tipo_vinculacion: string;
  modalidad: string;
  ciudad: string;
  apoyo_economico: string;
  cupos: string;
  duracion_meses: string;
  fecha_inicio: string;
  fecha_cierre: string;
  programas: Programa[];
  habilidades: ItemCatalogo[];
}

const VACIO: Formulario = {
  empresa: "", titulo: "", descripcion: "", funciones: "", nivel_formacion: "CUALQUIERA", tipo_vinculacion: "PRACTICA",
  modalidad: "PRESENCIAL", ciudad: "", apoyo_economico: "", cupos: "1", duracion_meses: "6",
  fecha_inicio: enDiasISO(60), fecha_cierre: enDiasISO(30), programas: [], habilidades: [],
};

/** Crear y editar convocatorias (RF-30, RF-31, RF-33). La usan la empresa y la oficina. */
export default function FormularioConvocatoria() {
  const { id } = useParams();
  const { usuario } = useAuth();
  const navegar = useNavigate();
  const cliente = useQueryClient();
  const avisar = useAviso();
  const esEmpresa = usuario?.rol === "EMPRESA";
  const base = esEmpresa ? "/empresa" : "/oficina";

  const [form, setForm] = useState<Formulario>(VACIO);
  const [errores, setErrores] = useState<{ general: string; campos: Record<string, string> }>({ general: "", campos: {} });
  const [enviando, setEnviando] = useState(false);

  const { data: programas = [] } = useQuery({ queryKey: ["catalogos", "programas"], queryFn: async () => (await api.get<Programa[]>("/catalogos/programas/")).data });
  const { data: habilidades = [] } = useQuery({ queryKey: ["catalogos", "habilidades"], queryFn: async () => (await api.get<ItemCatalogo[]>("/catalogos/habilidades/")).data });
  const { data: ciudades = [] } = useQuery({ queryKey: ["catalogos", "ciudades"], queryFn: async () => (await api.get<ItemCatalogo[]>("/catalogos/ciudades/")).data });
  const { data: aliadas } = useQuery({
    queryKey: ["oficina", "empresas", "aliadas"],
    queryFn: async () => (await api.get<Paginado<EmpresaOficina>>("/oficina/empresas/", { params: { estado: "ALIADA", tamano: 200 } })).data,
    enabled: !esEmpresa && !id,
  });
  const { data: actual } = useQuery({
    queryKey: ["convocatoria", id],
    queryFn: async () => (await api.get<Convocatoria>(`/convocatorias/${id}/`)).data,
    enabled: Boolean(id),
  });

  useEffect(() => {
    if (!actual || programas.length === 0) return;
    setForm({
      empresa: String(actual.empresa), titulo: actual.titulo, descripcion: actual.descripcion, funciones: actual.funciones,
      nivel_formacion: actual.nivel_formacion, tipo_vinculacion: actual.tipo_vinculacion, modalidad: actual.modalidad,
      ciudad: actual.ciudad ? String(actual.ciudad) : "", apoyo_economico: actual.apoyo_economico ? String(Math.round(Number(actual.apoyo_economico))) : "",
      cupos: String(actual.cupos), duracion_meses: String(actual.duracion_meses), fecha_inicio: actual.fecha_inicio,
      fecha_cierre: actual.fecha_cierre,
      programas: programas.filter((p) => actual.programas.includes(p.id)),
      habilidades: actual.habilidades_detalle,
    });
  }, [actual, programas]);

  const campo = (nombre: Exclude<keyof Formulario, "programas" | "habilidades">) => ({
    value: form[nombre],
    onChange: (e: { target: { value: string } }) => setForm({ ...form, [nombre]: e.target.value }),
    error: Boolean(errores.campos[nombre]),
    helperText: errores.campos[nombre],
    fullWidth: true,
  });

  async function guardar(evento: FormEvent) {
    evento.preventDefault();
    setEnviando(true);
    setErrores({ general: "", campos: {} });
    const cuerpo = {
      ...(esEmpresa || id ? {} : { empresa: form.empresa ? Number(form.empresa) : null }),
      titulo: form.titulo.trim(), descripcion: form.descripcion.trim(), funciones: form.funciones.trim(),
      nivel_formacion: form.nivel_formacion, tipo_vinculacion: form.tipo_vinculacion, modalidad: form.modalidad,
      ciudad: form.ciudad ? Number(form.ciudad) : null,
      apoyo_economico: form.apoyo_economico ? Number(form.apoyo_economico) : null,
      cupos: Number(form.cupos), duracion_meses: Number(form.duracion_meses),
      fecha_inicio: form.fecha_inicio, fecha_cierre: form.fecha_cierre,
      programas: form.programas.map((p) => p.id), habilidades: form.habilidades.map((h) => h.id),
    };
    try {
      const { data } = id
        ? await api.patch<Convocatoria>(`/convocatorias/${id}/`, cuerpo)
        : await api.post<Convocatoria>("/convocatorias/", cuerpo);
      cliente.invalidateQueries({ queryKey: ["convocatorias"] });
      cliente.setQueryData(["convocatoria", String(data.id)], data);
      avisar(id ? (data.estado === "EN_REVISION" && actual?.estado === "PUBLICADA" ? "Cambios guardados: la convocatoria volvió a revisión." : "Cambios guardados.") : "Convocatoria creada como borrador.");
      navegar(`${base}/convocatorias/${data.id}`);
    } catch (e) {
      setErrores(leerErrores(e));
    } finally {
      setEnviando(false);
    }
  }

  const remota = form.modalidad === "REMOTA";

  return (
    <Stack spacing={2} component="form" onSubmit={guardar} noValidate>
      <Button component={RouterLink} to={id ? `${base}/convocatorias/${id}` : `${base}/convocatorias`} startIcon={<ArrowBackIcon />} sx={{ alignSelf: "flex-start" }}>
        Volver
      </Button>
      <Typography variant="h5" component="h1">{id ? "Editar convocatoria" : "Nueva convocatoria"}</Typography>

      {esEmpresa && actual?.estado === "PUBLICADA" && (
        <Alert severity="warning">Esta convocatoria está publicada. Al guardar cambios vuelve a revisión y deja de verse hasta que la oficina la apruebe (RF-33).</Alert>
      )}
      {errores.general && <Alert severity="error">{errores.general}</Alert>}

      <Card>
        <CardContent>
          <Stack spacing={2}>
            {!esEmpresa && !id && (
              <TextField select label="Empresa aliada" required {...campo("empresa")} helperText={errores.campos.empresa ?? "Solo empresas aliadas con convenio vigente (RN-02)."}>
                {aliadas?.results.filter((e) => e.puede_publicar).map((e) => <MenuItem key={e.id} value={String(e.id)}>{e.razon_social}</MenuItem>)}
              </TextField>
            )}
            <TextField label="Título" required placeholder="Practicante de desarrollo web" {...campo("titulo")} />
            <TextField label="Descripción" required multiline minRows={3} {...campo("descripcion")} />
            <TextField label="Funciones" required multiline minRows={3} {...campo("funciones")} />

            <Divider />
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>¿A quién va dirigida?</Typography>
            <Autocomplete
              multiple
              options={programas}
              value={form.programas}
              onChange={(_, valor) => setForm({ ...form, programas: valor })}
              getOptionLabel={(p) => `${p.nombre} · ${p.nivel_nombre}`}
              isOptionEqualToValue={(a, b) => a.id === b.id}
              renderInput={(params) => (
                <TextField {...params} label="Programas afines" required error={Boolean(errores.campos.programas)}
                  helperText={errores.campos.programas ?? "Solo los estudiantes de estos programas podrán postularse (RN-05)."} />
              )}
            />
            <Autocomplete
              multiple
              options={habilidades}
              value={form.habilidades}
              onChange={(_, valor) => setForm({ ...form, habilidades: valor })}
              getOptionLabel={(h) => h.nombre}
              isOptionEqualToValue={(a, b) => a.id === b.id}
              renderInput={(params) => <TextField {...params} label="Habilidades requeridas" helperText="Se usan para calcular el índice de afinidad." />}
            />
            <TextField select label="Nivel de formación" {...campo("nivel_formacion")}>
              {NIVELES_FORMACION.map((o) => <MenuItem key={o.valor} value={o.valor}>{o.etiqueta}</MenuItem>)}
            </TextField>

            <Divider />
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Condiciones</Typography>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField select label="Tipo de vinculación" {...campo("tipo_vinculacion")}>
                {TIPOS_VINCULACION.map((o) => <MenuItem key={o.valor} value={o.valor}>{o.etiqueta}</MenuItem>)}
              </TextField>
              <TextField select label="Modalidad" {...campo("modalidad")}>
                {MODALIDADES.map((o) => <MenuItem key={o.valor} value={o.valor}>{o.etiqueta}</MenuItem>)}
              </TextField>
              <TextField select label={remota ? "Ciudad (opcional)" : "Ciudad"} required={!remota} {...campo("ciudad")}>
                {remota && <MenuItem value="">Sin ciudad</MenuItem>}
                {ciudades.map((c) => <MenuItem key={c.id} value={String(c.id)}>{c.nombre}</MenuItem>)}
              </TextField>
            </Stack>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField
                label="Apoyo económico mensual"
                type="number"
                {...campo("apoyo_economico")}
                helperText={errores.campos.apoyo_economico ?? "Déjalo vacío si no tiene apoyo económico."}
                slotProps={{ input: { startAdornment: <InputAdornment position="start">$</InputAdornment> }, htmlInput: { min: 0, step: 1000 } }}
              />
              <TextField label="Cupos" type="number" required {...campo("cupos")} slotProps={{ htmlInput: { min: 1 } }} />
              <TextField label="Duración (meses)" type="number" required {...campo("duracion_meses")} slotProps={{ htmlInput: { min: 1, max: 24 } }} />
            </Stack>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField label="Fecha de inicio de la práctica" type="date" required slotProps={{ inputLabel: { shrink: true } }} {...campo("fecha_inicio")} />
              <TextField label="Fecha de cierre de la convocatoria" type="date" required slotProps={{ inputLabel: { shrink: true } }} {...campo("fecha_cierre")}
                helperText={errores.campos.fecha_cierre ?? "Se cierra automáticamente ese día (RN-09)."} />
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      <Stack direction="row" spacing={2} sx={{ justifyContent: "flex-end" }}>
        <Button component={RouterLink} to={id ? `${base}/convocatorias/${id}` : `${base}/convocatorias`} disabled={enviando}>Cancelar</Button>
        <Button type="submit" variant="contained" disabled={enviando}>{id ? "Guardar cambios" : "Guardar borrador"}</Button>
      </Stack>
    </Stack>
  );
}
