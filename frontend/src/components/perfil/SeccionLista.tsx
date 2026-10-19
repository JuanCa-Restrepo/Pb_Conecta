import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import {
  Alert, Button, Card, CardContent, CardHeader, Dialog, DialogActions, DialogContent, DialogTitle, IconButton, List, ListItem,
  ListItemText, MenuItem, Stack, TextField, Tooltip, Typography,
} from "@mui/material";
import { useState } from "react";

import { api, leerErrores } from "../../api/cliente";

export interface Campo {
  nombre: string;
  etiqueta: string;
  tipo?: "texto" | "fecha" | "select" | "multilinea" | "url";
  opciones?: { valor: string; etiqueta: string }[];
  requerido?: boolean;
  ayuda?: string;
}

interface Props<T extends { id: number }> {
  titulo: string;
  ruta: string;
  items: T[];
  campos: Campo[];
  primario: (item: T) => string;
  secundario?: (item: T) => string;
  vacio: string;
  onCambio: () => void;
}

/** Una sección del perfil (idiomas, experiencia, proyectos…) con su lista y su diálogo para agregar o editar. */
export function SeccionLista<T extends { id: number }>(props: Props<T>) {
  const [editando, setEditando] = useState<T | "nuevo" | null>(null);
  const [valores, setValores] = useState<Record<string, string>>({});
  const [errores, setErrores] = useState<{ general: string; campos: Record<string, string> }>({ general: "", campos: {} });
  const [enviando, setEnviando] = useState(false);

  function abrir(item: T | "nuevo") {
    const inicial: Record<string, string> = {};
    for (const campo of props.campos) {
      const valor = item === "nuevo" ? "" : (item as Record<string, unknown>)[campo.nombre];
      inicial[campo.nombre] = valor === null || valor === undefined ? (campo.opciones?.[0]?.valor ?? "") : String(valor);
    }
    setValores(inicial);
    setErrores({ general: "", campos: {} });
    setEditando(item);
  }

  async function guardar() {
    setEnviando(true);
    // Las fechas opcionales vacías se envían como null
    const cuerpo = Object.fromEntries(
      props.campos.map((c) => [c.nombre, c.tipo === "fecha" && !valores[c.nombre] ? null : valores[c.nombre].trim()]),
    );
    try {
      if (editando === "nuevo") await api.post(props.ruta, cuerpo);
      else if (editando) await api.patch(`${props.ruta}${editando.id}/`, cuerpo);
      setEditando(null);
      props.onCambio();
    } catch (e) {
      setErrores(leerErrores(e));
    } finally {
      setEnviando(false);
    }
  }

  async function borrar(item: T) {
    await api.delete(`${props.ruta}${item.id}/`);
    props.onCambio();
  }

  return (
    <Card>
      <CardHeader
        title={props.titulo}
        slotProps={{ title: { variant: "h6" } }}
        action={<Button startIcon={<AddIcon />} onClick={() => abrir("nuevo")}>Agregar</Button>}
      />
      <CardContent sx={{ pt: 0 }}>
        {props.items.length === 0 ? (
          <Typography color="text.secondary" variant="body2">{props.vacio}</Typography>
        ) : (
          <List dense disablePadding>
            {props.items.map((item) => (
              <ListItem
                key={item.id}
                divider
                secondaryAction={
                  <Stack direction="row">
                    <Tooltip title="Editar"><IconButton size="small" aria-label="Editar" onClick={() => abrir(item)}><EditOutlinedIcon fontSize="small" /></IconButton></Tooltip>
                    <Tooltip title="Eliminar"><IconButton size="small" aria-label="Eliminar" onClick={() => borrar(item)}><DeleteOutlineIcon fontSize="small" /></IconButton></Tooltip>
                  </Stack>
                }
              >
                <ListItemText primary={props.primario(item)} secondary={props.secundario?.(item)} sx={{ pr: 8 }} />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>

      <Dialog open={editando !== null} onClose={() => setEditando(null)} fullWidth maxWidth="sm">
        <DialogTitle>{editando === "nuevo" ? "Agregar" : "Editar"} · {props.titulo.toLowerCase()}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            {errores.general && <Alert severity="error">{errores.general}</Alert>}
            {props.campos.map((campo) => (
              <TextField
                key={campo.nombre}
                label={campo.etiqueta}
                required={campo.requerido}
                select={campo.tipo === "select"}
                type={campo.tipo === "fecha" ? "date" : campo.tipo === "url" ? "url" : "text"}
                multiline={campo.tipo === "multilinea"}
                minRows={campo.tipo === "multilinea" ? 3 : undefined}
                value={valores[campo.nombre] ?? ""}
                onChange={(e) => setValores({ ...valores, [campo.nombre]: e.target.value })}
                error={Boolean(errores.campos[campo.nombre])}
                helperText={errores.campos[campo.nombre] ?? campo.ayuda}
                slotProps={campo.tipo === "fecha" ? { inputLabel: { shrink: true } } : undefined}
                fullWidth
              >
                {campo.opciones?.map((o) => <MenuItem key={o.valor} value={o.valor}>{o.etiqueta}</MenuItem>)}
              </TextField>
            ))}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditando(null)} disabled={enviando}>Cancelar</Button>
          <Button variant="contained" onClick={guardar} disabled={enviando}>Guardar</Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
}
