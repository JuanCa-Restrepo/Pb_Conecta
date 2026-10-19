import { Alert, AlertTitle, Box, Button, Card, CardContent, Chip, Stack, Typography } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import dayjs from "dayjs";
import { Link as RouterLink } from "react-router-dom";

import { api } from "../../api/cliente";
import type { Convocatoria, DatosEstudiante, Paginado, Practica } from "../../api/tipos";
import { useAuth } from "../../auth/AuthContext";
import { TarjetaConvocatoria } from "../../components/convocatorias/TarjetaConvocatoria";
import { TarjetaPractica } from "../../components/practicas/TarjetaPractica";

/** RF-18: el estudiante siempre ve su estado de habilitación. */
function EstadoHabilitacion({ estudiante }: { estudiante: DatosEstudiante }) {
  const { estado, habilitacion } = estudiante;

  if (estado === "NO_HABILITADO") {
    return (
      <Alert severity="warning">
        <AlertTitle>Aún no estás habilitado para prácticas</AlertTitle>
        Puedes explorar convocatorias, empresas y el muro, pero todavía no puedes postularte.
        Acércate a la oficina de prácticas para revisar tus requisitos.
        {habilitacion?.accion === "DESHABILITADO" && habilitacion.observacion && (
          <Typography variant="body2" sx={{ mt: 1 }}>Motivo: {habilitacion.observacion}</Typography>
        )}
      </Alert>
    );
  }

  return (
    <Alert severity="success">
      <AlertTitle>{estudiante.estado_nombre}</AlertTitle>
      {habilitacion
        ? `Habilitado por la oficina de prácticas para el periodo ${habilitacion.periodo} el ${dayjs(habilitacion.fecha).format("DD/MM/YYYY")}.`
        : "La oficina de prácticas registró tu habilitación."}
      {estado === "HABILITADO" && " Ya puedes postularte a las convocatorias de tu programa."}
    </Alert>
  );
}

export default function InicioEstudiante() {
  const { usuario } = useAuth();
  const estudiante = usuario?.estudiante;
  const { data: recomendadas = [] } = useQuery({
    queryKey: ["convocatorias", "recomendadas"],
    queryFn: async () => (await api.get<Convocatoria[]>("/convocatorias/recomendadas/")).data,
    enabled: Boolean(estudiante),
  });
  const { data: practicas } = useQuery({
    queryKey: ["practicas", "mias"],
    queryFn: async () => (await api.get<Paginado<Practica>>("/practicas/")).data,
    enabled: Boolean(estudiante),
  });
  const practica = practicas?.results[0];
  if (!usuario || !estudiante) return null;

  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h5" component="h1">Hola, {usuario.nombres}</Typography>
        <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: "wrap" }}>
          <Chip label={estudiante.programa_nombre} color="primary" variant="outlined" />
          <Chip label={estudiante.estado_nombre} color={estudiante.estado === "NO_HABILITADO" ? "warning" : "success"} />
        </Stack>
      </div>

      {practica && practica.estado !== "CANCELADA" ? <TarjetaPractica practica={practica} /> : <EstadoHabilitacion estudiante={estudiante} />}

      {recomendadas.length > 0 && (
        <div>
          <Typography variant="h6" gutterBottom>Recomendadas para ti</Typography>
          <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, 1fr)", lg: "repeat(3, 1fr)" } }}>
            {recomendadas.slice(0, 3).map((c) => <TarjetaConvocatoria key={c.id} c={c} />)}
          </Box>
        </div>
      )}

      <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Convocatorias de tu programa</Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>Explora las prácticas afines a {estudiante.programa_nombre}.</Typography>
            <Button variant="contained" component={RouterLink} to="/estudiante/convocatorias">Ver convocatorias</Button>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Completa tu perfil</Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>Habilidades, experiencia y hoja de vida mejoran tu índice de afinidad.</Typography>
            <Button variant="outlined" component={RouterLink} to="/estudiante/perfil">Ir a mi perfil</Button>
          </CardContent>
        </Card>
      </Stack>
    </Stack>
  );
}
