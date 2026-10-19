import DownloadIcon from "@mui/icons-material/Download";
import {
  Box, Button, Card, CardContent, CardHeader, FormControlLabel, LinearProgress, Menu, MenuItem, Stack, Switch, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, TextField, Typography,
} from "@mui/material";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import dayjs from "dayjs";
import { useState } from "react";

import { api, leerErrores } from "../../api/cliente";
import { descargarArchivo } from "../../api/descargas";
import type { Indicadores, Programa } from "../../api/tipos";
import { useAviso } from "../../components/Avisos";
import { BarrasAgrupadas } from "../../components/graficos/BarrasAgrupadas";
import { BarrasHorizontales } from "../../components/graficos/BarrasHorizontales";
import { grafico } from "../../theme";

const REPORTES = [
  { clave: "estudiantes", nombre: "Estudiantes" },
  { clave: "postulaciones", nombre: "Postulaciones" },
  { clave: "practicas", nombre: "Prácticas" },
  { clave: "convocatorias", nombre: "Convocatorias" },
  { clave: "empresas", nombre: "Empresas y convenios" },
];

// El embudo muestra el camino principal; retirados y cerrados por sistema se ven en la exportación
const ETAPAS_EMBUDO = ["POSTULADO", "EN_REVISION", "PRESELECCIONADO", "ENTREVISTA", "SELECCIONADO", "LEGALIZADO", "NO_SELECCIONADO"];

function Cifra({ valor, titulo, detalle }: { valor: string | number; titulo: string; detalle?: string }) {
  return (
    <Card sx={{ flex: "1 1 170px" }}>
      <CardContent>
        <Typography variant="h4" component="p" sx={{ fontWeight: 700 }}>{valor}</Typography>
        <Typography variant="subtitle2">{titulo}</Typography>
        {detalle && <Typography variant="caption" color="text.secondary">{detalle}</Typography>}
      </CardContent>
    </Card>
  );
}

/** RF-80 y RF-81: indicadores de la oficina y exportación a CSV. */
export function PanelIndicadores() {
  const avisar = useAviso();
  const [periodo, setPeriodo] = useState("");
  const [programa, setPrograma] = useState("");
  const [comoTabla, setComoTabla] = useState(false);
  const [menu, setMenu] = useState<HTMLElement | null>(null);

  const { data: periodos = [] } = useQuery({ queryKey: ["catalogos", "periodos"], queryFn: async () => (await api.get<{ id: number; codigo: string }[]>("/catalogos/periodos/")).data });
  const { data: programas = [] } = useQuery({ queryKey: ["catalogos", "programas"], queryFn: async () => (await api.get<Programa[]>("/catalogos/programas/")).data });
  const { data, isFetching } = useQuery({
    queryKey: ["oficina", "indicadores", periodo, programa],
    queryFn: async () => (await api.get<Indicadores>("/oficina/indicadores/", { params: { periodo: periodo || undefined, programa: programa || undefined } })).data,
    placeholderData: keepPreviousData,
  });

  async function exportar(clave: string) {
    setMenu(null);
    try {
      await descargarArchivo(`/oficina/exportar/${clave}.csv`, `pbconecta-${clave}.csv`);
    } catch (e) {
      avisar(leerErrores(e).general, "error");
    }
  }

  const embudo = (data?.embudo ?? [])
    .filter((e) => ETAPAS_EMBUDO.includes(e.estado))
    .sort((a, b) => ETAPAS_EMBUDO.indexOf(a.estado) - ETAPAS_EMBUDO.indexOf(b.estado));
  const tendencia = data?.tendencia ?? [];
  const meses = tendencia.map((t) => ({ clave: t.mes, etiqueta: dayjs(`${t.mes}-01`).format("MMM YYYY") }));
  const series = [
    { clave: "postulaciones", nombre: "Postulaciones", color: grafico.serie1 },
    { clave: "legalizaciones", nombre: "Prácticas legalizadas", color: grafico.serie2 },
  ];

  return (
    <Stack spacing={2}>
      {/* Filtros y exportación en una sola fila, encima de todo lo que afectan */}
      <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ alignItems: { md: "center" } }}>
        <Typography variant="h6" sx={{ flex: 1 }}>Indicadores</Typography>
        <TextField select size="small" label="Periodo" value={periodo} onChange={(e) => setPeriodo(e.target.value)}
          slotProps={{ select: { displayEmpty: true }, inputLabel: { shrink: true } }} sx={{ minWidth: 160 }}>
          <MenuItem value="">Todos</MenuItem>
          {periodos.map((p) => <MenuItem key={p.id} value={String(p.id)}>{p.codigo}</MenuItem>)}
        </TextField>
        <TextField select size="small" label="Programa" value={programa} onChange={(e) => setPrograma(e.target.value)}
          slotProps={{ select: { displayEmpty: true }, inputLabel: { shrink: true } }} sx={{ minWidth: 240 }}>
          <MenuItem value="">Todos los programas</MenuItem>
          {programas.map((p) => <MenuItem key={p.id} value={String(p.id)}>{p.nombre}</MenuItem>)}
        </TextField>
        <Button variant="outlined" startIcon={<DownloadIcon />} onClick={(e) => setMenu(e.currentTarget)}>Exportar CSV</Button>
        <Menu anchorEl={menu} open={Boolean(menu)} onClose={() => setMenu(null)}>
          {REPORTES.map((r) => <MenuItem key={r.clave} onClick={() => exportar(r.clave)}>{r.nombre}</MenuItem>)}
        </Menu>
      </Stack>
      {isFetching && <LinearProgress />}

      {data && (
        <>
          <Stack direction="row" spacing={2} useFlexGap sx={{ flexWrap: "wrap" }}>
            <Cifra valor={`${data.estudiantes.porcentaje_ubicacion} %`} titulo="Ubicación" detalle={`${data.estudiantes.ubicados} de ${data.estudiantes.habilitados} habilitados`} />
            <Cifra valor={data.estudiantes.en_busqueda} titulo="En búsqueda" detalle="Habilitados con postulaciones activas" />
            <Cifra
              valor={data.estudiantes.dias_promedio_hasta_ubicacion ?? "—"}
              titulo="Días hasta ubicarse"
              detalle="Promedio desde la habilitación"
            />
            <Cifra valor={data.oferta.convocatorias_activas} titulo="Convocatorias activas" detalle={`${data.oferta.cupos_ofertados} cupos ofertados`} />
            <Cifra
              valor={data.oferta.postulaciones_por_cupo ?? "—"}
              titulo="Postulaciones por cupo"
              detalle={`${data.oferta.postulaciones} postulaciones`}
            />
            <Cifra valor={data.oferta.empresas_aliadas} titulo="Empresas aliadas" detalle={`${data.oferta.empresas_pendientes} por aprobar`} />
          </Stack>

          <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr" } }}>
            <Card>
              <CardHeader title="Embudo de postulaciones" subheader="Cuántas postulaciones hay en cada etapa" slotProps={{ title: { variant: "subtitle1", fontWeight: 600 } }} />
              <CardContent sx={{ pt: 0 }}><BarrasHorizontales datos={embudo.map((e) => ({ etiqueta: e.nombre, valor: e.total }))} /></CardContent>
            </Card>
            <Card>
              <CardHeader
                title="Tendencia mensual"
                subheader="Últimos meses con actividad"
                slotProps={{ title: { variant: "subtitle1", fontWeight: 600 } }}
                action={<FormControlLabel control={<Switch size="small" checked={comoTabla} onChange={(e) => setComoTabla(e.target.checked)} />} label="Ver como tabla" />}
              />
              <CardContent sx={{ pt: 0 }}>
                {tendencia.length === 0 ? (
                  <Typography color="text.secondary">Todavía no hay actividad en este filtro.</Typography>
                ) : comoTabla ? (
                  <Table size="small">
                    <TableHead><TableRow><TableCell>Mes</TableCell><TableCell align="right">Postulaciones</TableCell><TableCell align="right">Legalizadas</TableCell></TableRow></TableHead>
                    <TableBody>
                      {tendencia.map((t, i) => (
                        <TableRow key={t.mes}>
                          <TableCell>{meses[i].etiqueta}</TableCell>
                          <TableCell align="right" sx={{ fontVariantNumeric: "tabular-nums" }}>{t.postulaciones}</TableCell>
                          <TableCell align="right" sx={{ fontVariantNumeric: "tabular-nums" }}>{t.legalizaciones}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <BarrasAgrupadas
                    categorias={meses}
                    series={series}
                    datos={Object.fromEntries(tendencia.map((t) => [t.mes, { postulaciones: t.postulaciones, legalizaciones: t.legalizaciones }]))}
                  />
                )}
              </CardContent>
            </Card>
          </Box>

          <Card>
            <CardHeader title="Por programa" subheader="Ordenado por número de habilitados" slotProps={{ title: { variant: "subtitle1", fontWeight: 600 } }} />
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Programa</TableCell>
                    <TableCell align="right">Registrados</TableCell>
                    <TableCell align="right">Habilitados</TableCell>
                    <TableCell align="right">Postulaciones</TableCell>
                    <TableCell align="right">Ubicados</TableCell>
                    <TableCell sx={{ minWidth: 160 }}>Ubicación</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.por_programa.map((f) => (
                    <TableRow key={f.programa}>
                      <TableCell>{f.programa}</TableCell>
                      {[f.registrados, f.habilitados, f.postulaciones, f.ubicados].map((v, i) => (
                        <TableCell key={i} align="right" sx={{ fontVariantNumeric: "tabular-nums" }}>{v}</TableCell>
                      ))}
                      <TableCell>
                        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                          <Box sx={{ flex: 1, height: 8, bgcolor: grafico.rejilla, borderRadius: 4, overflow: "hidden" }}>
                            <Box sx={{ width: `${f.porcentaje_ubicacion}%`, height: "100%", bgcolor: grafico.serie1, borderRadius: 4 }} />
                          </Box>
                          <Typography variant="body2" sx={{ fontVariantNumeric: "tabular-nums", minWidth: 48, textAlign: "right" }}>{f.porcentaje_ubicacion} %</Typography>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                  {data.por_programa.length === 0 && (
                    <TableRow><TableCell colSpan={6} sx={{ textAlign: "center", color: "text.secondary", py: 3 }}>Sin datos para este filtro.</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Card>
        </>
      )}
    </Stack>
  );
}
