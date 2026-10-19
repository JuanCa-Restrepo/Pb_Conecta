import SearchIcon from "@mui/icons-material/Search";
import {
  Box, Card, InputAdornment, Stack, Tab, Table, TableBody, TableCell, TableContainer, TableHead, TablePagination, TableRow, Tabs,
  TextField, Typography,
} from "@mui/material";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import { api } from "../../api/cliente";
import type { Paginado, PostulacionResumen, Resumen } from "../../api/tipos";
import { useAuth } from "../../auth/AuthContext";
import { AfinidadChip } from "../../components/Afinidad";
import { EstadoChip } from "../../components/EstadoChip";
import { fecha, fechaHora } from "../../utilidades/formato";

const PESTANAS = [
  { estado: "POSTULADO,EN_REVISION,PRESELECCIONADO,ENTREVISTA,SELECCIONADO", etiqueta: "Activas" },
  { estado: "SELECCIONADO", etiqueta: "Seleccionadas" },
  { estado: "LEGALIZADO", etiqueta: "Legalizadas" },
  { estado: "NO_SELECCIONADO,RETIRADO,CERRADO_SISTEMA", etiqueta: "Cerradas" },
  { estado: "", etiqueta: "Todas" },
];

/** "Mis postulaciones" del estudiante (RF-51) y vista global de la oficina (RF-63). */
export default function ListaPostulaciones() {
  const { usuario } = useAuth();
  const navegar = useNavigate();
  const esEstudiante = usuario?.rol === "ESTUDIANTE";
  const base = esEstudiante ? "/estudiante" : "/oficina";
  const [estado, setEstado] = useState(PESTANAS[0].estado);
  const [texto, setTexto] = useState("");
  const [pagina, setPagina] = useState(0);

  const { data: resumen } = useQuery({ queryKey: ["postulaciones", "resumen"], queryFn: async () => (await api.get<Resumen>("/postulaciones/resumen/")).data });
  const { data, isFetching } = useQuery({
    queryKey: ["postulaciones", "lista", estado, texto, pagina],
    queryFn: async () =>
      (await api.get<Paginado<PostulacionResumen>>("/postulaciones/", { params: { estado: estado || undefined, q: texto || undefined, page: pagina + 1 } })).data,
    placeholderData: keepPreviousData,
  });
  const total = (clave: string) =>
    resumen && (clave ? clave.split(",").reduce((s, e) => s + (resumen[e] ?? 0), 0) : Object.values(resumen).reduce((a, b) => a + b, 0));

  return (
    <Stack spacing={2}>
      <div>
        <Typography variant="h5" component="h1">{esEstudiante ? "Mis postulaciones" : "Postulaciones"}</Typography>
        <Typography color="text.secondary">
          {esEstudiante ? "Sigue el estado de cada proceso y conversa con las empresas." : "Todos los procesos estudiante–empresa. Puedes intervenir en cualquiera y dejar notas internas."}
        </Typography>
      </div>
      <Card>
        <Tabs value={estado} onChange={(_, v) => { setEstado(v); setPagina(0); }} variant="scrollable" allowScrollButtonsMobile>
          {PESTANAS.map((p) => <Tab key={p.etiqueta} value={p.estado} label={`${p.etiqueta}${total(p.estado) !== undefined ? ` (${total(p.estado)})` : ""}`} />)}
        </Tabs>
        {!esEstudiante && (
          <Box sx={{ p: 2, pt: 1 }}>
            <TextField
              size="small"
              placeholder="Buscar por estudiante o convocatoria"
              value={texto}
              onChange={(e) => { setTexto(e.target.value); setPagina(0); }}
              slotProps={{ input: { startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment> } }}
              sx={{ width: "100%", maxWidth: 420 }}
            />
          </Box>
        )}
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                {!esEstudiante && <TableCell>Estudiante</TableCell>}
                <TableCell>Convocatoria</TableCell>
                <TableCell>Afinidad</TableCell>
                <TableCell>Postulación</TableCell>
                <TableCell>Próxima entrevista</TableCell>
                <TableCell>Estado</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data?.results.map((p) => (
                <TableRow key={p.id} hover sx={{ cursor: "pointer" }} onClick={() => navegar(`${base}/postulaciones/${p.id}`)}>
                  {!esEstudiante && (
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>{p.estudiante.nombre}</Typography>
                      <Typography variant="caption" color="text.secondary">{p.estudiante.programa}</Typography>
                    </TableCell>
                  )}
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: esEstudiante ? 600 : 400 }}>{p.convocatoria.titulo}</Typography>
                    <Typography variant="caption" color="text.secondary">{p.convocatoria.empresa}</Typography>
                  </TableCell>
                  <TableCell><AfinidadChip valor={p.afinidad} /></TableCell>
                  <TableCell>{fecha(p.creado_en)}</TableCell>
                  <TableCell>{p.proxima_entrevista ? fechaHora(p.proxima_entrevista.fecha_hora) : "—"}</TableCell>
                  <TableCell><EstadoChip estado={p.estado} etiqueta={p.estado_nombre} /></TableCell>
                </TableRow>
              ))}
              {data && data.results.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} sx={{ py: 4, textAlign: "center", color: "text.secondary" }}>
                    {isFetching ? "Cargando…" : esEstudiante ? <>Aún no tienes postulaciones aquí. <RouterLink to="/estudiante/convocatorias">Explora convocatorias</RouterLink>.</> : "No hay postulaciones en esta vista."}
                  </TableCell>
                </TableRow>
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
        />
      </Card>
    </Stack>
  );
}
