import { Alert, Box, Button, Card, CardContent, Link, Stack, TextField, Typography } from "@mui/material";
import { useState, type FormEvent } from "react";
import { Navigate, Link as RouterLink, useLocation, useNavigate } from "react-router-dom";

import { leerErrores } from "../../api/cliente";
import { rutaInicio, useAuth } from "../../auth/AuthContext";

export default function IniciarSesion() {
  const { usuario, iniciarSesion } = useAuth();
  const navegar = useNavigate();
  const ubicacion = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  if (usuario) return <Navigate to={rutaInicio(usuario.rol)} replace />;

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setError("");
    setEnviando(true);
    try {
      const yo = await iniciarSesion(email.trim(), password);
      const desde = (ubicacion.state as { desde?: string } | null)?.desde;
      navegar(desde ?? rutaInicio(yo.rol), { replace: true });
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
          <Typography variant="h5" component="h1" gutterBottom>Iniciar sesión</Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>Estudiantes, empresas y oficina de prácticas.</Typography>
          <Stack component="form" spacing={2} onSubmit={enviar} noValidate>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField label="Correo" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
            <TextField label="Contraseña" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            <Link component={RouterLink} to="/recuperar-clave" variant="body2" sx={{ alignSelf: "flex-end" }}>¿Olvidaste tu contraseña?</Link>
            <Button type="submit" variant="contained" size="large" disabled={enviando || !email || !password}>
              {enviando ? "Ingresando…" : "Ingresar"}
            </Button>
          </Stack>
          <Typography variant="body2" sx={{ mt: 3 }}>
            ¿No tienes cuenta?{" "}
            <Link component={RouterLink} to="/registro/estudiante">Regístrate como estudiante</Link> o{" "}
            <Link component={RouterLink} to="/registro/empresa">como empresa</Link>.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
