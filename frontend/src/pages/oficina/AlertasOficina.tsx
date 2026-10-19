import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import { Box, Card, CardContent, CardHeader, Chip, List, ListItemButton, ListItemText, Stack, Typography } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { api } from "../../api/cliente";
import type { Alertas } from "../../api/tipos";
import { fecha } from "../../utilidades/formato";

const COLOR = { alta: "error", media: "warning", baja: "info" } as const;

/** RF-66: lo que requiere atención de la oficina para que ningún estudiante quede sin acompañamiento. */
export default function AlertasOficina() {
  const navegar = useNavigate();
  const { data } = useQuery({ queryKey: ["oficina", "alertas"], queryFn: async () => (await api.get<Alertas>("/oficina/alertas/")).data });

  if (!data) return null;
  const conItems = data.categorias.filter((c) => c.total > 0);

  return (
    <Stack spacing={2}>
      <div>
        <Typography variant="h5" component="h1">Alertas de seguimiento</Typography>
        <Typography color="text.secondary">
          Se calculan con los datos de hoy. Los días de cada alerta se ajustan en el panel de administración (Parámetros).
        </Typography>
      </div>

      {conItems.length === 0 && (
        <Card>
          <CardContent sx={{ display: "flex", gap: 2, alignItems: "center" }}>
            <CheckCircleOutlineIcon color="success" fontSize="large" />
            <Typography>Todo al día: no hay alertas de seguimiento.</Typography>
          </CardContent>
        </Card>
      )}

      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", lg: "repeat(2, 1fr)" } }}>
        {conItems.map((c) => (
          <Card key={c.clave}>
            <CardHeader
              title={c.titulo}
              subheader={c.descripcion}
              slotProps={{ title: { variant: "h6" } }}
              action={<Chip color={COLOR[c.gravedad]} label={c.total} sx={{ fontWeight: 700 }} />}
            />
            <List dense sx={{ pt: 0 }}>
              {c.items.map((item) => (
                <ListItemButton key={`${c.clave}-${item.id}`} onClick={() => navegar(item.url)}>
                  <ListItemText primary={item.titulo} secondary={`${item.detalle}${item.desde ? ` · desde el ${fecha(item.desde)}` : ""}`} />
                </ListItemButton>
              ))}
            </List>
          </Card>
        ))}
      </Box>
    </Stack>
  );
}
