import { Alert, Box, Button, Card, CardContent, Checkbox, FormControlLabel, FormHelperText, Link, Stack, Typography } from "@mui/material";
import type { FormEvent, ReactNode } from "react";
import { Link as RouterLink } from "react-router-dom";

interface Props {
  titulo: string;
  descripcion: string;
  errorGeneral: string;
  errorPolitica?: string;
  aceptaPolitica: boolean;
  onAceptaPolitica: (valor: boolean) => void;
  enviando: boolean;
  exito: string;
  onEnviar: (evento: FormEvent) => void;
  children: ReactNode;
}

/** Estructura común de los formularios de registro: tarjeta, errores, política de datos (RF-06) y pantalla de éxito. */
export function FormularioRegistro(props: Props) {
  if (props.exito) {
    return (
      <Box sx={{ maxWidth: 560, mx: "auto" }}>
        <Alert severity="success" sx={{ mb: 2 }}>{props.exito}</Alert>
        {import.meta.env.DEV && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Entorno de desarrollo: el correo de verificación llega a la bandeja de Mailpit en{" "}
            <Link href="http://localhost:8025" target="_blank" rel="noreferrer">http://localhost:8025</Link>.
          </Alert>
        )}
        <Button variant="contained" component={RouterLink} to="/iniciar-sesion">Ir a iniciar sesión</Button>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 640, mx: "auto" }}>
      <Card>
        <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
          <Typography variant="h5" component="h1" gutterBottom>{props.titulo}</Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>{props.descripcion}</Typography>
          <Stack component="form" spacing={2} onSubmit={props.onEnviar} noValidate>
            {props.errorGeneral && <Alert severity="error">{props.errorGeneral}</Alert>}
            {props.children}
            <Box>
              <FormControlLabel
                control={<Checkbox checked={props.aceptaPolitica} onChange={(e) => props.onAceptaPolitica(e.target.checked)} />}
                label="Acepto la política de tratamiento de datos personales (Ley 1581 de 2012)."
              />
              {props.errorPolitica && <FormHelperText error>{props.errorPolitica}</FormHelperText>}
            </Box>
            <Button type="submit" variant="contained" size="large" disabled={props.enviando}>
              {props.enviando ? "Enviando…" : "Crear cuenta"}
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
