import { Box, Chip, Divider, Stack, Typography } from "@mui/material";
import type { ReactNode } from "react";

import type { Convocatoria } from "../../api/tipos";
import { fecha, fechaHora, pesos } from "../../utilidades/formato";

function Dato({ etiqueta, children }: { etiqueta: string; children: ReactNode }) {
  return (
    <Box sx={{ minWidth: 160, flex: "1 1 160px" }}>
      <Typography variant="caption" color="text.secondary">{etiqueta}</Typography>
      <Typography variant="body2">{children}</Typography>
    </Box>
  );
}

function Seccion({ titulo, texto }: { titulo: string; texto: string }) {
  return (
    <div>
      <Typography variant="subtitle2" gutterBottom>{titulo}</Typography>
      <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>{texto}</Typography>
    </div>
  );
}

/** Condiciones, programas, habilidades y textos de una convocatoria. La comparten todos los roles. */
export function InfoConvocatoria({ c, mostrarAutoria = true }: { c: Convocatoria; mostrarAutoria?: boolean }) {
  return (
    <>
      <Stack direction="row" useFlexGap spacing={2} sx={{ flexWrap: "wrap" }}>
        <Dato etiqueta="Tipo de vinculación">{c.tipo_vinculacion_nombre}</Dato>
        <Dato etiqueta="Modalidad">{c.modalidad_nombre}{c.ciudad_nombre ? ` · ${c.ciudad_nombre}` : ""}</Dato>
        <Dato etiqueta="Apoyo económico">{pesos(c.apoyo_economico)}</Dato>
        <Dato etiqueta="Cupos">{c.cupos}</Dato>
        <Dato etiqueta="Inicio · duración">{fecha(c.fecha_inicio)} · {c.duracion_meses} meses</Dato>
        <Dato etiqueta="Cierre de la convocatoria">{fecha(c.fecha_cierre)}</Dato>
        <Dato etiqueta="Nivel de formación">{c.nivel_formacion_nombre}</Dato>
        <Dato etiqueta="Publicada">{c.publicada_en ? fechaHora(c.publicada_en) : "—"}</Dato>
      </Stack>
      <Divider sx={{ my: 2 }} />
      <Typography variant="subtitle2" gutterBottom>Programas afines</Typography>
      <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap", mb: 2 }}>
        {c.programas_detalle.map((p) => <Chip key={p.id} label={p.nombre} color="primary" variant="outlined" />)}
      </Stack>
      {c.habilidades_detalle.length > 0 && (
        <>
          <Typography variant="subtitle2" gutterBottom>Habilidades requeridas</Typography>
          <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap", mb: 2 }}>
            {c.habilidades_detalle.map((h) => <Chip key={h.id} size="small" label={h.nombre} />)}
          </Stack>
        </>
      )}
      <Divider sx={{ mb: 2 }} />
      <Stack spacing={2}>
        <Seccion titulo="Descripción" texto={c.descripcion} />
        <Seccion titulo="Funciones" texto={c.funciones} />
      </Stack>
      {mostrarAutoria && (
        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 3 }}>
          Creada por {c.creada_por_nombre} el {fecha(c.creado_en)} · última actualización {fechaHora(c.actualizado_en)}
        </Typography>
      )}
    </>
  );
}
