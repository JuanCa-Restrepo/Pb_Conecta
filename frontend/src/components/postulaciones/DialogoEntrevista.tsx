import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, TextField } from "@mui/material";
import { useEffect, useState } from "react";

import { api, leerErrores } from "../../api/cliente";
import { MODALIDADES_ENTREVISTA } from "../../api/opciones";

const mananaALas9 = () => {
  const fecha = new Date();
  fecha.setDate(fecha.getDate() + 1);
  fecha.setHours(9, 0, 0, 0);
  fecha.setMinutes(fecha.getMinutes() - fecha.getTimezoneOffset());
  return fecha.toISOString().slice(0, 16);
};

/** RF-55: la empresa programa la entrevista; el estudiante recibe la notificación con fecha y lugar. */
export function DialogoEntrevista({ abierto, postulacionId, onCerrar, onProgramada }: {
  abierto: boolean; postulacionId: number; onCerrar: () => void; onProgramada: () => void;
}) {
  const [form, setForm] = useState({ fecha_hora: mananaALas9(), modalidad: "VIRTUAL", lugar_o_enlace: "", notas: "" });
  const [errores, setErrores] = useState<{ general: string; campos: Record<string, string> }>({ general: "", campos: {} });
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (abierto) {
      setForm({ fecha_hora: mananaALas9(), modalidad: "VIRTUAL", lugar_o_enlace: "", notas: "" });
      setErrores({ general: "", campos: {} });
    }
  }, [abierto]);

  const campo = (nombre: keyof typeof form) => ({
    value: form[nombre],
    onChange: (e: { target: { value: string } }) => setForm({ ...form, [nombre]: e.target.value }),
    error: Boolean(errores.campos[nombre]),
    helperText: errores.campos[nombre],
    fullWidth: true,
  });

  async function programar() {
    setEnviando(true);
    try {
      await api.post(`/postulaciones/${postulacionId}/entrevistas/`, { ...form, fecha_hora: new Date(form.fecha_hora).toISOString() });
      onProgramada();
    } catch (e) {
      setErrores(leerErrores(e));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Dialog open={abierto} onClose={onCerrar} fullWidth maxWidth="sm">
      <DialogTitle>Programar entrevista</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {errores.general && <Alert severity="error">{errores.general}</Alert>}
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField label="Fecha y hora" type="datetime-local" required slotProps={{ inputLabel: { shrink: true } }} {...campo("fecha_hora")} />
            <TextField select label="Modalidad" {...campo("modalidad")}>
              {MODALIDADES_ENTREVISTA.map((m) => <MenuItem key={m.valor} value={m.valor}>{m.etiqueta}</MenuItem>)}
            </TextField>
          </Stack>
          <TextField
            label={form.modalidad === "PRESENCIAL" ? "Dirección" : form.modalidad === "VIRTUAL" ? "Enlace de la reunión" : "Teléfono"}
            required
            {...campo("lugar_o_enlace")}
          />
          <TextField label="Notas para el estudiante (opcional)" multiline minRows={2} {...campo("notas")} />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCerrar} disabled={enviando}>Cancelar</Button>
        <Button variant="contained" onClick={programar} disabled={enviando || !form.lugar_o_enlace.trim()}>Programar</Button>
      </DialogActions>
    </Dialog>
  );
}
