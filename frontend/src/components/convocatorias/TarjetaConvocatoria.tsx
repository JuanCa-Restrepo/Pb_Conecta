import { Card, CardActionArea, CardContent, Chip, Stack, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

import type { Convocatoria } from "../../api/tipos";
import { fecha, pesos } from "../../utilidades/formato";
import { AfinidadChip } from "../Afinidad";
import { EstadoChip } from "../EstadoChip";

/** Tarjeta de convocatoria para el estudiante: afinidad y estado de su postulación a la vista. */
export function TarjetaConvocatoria({ c }: { c: Convocatoria }) {
  const datos = c.para_estudiante;
  return (
    <Card sx={{ height: "100%" }}>
      <CardActionArea component={RouterLink} to={`/estudiante/convocatorias/${c.id}`} sx={{ height: "100%", alignItems: "flex-start" }}>
        <CardContent>
          <Stack direction="row" spacing={1} useFlexGap sx={{ mb: 1, flexWrap: "wrap" }}>
            {datos && <AfinidadChip valor={datos.afinidad.total} />}
            {datos?.postulacion && <EstadoChip estado={datos.postulacion.estado} etiqueta={`Postulado · ${datos.postulacion.estado_nombre}`} />}
            {datos && !datos.afinidad.es_afin && <Chip size="small" variant="outlined" label="Otro programa" />}
          </Stack>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, lineHeight: 1.3 }}>{c.titulo}</Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>{c.empresa_nombre}</Typography>
          <Typography variant="body2">{c.modalidad_nombre}{c.ciudad_nombre ? ` · ${c.ciudad_nombre}` : ""} · {c.tipo_vinculacion_nombre}</Typography>
          <Typography variant="body2">{pesos(c.apoyo_economico)}</Typography>
          <Typography variant="caption" color="text.secondary">Cierra el {fecha(c.fecha_cierre)}</Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
