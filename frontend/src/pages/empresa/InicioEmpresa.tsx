import {
  Alert, AlertTitle, Button, Card, CardContent, CardHeader, Chip, Stack, Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import { api } from "../../api/cliente";
import type { DatosEmpresa, ResumenConvocatoriaEmpresa } from "../../api/tipos";
import { useAuth } from "../../auth/AuthContext";
import { EstadoChip } from "../../components/EstadoChip";

/** RF-82: cuántos postulantes hay en cada etapa de cada convocatoria. */
function ResumenConvocatorias() {
  const navegar = useNavigate();
  const { data = [] } = useQuery({
    queryKey: ["empresa", "resumen"],
    queryFn: async () => (await api.get<ResumenConvocatoriaEmpresa[]>("/empresas/yo/resumen/")).data,
  });
  if (data.length === 0) return null;
  return (
    <Card>
      <CardHeader title="Resumen de tus convocatorias" subheader="Postulantes por etapa" slotProps={{ title: { variant: "h6" } }} />
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Convocatoria</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell align="right">Cupos</TableCell>
              <TableCell align="right">Por revisar</TableCell>
              <TableCell align="right">En proceso</TableCell>
              <TableCell align="right">Seleccionados</TableCell>
              <TableCell align="right">Total</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((c) => (
              <TableRow key={c.id} hover sx={{ cursor: "pointer" }} onClick={() => navegar(`/empresa/convocatorias/${c.id}`)}>
                <TableCell>{c.titulo}</TableCell>
                <TableCell><EstadoChip estado={c.estado} etiqueta={c.estado_nombre} /></TableCell>
                {[c.cupos, c.por_revisar, c.en_proceso, c.seleccionados, c.total].map((v, i) => (
                  <TableCell key={i} align="right" sx={{ fontVariantNumeric: "tabular-nums", fontWeight: i === 1 && v > 0 ? 700 : 400 }}>{v}</TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Card>
  );
}

function EstadoEmpresa({ empresa }: { empresa: DatosEmpresa }) {
  if (empresa.estado === "PENDIENTE") {
    return (
      <Alert severity="info">
        <AlertTitle>Solicitud en revisión</AlertTitle>
        La oficina de prácticas está revisando tu empresa y registrará el convenio. Te avisaremos por correo.
      </Alert>
    );
  }
  if (!empresa.puede_publicar) {
    return (
      <Alert severity="warning">
        <AlertTitle>{empresa.estado_nombre}</AlertTitle>
        Por ahora no puedes publicar convocatorias nuevas. Comunícate con la oficina de prácticas.
      </Alert>
    );
  }
  return (
    <Alert severity="success">
      <AlertTitle>Empresa aliada con convenio vigente</AlertTitle>
      Puedes publicar convocatorias. Cada una pasa por la revisión de la oficina de prácticas antes de publicarse.
    </Alert>
  );
}

export default function InicioEmpresa() {
  const { usuario } = useAuth();
  const empresa = usuario?.empresa;
  if (!usuario || !empresa) return null;

  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h5" component="h1">{empresa.razon_social}</Typography>
        <Chip sx={{ mt: 1 }} label={empresa.estado_nombre} color={empresa.puede_publicar ? "success" : "warning"} />
      </div>
      <EstadoEmpresa empresa={empresa} />
      <ResumenConvocatorias />
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Convocatorias</Typography>
          <Typography color="text.secondary" sx={{ mb: 2 }}>Crea convocatorias y revisa a los postulantes con su índice de afinidad.</Typography>
          <Button variant="contained" component={RouterLink} to="/empresa/convocatorias">
            Mis convocatorias
          </Button>
        </CardContent>
      </Card>
    </Stack>
  );
}
