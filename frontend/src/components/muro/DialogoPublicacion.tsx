import UploadFileIcon from "@mui/icons-material/UploadFile";
import {
  Alert, Autocomplete, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, MenuItem, Stack, Switch,
  TextField, Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import dayjs from "dayjs";
import { useEffect, useState } from "react";

import { api, leerErrores } from "../../api/cliente";
import { NOMBRE_TIPO_PUBLICACION } from "../../api/opciones";
import type { Programa, Publicacion } from "../../api/tipos";

interface Props {
  abierto: boolean;
  tipos: string[];
  existente?: Publicacion | null;
  onCerrar: () => void;
  onGuardada: () => void;
}

/** Crear o editar una publicación del muro (RF-101 a RF-104). Cada tipo pide sus propios datos. */
export function DialogoPublicacion({ abierto, tipos, existente, onCerrar, onGuardada }: Props) {
  const { data: programas = [] } = useQuery({ queryKey: ["catalogos", "programas"], queryFn: async () => (await api.get<Programa[]>("/catalogos/programas/")).data });
  const [form, setForm] = useState({ tipo: "", titulo: "", texto: "", enlace_url: "", fuente_externa: "", fecha_evento: "", lugar_evento: "" });
  const [paraTodos, setParaTodos] = useState(true);
  const [destinatarios, setDestinatarios] = useState<Programa[]>([]);
  const [imagen, setImagen] = useState<File | null>(null);
  const [errores, setErrores] = useState<{ general: string; campos: Record<string, string> }>({ general: "", campos: {} });
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (!abierto) return;
    setForm({
      tipo: existente?.tipo ?? tipos[0] ?? "",
      titulo: existente?.titulo ?? "", texto: existente?.texto ?? "",
      enlace_url: existente?.enlace_url ?? "", fuente_externa: existente?.fuente_externa ?? "",
      fecha_evento: existente?.fecha_evento ? dayjs(existente.fecha_evento).format("YYYY-MM-DDTHH:mm") : "",
      lugar_evento: existente?.lugar_evento ?? "",
    });
    setParaTodos(existente?.para_todos_programas ?? true);
    setDestinatarios(programas.filter((p) => existente?.programas_detalle.some((d) => d.id === p.id)));
    setImagen(null);
    setErrores({ general: "", campos: {} });
  }, [abierto, existente, tipos, programas]);

  const campo = (nombre: keyof typeof form) => ({
    value: form[nombre],
    onChange: (e: { target: { value: string } }) => setForm({ ...form, [nombre]: e.target.value }),
    error: Boolean(errores.campos[nombre]),
    helperText: errores.campos[nombre],
    fullWidth: true,
  });

  async function guardar() {
    const datos = new FormData();
    const { tipo, fecha_evento, ...resto } = form;
    if (!existente) datos.append("tipo", tipo);
    Object.entries(resto).forEach(([clave, valor]) => datos.append(clave, valor.trim()));
    if (tipo === "EVENTO" && fecha_evento) datos.append("fecha_evento", new Date(fecha_evento).toISOString());
    datos.append("para_todos_programas", String(paraTodos));
    if (!paraTodos) destinatarios.forEach((p) => datos.append("programas", String(p.id)));
    if (imagen) datos.append("imagen", imagen);
    setEnviando(true);
    try {
      if (existente) await api.patch(`/muro/publicaciones/${existente.id}/`, datos);
      else await api.post("/muro/publicaciones/", datos);
      onGuardada();
    } catch (e) {
      setErrores(leerErrores(e));
    } finally {
      setEnviando(false);
    }
  }

  const tipo = form.tipo;
  const hayTexto = Boolean(form.titulo.trim() || form.texto.trim());
  return (
    // Con texto escrito, Escape o un clic fuera no cierran el diálogo: solo «Cancelar» (evita perder lo escrito)
    <Dialog open={abierto} onClose={hayTexto ? undefined : onCerrar} fullWidth maxWidth="sm">
      <DialogTitle>{existente ? "Editar publicación" : "Nueva publicación"}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {errores.general && <Alert severity="error">{errores.general}</Alert>}
          {!existente && (
            <TextField select label="Tipo" {...campo("tipo")}>
              {tipos.map((t) => <MenuItem key={t} value={t}>{NOMBRE_TIPO_PUBLICACION[t] ?? t}</MenuItem>)}
            </TextField>
          )}
          {tipo === "OFERTA_EXTERNA" && (
            <Alert severity="info">Los estudiantes se postulan en la fuente original, no en PB Conecta (RF-104).</Alert>
          )}
          <TextField label="Título" required {...campo("titulo")} slotProps={{ htmlInput: { maxLength: 200 } }} />
          <TextField label="Texto" required multiline minRows={4} {...campo("texto")} />
          {tipo === "OFERTA_EXTERNA" && (
            <>
              <TextField label="Enlace a la oferta" type="url" required placeholder="https://" {...campo("enlace_url")} />
              <TextField label="Fuente" placeholder="Bolsa de empleo, empresa…" {...campo("fuente_externa")} />
            </>
          )}
          {tipo === "EVENTO" && (
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField label="Fecha y hora" type="datetime-local" required slotProps={{ inputLabel: { shrink: true } }} {...campo("fecha_evento")} />
              <TextField label="Lugar" {...campo("lugar_evento")} />
            </Stack>
          )}
          {tipo !== "OFERTA_EXTERNA" && <TextField label="Enlace (opcional)" type="url" placeholder="https://" {...campo("enlace_url")} />}

          <Box>
            <FormControlLabel control={<Switch checked={paraTodos} onChange={(e) => setParaTodos(e.target.checked)} />} label="Para todos los programas" />
            {!paraTodos && (
              <Autocomplete
                multiple
                options={programas}
                value={destinatarios}
                onChange={(_, valor) => setDestinatarios(valor)}
                getOptionLabel={(p) => p.nombre}
                isOptionEqualToValue={(a, b) => a.id === b.id}
                renderInput={(params) => <TextField {...params} label="Programas destinatarios" helperText="Sus estudiantes reciben un aviso en la campana." />}
                sx={{ mt: 1 }}
              />
            )}
          </Box>
          <Box>
            <Button component="label" variant="outlined" startIcon={<UploadFileIcon />}>
              {imagen ? "Cambiar imagen" : existente?.imagen ? "Reemplazar imagen" : "Agregar imagen (opcional)"}
              <input hidden type="file" accept="image/png,image/jpeg,image/webp" onChange={(e) => setImagen(e.target.files?.[0] ?? null)} />
            </Button>
            {imagen && <Typography variant="body2" sx={{ mt: 1 }}>{imagen.name}</Typography>}
            {errores.campos.imagen && <Typography variant="body2" color="error" sx={{ mt: 1 }}>{errores.campos.imagen}</Typography>}
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCerrar} disabled={enviando}>Cancelar</Button>
        <Button variant="contained" onClick={guardar} disabled={enviando || !form.titulo.trim() || !form.texto.trim()}>
          {existente ? "Guardar cambios" : "Publicar"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
