import AddIcon from "@mui/icons-material/Add";
import SearchIcon from "@mui/icons-material/Search";
import {
  Alert, Box, Button, Card, Chip, InputAdornment, Stack, Tab, Table, TableBody, TableCell, TableContainer, TableHead,
  TablePagination, TableRow, Tabs, TextField, Tooltip, Typography,
} from "@mui/material";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import { api } from "../../api/cliente";
import type { Convocatoria, Paginado, Resumen } from "../../api/tipos";
import { useAuth } from "../../auth/AuthContext";
import { EstadoChip } from "../../components/EstadoChip";
import { fecha } from "../../utilidades/formato";

const PESTANAS_OFICINA = [
  { estado: "EN_REVISION", etiqueta: "Por revisar" },
  { estado: "PUBLICADA", etiqueta: "Publicadas" },
  { estado: "DEVUELTA", etiqueta: "Devueltas" },
  { estado: "BORRADOR", etiqueta: "Borradores" },
  { estado: "CERRADA,CANCELADA", etiqueta: "Cerradas" },
  { estado: "", etiqueta: "Todas" },
];

const PESTANAS_EMPRESA = [
  { estado: "", etiqueta: "Todas" },
  { estado: "BORRADOR", etiqueta: "Borradores" },
  { estado: "EN_REVISION", etiqueta: "En revisión" },
  { estado: "DEVUELTA", etiqueta: "Devueltas" },
  { estado: "PUBLICADA", etiqueta: "Publicadas" },
  { estado: "CERRADA,CANCELADA", etiqueta: "Cerradas" },
];

export default function ListaConvocatorias() {
  const { usuario } = useAuth();
  const navegar = useNavigate();
  const esEmpresa = usuario?.rol === "EMPRESA";
  const base = esEmpresa ? "/empresa" : "/oficina";
  const pestanas = esEmpresa ? PESTANAS_EMPRESA : PESTANAS_OFICINA;
  const puedeCrear = !esEmpresa || Boolean(usuario?.empresa?.puede_publicar);

  const [estado, setEstado] = useState(pestanas[0].estado);
  const [texto, setTexto] = useState("");
  const [pagina, setPagina] = useState(0);

  const { data: resumen } = useQuery({ queryKey: ["convocatorias", "resumen"], queryFn: async () => (await api.get<Resumen>("/convocatorias/resumen/")).data });
  const { data, isFetching } = useQuery({
    queryKey: ["convocatorias", "lista", estado, texto, pagina],
    queryFn: async () =>
      (await api.get<Paginado<Convocatoria>>("/convocatorias/", { params: { estado: estado || undefined, q: texto || undefined, page: pagina + 1 } })).data,
    placeholderData: keepPreviousData,
  });

  const total = (clave: string) =>
    resumen && (clave ? clave.split(",").reduce((s, e) => s + (resumen[e] ?? 0), 0) : Object.values(resumen).reduce((a, b) => a + b, 0));

  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ justifyContent: "space-between", alignItems: { sm: "center" } }}>
        <div>
          <Typography variant="h5" component="h1">{esEmpresa ? "Mis convocatorias" : "Convocatorias"}</Typography>
          <Typography color="text.secondary">
            {esEmpresa
              ? "Crea convocatorias y envíalas a revisión. La oficina de prácticas las aprueba antes de publicarlas."
              : "Revisa las convocatorias de las empresas o publica convocatorias en nombre de una empresa aliada."}
          </Typography>
        </div>
        <Tooltip title={puedeCrear ? "" : "Tu empresa necesita estar aliada y con convenio vigente"}>
          <span>
            <Button variant="contained" startIcon={<AddIcon />} component={RouterLink} to={`${base}/convocatorias/nueva`} disabled={!puedeCrear}>
              Nueva convocatoria
            </Button>
          </span>
        </Tooltip>
      </Stack>

      {esEmpresa && !puedeCrear && (
        <Alert severity="warning">Tu empresa no tiene un convenio vigente: puedes consultar tus convocatorias, pero no crear ni enviar nuevas.</Alert>
      )}

      <Card>
        <Tabs value={estado} onChange={(_, valor) => { setEstado(valor); setPagina(0); }} variant="scrollable" allowScrollButtonsMobile>
          {pestanas.map((p) => (
            <Tab key={p.estado} value={p.estado} label={`${p.etiqueta}${total(p.estado) !== undefined ? ` (${total(p.estado)})` : ""}`} />
          ))}
        </Tabs>
        <Box sx={{ p: 2, pt: 1 }}>
          <TextField
            size="small"
            placeholder={esEmpresa ? "Buscar por título" : "Buscar por título o empresa"}
            value={texto}
            onChange={(e) => { setTexto(e.target.value); setPagina(0); }}
            slotProps={{ input: { startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment> } }}
            sx={{ width: "100%", maxWidth: 420 }}
          />
        </Box>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Convocatoria</TableCell>
                <TableCell>Programas afines</TableCell>
                <TableCell>Modalidad</TableCell>
                <TableCell align="center">Cupos</TableCell>
                <TableCell>Cierre</TableCell>
                <TableCell>Estado</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data?.results.map((c) => (
                <TableRow key={c.id} hover sx={{ cursor: "pointer" }} onClick={() => navegar(`${base}/convocatorias/${c.id}`)}>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{c.titulo}</Typography>
                    {!esEmpresa && <Typography variant="caption" color="text.secondary">{c.empresa_nombre}</Typography>}
                  </TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={0.5} useFlexGap sx={{ flexWrap: "wrap" }}>
                      {c.programas_detalle.slice(0, 2).map((p) => <Chip key={p.id} size="small" variant="outlined" label={p.nombre} />)}
                      {c.programas_detalle.length > 2 && <Chip size="small" label={`+${c.programas_detalle.length - 2}`} />}
                    </Stack>
                  </TableCell>
                  <TableCell>{c.modalidad_nombre}{c.ciudad_nombre ? ` · ${c.ciudad_nombre}` : ""}</TableCell>
                  <TableCell align="center">{c.cupos}</TableCell>
                  <TableCell>{fecha(c.fecha_cierre)}</TableCell>
                  <TableCell><EstadoChip estado={c.estado} etiqueta={c.estado_nombre} /></TableCell>
                </TableRow>
              ))}
              {data && data.results.length === 0 && (
                <TableRow><TableCell colSpan={6} sx={{ py: 4, textAlign: "center", color: "text.secondary" }}>{isFetching ? "Cargando…" : "No hay convocatorias en esta vista."}</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={data?.count ?? 0}
          page={pagina}
          onPageChange={(_, p) => setPagina(p)}
          rowsPerPage={20}
          rowsPerPageOptions={[20]}
          labelDisplayedRows={({ from, to, count }) => `${from}–${to} de ${count}`}
        />
      </Card>
    </Stack>
  );
}
