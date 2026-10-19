import AddIcon from "@mui/icons-material/Add";
import SearchIcon from "@mui/icons-material/Search";
import { Box, Button, Card, Chip, InputAdornment, Stack, TextField, ToggleButton, ToggleButtonGroup, Typography } from "@mui/material";
import { useInfiniteQuery, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api, leerErrores } from "../../api/cliente";
import { TIPOS_PUBLICACION } from "../../api/opciones";
import type { Paginado, Publicacion } from "../../api/tipos";
import { useAuth } from "../../auth/AuthContext";
import { useAviso } from "../../components/Avisos";
import { DialogoTexto } from "../../components/DialogoTexto";
import { DialogoPublicacion } from "../../components/muro/DialogoPublicacion";
import { TarjetaPublicacion } from "../../components/muro/TarjetaPublicacion";

type Vista = "para_mi" | "todo" | "guardadas" | "ocultas";

/** M10: muro compartido por estudiantes, empresas y oficina. Cada rol ve sus opciones. */
export default function Muro() {
  const { usuario } = useAuth();
  const cliente = useQueryClient();
  const avisar = useAviso();
  const esEstudiante = usuario?.rol === "ESTUDIANTE";
  const esOficina = usuario?.rol === "OFICINA" || usuario?.rol === "SUPERADMIN";
  const base = esEstudiante ? "/estudiante" : usuario?.rol === "EMPRESA" ? "/empresa" : "/oficina";

  const [vista, setVista] = useState<Vista>(esEstudiante ? "para_mi" : "todo");
  const [tipo, setTipo] = useState("");
  const [texto, setTexto] = useState("");
  const [editando, setEditando] = useState<Publicacion | null | "nueva">(null);
  const [ocultando, setOcultando] = useState<Publicacion | null>(null);

  const { data: permisos } = useQuery({
    queryKey: ["muro", "permisos"],
    queryFn: async () => (await api.get<{ tipos: string[] }>("/muro/publicaciones/permisos/")).data,
  });
  const parametros = {
    tipo: tipo || undefined, q: texto || undefined,
    para_mi: vista === "para_mi" ? "1" : undefined, guardadas: vista === "guardadas" ? "1" : undefined,
    estado: vista === "ocultas" ? "OCULTA" : undefined,
  };
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading } = useInfiniteQuery({
    queryKey: ["muro", "feed", parametros],
    queryFn: async ({ pageParam }) => (await api.get<Paginado<Publicacion>>("/muro/publicaciones/", { params: { ...parametros, page: pageParam } })).data,
    initialPageParam: 1,
    getNextPageParam: (ultima, todas) => (ultima.next ? todas.length + 1 : undefined),
  });
  const publicaciones = data?.pages.flatMap((pagina) => pagina.results) ?? [];
  const refrescar = () => cliente.invalidateQueries({ queryKey: ["muro", "feed"] });

  async function accion(clave: "reaccionar" | "guardar" | "editar" | "eliminar" | "ocultar" | "mostrar", p: Publicacion) {
    if (clave === "editar") return setEditando(p);
    if (clave === "ocultar") return setOcultando(p);
    try {
      if (clave === "eliminar") {
        await api.delete(`/muro/publicaciones/${p.id}/`);
        avisar("Publicación eliminada.");
      } else {
        await api.post(`/muro/publicaciones/${p.id}/${clave}/`);
        if (clave === "mostrar") avisar("La publicación vuelve a estar visible.");
      }
      refrescar();
    } catch (e) {
      avisar(leerErrores(e).general, "error");
    }
  }

  return (
    <Stack spacing={2} sx={{ maxWidth: 760, mx: "auto" }}>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ justifyContent: "space-between", alignItems: { sm: "center" } }}>
        <div>
          <Typography variant="h5" component="h1">Muro</Typography>
          <Typography color="text.secondary">Convocatorias, ofertas de bolsas de empleo, eventos y noticias.</Typography>
        </div>
        {permisos && permisos.tipos.length > 0 && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setEditando("nueva")}>Publicar</Button>
        )}
      </Stack>

      <Card sx={{ p: 2 }}>
        <Stack spacing={1.5}>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ alignItems: { sm: "center" } }}>
            <ToggleButtonGroup exclusive size="small" color="primary" value={vista} onChange={(_, v) => v && setVista(v)}>
              {esEstudiante && <ToggleButton value="para_mi">Para mi programa</ToggleButton>}
              <ToggleButton value="todo">Todo el muro</ToggleButton>
              <ToggleButton value="guardadas">Guardadas</ToggleButton>
              {esOficina && <ToggleButton value="ocultas">Ocultas</ToggleButton>}
            </ToggleButtonGroup>
            <TextField
              size="small"
              placeholder="Buscar en el muro"
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              slotProps={{ input: { startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment> } }}
              sx={{ flex: 1 }}
            />
          </Stack>
          <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
            <Chip label="Todo" color={tipo === "" ? "primary" : "default"} onClick={() => setTipo("")} />
            {TIPOS_PUBLICACION.map((t) => (
              <Chip key={t.valor} label={t.etiqueta} color={tipo === t.valor ? "primary" : "default"} onClick={() => setTipo(tipo === t.valor ? "" : t.valor)} />
            ))}
          </Stack>
        </Stack>
      </Card>

      {publicaciones.map((p) => <TarjetaPublicacion key={p.id} p={p} base={base} onAccion={accion} onCambio={refrescar} />)}
      {!isLoading && publicaciones.length === 0 && (
        <Typography color="text.secondary" sx={{ textAlign: "center", py: 4 }}>No hay publicaciones en esta vista.</Typography>
      )}
      {hasNextPage && (
        <Box sx={{ textAlign: "center" }}>
          <Button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>{isFetchingNextPage ? "Cargando…" : "Ver más publicaciones"}</Button>
        </Box>
      )}

      <DialogoPublicacion
        abierto={editando !== null}
        tipos={permisos?.tipos ?? []}
        existente={editando === "nueva" ? null : editando}
        onCerrar={() => setEditando(null)}
        onGuardada={() => { setEditando(null); refrescar(); avisar("Publicación guardada."); }}
      />
      <DialogoTexto
        abierto={ocultando !== null}
        titulo="Ocultar publicación"
        descripcion="Dejará de verse en el muro. Su autor recibirá el motivo (RF-105)."
        etiqueta="Motivo"
        obligatorio
        textoConfirmar="Ocultar"
        colorConfirmar="warning"
        onCerrar={() => setOcultando(null)}
        onConfirmar={async (motivo) => {
          await api.post(`/muro/publicaciones/${ocultando!.id}/ocultar/`, { motivo });
          refrescar();
          avisar("Publicación oculta.");
        }}
      />
    </Stack>
  );
}
