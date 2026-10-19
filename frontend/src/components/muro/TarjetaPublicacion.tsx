import BookmarkIcon from "@mui/icons-material/Bookmark";
import BookmarkBorderIcon from "@mui/icons-material/BookmarkBorder";
import ChatBubbleOutlineIcon from "@mui/icons-material/ChatBubbleOutline";
import EventIcon from "@mui/icons-material/Event";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import StarIcon from "@mui/icons-material/Star";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import {
  Alert, Avatar, Box, Button, Card, CardContent, Chip, Collapse, Divider, IconButton, Menu, MenuItem, Stack, Typography,
  type ChipProps,
} from "@mui/material";
import { useState } from "react";
import { Link as RouterLink } from "react-router-dom";

import type { Publicacion } from "../../api/tipos";
import { fecha, fechaHora } from "../../utilidades/formato";
import { Comentarios } from "./Comentarios";

const COLOR_TIPO: Record<string, ChipProps["color"]> = {
  CONVOCATORIA: "primary", OFERTA_EXTERNA: "secondary", EVENTO: "info", NOTICIA: "default", COMUNICADO: "warning",
};

interface Props {
  p: Publicacion;
  /** Ruta base del rol para enlazar la convocatoria ("/estudiante", "/empresa" u "/oficina"). */
  base: string;
  onAccion: (accion: "reaccionar" | "guardar" | "editar" | "eliminar" | "ocultar" | "mostrar", p: Publicacion) => void;
  onCambio: () => void;
}

export function TarjetaPublicacion({ p, base, onAccion, onCambio }: Props) {
  const [menu, setMenu] = useState<HTMLElement | null>(null);
  const [verComentarios, setVerComentarios] = useState(false);
  const firma = p.empresa?.razon_social ?? (p.autor.rol === "Oficina de prácticas" || p.autor.rol === "Superadministrador" ? "Oficina de prácticas" : p.autor.nombre);
  const convocatoriaAbierta = p.convocatoria?.estado === "PUBLICADA";
  // Página de la empresa según el rol: directorio del estudiante, gestión de la oficina o página pública
  const rutaEmpresa = base === "/estudiante" ? "/estudiante/empresas" : base === "/oficina" ? "/oficina/empresas" : "/empresas";
  const acciones = [
    p.puede_editar && { clave: "editar" as const, texto: "Editar" },
    p.puede_editar && { clave: "eliminar" as const, texto: "Eliminar" },
    p.puede_moderar && p.estado === "PUBLICADA" && { clave: "ocultar" as const, texto: "Ocultar (moderación)" },
    p.puede_moderar && p.estado === "OCULTA" && { clave: "mostrar" as const, texto: "Volver a mostrar" },
  ].filter(Boolean) as { clave: "editar" | "eliminar" | "ocultar" | "mostrar"; texto: string }[];

  return (
    <Card sx={{ opacity: p.estado === "OCULTA" ? 0.7 : 1 }}>
      <CardContent>
        <Stack direction="row" spacing={1.5} sx={{ alignItems: "center", mb: 1.5 }}>
          <Avatar src={p.empresa?.logo ?? undefined} sx={{ bgcolor: "primary.main", width: 40, height: 40 }}>{firma[0]}</Avatar>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="subtitle2" noWrap>
              {p.empresa ? <RouterLink to={`${rutaEmpresa}/${p.empresa.id}`} style={{ color: "inherit" }}>{firma}</RouterLink> : firma}
            </Typography>
            <Typography variant="caption" color="text.secondary">{fechaHora(p.creado_en)}</Typography>
          </Box>
          <Chip size="small" color={COLOR_TIPO[p.tipo]} label={p.tipo_nombre} />
          {acciones.length > 0 && (
            <>
              <IconButton size="small" aria-label="Más opciones" onClick={(e) => setMenu(e.currentTarget)}><MoreVertIcon fontSize="small" /></IconButton>
              <Menu anchorEl={menu} open={Boolean(menu)} onClose={() => setMenu(null)}>
                {acciones.map((a) => <MenuItem key={a.clave} onClick={() => { setMenu(null); onAccion(a.clave, p); }}>{a.texto}</MenuItem>)}
              </Menu>
            </>
          )}
        </Stack>

        {p.estado === "OCULTA" && <Alert severity="warning" sx={{ mb: 1.5 }}>Oculta para los usuarios. Motivo: {p.motivo_ocultamiento}</Alert>}

        <Typography variant="h6" sx={{ fontSize: 18, mb: 0.5 }}>{p.titulo}</Typography>
        <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>{p.texto}</Typography>

        {p.imagen && (
          <Box component="img" src={p.imagen} alt="" sx={{ mt: 1.5, width: "100%", maxHeight: 360, objectFit: "cover", borderRadius: 1 }} />
        )}

        {p.tipo === "EVENTO" && p.fecha_evento && (
          <Stack direction="row" spacing={1} sx={{ mt: 1.5, alignItems: "center" }}>
            <EventIcon fontSize="small" color="info" />
            <Typography variant="body2"><strong>{fechaHora(p.fecha_evento)}</strong>{p.lugar_evento && ` · ${p.lugar_evento}`}</Typography>
          </Stack>
        )}

        {!p.para_todos_programas && p.programas_detalle.length > 0 && (
          <Stack direction="row" spacing={0.5} useFlexGap sx={{ mt: 1.5, flexWrap: "wrap" }}>
            {p.programas_detalle.map((pr) => <Chip key={pr.id} size="small" variant="outlined" label={pr.nombre} />)}
          </Stack>
        )}

        <Stack direction="row" spacing={1} useFlexGap sx={{ mt: 1.5, flexWrap: "wrap" }}>
          {p.convocatoria && (
            <Button size="small" variant={convocatoriaAbierta ? "contained" : "outlined"} component={RouterLink} to={`${base}/convocatorias/${p.convocatoria.id}`}>
              {convocatoriaAbierta ? `Ver convocatoria · cierra el ${fecha(p.convocatoria.fecha_cierre)}` : `Convocatoria ${p.convocatoria.estado_nombre.toLowerCase()}`}
            </Button>
          )}
          {p.enlace_url && (
            <Button size="small" variant={p.tipo === "OFERTA_EXTERNA" ? "contained" : "outlined"} endIcon={<OpenInNewIcon />} href={p.enlace_url} target="_blank" rel="noreferrer">
              {p.tipo === "OFERTA_EXTERNA" ? `Postularme en ${p.fuente_externa || "la fuente original"}` : "Abrir enlace"}
            </Button>
          )}
        </Stack>
      </CardContent>

      <Divider />
      <Stack direction="row" sx={{ px: 1, py: 0.5 }}>
        <Button size="small" color={p.me_interesa ? "secondary" : "inherit"} startIcon={p.me_interesa ? <StarIcon /> : <StarBorderIcon />} onClick={() => onAccion("reaccionar", p)}>
          Me interesa{p.reacciones_total > 0 && ` · ${p.reacciones_total}`}
        </Button>
        <Button size="small" color="inherit" startIcon={<ChatBubbleOutlineIcon />} onClick={() => setVerComentarios(!verComentarios)}>
          Comentar{p.comentarios_total > 0 && ` · ${p.comentarios_total}`}
        </Button>
        <Box sx={{ flex: 1 }} />
        <IconButton size="small" aria-label={p.guardada ? "Quitar de guardadas" : "Guardar"} onClick={() => onAccion("guardar", p)}>
          {p.guardada ? <BookmarkIcon fontSize="small" color="primary" /> : <BookmarkBorderIcon fontSize="small" />}
        </IconButton>
      </Stack>
      <Collapse in={verComentarios} unmountOnExit>
        <Box sx={{ px: 2, pb: 2 }}>
          <Comentarios publicacionId={p.id} moderar={p.puede_moderar} onCambio={onCambio} />
        </Box>
      </Collapse>
    </Card>
  );
}
