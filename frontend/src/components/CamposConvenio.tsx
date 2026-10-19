import { Box, Button, Stack, TextField, Typography } from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";

import { enDiasISO, hoyISO } from "../utilidades/formato";

export interface DatosConvenio {
  numero: string;
  fecha_inicio: string;
  fecha_fin: string;
  documento: File | null;
}

export const convenioInicial = (): DatosConvenio => ({ numero: "", fecha_inicio: hoyISO(), fecha_fin: enDiasISO(365), documento: null });

/** Agrega los campos del convenio a un FormData (multipart, para poder enviar el PDF). */
export function agregarConvenio(formulario: FormData, convenio: DatosConvenio) {
  formulario.append("numero", convenio.numero.trim());
  formulario.append("fecha_inicio", convenio.fecha_inicio);
  formulario.append("fecha_fin", convenio.fecha_fin);
  if (convenio.documento) formulario.append("documento", convenio.documento);
}

interface Props {
  valor: DatosConvenio;
  onCambio: (valor: DatosConvenio) => void;
  errores: Record<string, string>;
}

export function CamposConvenio({ valor, onCambio, errores }: Props) {
  const campo = (nombre: "numero" | "fecha_inicio" | "fecha_fin") => ({
    value: valor[nombre],
    onChange: (e: { target: { value: string } }) => onCambio({ ...valor, [nombre]: e.target.value }),
    error: Boolean(errores[nombre]),
    helperText: errores[nombre],
  });

  return (
    <Stack spacing={2}>
      <TextField label="Número del convenio" placeholder="CONV-2026-001" required {...campo("numero")} />
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <TextField label="Inicio" type="date" fullWidth required slotProps={{ inputLabel: { shrink: true } }} {...campo("fecha_inicio")} />
        <TextField label="Fin" type="date" fullWidth required slotProps={{ inputLabel: { shrink: true } }} {...campo("fecha_fin")} />
      </Stack>
      <Box>
        <Button component="label" variant="outlined" startIcon={<UploadFileIcon />}>
          {valor.documento ? "Cambiar PDF" : "Adjuntar convenio (PDF, opcional)"}
          <input
            hidden
            type="file"
            accept="application/pdf,.pdf"
            onChange={(e) => onCambio({ ...valor, documento: e.target.files?.[0] ?? null })}
          />
        </Button>
        {valor.documento && <Typography variant="body2" sx={{ mt: 1 }}>{valor.documento.name}</Typography>}
        {errores.documento && <Typography variant="body2" color="error" sx={{ mt: 1 }}>{errores.documento}</Typography>}
      </Box>
    </Stack>
  );
}
