import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  Alert, Autocomplete, Button, Dialog, DialogActions, DialogContent, DialogTitle, IconButton, MenuItem, Stack, TextField, Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api, leerErrores } from "../../api/cliente";
import { NIVELES_HABILIDAD } from "../../api/opciones";
import type { HabilidadPerfil, ItemCatalogo } from "../../api/tipos";

interface Fila {
  id?: number; // Sin id: habilidad nueva escrita por el estudiante
  nombre: string;
  nivel: string;
}

/** RF-11: elige habilidades del catálogo o escribe una nueva; cada una con su nivel. */
export function EditorHabilidades({ abierto, actuales, onCerrar, onGuardado }: {
  abierto: boolean; actuales: HabilidadPerfil[]; onCerrar: () => void; onGuardado: () => void;
}) {
  const { data: catalogo = [] } = useQuery({
    queryKey: ["catalogos", "habilidades"],
    queryFn: async () => (await api.get<ItemCatalogo[]>("/catalogos/habilidades/")).data,
  });
  const [filas, setFilas] = useState<Fila[]>([]);
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (abierto) {
      setFilas(actuales.map((h) => ({ id: h.id, nombre: h.nombre, nivel: h.nivel })));
      setError("");
    }
  }, [abierto, actuales]);

  function agregar(valor: string | ItemCatalogo | null) {
    if (!valor) return;
    const nombre = typeof valor === "string" ? valor.trim() : valor.nombre;
    if (!nombre || filas.some((f) => f.nombre.toLowerCase() === nombre.toLowerCase())) return;
    const delCatalogo = typeof valor === "string" ? catalogo.find((h) => h.nombre.toLowerCase() === nombre.toLowerCase()) : valor;
    setFilas([...filas, { id: delCatalogo?.id, nombre: delCatalogo?.nombre ?? nombre, nivel: "BASICO" }]);
  }

  async function guardar() {
    setEnviando(true);
    try {
      await api.put("/estudiantes/yo/habilidades/", {
        habilidades: filas.map((f) => (f.id ? { habilidad: f.id, nivel: f.nivel } : { nombre: f.nombre, nivel: f.nivel })),
      });
      onGuardado();
    } catch (e) {
      setError(leerErrores(e).general);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Dialog open={abierto} onClose={onCerrar} fullWidth maxWidth="sm">
      <DialogTitle>Habilidades</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <Autocomplete<ItemCatalogo, false, false, true>
            freeSolo
            options={catalogo.filter((h) => !filas.some((f) => f.id === h.id))}
            getOptionLabel={(o) => (typeof o === "string" ? o : o.nombre)}
            onChange={(_, valor) => agregar(valor)}
            value={null}
            blurOnSelect
            clearOnBlur
            renderInput={(params) => (
              <TextField {...params} label="Agregar habilidad" helperText="Elige del catálogo o escribe una nueva y presiona Enter." />
            )}
          />
          {filas.length === 0 && <Typography color="text.secondary" variant="body2">Aún no agregas habilidades.</Typography>}
          {filas.map((fila, i) => (
            <Stack key={fila.nombre} direction="row" spacing={1} sx={{ alignItems: "center" }}>
              <Typography sx={{ flex: 1 }}>{fila.nombre}{!fila.id && <Typography component="span" variant="caption" color="text.secondary"> · nueva</Typography>}</Typography>
              <TextField
                select
                size="small"
                value={fila.nivel}
                onChange={(e) => setFilas(filas.map((f, j) => (j === i ? { ...f, nivel: e.target.value } : f)))}
                sx={{ width: 150 }}
                slotProps={{ htmlInput: { "aria-label": `Nivel de ${fila.nombre}` } }}
              >
                {NIVELES_HABILIDAD.map((n) => <MenuItem key={n.valor} value={n.valor}>{n.etiqueta}</MenuItem>)}
              </TextField>
              <IconButton aria-label={`Quitar ${fila.nombre}`} onClick={() => setFilas(filas.filter((_, j) => j !== i))}>
                <DeleteOutlineIcon fontSize="small" />
              </IconButton>
            </Stack>
          ))}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCerrar} disabled={enviando}>Cancelar</Button>
        <Button variant="contained" onClick={guardar} disabled={enviando}>Guardar habilidades</Button>
      </DialogActions>
    </Dialog>
  );
}
