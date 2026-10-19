import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import EventIcon from "@mui/icons-material/Event";
import {
  Alert, AlertTitle, Box, Button, Card, CardContent, CardHeader, Link, List, ListItem, ListItemText, Stack, Typography,
} from "@mui/material";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link as RouterLink, useParams } from "react-router-dom";

import { api, leerErrores } from "../../api/cliente";
import { abrirArchivoProtegido } from "../../api/descargas";
import { ACCION_ESTADO } from "../../api/opciones";
import type { EstadoPostulacion, PostulacionDetalle } from "../../api/tipos";
import { useAuth } from "../../auth/AuthContext";
import { AfinidadChip, AfinidadDetalle } from "../../components/Afinidad";
import { useAviso } from "../../components/Avisos";
import { DialogoTexto } from "../../components/DialogoTexto";
import { EstadoChip } from "../../components/EstadoChip";
import { PerfilProfesionalCard } from "../../components/perfil/PerfilProfesionalCard";
import { Legalizacion } from "../../components/postulaciones/Legalizacion";
import { TarjetaPractica } from "../../components/practicas/TarjetaPractica";
import { Bitacora } from "../../components/postulaciones/Bitacora";
import { DialogoEntrevista } from "../../components/postulaciones/DialogoEntrevista";
import { fechaHora } from "../../utilidades/formato";

/** Detalle de una postulación. Lo comparten el estudiante, la empresa y la oficina; cada uno ve lo suyo (RN-10). */
export default function DetallePostulacion() {
  const { id } = useParams();
  const { usuario } = useAuth();
  const cliente = useQueryClient();
  const avisar = useAviso();
  const [destino, setDestino] = useState<EstadoPostulacion | null>(null);
  const [retirando, setRetirando] = useState(false);
  const [entrevistando, setEntrevistando] = useState(false);

  const clave = ["postulacion", id];
  const { data: p } = useQuery({ queryKey: clave, queryFn: async () => (await api.get<PostulacionDetalle>(`/postulaciones/${id}/`)).data });

  const esEstudiante = usuario?.rol === "ESTUDIANTE";
  const esOficina = usuario?.rol === "OFICINA" || usuario?.rol === "SUPERADMIN";
  const base = esEstudiante ? "/estudiante" : usuario?.rol === "EMPRESA" ? "/empresa" : "/oficina";

  function refrescar(datos?: PostulacionDetalle) {
    if (datos) cliente.setQueryData(clave, datos);
    else cliente.invalidateQueries({ queryKey: clave });
    cliente.invalidateQueries({ queryKey: ["postulaciones"] });
    cliente.invalidateQueries({ queryKey: ["convocatorias"] });
  }

  async function cambiar(texto: string) {
    if (!destino) return;
    const cuerpo = destino === "NO_SELECCIONADO" ? { estado: destino, motivo: texto } : { estado: destino, comentario: texto };
    const { data } = await api.post<PostulacionDetalle>(`/postulaciones/${id}/cambiar-estado/`, cuerpo);
    refrescar(data);
    avisar(`Postulación: ${data.estado_nombre.toLowerCase()}. Se notificó al estudiante.`);
  }

  if (!p) return null;
  const volver = esEstudiante ? "/estudiante/postulaciones" : usuario?.rol === "EMPRESA" ? `/empresa/convocatorias/${p.convocatoria.id}` : "/oficina/postulaciones";
  const verHv = () => abrirArchivoProtegido(`/postulaciones/${p.id}/hoja-vida/`).catch((e) => avisar(leerErrores(e).general, "error"));

  return (
    <Stack spacing={2}>
      <Button component={RouterLink} to={volver} startIcon={<ArrowBackIcon />} sx={{ alignSelf: "flex-start" }}>
        {esEstudiante ? "Mis postulaciones" : usuario?.rol === "EMPRESA" ? "Convocatoria" : "Postulaciones"}
      </Button>

      <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ justifyContent: "space-between" }}>
        <div>
          <Typography variant="h5" component="h1">{esEstudiante ? p.convocatoria.titulo : p.estudiante.nombre}</Typography>
          <Typography color="text.secondary">
            {esEstudiante ? p.convocatoria.empresa : (
              <>
                <Link component={RouterLink} to={`${base}/convocatorias/${p.convocatoria.id}`}>{p.convocatoria.titulo}</Link> · {p.convocatoria.empresa}
              </>
            )}
          </Typography>
          <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
            <EstadoChip estado={p.estado} etiqueta={p.estado_nombre} />
            <AfinidadChip valor={p.afinidad} />
          </Stack>
        </div>
        <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap", alignItems: "flex-start" }}>
          {p.acciones.estados.filter((e) => e !== "NO_SELECCIONADO").map((e) => (
            <Button key={e} variant="contained" onClick={() => setDestino(e)}>{ACCION_ESTADO[e] ?? e}</Button>
          ))}
          {p.acciones.programar_entrevista && (
            <Button variant={p.estado === "PRESELECCIONADO" ? "contained" : "outlined"} startIcon={<EventIcon />} onClick={() => setEntrevistando(true)}>
              {p.estado === "ENTREVISTA" ? "Reprogramar entrevista" : "Programar entrevista"}
            </Button>
          )}
          {p.acciones.estados.includes("NO_SELECCIONADO") && <Button color="error" variant="outlined" onClick={() => setDestino("NO_SELECCIONADO")}>No seleccionar</Button>}
          <Button variant="outlined" onClick={verHv}>Ver hoja de vida</Button>
          {p.acciones.retirar && <Button color="error" onClick={() => setRetirando(true)}>Retirar postulación</Button>}
        </Stack>
      </Stack>

      {p.estado === "NO_SELECCIONADO" && (
        <Alert severity="error"><AlertTitle>No seleccionado</AlertTitle>Motivo de la empresa: {p.motivo_no_seleccion}</Alert>
      )}
      {p.estado === "SELECCIONADO" && esEstudiante && (
        <Alert severity="success">
          <AlertTitle>¡Fuiste seleccionado!</AlertTitle>
          Acércate a la oficina de prácticas para verificar tus requisitos y legalizar la práctica.
        </Alert>
      )}
      {p.estado === "SELECCIONADO" && usuario?.rol === "EMPRESA" && (
        <Alert severity="info">Seleccionado. La oficina de prácticas verificará los requisitos en persona y legalizará la práctica.</Alert>
      )}
      {p.estado === "LEGALIZADO" && esEstudiante && (
        <Alert severity="success"><AlertTitle>¡Tu práctica quedó legalizada!</AlertTitle>Revisa las fechas, tu docente asesor y tu tutor en la empresa.</Alert>
      )}
      {p.practica && <TarjetaPractica practica={p.practica} enlaceOficina={esOficina} />}
      {esOficina && !p.practica && (p.acciones.verificar || p.verificaciones.length > 0) && (
        <Legalizacion postulacion={p} onCambio={(datos, mensaje) => { refrescar(datos); avisar(mensaje); }} />
      )}

      {p.proxima_entrevista && p.estado !== "LEGALIZADO" && (
        <Alert severity="info" icon={<EventIcon />}>
          <AlertTitle>Entrevista el {fechaHora(p.proxima_entrevista.fecha_hora)}</AlertTitle>
          {p.proxima_entrevista.modalidad_nombre} · {p.proxima_entrevista.lugar_o_enlace}
          {p.proxima_entrevista.notas && <Typography variant="body2" sx={{ mt: 0.5 }}>{p.proxima_entrevista.notas}</Typography>}
        </Alert>
      )}

      <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ alignItems: "flex-start" }}>
        <Stack spacing={2} sx={{ flex: 1, minWidth: 0, width: "100%" }}>
          {p.perfil_estudiante && <PerfilProfesionalCard perfil={p.perfil_estudiante} />}
          {p.mensaje_presentacion && (
            <Card>
              <CardHeader title="Mensaje de presentación" slotProps={{ title: { variant: "h6" } }} />
              <CardContent sx={{ pt: 0 }}><Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>{p.mensaje_presentacion}</Typography></CardContent>
            </Card>
          )}
          <Bitacora postulacionId={p.id} entradas={p.seguimiento} tipos={p.acciones.seguimiento} onNueva={() => refrescar()} />
        </Stack>

        <Stack spacing={2} sx={{ width: { xs: "100%", md: 340 }, flexShrink: 0 }}>
          <Card><CardContent><AfinidadDetalle afinidad={p.afinidad_detalle} /></CardContent></Card>
          {esEstudiante && (
            <Card>
              <CardHeader title="Contacto de la empresa" slotProps={{ title: { variant: "h6" } }} />
              <CardContent sx={{ pt: 0 }}>
                {p.contacto_empresa ? (
                  <Typography variant="body2">
                    {p.contacto_empresa.nombre}<br />
                    <Link href={`mailto:${p.contacto_empresa.email}`}>{p.contacto_empresa.email}</Link>
                    {p.contacto_empresa.telefono && <><br />{p.contacto_empresa.telefono}</>}
                  </Typography>
                ) : (
                  <Typography variant="body2" color="text.secondary">Verás los datos de contacto cuando la empresa te preseleccione (RF-58).</Typography>
                )}
              </CardContent>
            </Card>
          )}
          <Card>
            <CardHeader title="Historial" slotProps={{ title: { variant: "h6" } }} />
            <List dense sx={{ pt: 0 }}>
              {p.historial.map((h) => (
                <ListItem key={h.id} sx={{ alignItems: "flex-start" }}>
                  <Box sx={{ width: 10, height: 10, borderRadius: "50%", bgcolor: "primary.main", mt: 0.9, mr: 1.5, flexShrink: 0 }} />
                  <ListItemText
                    primary={h.estado_nuevo_nombre}
                    secondary={`${fechaHora(h.creado_en)} · ${h.usuario}${h.comentario ? ` · ${h.comentario}` : ""}`}
                  />
                </ListItem>
              ))}
            </List>
          </Card>
        </Stack>
      </Stack>

      <DialogoTexto
        abierto={destino !== null && destino !== "NO_SELECCIONADO"}
        titulo={destino ? ACCION_ESTADO[destino] ?? "Cambiar estado" : ""}
        descripcion={destino === "SELECCIONADO" ? "La oficina de prácticas recibirá un aviso para verificar requisitos y legalizar la práctica." : "El estudiante recibirá una notificación con el nuevo estado."}
        etiqueta="Comentario (opcional, queda en el historial)"
        textoConfirmar="Confirmar"
        onCerrar={() => setDestino(null)}
        onConfirmar={cambiar}
      />
      <DialogoTexto
        abierto={destino === "NO_SELECCIONADO"}
        titulo="No seleccionar"
        descripcion="El estudiante verá este motivo. Una retroalimentación clara le ayuda a mejorar (RN-11)."
        etiqueta="Motivo"
        obligatorio
        textoConfirmar="No seleccionar"
        colorConfirmar="error"
        onCerrar={() => setDestino(null)}
        onConfirmar={cambiar}
      />
      <DialogoTexto
        abierto={retirando}
        titulo="Retirar postulación"
        descripcion="La empresa recibirá un aviso. Esta acción no se puede deshacer."
        etiqueta="Motivo (opcional)"
        textoConfirmar="Retirar"
        colorConfirmar="error"
        onCerrar={() => setRetirando(false)}
        onConfirmar={async (comentario) => {
          const { data } = await api.post<PostulacionDetalle>(`/postulaciones/${id}/retirar/`, { comentario });
          refrescar(data);
          avisar("Retiraste tu postulación.");
        }}
      />
      <DialogoEntrevista
        abierto={entrevistando}
        postulacionId={p.id}
        onCerrar={() => setEntrevistando(false)}
        onProgramada={() => { setEntrevistando(false); refrescar(); avisar("Entrevista programada. Se notificó al estudiante."); }}
      />
    </Stack>
  );
}
