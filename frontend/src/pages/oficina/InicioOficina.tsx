import { Card, CardActionArea, CardContent, Stack, Typography } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink } from "react-router-dom";

import { api } from "../../api/cliente";
import type { Alertas, Resumen } from "../../api/tipos";
import { useAuth } from "../../auth/AuthContext";
import { PanelIndicadores } from "./PanelIndicadores";

const resumen = (ruta: string) => async () => (await api.get<Resumen>(ruta)).data;

export default function InicioOficina() {
  const { usuario } = useAuth();
  const { data: empresas } = useQuery({ queryKey: ["oficina", "empresas", "resumen"], queryFn: resumen("/oficina/empresas/resumen/") });
  const { data: estudiantes } = useQuery({ queryKey: ["oficina", "estudiantes", "resumen"], queryFn: resumen("/oficina/estudiantes/resumen/") });
  const { data: convocatorias } = useQuery({ queryKey: ["convocatorias", "resumen"], queryFn: resumen("/convocatorias/resumen/") });
  const { data: practicas } = useQuery({ queryKey: ["practicas", "resumen"], queryFn: resumen("/practicas/resumen/") });
  const { data: alertas } = useQuery({ queryKey: ["oficina", "alertas"], queryFn: async () => (await api.get<Alertas>("/oficina/alertas/")).data });
  const porLegalizar = alertas?.categorias.find((c) => c.clave === "por_legalizar")?.total;

  const pendientes = [
    { cifra: porLegalizar, titulo: "Seleccionados por legalizar", texto: "Verifica requisitos en persona y legaliza la práctica.", ruta: "/oficina/alertas" },
    { cifra: alertas?.total, titulo: "Alertas de seguimiento", texto: "Estudiantes y procesos que necesitan acompañamiento.", ruta: "/oficina/alertas" },
    { cifra: estudiantes?.NO_HABILITADO, titulo: "Estudiantes por habilitar", texto: "Verifica requisitos y habilítalos para postularse.", ruta: "/oficina/estudiantes" },
    { cifra: empresas?.PENDIENTE, titulo: "Empresas por aprobar", texto: "Aprueba las solicitudes y registra el convenio.", ruta: "/oficina/empresas" },
    { cifra: convocatorias?.EN_REVISION, titulo: "Convocatorias por revisar", texto: "Apruébalas o devuélvelas con observaciones.", ruta: "/oficina/convocatorias" },
    { cifra: convocatorias?.PUBLICADA, titulo: "Convocatorias publicadas", texto: "Visibles hoy para los estudiantes.", ruta: "/oficina/convocatorias" },
    { cifra: practicas && (practicas.LEGALIZADA ?? 0) + (practicas.EN_CURSO ?? 0), titulo: "Prácticas activas", texto: "Legalizadas y en curso.", ruta: "/oficina/practicas" },
  ];

  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h5" component="h1">Oficina de prácticas</Typography>
        <Typography color="text.secondary">Hola, {usuario?.nombres}. Esto es lo que requiere tu atención.</Typography>
      </div>
      <Stack direction={{ xs: "column", md: "row" }} spacing={2} useFlexGap sx={{ flexWrap: "wrap" }}>
        {pendientes.map((p) => (
          <Card key={p.titulo} sx={{ flex: "1 1 220px" }}>
            <CardActionArea component={RouterLink} to={p.ruta} sx={{ height: "100%" }}>
              <CardContent>
                <Typography variant="h4" color="primary" sx={{ fontVariantNumeric: "tabular-nums" }}>{p.cifra ?? "—"}</Typography>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>{p.titulo}</Typography>
                <Typography variant="body2" color="text.secondary">{p.texto}</Typography>
              </CardContent>
            </CardActionArea>
          </Card>
        ))}
      </Stack>
      <PanelIndicadores />
    </Stack>
  );
}
