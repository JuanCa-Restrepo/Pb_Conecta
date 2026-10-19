import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import BookmarkIcon from "@mui/icons-material/Bookmark";
import BookmarkBorderIcon from "@mui/icons-material/BookmarkBorder";
import {
  Alert, Box, Button, Card, CardContent, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, Stack, TextField,
  Typography,
} from "@mui/material";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link as RouterLink, useNavigate, useParams } from "react-router-dom";

import { api, leerErrores } from "../../api/cliente";
import type { Convocatoria, PostulacionDetalle } from "../../api/tipos";
import { AfinidadDetalle } from "../../components/Afinidad";
import { useAviso } from "../../components/Avisos";
import { InfoConvocatoria } from "../../components/convocatorias/InfoConvocatoria";
import { EstadoChip } from "../../components/EstadoChip";

export default function ConvocatoriaEstudiante() {
  const { id } = useParams();
  const navegar = useNavigate();
  const cliente = useQueryClient();
  const avisar = useAviso();
  const [postulando, setPostulando] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  const { data: c } = useQuery({ queryKey: ["convocatoria", id], queryFn: async () => (await api.get<Convocatoria>(`/convocatorias/${id}/`)).data });

  async function alternarGuardada() {
    if (!c?.para_estudiante) return;
    const { data } = c.para_estudiante.guardada
      ? await api.delete<Convocatoria>(`/convocatorias/${id}/guardar/`)
      : await api.post<Convocatoria>(`/convocatorias/${id}/guardar/`);
    cliente.setQueryData(["convocatoria", id], data);
    cliente.invalidateQueries({ queryKey: ["convocatorias"] });
  }

  async function postular() {
    setEnviando(true);
    setError("");
    try {
      const { data } = await api.post<PostulacionDetalle>("/postulaciones/", { convocatoria: Number(id), mensaje_presentacion: mensaje });
      cliente.invalidateQueries({ queryKey: ["convocatorias"] });
      cliente.invalidateQueries({ queryKey: ["convocatoria", id] });
      avisar("¡Listo! Te postulaste. La empresa recibió tu hoja de vida.");
      navegar(`/estudiante/postulaciones/${data.id}`);
    } catch (e) {
      setError(leerErrores(e).general);
    } finally {
      setEnviando(false);
    }
  }

  if (!c?.para_estudiante) return null;
  const datos = c.para_estudiante;

  return (
    <Stack spacing={2}>
      <Button component={RouterLink} to="/estudiante/convocatorias" startIcon={<ArrowBackIcon />} sx={{ alignSelf: "flex-start" }}>Convocatorias</Button>

      <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ justifyContent: "space-between" }}>
        <div>
          <Typography variant="h5" component="h1">{c.titulo}</Typography>
          <Typography color="text.secondary">{c.empresa_nombre}</Typography>
        </div>
        <Stack direction="row" spacing={1} sx={{ alignItems: "flex-start" }}>
          <Button
            variant="outlined"
            startIcon={datos.guardada ? <BookmarkIcon /> : <BookmarkBorderIcon />}
            onClick={() => alternarGuardada().catch((e) => avisar(leerErrores(e).general, "error"))}
          >
            {datos.guardada ? "Guardada" : "Guardar"}
          </Button>
          {datos.postulacion ? (
            <Button variant="contained" component={RouterLink} to={`/estudiante/postulaciones/${datos.postulacion.id}`}>Ver mi postulación</Button>
          ) : (
            <Button variant="contained" disabled={!datos.puede_postularse} onClick={() => setPostulando(true)}>Postularme</Button>
          )}
        </Stack>
      </Stack>

      {datos.postulacion && (
        <Alert severity="info" icon={false}>
          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <span>Ya te postulaste.</span>
            <EstadoChip estado={datos.postulacion.estado} etiqueta={datos.postulacion.estado_nombre} />
          </Stack>
        </Alert>
      )}
      {!datos.postulacion && datos.motivo_no_postular && (
        <Alert severity="warning" action={datos.motivo_no_postular.includes("perfil") ? <Button color="inherit" component={RouterLink} to="/estudiante/perfil">Ir a mi perfil</Button> : undefined}>
          {datos.motivo_no_postular}
        </Alert>
      )}

      <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ alignItems: "flex-start" }}>
        <Card sx={{ flex: 1, minWidth: 0 }}>
          <CardContent><InfoConvocatoria c={c} mostrarAutoria={false} /></CardContent>
        </Card>
        <Card sx={{ width: { xs: "100%", md: 320 }, flexShrink: 0 }}>
          <CardContent>
            <AfinidadDetalle afinidad={datos.afinidad} />
            {datos.afinidad.habilidades_faltan.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Button size="small" component={RouterLink} to="/estudiante/perfil">Actualizar mis habilidades</Button>
              </Box>
            )}
          </CardContent>
        </Card>
      </Stack>

      <Dialog open={postulando} onClose={() => setPostulando(false)} fullWidth maxWidth="sm">
        <DialogTitle>Postularme a «{c.titulo}»</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            {c.empresa_nombre} recibirá tu perfil profesional y una copia de tu hoja de vida actual. Podrás seguir el proceso desde «Mis postulaciones».
          </DialogContentText>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <TextField
            label="Mensaje de presentación (opcional)"
            placeholder="Cuéntale a la empresa por qué te interesa esta práctica."
            value={mensaje}
            onChange={(e) => setMensaje(e.target.value)}
            multiline
            minRows={4}
            fullWidth
            slotProps={{ htmlInput: { maxLength: 2000 } }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPostulando(false)} disabled={enviando}>Cancelar</Button>
          <Button variant="contained" onClick={postular} disabled={enviando}>Enviar postulación</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
