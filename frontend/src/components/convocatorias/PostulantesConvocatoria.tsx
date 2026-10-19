import {
  Card, CardHeader, Tab, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Tabs, Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../api/cliente";
import type { Paginado, PostulacionResumen, Resumen } from "../../api/tipos";
import { fecha, fechaHora } from "../../utilidades/formato";
import { AfinidadChip } from "../Afinidad";
import { EstadoChip } from "../EstadoChip";

const PESTANAS = [
  { estado: "POSTULADO,EN_REVISION", etiqueta: "Por revisar" },
  { estado: "PRESELECCIONADO,ENTREVISTA", etiqueta: "En proceso" },
  { estado: "SELECCIONADO,LEGALIZADO", etiqueta: "Seleccionados" },
  { estado: "NO_SELECCIONADO,RETIRADO,CERRADO_SISTEMA", etiqueta: "Cerradas" },
  { estado: "", etiqueta: "Todas" },
];

/** RF-53: postulantes de una convocatoria, ordenados por afinidad. */
export function PostulantesConvocatoria({ convocatoriaId, base }: { convocatoriaId: number; base: string }) {
  const navegar = useNavigate();
  const [estado, setEstado] = useState(PESTANAS[0].estado);

  const { data: resumen } = useQuery({
    queryKey: ["postulaciones", "resumen", convocatoriaId],
    queryFn: async () => (await api.get<Resumen>("/postulaciones/resumen/", { params: { convocatoria: convocatoriaId } })).data,
  });
  const { data } = useQuery({
    queryKey: ["postulaciones", "convocatoria", convocatoriaId, estado],
    queryFn: async () =>
      (await api.get<Paginado<PostulacionResumen>>("/postulaciones/", {
        params: { convocatoria: convocatoriaId, estado: estado || undefined, orden: "afinidad", tamano: 200 },
      })).data,
  });

  const total = (clave: string) =>
    resumen && (clave ? clave.split(",").reduce((s, e) => s + (resumen[e] ?? 0), 0) : Object.values(resumen).reduce((a, b) => a + b, 0));

  return (
    <Card>
      <CardHeader title="Postulantes" subheader="Ordenados por índice de afinidad" slotProps={{ title: { variant: "h6" } }} />
      <Tabs value={estado} onChange={(_, valor) => setEstado(valor)} variant="scrollable" allowScrollButtonsMobile>
        {PESTANAS.map((p) => <Tab key={p.estado} value={p.estado} label={`${p.etiqueta}${total(p.estado) !== undefined ? ` (${total(p.estado)})` : ""}`} />)}
      </Tabs>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Estudiante</TableCell>
              <TableCell>Afinidad</TableCell>
              <TableCell>Postulado</TableCell>
              <TableCell>Entrevista</TableCell>
              <TableCell>Estado</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.results.map((p) => (
              <TableRow key={p.id} hover sx={{ cursor: "pointer" }} onClick={() => navegar(`${base}/postulaciones/${p.id}`)}>
                <TableCell>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>{p.estudiante.nombre}</Typography>
                  <Typography variant="caption" color="text.secondary">{p.estudiante.programa}{p.estudiante.semestre ? ` · semestre ${p.estudiante.semestre}` : ""}</Typography>
                </TableCell>
                <TableCell><AfinidadChip valor={p.afinidad} /></TableCell>
                <TableCell>{fecha(p.creado_en)}</TableCell>
                <TableCell>{p.proxima_entrevista ? fechaHora(p.proxima_entrevista.fecha_hora) : "—"}</TableCell>
                <TableCell><EstadoChip estado={p.estado} etiqueta={p.estado_nombre} /></TableCell>
              </TableRow>
            ))}
            {data && data.results.length === 0 && (
              <TableRow><TableCell colSpan={5} sx={{ py: 4, textAlign: "center", color: "text.secondary" }}>No hay postulantes en esta vista.</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Card>
  );
}
