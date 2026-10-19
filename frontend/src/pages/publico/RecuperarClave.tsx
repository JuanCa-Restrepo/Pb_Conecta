import { Alert, Box, Button, Card, CardContent, Link, Stack, TextField, Typography } from "@mui/material";
import { useState, type FormEvent } from "react";
import { Link as RouterLink } from "react-router-dom";

import { api, leerErrores } from "../../api/cliente";

/** RF-05: pide el enlace para restablecer la contraseña. */
export default function RecuperarClave() {
  const [email, setEmail] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setEnviando(true);
    setError("");
    try {
      const { data } = await api.post<{ detalle: string }>("/auth/recuperar/", { email: email.trim() });
      setMensaje(data.detalle);
    } catch (e) {
      setError(leerErrores(e).general);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Box sx={{ maxWidth: 420, mx: "auto" }}>
      <Card>
        <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
          <Typography variant="h5" component="h1" gutterBottom>Recuperar contraseña</Typography>
          {mensaje ? (
            <Stack spacing={2}>
              <Alert severity="success">{mensaje}</Alert>
              {import.meta.env.DEV && (
                <Alert severity="info">Entorno de desarrollo: el correo llega a <Link href="http://localhost:8025" target="_blank" rel="noreferrer">Mailpit</Link>.</Alert>
              )}
            </Stack>
          ) : (
            <Stack component="form" spacing={2} onSubmit={enviar} noValidate>
              <Typography color="text.secondary">Te enviaremos un enlace para crear una contraseña nueva.</Typography>
              {error && <Alert severity="error">{error}</Alert>}
              <TextField label="Correo" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
              <Button type="submit" variant="contained" disabled={enviando || !email.trim()}>Enviar enlace</Button>
            </Stack>
          )}
          <Typography variant="body2" sx={{ mt: 3 }}><Link component={RouterLink} to="/iniciar-sesion">Volver a iniciar sesión</Link></Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
