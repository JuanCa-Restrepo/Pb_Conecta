import SearchIcon from "@mui/icons-material/Search";
import {
  Box, Card, InputAdornment, Stack, Tab, Table, TableBody, TableCell, TableContainer, TableHead, TablePagination, TableRow,
  Tabs, TextField, Typography,
} from "@mui/material";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api/cliente";
import type { Paginado, Practica, Resumen } from "../../api/tipos";
import { EstadoChip } from "../../components/EstadoChip";
import { fecha } from "../../utilidades/formato";

const PESTANAS = [
  { estado: "LEGALIZADA,EN_CURSO", etiqueta: "Activas" },
  { estado: "LEGALIZADA", etiqueta: "Por iniciar" },
  { estado: "EN_CURSO", etiqueta: "En curso" },
  { estado: "FINALIZADA", etiqueta: "Finalizadas" },
  { estado: "CANCELADA", etiqueta: "Canceladas" },
  { estado: "", etiqueta: "Todas" },
];

export default function PracticasOficina() {
  const navegar = useNavigate();
  const [estado, setEstado] = useState(PESTANAS[0].estado);
  const [texto, setTexto] = useState("");
  const [pagina, setPagina] = useState(0);

  const { data: resumen } = useQuery({ queryKey: ["practicas", "resumen"], queryFn: async () => (await api.get<Resumen>("/practicas/resumen/")).data });
  const { data, isFetching } = useQuery({
    queryKey: ["practicas", "lista", estado, texto, pagina],
    queryFn: async () => (await api.get<Paginado<Practica>>("/practicas/", { params: { estado: estado || undefined, q: texto || undefined, page: pagina + 1 } })).data,
    placeholderData: keepPreviousData,
  });
  const total = (clave: string) =>
    resumen && (clave ? clave.split(",").reduce((s, e) => s + (resumen[e] ?? 0), 0) : Object.values(resumen).reduce((a, b) => a + b, 0));

  return (
    <Stack spacing={2}>
      <div>
        <Typography variant="h5" component="h1">Prácticas</Typography>
        <Typography color="text.secondary">Prácticas legalizadas: seguimiento hasta su cierre (RF-64, RF-65).</Typography>
      </div>
      <Card>
        <Tabs value={estado} onChange={(_, v) => { setEstado(v); setPagina(0); }} variant="scrollable" allowScrollButtonsMobile>
          {PESTANAS.map((p) => <Tab key={p.etiqueta} value={p.estado} label={`${p.etiqueta}${total(p.estado) !== undefined ? ` (${total(p.estado)})` : ""}`} />)}
        </Tabs>
        <Box sx={{ p: 2, pt: 1 }}>
          <TextField
            size="small"
            placeholder="Buscar por estudiante o empresa"
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
                <TableCell>Estudiante</TableCell>
                <TableCell>Empresa · convocatoria</TableCell>
                <TableCell>Fechas</TableCell>
                <TableCell>Docente asesor</TableCell>
                <TableCell>Estado</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data?.results.map((p) => (
                <TableRow key={p.id} hover sx={{ cursor: "pointer" }} onClick={() => navegar(`/oficina/practicas/${p.id}`)}>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{p.estudiante.nombre}</Typography>
                    <Typography variant="caption" color="text.secondary">{p.estudiante.programa}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{p.convocatoria.empresa}</Typography>
                    <Typography variant="caption" color="text.secondary">{p.convocatoria.titulo}</Typography>
                  </TableCell>
                  <TableCell>{fecha(p.fecha_inicio)} – {fecha(p.fecha_fin)}</TableCell>
                  <TableCell>{p.asesor_nombre}</TableCell>
                  <TableCell><EstadoChip estado={p.estado} etiqueta={p.estado_nombre} /></TableCell>
                </TableRow>
              ))}
              {data && data.results.length === 0 && (
                <TableRow><TableCell colSpan={5} sx={{ py: 4, textAlign: "center", color: "text.secondary" }}>{isFetching ? "Cargando…" : "No hay prácticas en esta vista."}</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination component="div" count={data?.count ?? 0} page={pagina} onPageChange={(_, p) => setPagina(p)} rowsPerPage={20} rowsPerPageOptions={[20]} />
      </Card>
    </Stack>
  );
}
