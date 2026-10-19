import HistoryIcon from "@mui/icons-material/History";
import SearchIcon from "@mui/icons-material/Search";
import {
  Alert, Button, Card, Checkbox, Chip, Dialog, DialogActions, DialogContent, DialogTitle, IconButton, InputAdornment,
  List, ListItem, ListItemText, MenuItem, Stack, Tab, Table, TableBody, TableCell, TableContainer, TableHead,
  TablePagination, TableRow, Tabs, TextField, Tooltip, Typography,
} from "@mui/material";
import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../api/cliente";
import type { EstudianteOficina, NotaAsesoria, Paginado, Programa, Resumen } from "../../api/tipos";
import { useAviso } from "../../components/Avisos";
import { DialogoTexto } from "../../components/DialogoTexto";
import { EstadoChip } from "../../components/EstadoChip";
import { fecha, fechaHora } from "../../utilidades/formato";

const PESTANAS = [
  { estado: "NO_HABILITADO", etiqueta: "Por habilitar" },
  { estado: "HABILITADO", etiqueta: "Habilitados" },
  { estado: "UBICADO,EN_PRACTICA", etiqueta: "Ubicados y en práctica" },
  { estado: "PRACTICA_FINALIZADA", etiqueta: "Práctica finalizada" },
  { estado: "", etiqueta: "Todos" },
];

type Accion = { tipo: "habilitar" | "deshabilitar"; estudiante: EstudianteOficina } | { tipo: "varios" } | null;

/** Historial de habilitación y notas de asesoría (RF-67) de un estudiante. */
function Seguimiento({ estudiante, onCerrar }: { estudiante: EstudianteOficina | null; onCerrar: () => void }) {
  const cliente = useQueryClient();
  const [nota, setNota] = useState("");
  const { data } = useQuery({
    queryKey: ["oficina", "estudiante", estudiante?.id],
    queryFn: async () => (await api.get<EstudianteOficina>(`/oficina/estudiantes/${estudiante!.id}/`)).data,
    enabled: Boolean(estudiante),
  });
  const claveNotas = ["oficina", "estudiante", estudiante?.id, "notas"];
  const { data: notas = [] } = useQuery({
    queryKey: claveNotas,
    queryFn: async () => (await api.get<NotaAsesoria[]>(`/oficina/estudiantes/${estudiante!.id}/notas/`)).data,
    enabled: Boolean(estudiante),
  });

  async function guardarNota() {
    const { data: actualizadas } = await api.post<NotaAsesoria[]>(`/oficina/estudiantes/${estudiante!.id}/notas/`, { texto: nota });
    cliente.setQueryData(claveNotas, actualizadas);
    setNota("");
  }

  return (
    <Dialog open={Boolean(estudiante)} onClose={onCerrar} fullWidth maxWidth="sm">
      <DialogTitle>Seguimiento · {estudiante?.nombre}</DialogTitle>
      <DialogContent>
        <Typography variant="subtitle2">Historial de habilitación</Typography>
        {data?.historial?.length === 0 && <Typography variant="body2" color="text.secondary">Sin movimientos todavía.</Typography>}
        <List dense>
          {data?.historial?.map((h) => (
            <ListItem key={h.id} divider>
              <ListItemText
                primary={`${h.accion_nombre} · periodo ${h.periodo}`}
                secondary={`${fechaHora(h.creado_en)} · ${h.funcionario}${h.observacion ? ` · ${h.observacion}` : ""}`}
              />
            </ListItem>
          ))}
        </List>

        <Typography variant="subtitle2" sx={{ mt: 2 }}>Notas de asesoría</Typography>
        <Typography variant="caption" color="text.secondary">Solo las ve la oficina de prácticas.</Typography>
        <List dense>
          {notas.map((n) => (
            <ListItem key={n.id} divider>
              <ListItemText primary={n.texto} secondary={`${fechaHora(n.creado_en)} · ${n.autor}`} />
            </ListItem>
          ))}
        </List>
        <Stack direction="row" spacing={1} sx={{ alignItems: "flex-start" }}>
          <TextField size="small" label="Nueva nota" value={nota} onChange={(e) => setNota(e.target.value)} multiline fullWidth />
          <Button variant="contained" onClick={guardarNota} disabled={!nota.trim()}>Agregar</Button>
        </Stack>
      </DialogContent>
      <DialogActions><Button onClick={onCerrar}>Cerrar</Button></DialogActions>
    </Dialog>
  );
}

export default function EstudiantesOficina() {
  const cliente = useQueryClient();
  const avisar = useAviso();
  const [estado, setEstado] = useState("NO_HABILITADO");
  const [texto, setTexto] = useState("");
  const [programa, setPrograma] = useState("");
  const [pagina, setPagina] = useState(0);
  const [seleccion, setSeleccion] = useState<number[]>([]);
  const [accion, setAccion] = useState<Accion>(null);
  const [historial, setHistorial] = useState<EstudianteOficina | null>(null);

  const { data: programas = [] } = useQuery({ queryKey: ["catalogos", "programas"], queryFn: async () => (await api.get<Programa[]>("/catalogos/programas/")).data });
  const { data: resumen } = useQuery({ queryKey: ["oficina", "estudiantes", "resumen"], queryFn: async () => (await api.get<Resumen>("/oficina/estudiantes/resumen/")).data });
  const { data, isFetching } = useQuery({
    queryKey: ["oficina", "estudiantes", estado, texto, programa, pagina],
    queryFn: async () =>
      (await api.get<Paginado<EstudianteOficina>>("/oficina/estudiantes/", {
        params: { estado: estado || undefined, q: texto || undefined, programa: programa || undefined, page: pagina + 1 },
      })).data,
    placeholderData: keepPreviousData,
  });

  const filas = data?.results ?? [];
  const seleccionables = filas.filter((f) => f.estado === "NO_HABILITADO").map((f) => f.id);
  const total = (clave: string) =>
    resumen && (clave ? clave.split(",").reduce((suma, e) => suma + (resumen[e] ?? 0), 0) : Object.values(resumen).reduce((a, b) => a + b, 0));

  function refrescar() {
    setSeleccion([]);
    cliente.invalidateQueries({ queryKey: ["oficina", "estudiantes"] });
    cliente.invalidateQueries({ queryKey: ["oficina", "estudiante"] });
  }

  function cambiarFiltro(cambio: () => void) {
    cambio();
    setPagina(0);
    setSeleccion([]);
  }

  async function confirmar(texto: string) {
    if (!accion) return;
    if (accion.tipo === "varios") {
      const { data: resultado } = await api.post<{ habilitados: number[]; omitidos: { nombre: string; motivo: string }[] }>(
        "/oficina/estudiantes/habilitar-varios/", { ids: seleccion, observacion: texto },
      );
      const omitidos = resultado.omitidos.length ? ` · ${resultado.omitidos.length} omitidos` : "";
      avisar(`${resultado.habilitados.length} estudiantes habilitados${omitidos}.`, resultado.omitidos.length ? "warning" : "success");
    } else {
      await api.post(`/oficina/estudiantes/${accion.estudiante.id}/${accion.tipo}/`, { observacion: texto });
      avisar(accion.tipo === "habilitar" ? `${accion.estudiante.nombre} quedó habilitado.` : `Se retiró la habilitación de ${accion.estudiante.nombre}.`);
    }
    refrescar();
  }

  return (
    <Stack spacing={2}>
      <div>
        <Typography variant="h5" component="h1">Estudiantes y habilitación</Typography>
        <Typography color="text.secondary">Habilita a los estudiantes que cumplen los requisitos para que puedan postularse (RF-62).</Typography>
      </div>

      <Card>
        <Tabs value={estado} onChange={(_, valor) => cambiarFiltro(() => setEstado(valor))} variant="scrollable" allowScrollButtonsMobile>
          {PESTANAS.map((p) => (
            <Tab key={p.estado} value={p.estado} label={`${p.etiqueta}${total(p.estado) !== undefined ? ` (${total(p.estado)})` : ""}`} />
          ))}
        </Tabs>
        <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ p: 2, pt: 1 }}>
          <TextField
            size="small"
            placeholder="Buscar por nombre, correo o documento"
            value={texto}
            onChange={(e) => cambiarFiltro(() => setTexto(e.target.value))}
            slotProps={{ input: { startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment> } }}
            sx={{ flex: 1, maxWidth: { md: 380 } }}
          />
          <TextField
            select
            size="small"
            label="Programa"
            value={programa}
            onChange={(e) => cambiarFiltro(() => setPrograma(e.target.value))}
            slotProps={{ select: { displayEmpty: true }, inputLabel: { shrink: true } }}
            sx={{ minWidth: 260 }}
          >
            <MenuItem value="">Todos los programas</MenuItem>
            {programas.map((p) => <MenuItem key={p.id} value={String(p.id)}>{p.nombre}</MenuItem>)}
          </TextField>
        </Stack>

        {seleccion.length > 0 && (
          <Alert severity="info" sx={{ mx: 2, mb: 2 }} action={<Button color="inherit" onClick={() => setAccion({ tipo: "varios" })}>Habilitar seleccionados</Button>}>
            {seleccion.length} estudiante(s) seleccionado(s).
          </Alert>
        )}

        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox">
                  <Checkbox
                    disabled={seleccionables.length === 0}
                    checked={seleccionables.length > 0 && seleccionables.every((s) => seleccion.includes(s))}
                    onChange={(e) => setSeleccion(e.target.checked ? seleccionables : [])}
                    slotProps={{ input: { "aria-label": "Seleccionar todos los de esta página" } }}
                  />
                </TableCell>
                <TableCell>Estudiante</TableCell>
                <TableCell>Programa</TableCell>
                <TableCell>Sem.</TableCell>
                <TableCell>Estado</TableCell>
                <TableCell>Último movimiento</TableCell>
                <TableCell align="right">Acciones</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filas.map((f) => (
                <TableRow key={f.id} hover selected={seleccion.includes(f.id)}>
                  <TableCell padding="checkbox">
                    <Checkbox
                      disabled={f.estado !== "NO_HABILITADO"}
                      checked={seleccion.includes(f.id)}
                      onChange={(e) => setSeleccion(e.target.checked ? [...seleccion, f.id] : seleccion.filter((s) => s !== f.id))}
                      slotProps={{ input: { "aria-label": `Seleccionar a ${f.nombre}` } }}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{f.nombre}</Typography>
                    <Typography variant="caption" color="text.secondary">{f.email}</Typography>
                    {!f.correo_verificado && <Chip size="small" variant="outlined" color="warning" label="Correo sin verificar" sx={{ ml: 1 }} />}
                  </TableCell>
                  <TableCell>{f.programa_nombre}</TableCell>
                  <TableCell>{f.semestre ?? "—"}</TableCell>
                  <TableCell><EstadoChip estado={f.estado} etiqueta={f.estado_nombre} /></TableCell>
                  <TableCell>
                    {f.ultima_habilitacion ? (
                      <Typography variant="caption">
                        {f.ultima_habilitacion.accion_nombre} · {f.ultima_habilitacion.periodo} · {fecha(f.ultima_habilitacion.creado_en)}
                      </Typography>
                    ) : "—"}
                  </TableCell>
                  <TableCell align="right" sx={{ whiteSpace: "nowrap" }}>
                    {f.estado === "NO_HABILITADO" && <Button size="small" onClick={() => setAccion({ tipo: "habilitar", estudiante: f })}>Habilitar</Button>}
                    {f.estado === "HABILITADO" && <Button size="small" color="error" onClick={() => setAccion({ tipo: "deshabilitar", estudiante: f })}>Deshabilitar</Button>}
                    <Tooltip title="Historial y notas de asesoría">
                      <IconButton size="small" aria-label={`Historial de ${f.nombre}`} onClick={() => setHistorial(f)}><HistoryIcon fontSize="small" /></IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
              {data && filas.length === 0 && (
                <TableRow><TableCell colSpan={7} sx={{ py: 4, textAlign: "center", color: "text.secondary" }}>{isFetching ? "Cargando…" : "No hay estudiantes en esta vista."}</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={data?.count ?? 0}
          page={pagina}
          onPageChange={(_, p) => { setPagina(p); setSeleccion([]); }}
          rowsPerPage={20}
          rowsPerPageOptions={[20]}
          labelDisplayedRows={({ from, to, count }) => `${from}–${to} de ${count}`}
        />
      </Card>

      <DialogoTexto
        abierto={accion?.tipo === "habilitar" || accion?.tipo === "varios"}
        titulo={accion?.tipo === "varios" ? `Habilitar ${seleccion.length} estudiante(s)` : `Habilitar a ${accion && "estudiante" in accion ? accion.estudiante.nombre : ""}`}
        descripcion="Confirma que la oficina verificó los requisitos. Se registra en el periodo vigente y el estudiante recibe una notificación."
        etiqueta="Observación (opcional)"
        textoConfirmar="Habilitar"
        onCerrar={() => setAccion(null)}
        onConfirmar={confirmar}
      />
      <DialogoTexto
        abierto={accion?.tipo === "deshabilitar"}
        titulo={`Deshabilitar a ${accion && "estudiante" in accion ? accion.estudiante.nombre : ""}`}
        descripcion="El estudiante verá el motivo. Sus postulaciones activas se mantienen, pero no podrá crear nuevas (RN-15)."
        etiqueta="Motivo"
        obligatorio
        textoConfirmar="Deshabilitar"
        colorConfirmar="error"
        onCerrar={() => setAccion(null)}
        onConfirmar={confirmar}
      />
      <Seguimiento estudiante={historial} onCerrar={() => setHistorial(null)} />
    </Stack>
  );
}
