import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import RadioButtonUncheckedIcon from "@mui/icons-material/RadioButtonUnchecked";
import { Box, Chip, LinearProgress, Stack, Tooltip, Typography, type ChipProps } from "@mui/material";
import type { ReactNode } from "react";

import type { Afinidad as DatosAfinidad } from "../api/tipos";

function color(valor: number): "success" | "primary" | "warning" | "inherit" {
  if (valor >= 80) return "success";
  if (valor >= 60) return "primary";
  if (valor > 0) return "warning";
  return "inherit";
}

/** Índice de afinidad compacto (RF-42, RF-53). */
export function AfinidadChip({ valor, size = "small" }: { valor: number; size?: ChipProps["size"] }) {
  return (
    <Tooltip title="Índice de afinidad: programa, habilidades, modalidad y disponibilidad">
      <Chip size={size} color={valor ? color(valor) as ChipProps["color"] : "default"} variant={valor ? "filled" : "outlined"} label={`${valor} % afinidad`} />
    </Tooltip>
  );
}

function Criterio({ ok, children }: { ok: boolean; children: ReactNode }) {
  return (
    <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
      {ok ? <CheckCircleIcon fontSize="small" color="success" /> : <RadioButtonUncheckedIcon fontSize="small" color="disabled" />}
      <Typography variant="body2">{children}</Typography>
    </Stack>
  );
}

/** Desglose explicable del índice (arquitectura 3.7). */
export function AfinidadDetalle({ afinidad }: { afinidad: DatosAfinidad }) {
  const requeridas = afinidad.habilidades_coinciden.length + afinidad.habilidades_faltan.length;
  return (
    <Stack spacing={1}>
      <Box>
        <Stack direction="row" sx={{ justifyContent: "space-between", mb: 0.5 }}>
          <Typography variant="subtitle2">Afinidad</Typography>
          <Typography variant="subtitle2" sx={{ fontVariantNumeric: "tabular-nums" }}>{afinidad.total} %</Typography>
        </Stack>
        <LinearProgress variant="determinate" value={afinidad.total} color={color(afinidad.total)} sx={{ height: 8, borderRadius: 4 }} />
      </Box>
      <Criterio ok={afinidad.es_afin}>{afinidad.es_afin ? "Programa afín" : "El programa no está entre los afines"}</Criterio>
      <Criterio ok={requeridas === 0 || afinidad.habilidades_faltan.length === 0}>
        {requeridas === 0 ? "No pide habilidades específicas" : `${afinidad.habilidades_coinciden.length} de ${requeridas} habilidades requeridas`}
        {afinidad.habilidades_faltan.length > 0 && ` (faltan: ${afinidad.habilidades_faltan.join(", ")})`}
      </Criterio>
      <Criterio ok={afinidad.modalidad}>Modalidad acorde a la preferencia del estudiante</Criterio>
      <Criterio ok={afinidad.disponibilidad}>Disponible antes del inicio</Criterio>
    </Stack>
  );
}
