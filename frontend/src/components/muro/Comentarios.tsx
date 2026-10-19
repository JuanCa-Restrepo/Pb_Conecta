import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import { Box, Button, IconButton, Stack, TextField, Tooltip, Typography } from "@mui/material";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api, leerErrores } from "../../api/cliente";
import type { Comentario } from "../../api/tipos";
import { fechaHora } from "../../utilidades/formato";
import { useAviso } from "../Avisos";

/** RF-106: comentarios de una publicación. La oficina puede ocultarlos (RF-105). */
export function Comentarios({ publicacionId, moderar, onCambio }: { publicacionId: number; moderar: boolean; onCambio: () => void }) {
  const cliente = useQueryClient();
  const avisar = useAviso();
  const [texto, setTexto] = useState("");
  const clave = ["muro", "comentarios", publicacionId];
  const { data: comentarios = [] } = useQuery({
    queryKey: clave,
    queryFn: async () => (await api.get<Comentario[]>(`/muro/publicaciones/${publicacionId}/comentarios/`)).data,
  });

  async function comentar() {
    try {
      const { data } = await api.post<Comentario[]>(`/muro/publicaciones/${publicacionId}/comentarios/`, { texto });
      cliente.setQueryData(clave, data);
      setTexto("");
      onCambio();
    } catch (e) {
      avisar(leerErrores(e).general, "error");
    }
  }

  async function ocultar(comentarioId: number) {
    await api.post(`/muro/publicaciones/${publicacionId}/comentarios/${comentarioId}/ocultar/`);
    cliente.invalidateQueries({ queryKey: clave });
    onCambio();
  }

  return (
    <Stack spacing={1.5} sx={{ pt: 1 }}>
      {comentarios.map((c) => (
        <Box key={c.id} sx={{ px: 1.5, py: 1, borderRadius: 1, bgcolor: "action.hover", opacity: c.oculto ? 0.5 : 1 }}>
          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <Typography variant="subtitle2">{c.autor}</Typography>
            <Typography variant="caption" color="text.secondary" sx={{ flex: 1 }}>{c.autor_rol} · {fechaHora(c.creado_en)}{c.oculto && " · oculto"}</Typography>
            {moderar && !c.oculto && (
              <Tooltip title="Ocultar comentario">
                <IconButton size="small" aria-label="Ocultar comentario" onClick={() => ocultar(c.id)}><VisibilityOffIcon fontSize="small" /></IconButton>
              </Tooltip>
            )}
          </Stack>
          <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>{c.texto}</Typography>
        </Box>
      ))}
      <Stack direction="row" spacing={1} sx={{ alignItems: "flex-start" }}>
        <TextField size="small" placeholder="Escribe un comentario" value={texto} onChange={(e) => setTexto(e.target.value)} multiline fullWidth slotProps={{ htmlInput: { maxLength: 1000 } }} />
        <Button variant="contained" onClick={comentar} disabled={!texto.trim()}>Comentar</Button>
      </Stack>
    </Stack>
  );
}
