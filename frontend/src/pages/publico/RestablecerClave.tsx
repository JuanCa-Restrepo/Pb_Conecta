import { Alert, Box, Button, Card, CardContent, Link, Stack, TextField, Typography } from "@mui/material";
import { useState, type FormEvent } from "react";
import { Link as RouterLink, useSearchParams } from "react-router-dom";

import { api, leerErrores } from "../../api/cliente";

/** RF-05: crea la contraseña nueva con el enlace recibido por correo (sirve una sola vez). */
export default function RestablecerClave() {
  const [parametros] = useSearchParams();
  const [password, setPassword] = useState("");
  const [confirmacion, setConfirmacion] = useState("");
  const [errores, setErrores] = useState<{ general: string; campos: Record<string, string> }>({ general: "", campos: {} });
  const [listo, setListo] = useState("");

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    if (password !== confirmacion) {
      setErrores({ general: "", campos: { confirmacion: "Las contraseñas no coinciden." } });
      return;
    }
    try {
      const { data } = await api.post<{ detalle: string }>("/auth/restablecer/", { uid: parametros.get("uid"), token: parametros.get("token"), password });
      setListo(data.detalle);
    } catch (e) {
      setErrores(leerErrores(e));
    }
  }

  return (
    <Box sx={{ maxWidth: 420, mx: "auto" }}>
      <Card>
        <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
          <Typography variant="h5" component="h1" gutterBottom>Nueva contraseña</Typography>
          {listo ? (
            <Stack spacing={2}>
              <Alert severity="success">{listo}</Alert>
              <Button variant="contained" component={RouterLink} to="/iniciar-sesion">Iniciar sesión</Button>
            </Stack>
          ) : (
            <Stack component="form" spacing={2} onSubmit={enviar} noValidate>
              {(errores.general || errores.campos.token) && (
                <Alert severity="error" action={errores.campos.token ? <Button color="inherit" component={RouterLink} to="/recuperar-clave">Pedir otro</Button> : undefined}>
                  {errores.campos.token ?? errores.general}
                </Alert>
              )}
              <TextField label="Contraseña nueva" type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)}
                error={Boolean(errores.campos.password)} helperText={errores.campos.password ?? "Mínimo 8 caracteres, no solo números."} required />
              <TextField label="Repite la contraseña" type="password" autoComplete="new-password" value={confirmacion} onChange={(e) => setConfirmacion(e.target.value)}
                error={Boolean(errores.campos.confirmacion)} helperText={errores.campos.confirmacion} required />
              <Button type="submit" variant="contained" disabled={!password || !confirmacion}>Guardar contraseña</Button>
            </Stack>
          )}
          <Typography variant="body2" sx={{ mt: 3 }}><Link component={RouterLink} to="/iniciar-sesion">Volver a iniciar sesión</Link></Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
