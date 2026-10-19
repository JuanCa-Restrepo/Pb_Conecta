import { Button, Card, List, ListItemButton, ListItemText, Stack, Typography } from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import dayjs from "dayjs";
import { useNavigate } from "react-router-dom";

import { api } from "../api/cliente";
import type { Notificacion, Paginado } from "../api/tipos";

export default function Notificaciones() {
  const cliente = useQueryClient();
  const navegar = useNavigate();
  const { data, isLoading } = useQuery({
    queryKey: ["notificaciones", "lista"],
    queryFn: async () => (await api.get<Paginado<Notificacion>>("/notificaciones/")).data,
  });

  const refrescar = () => cliente.invalidateQueries({ queryKey: ["notificaciones"] });
  const leer = useMutation({ mutationFn: (id: number) => api.post(`/notificaciones/${id}/leer/`), onSuccess: refrescar });
  const leerTodas = useMutation({ mutationFn: () => api.post("/notificaciones/leer-todas/"), onSuccess: refrescar });

  const notificaciones = data?.results ?? [];

  return (
    <Stack spacing={2}>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
        <Typography variant="h5" component="h1">Notificaciones</Typography>
        <Button onClick={() => leerTodas.mutate()} disabled={!notificaciones.some((n) => !n.leida)}>Marcar todas como leídas</Button>
      </Stack>
      <Card>
        {isLoading ? null : notificaciones.length === 0 ? (
          <Typography color="text.secondary" sx={{ p: 3 }}>No tienes notificaciones.</Typography>
        ) : (
          <List disablePadding>
            {notificaciones.map((n) => (
              <ListItemButton
                key={n.id}
                divider
                sx={{ bgcolor: n.leida ? undefined : "action.hover" }}
                onClick={() => {
                  if (!n.leida) leer.mutate(n.id);
                  if (n.url_destino) navegar(n.url_destino);
                }}
              >
                <ListItemText
                  primary={n.titulo}
                  secondary={`${n.mensaje} · ${dayjs(n.creado_en).format("DD/MM/YYYY HH:mm")}`}
                  slotProps={{ primary: { sx: { fontWeight: n.leida ? 400 : 600 } } }}
                />
              </ListItemButton>
            ))}
          </List>
        )}
      </Card>
    </Stack>
  );
}
