import SearchIcon from "@mui/icons-material/Search";
import {
  Alert, Box, Card, FormControlLabel, InputAdornment, MenuItem, Pagination, Stack, Switch, TextField, ToggleButton,
  ToggleButtonGroup, Typography,
} from "@mui/material";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../api/cliente";
import { MODALIDADES, TIPOS_VINCULACION } from "../../api/opciones";
import type { Convocatoria, ItemCatalogo, Paginado } from "../../api/tipos";
import { useAuth } from "../../auth/AuthContext";
import { TarjetaConvocatoria } from "../../components/convocatorias/TarjetaConvocatoria";

const REJILLA = { display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, 1fr)", lg: "repeat(3, 1fr)" } };

export default function ConvocatoriasEstudiante() {
  const { usuario } = useAuth();
  const [vista, setVista] = useState<"mi_programa" | "todas" | "guardadas">("mi_programa");
  const [texto, setTexto] = useState("");
  const [modalidad, setModalidad] = useState("");
  const [tipo, setTipo] = useState("");
  const [ciudad, setCiudad] = useState("");
  const [conApoyo, setConApoyo] = useState(false);
  const [pagina, setPagina] = useState(1);

  const { data: ciudades = [] } = useQuery({ queryKey: ["catalogos", "ciudades"], queryFn: async () => (await api.get<ItemCatalogo[]>("/catalogos/ciudades/")).data });
  const { data: recomendadas = [] } = useQuery({
    queryKey: ["convocatorias", "recomendadas"],
    queryFn: async () => (await api.get<Convocatoria[]>("/convocatorias/recomendadas/")).data,
  });
  const parametros = {
    mi_programa: vista === "mi_programa" ? "1" : undefined,
    guardadas: vista === "guardadas" ? "1" : undefined,
    q: texto || undefined, modalidad: modalidad || undefined, tipo_vinculacion: tipo || undefined,
    ciudad: ciudad || undefined, con_apoyo: conApoyo ? "1" : undefined, page: pagina,
  };
  const { data, isFetching } = useQuery({
    queryKey: ["convocatorias", "estudiante", parametros],
    queryFn: async () => (await api.get<Paginado<Convocatoria>>("/convocatorias/", { params: parametros })).data,
    placeholderData: keepPreviousData,
  });

  const filtrar = (cambio: () => void) => { cambio(); setPagina(1); };
  const hayFiltros = Boolean(texto || modalidad || tipo || ciudad || conApoyo);
  const mostrarRecomendadas = vista === "mi_programa" && !hayFiltros && pagina === 1 && recomendadas.length > 0;

  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h5" component="h1">Convocatorias</Typography>
        <Typography color="text.secondary">Prácticas de las empresas aliadas para {usuario?.estudiante?.programa_nombre}.</Typography>
      </div>

      {usuario?.estudiante?.estado === "NO_HABILITADO" && (
        <Alert severity="info">Puedes explorar las convocatorias, pero para postularte la oficina de prácticas debe habilitarte.</Alert>
      )}

      {mostrarRecomendadas && (
        <Box>
          <Typography variant="h6" gutterBottom>Recomendadas para ti</Typography>
          <Box sx={REJILLA}>{recomendadas.slice(0, 3).map((c) => <TarjetaConvocatoria key={c.id} c={c} />)}</Box>
        </Box>
      )}

      <Card sx={{ p: 2 }}>
        <Stack spacing={2}>
          <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ alignItems: { md: "center" } }}>
            <ToggleButtonGroup exclusive size="small" color="primary" value={vista} onChange={(_, v) => v && filtrar(() => setVista(v))}>
              <ToggleButton value="mi_programa">Mi programa</ToggleButton>
              <ToggleButton value="todas">Ver todas</ToggleButton>
              <ToggleButton value="guardadas">Guardadas</ToggleButton>
            </ToggleButtonGroup>
            <TextField
              size="small"
              placeholder="Buscar por cargo, empresa o palabra clave"
              value={texto}
              onChange={(e) => filtrar(() => setTexto(e.target.value))}
              slotProps={{ input: { startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment> } }}
              sx={{ flex: 1 }}
            />
          </Stack>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2} useFlexGap sx={{ flexWrap: "wrap", alignItems: { sm: "center" } }}>
            {[
              { etiqueta: "Modalidad", valor: modalidad, poner: setModalidad, opciones: MODALIDADES },
              { etiqueta: "Vinculación", valor: tipo, poner: setTipo, opciones: TIPOS_VINCULACION },
              { etiqueta: "Ciudad", valor: ciudad, poner: setCiudad, opciones: ciudades.map((c) => ({ valor: String(c.id), etiqueta: c.nombre })) },
            ].map((f) => (
              <TextField
                key={f.etiqueta}
                select
                size="small"
                label={f.etiqueta}
                value={f.valor}
                onChange={(e) => filtrar(() => f.poner(e.target.value))}
                slotProps={{ select: { displayEmpty: true }, inputLabel: { shrink: true } }}
                sx={{ minWidth: 180 }}
              >
                <MenuItem value="">Todas</MenuItem>
                {f.opciones.map((o) => <MenuItem key={o.valor} value={o.valor}>{o.etiqueta}</MenuItem>)}
              </TextField>
            ))}
            <FormControlLabel control={<Switch checked={conApoyo} onChange={(e) => filtrar(() => setConApoyo(e.target.checked))} />} label="Con apoyo económico" />
          </Stack>
        </Stack>
      </Card>

      <Typography variant="body2" color="text.secondary">{data ? `${data.count} convocatoria(s)` : isFetching ? "Cargando…" : ""}</Typography>
      <Box sx={REJILLA}>{data?.results.map((c) => <TarjetaConvocatoria key={c.id} c={c} />)}</Box>
      {data && data.results.length === 0 && (
        <Typography color="text.secondary" sx={{ textAlign: "center", py: 4 }}>
          {vista === "guardadas" ? "No tienes convocatorias guardadas." : "No hay convocatorias con estos filtros."}
        </Typography>
      )}
      {data && data.count > 20 && (
        <Pagination sx={{ alignSelf: "center" }} count={Math.ceil(data.count / 20)} page={pagina} onChange={(_, p) => setPagina(p)} />
      )}
    </Stack>
  );
}
