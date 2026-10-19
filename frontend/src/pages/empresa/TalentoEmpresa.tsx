import SearchIcon from "@mui/icons-material/Search";
import {
  Alert, Autocomplete, Box, Button, Card, CardActions, CardContent, Chip, Dialog, DialogActions, DialogContent, DialogTitle,
  InputAdornment, MenuItem, Pagination, Stack, TextField, Typography,
} from "@mui/material";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api, leerErrores } from "../../api/cliente";
import { MODALIDADES } from "../../api/opciones";
import type { Convocatoria, ItemCatalogo, Paginado, PerfilTalento, Programa } from "../../api/tipos";
import { useAuth } from "../../auth/AuthContext";
import { useAviso } from "../../components/Avisos";
import { PerfilProfesionalCard } from "../../components/perfil/PerfilProfesionalCard";

function DialogoInvitar({ perfil, onCerrar }: { perfil: PerfilTalento | null; onCerrar: () => void }) {
  const avisar = useAviso();
  const [convocatoria, setConvocatoria] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  const { data } = useQuery({
    queryKey: ["convocatorias", "lista", "PUBLICADA", "invitar"],
    queryFn: async () => (await api.get<Paginado<Convocatoria>>("/convocatorias/", { params: { estado: "PUBLICADA", tamano: 200 } })).data,
    enabled: Boolean(perfil),
  });
  // Solo convocatorias que incluyen el programa del estudiante: si no, no podría postularse (RN-05)
  const afines = (data?.results ?? []).filter((c) => perfil && c.programas.includes(perfil.programa));

  async function invitar() {
    setError("");
    try {
      const { data: respuesta } = await api.post<{ detalle: string }>(`/talento/${perfil!.id}/invitar/`, { convocatoria: Number(convocatoria), mensaje });
      avisar(respuesta.detalle);
      setConvocatoria("");
      setMensaje("");
      onCerrar();
    } catch (e) {
      setError(leerErrores(e).general);
    }
  }

  return (
    <Dialog open={Boolean(perfil)} onClose={onCerrar} fullWidth maxWidth="sm">
      <DialogTitle>Invitar a {perfil?.nombre} a postularse</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          {afines.length === 0 ? (
            <Alert severity="info">No tienes convocatorias publicadas para {perfil?.programa_nombre}.</Alert>
          ) : (
            <TextField select label="Convocatoria" value={convocatoria} onChange={(e) => setConvocatoria(e.target.value)} required>
              {afines.map((c) => <MenuItem key={c.id} value={String(c.id)}>{c.titulo}</MenuItem>)}
            </TextField>
          )}
          <TextField label="Mensaje (opcional)" value={mensaje} onChange={(e) => setMensaje(e.target.value)} multiline minRows={3}
            placeholder="Cuéntale por qué su perfil te interesa." slotProps={{ htmlInput: { maxLength: 1000 } }} />
          <Typography variant="caption" color="text.secondary">
            El estudiante recibe la invitación por notificación y correo. Si se postula, verás sus datos de contacto en la postulación.
          </Typography>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCerrar}>Cancelar</Button>
        <Button variant="contained" onClick={invitar} disabled={!convocatoria}>Enviar invitación</Button>
      </DialogActions>
    </Dialog>
  );
}

/** RF-45: búsqueda de talento entre los estudiantes habilitados que están «Abiertos a oportunidades». */
export default function TalentoEmpresa() {
  const { usuario } = useAuth();
  const [texto, setTexto] = useState("");
  const [programa, setPrograma] = useState("");
  const [modalidad, setModalidad] = useState("");
  const [habilidades, setHabilidades] = useState<ItemCatalogo[]>([]);
  const [pagina, setPagina] = useState(1);
  const [viendo, setViendo] = useState<PerfilTalento | null>(null);
  const [invitando, setInvitando] = useState<PerfilTalento | null>(null);

  const puede = Boolean(usuario?.empresa?.puede_publicar);
  const { data: programas = [] } = useQuery({ queryKey: ["catalogos", "programas"], queryFn: async () => (await api.get<Programa[]>("/catalogos/programas/")).data });
  const { data: catalogo = [] } = useQuery({ queryKey: ["catalogos", "habilidades"], queryFn: async () => (await api.get<ItemCatalogo[]>("/catalogos/habilidades/")).data });
  const parametros = {
    q: texto || undefined, programa: programa || undefined, modalidad: modalidad || undefined,
    habilidades: habilidades.map((h) => h.id).join(",") || undefined, page: pagina,
  };
  const { data } = useQuery({
    queryKey: ["talento", parametros],
    queryFn: async () => (await api.get<Paginado<PerfilTalento>>("/talento/", { params: parametros })).data,
    placeholderData: keepPreviousData,
    enabled: puede,
  });
  const filtrar = (cambio: () => void) => { cambio(); setPagina(1); };
  const buscadas = new Set(habilidades.map((h) => h.id));

  if (!puede) {
    return <Alert severity="warning">La búsqueda de talento está disponible para empresas aliadas con convenio vigente (RN-02).</Alert>;
  }

  return (
    <Stack spacing={2}>
      <div>
        <Typography variant="h5" component="h1">Buscar talento</Typography>
        <Typography color="text.secondary">Estudiantes habilitados para prácticas que activaron «Abierto a oportunidades».</Typography>
      </div>
      <Card sx={{ p: 2 }}>
        <Stack spacing={2}>
          <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
            <TextField
              size="small"
              placeholder="Buscar por nombre, titular o descripción"
              value={texto}
              onChange={(e) => filtrar(() => setTexto(e.target.value))}
              slotProps={{ input: { startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment> } }}
              sx={{ flex: 1 }}
            />
            <TextField select size="small" label="Programa" value={programa} onChange={(e) => filtrar(() => setPrograma(e.target.value))}
              slotProps={{ select: { displayEmpty: true }, inputLabel: { shrink: true } }} sx={{ minWidth: 240 }}>
              <MenuItem value="">Todos</MenuItem>
              {programas.map((p) => <MenuItem key={p.id} value={String(p.id)}>{p.nombre}</MenuItem>)}
            </TextField>
            <TextField select size="small" label="Modalidad" value={modalidad} onChange={(e) => filtrar(() => setModalidad(e.target.value))}
              slotProps={{ select: { displayEmpty: true }, inputLabel: { shrink: true } }} sx={{ minWidth: 160 }}>
              <MenuItem value="">Todas</MenuItem>
              {MODALIDADES.map((m) => <MenuItem key={m.valor} value={m.valor}>{m.etiqueta}</MenuItem>)}
            </TextField>
          </Stack>
          <Autocomplete
            multiple
            size="small"
            options={catalogo}
            value={habilidades}
            onChange={(_, valor) => filtrar(() => setHabilidades(valor))}
            getOptionLabel={(h) => h.nombre}
            isOptionEqualToValue={(a, b) => a.id === b.id}
            renderInput={(params) => <TextField {...params} label="Habilidades" helperText="Primero aparecen quienes tienen más de estas habilidades." />}
          />
        </Stack>
      </Card>

      <Typography variant="body2" color="text.secondary">{data ? `${data.count} estudiante(s)` : ""}</Typography>
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", md: "repeat(2, 1fr)", xl: "repeat(3, 1fr)" } }}>
        {data?.results.map((e) => (
          <Card key={e.id} sx={{ display: "flex", flexDirection: "column" }}>
            <CardContent sx={{ flex: 1 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>{e.nombre}</Typography>
              <Typography variant="body2" color="text.secondary">
                {e.programa_nombre}{e.semestre ? ` · semestre ${e.semestre}` : ""}{e.ciudad_nombre ? ` · ${e.ciudad_nombre}` : ""}
              </Typography>
              {e.titular && <Typography variant="body2" sx={{ mt: 1 }}>{e.titular}</Typography>}
              <Stack direction="row" spacing={0.5} useFlexGap sx={{ mt: 1.5, flexWrap: "wrap" }}>
                {e.habilidades.map((h) => (
                  <Chip key={h.id} size="small" label={h.nombre} color={buscadas.has(h.id) ? "primary" : "default"} variant={buscadas.has(h.id) ? "filled" : "outlined"} />
                ))}
              </Stack>
              {e.modalidad_preferida_nombre && <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 1 }}>Prefiere {e.modalidad_preferida_nombre.toLowerCase()}</Typography>}
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => setViendo(e)}>Ver perfil</Button>
              <Button size="small" variant="contained" onClick={() => setInvitando(e)}>Invitar a postularse</Button>
            </CardActions>
          </Card>
        ))}
      </Box>
      {data && data.results.length === 0 && <Typography color="text.secondary" sx={{ textAlign: "center", py: 3 }}>No hay estudiantes con estos filtros.</Typography>}
      {data && data.count > 20 && <Pagination sx={{ alignSelf: "center" }} count={Math.ceil(data.count / 20)} page={pagina} onChange={(_, p) => setPagina(p)} />}

      <Dialog open={Boolean(viendo)} onClose={() => setViendo(null)} fullWidth maxWidth="md">
        <DialogContent sx={{ p: 0 }}>{viendo && <PerfilProfesionalCard perfil={viendo} />}</DialogContent>
        <DialogActions>
          <Button onClick={() => setViendo(null)}>Cerrar</Button>
          <Button variant="contained" onClick={() => { setInvitando(viendo); setViendo(null); }}>Invitar a postularse</Button>
        </DialogActions>
      </Dialog>
      <DialogoInvitar perfil={invitando} onCerrar={() => setInvitando(null)} />
    </Stack>
  );
}
