import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import {
  Avatar, Button, Card, CardContent, CardHeader, Chip, List, ListItemButton, ListItemText, Stack, Typography,
} from "@mui/material";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link as RouterLink, useNavigate, useParams } from "react-router-dom";

import { api, leerErrores } from "../../api/cliente";
import type { EmpresaPagina } from "../../api/tipos";
import { useAviso } from "../../components/Avisos";
import { fecha, fechaHora, pesos } from "../../utilidades/formato";

/** RF-22: página de la empresa aliada. Para visitantes (`base` "") o estudiantes (`base` "/estudiante", con «Seguir»). */
export default function PaginaEmpresa({ base = "" }: { base?: string }) {
  const { id } = useParams();
  const navegar = useNavigate();
  const cliente = useQueryClient();
  const avisar = useAviso();
  const esEstudiante = base === "/estudiante";
  const { data: e } = useQuery({ queryKey: ["empresa", id], queryFn: async () => (await api.get<EmpresaPagina>(`/empresas/${id}/`)).data });

  async function alternarSeguir() {
    try {
      const { data } = e?.seguida ? await api.delete<EmpresaPagina>(`/empresas/${id}/seguir/`) : await api.post<EmpresaPagina>(`/empresas/${id}/seguir/`);
      cliente.setQueryData(["empresa", id], data);
      cliente.invalidateQueries({ queryKey: ["empresas"] });
      avisar(data.seguida ? `Ahora sigues a ${data.razon_social}: te avisaremos de sus nuevas convocatorias.` : "Dejaste de seguir a la empresa.");
    } catch (error) {
      avisar(leerErrores(error).general, "error");
    }
  }

  if (!e) return null;
  return (
    <Stack spacing={2}>
      <Button component={RouterLink} to={`${base}/empresas`} startIcon={<ArrowBackIcon />} sx={{ alignSelf: "flex-start" }}>Empresas aliadas</Button>

      <Card>
        <CardContent>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ alignItems: { sm: "center" } }}>
            <Avatar src={e.logo ?? undefined} variant="rounded" sx={{ width: 80, height: 80, bgcolor: "primary.main", fontSize: 32 }}>{e.razon_social[0]}</Avatar>
            <Stack sx={{ flex: 1 }} spacing={0.5}>
              <Typography variant="h5" component="h1">{e.razon_social}</Typography>
              <Typography color="text.secondary">{e.sector_nombre} · {e.ciudad_nombre}{e.tamano_nombre ? ` · ${e.tamano_nombre}` : ""}</Typography>
              {e.sitio_web && (
                <Button size="small" href={e.sitio_web} target="_blank" rel="noreferrer" endIcon={<OpenInNewIcon />} sx={{ alignSelf: "flex-start", px: 0 }}>
                  Sitio web
                </Button>
              )}
            </Stack>
            {esEstudiante && (
              <Button variant={e.seguida ? "outlined" : "contained"} onClick={alternarSeguir}>{e.seguida ? "Siguiendo" : "Seguir"}</Button>
            )}
          </Stack>
          {e.descripcion && <Typography variant="body1" sx={{ mt: 2, whiteSpace: "pre-wrap" }}>{e.descripcion}</Typography>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader title={`Convocatorias abiertas (${e.convocatorias.length})`} slotProps={{ title: { variant: "h6" } }} />
        {e.convocatorias.length === 0 ? (
          <CardContent sx={{ pt: 0 }}><Typography color="text.secondary">Por ahora no tiene convocatorias abiertas.</Typography></CardContent>
        ) : (
          <List sx={{ pt: 0 }}>
            {e.convocatorias.map((c) => (
              <ListItemButton key={c.id} divider onClick={() => navegar(esEstudiante ? `/estudiante/convocatorias/${c.id}` : "/iniciar-sesion")}>
                <ListItemText
                  primary={c.titulo}
                  secondary={`${c.modalidad_nombre}${c.ciudad_nombre ? ` · ${c.ciudad_nombre}` : ""} · ${pesos(c.apoyo_economico)} · cierra el ${fecha(c.fecha_cierre)}`}
                />
                <Stack direction="row" spacing={0.5} useFlexGap sx={{ flexWrap: "wrap", justifyContent: "flex-end", maxWidth: "45%" }}>
                  {c.programas.slice(0, 2).map((p) => <Chip key={p} size="small" variant="outlined" label={p} />)}
                </Stack>
              </ListItemButton>
            ))}
          </List>
        )}
        {!esEstudiante && e.convocatorias.length > 0 && (
          <CardContent sx={{ pt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              ¿Eres estudiante del Pascual Bravo? <RouterLink to="/iniciar-sesion">Inicia sesión</RouterLink> para ver tu afinidad y postularte.
            </Typography>
          </CardContent>
        )}
      </Card>

      {e.publicaciones.length > 0 && (
        <Card>
          <CardHeader title="Publicaciones recientes" slotProps={{ title: { variant: "h6" } }} />
          <CardContent sx={{ pt: 0 }}>
            <Stack spacing={2}>
              {e.publicaciones.map((p) => (
                <div key={p.id}>
                  <Typography variant="caption" color="text.secondary">{p.tipo_nombre} · {fechaHora(p.creado_en)}</Typography>
                  <Typography variant="subtitle2">{p.titulo}</Typography>
                  <Typography variant="body2" color="text.secondary">{p.texto}</Typography>
                </div>
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}
    </Stack>
  );
}
