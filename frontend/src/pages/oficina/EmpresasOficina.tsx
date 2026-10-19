import AddIcon from "@mui/icons-material/Add";
import {
  Button, Card, InputAdornment, Stack, Tab, Table, TableBody, TableCell, TableContainer, TableHead, TablePagination,
  TableRow, Tabs, TextField, Typography,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api/cliente";
import type { EmpresaOficina, Paginado, Resumen } from "../../api/tipos";
import { useAviso } from "../../components/Avisos";
import { EstadoChip } from "../../components/EstadoChip";
import { fecha } from "../../utilidades/formato";
import { CrearEmpresaDialogo } from "./CrearEmpresaDialogo";

const PESTANAS = [
  { estado: "PENDIENTE", etiqueta: "Pendientes" },
  { estado: "ALIADA", etiqueta: "Aliadas" },
  { estado: "CONVENIO_VENCIDO", etiqueta: "Convenio vencido" },
  { estado: "SUSPENDIDA", etiqueta: "Suspendidas" },
  { estado: "RECHAZADA", etiqueta: "Rechazadas" },
  { estado: "", etiqueta: "Todas" },
];

export default function EmpresasOficina() {
  const navegar = useNavigate();
  const avisar = useAviso();
  const [estado, setEstado] = useState("PENDIENTE");
  const [texto, setTexto] = useState("");
  const [pagina, setPagina] = useState(0);
  const [creando, setCreando] = useState(false);

  const { data: resumen } = useQuery({
    queryKey: ["oficina", "empresas", "resumen"],
    queryFn: async () => (await api.get<Resumen>("/oficina/empresas/resumen/")).data,
  });
  const { data, isFetching } = useQuery({
    queryKey: ["oficina", "empresas", estado, texto, pagina],
    queryFn: async () =>
      (await api.get<Paginado<EmpresaOficina>>("/oficina/empresas/", { params: { estado: estado || undefined, q: texto || undefined, page: pagina + 1 } })).data,
    placeholderData: keepPreviousData,
  });

  const total = (clave: string) => (clave ? resumen?.[clave] : resumen && Object.values(resumen).reduce((a, b) => a + b, 0));

  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ justifyContent: "space-between", alignItems: { sm: "center" } }}>
        <div>
          <Typography variant="h5" component="h1">Empresas y convenios</Typography>
          <Typography color="text.secondary">Aprueba solicitudes, registra convenios y gestiona el estado de las empresas aliadas.</Typography>
        </div>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreando(true)}>Registrar empresa</Button>
      </Stack>

      <Card>
        <Tabs value={estado} onChange={(_, valor) => { setEstado(valor); setPagina(0); }} variant="scrollable" allowScrollButtonsMobile>
          {PESTANAS.map((p) => (
            <Tab key={p.estado} value={p.estado} label={`${p.etiqueta}${total(p.estado) !== undefined ? ` (${total(p.estado)})` : ""}`} />
          ))}
        </Tabs>
        <Stack sx={{ p: 2, pt: 1 }}>
          <TextField
            size="small"
            placeholder="Buscar por razón social o NIT"
            value={texto}
            onChange={(e) => { setTexto(e.target.value); setPagina(0); }}
            slotProps={{ input: { startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment> } }}
            sx={{ maxWidth: 420 }}
          />
        </Stack>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Empresa</TableCell>
                <TableCell>Sector · ciudad</TableCell>
                <TableCell>Contacto</TableCell>
                <TableCell>Convenio vigente</TableCell>
                <TableCell>Estado</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data?.results.map((e) => (
                <TableRow key={e.id} hover sx={{ cursor: "pointer" }} onClick={() => navegar(`/oficina/empresas/${e.id}`)}>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{e.razon_social}</Typography>
                    <Typography variant="caption" color="text.secondary">NIT {e.nit}{e.creada_por_oficina ? " · registrada por la oficina" : ""}</Typography>
                  </TableCell>
                  <TableCell>{e.sector_nombre} · {e.ciudad_nombre}</TableCell>
                  <TableCell>
                    <Typography variant="body2">{e.contacto_nombre}</Typography>
                    <Typography variant="caption" color="text.secondary">{e.contacto_email}</Typography>
                  </TableCell>
                  <TableCell>{e.convenio_vigente ? `${e.convenio_vigente.numero} · hasta ${fecha(e.convenio_vigente.fecha_fin)}` : "—"}</TableCell>
                  <TableCell><EstadoChip estado={e.estado} etiqueta={e.estado_nombre} /></TableCell>
                </TableRow>
              ))}
              {data && data.results.length === 0 && (
                <TableRow><TableCell colSpan={5} sx={{ py: 4, textAlign: "center", color: "text.secondary" }}>{isFetching ? "Cargando…" : "No hay empresas en esta vista."}</TableCell></TableRow>
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

      <CrearEmpresaDialogo
        abierto={creando}
        onCerrar={() => setCreando(false)}
        onCreada={(empresa) => {
          setCreando(false);
          avisar(`${empresa.razon_social} quedó registrada como empresa aliada.`);
          navegar(`/oficina/empresas/${empresa.id}`);
        }}
      />
    </Stack>
  );
}
