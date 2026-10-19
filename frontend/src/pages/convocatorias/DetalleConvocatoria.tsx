import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { Alert, AlertTitle, Button, Card, CardContent, Chip, Stack, Typography } from "@mui/material";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link as RouterLink, useNavigate, useParams } from "react-router-dom";

import { api, leerErrores } from "../../api/cliente";
import type { AccionConvocatoria, Convocatoria } from "../../api/tipos";
import { useAuth } from "../../auth/AuthContext";
import { useAviso } from "../../components/Avisos";
import { InfoConvocatoria } from "../../components/convocatorias/InfoConvocatoria";
import { PostulantesConvocatoria } from "../../components/convocatorias/PostulantesConvocatoria";
import { DialogoTexto } from "../../components/DialogoTexto";
import { EstadoChip } from "../../components/EstadoChip";

export default function DetalleConvocatoria() {
  const { id } = useParams();
  const { usuario } = useAuth();
  const navegar = useNavigate();
  const cliente = useQueryClient();
  const avisar = useAviso();
  const esEmpresa = usuario?.rol === "EMPRESA";
  const base = esEmpresa ? "/empresa" : "/oficina";
  const [dialogo, setDialogo] = useState<null | "devolver" | "cerrar" | "eliminar">(null);
  const [ocupado, setOcupado] = useState(false);

  const { data: c } = useQuery({
    queryKey: ["convocatoria", id],
    queryFn: async () => (await api.get<Convocatoria>(`/convocatorias/${id}/`)).data,
  });

  async function ejecutar(accion: string, mensaje: string, cuerpo: object = {}) {
    const { data } = await api.post<Convocatoria>(`/convocatorias/${id}/${accion}/`, cuerpo);
    cliente.invalidateQueries({ queryKey: ["convocatorias"] });
    if (accion === "duplicar") {
      navegar(`${base}/convocatorias/${data.id}/editar`);
    } else {
      cliente.setQueryData(["convocatoria", id], data);
    }
    avisar(mensaje);
  }

  async function directa(accion: string, mensaje: string) {
    setOcupado(true);
    try {
      await ejecutar(accion, mensaje);
    } catch (e) {
      avisar(leerErrores(e).general, "error");
    } finally {
      setOcupado(false);
    }
  }

  if (!c) return null;
  const puede = (accion: AccionConvocatoria) => c.acciones.includes(accion);

  return (
    <Stack spacing={2}>
      <Button component={RouterLink} to={`${base}/convocatorias`} startIcon={<ArrowBackIcon />} sx={{ alignSelf: "flex-start" }}>
        Convocatorias
      </Button>

      <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ justifyContent: "space-between" }}>
        <div>
          <Typography variant="h5" component="h1">{c.titulo}</Typography>
          <Stack direction="row" spacing={1} sx={{ mt: 1, alignItems: "center", flexWrap: "wrap" }}>
            <EstadoChip estado={c.estado} etiqueta={c.estado_nombre} />
            <Typography variant="body2" color="text.secondary">{c.empresa_nombre}</Typography>
            {c.postulantes !== null && c.estado !== "BORRADOR" && <Chip size="small" variant="outlined" label={`${c.postulantes} postulante(s)`} />}
            {c.creada_por_oficina && <Chip size="small" variant="outlined" label="Publicada por la oficina" />}
          </Stack>
        </div>
        <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap", alignItems: "flex-start" }}>
          {puede("aprobar") && <Button variant="contained" disabled={ocupado} onClick={() => directa("aprobar", "Convocatoria publicada. Ya aparece en el muro.")}>{c.estado === "BORRADOR" ? "Publicar" : "Aprobar y publicar"}</Button>}
          {puede("devolver") && <Button variant="outlined" color="warning" onClick={() => setDialogo("devolver")}>Devolver con observaciones</Button>}
          {puede("enviar_revision") && <Button variant="contained" disabled={ocupado} onClick={() => directa("enviar-revision", "Convocatoria enviada a revisión de la oficina.")}>Enviar a revisión</Button>}
          {puede("editar") && <Button variant="outlined" component={RouterLink} to={`${base}/convocatorias/${c.id}/editar`}>Editar</Button>}
          {puede("cerrar") && <Button variant="outlined" color="error" onClick={() => setDialogo("cerrar")}>Cerrar</Button>}
          {puede("duplicar") && <Button disabled={ocupado} onClick={() => directa("duplicar", "Se creó una copia como borrador.")}>Duplicar</Button>}
          {puede("eliminar") && <Button color="error" onClick={() => setDialogo("eliminar")}>Eliminar</Button>}
        </Stack>
      </Stack>

      {c.estado === "DEVUELTA" && (
        <Alert severity="warning">
          <AlertTitle>Observaciones de la oficina de prácticas</AlertTitle>
          {c.observacion_revision}
          {esEmpresa && <Typography variant="body2" sx={{ mt: 1 }}>Corrige la convocatoria y vuelve a enviarla a revisión.</Typography>}
        </Alert>
      )}
      {c.estado === "EN_REVISION" && esEmpresa && <Alert severity="info">La oficina de prácticas está revisando la convocatoria. Te avisaremos cuando la apruebe o la devuelva.</Alert>}
      {c.estado === "BORRADOR" && esEmpresa && <Alert severity="info">Borrador: cuando esté lista, envíala a revisión de la oficina.</Alert>}
      {c.estado === "CERRADA" && c.motivo_cierre_nombre && <Alert severity="info">Cerrada · {c.motivo_cierre_nombre}.</Alert>}

      <Card>
        <CardContent>
          <InfoConvocatoria c={c} />
        </CardContent>
      </Card>

      {c.estado !== "BORRADOR" && <PostulantesConvocatoria convocatoriaId={c.id} base={base} />}

      <DialogoTexto
        abierto={dialogo === "devolver"}
        titulo="Devolver con observaciones"
        descripcion="La empresa verá estas observaciones y podrá corregir la convocatoria."
        etiqueta="Observaciones"
        obligatorio
        textoConfirmar="Devolver"
        colorConfirmar="warning"
        onCerrar={() => setDialogo(null)}
        onConfirmar={(observacion) => ejecutar("devolver", "Convocatoria devuelta a la empresa.", { observacion })}
      />
      <DialogoTexto
        abierto={dialogo === "cerrar"}
        titulo="Cerrar convocatoria"
        descripcion="Los estudiantes ya no podrán postularse. Esta acción no se puede deshacer."
        textoConfirmar="Cerrar convocatoria"
        colorConfirmar="error"
        onCerrar={() => setDialogo(null)}
        onConfirmar={() => ejecutar("cerrar", "Convocatoria cerrada.")}
      />
      <DialogoTexto
        abierto={dialogo === "eliminar"}
        titulo="Eliminar borrador"
        descripcion="El borrador se eliminará definitivamente."
        textoConfirmar="Eliminar"
        colorConfirmar="error"
        onCerrar={() => setDialogo(null)}
        onConfirmar={async () => {
          await api.delete(`/convocatorias/${id}/`);
          cliente.invalidateQueries({ queryKey: ["convocatorias"] });
          avisar("Borrador eliminado.");
          navegar(`${base}/convocatorias`);
        }}
      />
    </Stack>
  );
}
