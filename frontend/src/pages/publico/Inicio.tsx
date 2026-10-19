import ApartmentIcon from "@mui/icons-material/Apartment";
import SchoolIcon from "@mui/icons-material/School";
import VerifiedIcon from "@mui/icons-material/Verified";
import { Box, Button, Card, CardContent, Stack, Typography } from "@mui/material";
import type { ReactNode } from "react";
import { Navigate, Link as RouterLink } from "react-router-dom";

import { rutaInicio, useAuth } from "../../auth/AuthContext";

function Beneficio({ icono, titulo, texto }: { icono: ReactNode; titulo: string; texto: string }) {
  return (
    <Card sx={{ flex: 1 }}>
      <CardContent>
        <Box sx={{ color: "primary.main", mb: 1 }}>{icono}</Box>
        <Typography variant="h6" gutterBottom>{titulo}</Typography>
        <Typography color="text.secondary">{texto}</Typography>
      </CardContent>
    </Card>
  );
}

export default function Inicio() {
  const { usuario } = useAuth();
  if (usuario) return <Navigate to={rutaInicio(usuario.rol)} replace />;

  return (
    <Stack spacing={5}>
      <Box sx={{ textAlign: { xs: "left", md: "center" }, maxWidth: 760, mx: "auto" }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Tu práctica profesional empieza aquí
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ fontWeight: 400, mb: 3 }}>
          PB Conecta reúne en un solo lugar las convocatorias de las empresas aliadas del Pascual Bravo,
          para que encuentres una práctica afín a tu programa y hagas seguimiento a todo el proceso.
        </Typography>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ justifyContent: "center" }}>
          <Button variant="contained" size="large" component={RouterLink} to="/registro/estudiante">
            Soy estudiante
          </Button>
          <Button variant="outlined" size="large" component={RouterLink} to="/registro/empresa">
            Soy una empresa
          </Button>
        </Stack>
      </Box>

      <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
        <Beneficio
          icono={<SchoolIcon fontSize="large" />}
          titulo="Para estudiantes"
          texto="Crea tu perfil profesional, mira las convocatorias de tu programa y sigue el estado de cada postulación."
        />
        <Beneficio
          icono={<ApartmentIcon fontSize="large" />}
          titulo="Para empresas aliadas"
          texto="Publica convocatorias, revisa postulantes con su índice de afinidad y agenda entrevistas."
        />
        <Beneficio
          icono={<VerifiedIcon fontSize="large" />}
          titulo="Con acompañamiento de la oficina"
          texto="La oficina de prácticas habilita estudiantes, aprueba convocatorias y legaliza cada práctica."
        />
      </Stack>
    </Stack>
  );
}
