import { Button, Card, CardContent, CardHeader, Stack, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

import { leerErrores } from "../../api/cliente";
import { abrirArchivoProtegido } from "../../api/descargas";
import type { Practica } from "../../api/tipos";
import { fecha } from "../../utilidades/formato";
import { useAviso } from "../Avisos";
import { EstadoChip } from "../EstadoChip";

/** Resumen de la práctica legalizada. Lo ven el estudiante, la empresa y la oficina. */
export function TarjetaPractica({ practica, enlaceOficina = false }: { practica: Practica; enlaceOficina?: boolean }) {
  const avisar = useAviso();
  return (
    <Card>
      <CardHeader
        title="Práctica legalizada"
        slotProps={{ title: { variant: "h6" } }}
        action={<EstadoChip estado={practica.estado} etiqueta={practica.estado_nombre} />}
      />
      <CardContent sx={{ pt: 0 }}>
        <Stack spacing={0.5}>
          <Typography variant="body2"><strong>Fechas:</strong> {fecha(practica.fecha_inicio)} – {fecha(practica.fecha_fin)}</Typography>
          <Typography variant="body2"><strong>Vinculación:</strong> {practica.tipo_vinculacion_nombre}</Typography>
          <Typography variant="body2"><strong>Docente asesor:</strong> {practica.asesor_nombre}</Typography>
          <Typography variant="body2">
            <strong>Tutor en la empresa:</strong> {practica.tutor_empresa_nombre}{practica.tutor_empresa_email && ` · ${practica.tutor_empresa_email}`}
          </Typography>
          <Typography variant="caption" color="text.secondary">Legalizada por {practica.legalizada_por} el {fecha(practica.legalizada_en)}</Typography>
          {practica.observacion_cierre && (
            <Typography variant="body2" sx={{ mt: 1 }}><strong>Cierre:</strong> {practica.observacion_cierre}</Typography>
          )}
        </Stack>
        <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
          {practica.tiene_documento && (
            <Button size="small" onClick={() => abrirArchivoProtegido(`/practicas/${practica.id}/documento/`).catch((e) => avisar(leerErrores(e).general, "error"))}>
              Ver soporte
            </Button>
          )}
          {enlaceOficina && <Button size="small" component={RouterLink} to={`/oficina/practicas/${practica.id}`}>Gestionar práctica</Button>}
        </Stack>
      </CardContent>
    </Card>
  );
}
