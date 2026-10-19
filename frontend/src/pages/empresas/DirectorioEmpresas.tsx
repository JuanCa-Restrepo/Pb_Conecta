import SearchIcon from "@mui/icons-material/Search";
import {
  Avatar, Box, Card, CardActionArea, CardContent, Chip, InputAdornment, MenuItem, Pagination, Stack, TextField, ToggleButton,
  ToggleButtonGroup, Typography,
} from "@mui/material";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link as RouterLink } from "react-router-dom";

import { api } from "../../api/cliente";
import type { EmpresaPublica, ItemCatalogo, Paginado } from "../../api/tipos";

/** RF-21: directorio de empresas aliadas. `base` es "" (público) o "/estudiante" (con la opción de ver las seguidas). */
export default function DirectorioEmpresas({ base = "" }: { base?: string }) {
  const esEstudiante = base === "/estudiante";
  const [texto, setTexto] = useState("");
  const [sector, setSector] = useState("");
  const [ciudad, setCiudad] = useState("");
  const [seguidas, setSeguidas] = useState(false);
  const [pagina, setPagina] = useState(1);

  const { data: sectores = [] } = useQuery({ queryKey: ["catalogos", "sectores"], queryFn: async () => (await api.get<ItemCatalogo[]>("/catalogos/sectores/")).data });
  const { data: ciudades = [] } = useQuery({ queryKey: ["catalogos", "ciudades"], queryFn: async () => (await api.get<ItemCatalogo[]>("/catalogos/ciudades/")).data });
  const parametros = { q: texto || undefined, sector: sector || undefined, ciudad: ciudad || undefined, seguidas: seguidas ? "1" : undefined, page: pagina };
  const { data } = useQuery({
    queryKey: ["empresas", "directorio", parametros],
    queryFn: async () => (await api.get<Paginado<EmpresaPublica>>("/empresas/", { params: parametros })).data,
    placeholderData: keepPreviousData,
  });
  const filtrar = (cambio: () => void) => { cambio(); setPagina(1); };

  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h5" component="h1">Empresas aliadas</Typography>
        <Typography color="text.secondary">Organizaciones con convenio vigente con la Institución Universitaria Pascual Bravo.</Typography>
      </div>

      <Card sx={{ p: 2 }}>
        <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ alignItems: { md: "center" } }}>
          <TextField
            size="small"
            placeholder="Buscar empresa"
            value={texto}
            onChange={(e) => filtrar(() => setTexto(e.target.value))}
            slotProps={{ input: { startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment> } }}
            sx={{ flex: 1 }}
          />
          {[
            { etiqueta: "Sector", valor: sector, poner: setSector, opciones: sectores },
            { etiqueta: "Ciudad", valor: ciudad, poner: setCiudad, opciones: ciudades },
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
              <MenuItem value="">Todos</MenuItem>
              {f.opciones.map((o) => <MenuItem key={o.id} value={String(o.id)}>{o.nombre}</MenuItem>)}
            </TextField>
          ))}
          {esEstudiante && (
            <ToggleButtonGroup exclusive size="small" color="primary" value={seguidas ? "si" : "todas"} onChange={(_, v) => v && filtrar(() => setSeguidas(v === "si"))}>
              <ToggleButton value="todas">Todas</ToggleButton>
              <ToggleButton value="si">Siguiendo</ToggleButton>
            </ToggleButtonGroup>
          )}
        </Stack>
      </Card>

      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, 1fr)", lg: "repeat(3, 1fr)" } }}>
        {data?.results.map((e) => (
          <Card key={e.id}>
            <CardActionArea component={RouterLink} to={`${base}/empresas/${e.id}`} sx={{ height: "100%", alignItems: "flex-start" }}>
              <CardContent>
                <Stack direction="row" spacing={1.5} sx={{ alignItems: "center", mb: 1.5 }}>
                  <Avatar src={e.logo ?? undefined} variant="rounded" sx={{ width: 48, height: 48, bgcolor: "primary.main" }}>{e.razon_social[0]}</Avatar>
                  <Box sx={{ minWidth: 0 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, lineHeight: 1.2 }}>{e.razon_social}</Typography>
                    <Typography variant="caption" color="text.secondary">{e.sector_nombre} · {e.ciudad_nombre}</Typography>
                  </Box>
                </Stack>
                {e.descripcion && (
                  <Typography variant="body2" color="text.secondary" sx={{ display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden", mb: 1.5 }}>
                    {e.descripcion}
                  </Typography>
                )}
                <Stack direction="row" spacing={1}>
                  <Chip size="small" color={e.convocatorias_activas ? "primary" : "default"} label={`${e.convocatorias_activas} convocatoria(s) abierta(s)`} />
                  {e.seguida && <Chip size="small" variant="outlined" label="Siguiendo" />}
                </Stack>
              </CardContent>
            </CardActionArea>
          </Card>
        ))}
      </Box>
      {data && data.results.length === 0 && <Typography color="text.secondary" sx={{ textAlign: "center" }}>No hay empresas con estos filtros.</Typography>}
      {data && data.count > 20 && <Pagination sx={{ alignSelf: "center" }} count={Math.ceil(data.count / 20)} page={pagina} onChange={(_, p) => setPagina(p)} />}
    </Stack>
  );
}
