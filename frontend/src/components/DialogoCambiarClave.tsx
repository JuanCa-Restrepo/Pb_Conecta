import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField } from "@mui/material";
import { useEffect, useState } from "react";

import { api, leerErrores } from "../api/cliente";
import { useAviso } from "./Avisos";

/** RF-05: cambio de contraseña desde la cuenta. */
export function DialogoCambiarClave({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const avisar = useAviso();
  const [form, setForm] = useState({ actual: "", password: "", confirmacion: "" });
  const [errores, setErrores] = useState<{ general: string; campos: Record<string, string> }>({ general: "", campos: {} });

  useEffect(() => {
    if (abierto) {
      setForm({ actual: "", password: "", confirmacion: "" });
      setErrores({ general: "", campos: {} });
    }
  }, [abierto]);

  const campo = (nombre: keyof typeof form, etiqueta: string, autoComplete: string) => ({
    label: etiqueta,
    type: "password",
    autoComplete,
    value: form[nombre],
    onChange: (e: { target: { value: string } }) => setForm({ ...form, [nombre]: e.target.value }),
    error: Boolean(errores.campos[nombre]),
    helperText: errores.campos[nombre],
    fullWidth: true,
  });

  async function guardar() {
    if (form.password !== form.confirmacion) {
      setErrores({ general: "", campos: { confirmacion: "Las contraseñas no coinciden." } });
      return;
    }
    try {
      await api.post("/auth/cambiar-clave/", { actual: form.actual, password: form.password });
      avisar("Contraseña actualizada.");
      onCerrar();
    } catch (e) {
      setErrores(leerErrores(e));
    }
  }

  return (
    <Dialog open={abierto} onClose={onCerrar} fullWidth maxWidth="xs">
      <DialogTitle>Cambiar contraseña</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {errores.general && <Alert severity="error">{errores.general}</Alert>}
          <TextField {...campo("actual", "Contraseña actual", "current-password")} />
          <TextField {...campo("password", "Contraseña nueva", "new-password")} helperText={errores.campos.password ?? "Mínimo 8 caracteres, no solo números."} />
          <TextField {...campo("confirmacion", "Repite la contraseña nueva", "new-password")} />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCerrar}>Cancelar</Button>
        <Button variant="contained" onClick={guardar} disabled={!form.actual || !form.password}>Guardar</Button>
      </DialogActions>
    </Dialog>
  );
}
