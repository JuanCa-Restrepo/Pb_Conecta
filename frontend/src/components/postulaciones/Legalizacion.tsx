import UploadFileIcon from "@mui/icons-material/UploadFile";
import {
  Alert, Box, Button, Card, CardContent, CardHeader, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel,
  List, ListItem, ListItemText, MenuItem, Radio, RadioGroup, Stack, TextField, Typography,
} from "@mui/material";
import dayjs from "dayjs";
import { useEffect, useState } from "react";

import { api, leerErrores } from "../../api/cliente";
import { TIPOS_VINCULACION } from "../../api/opciones";
import type { PostulacionDetalle } from "../../api/tipos";
import { fechaHora } from "../../utilidades/formato";
import { EstadoChip } from "../EstadoChip";

type Errores = { general: string; campos: Record<string, string> };
const SIN_ERRORES: Errores = { general: "", campos: {} };

function DialogoVerificacion({ abierto, postulacion, onCerrar, onHecho }: {
  abierto: boolean; postulacion: PostulacionDetalle; onCerrar: () => void; onHecho: (p: PostulacionDetalle) => void;
}) {
  const [resultado, setResultado] = useState("CUMPLE");
  const [observacion, setObservacion] = useState("");
  const [errores, setErrores] = useState<Errores>(SIN_ERRORES);

  useEffect(() => {
    if (abierto) { setResultado("CUMPLE"); setObservacion(""); setErrores(SIN_ERRORES); }
  }, [abierto]);

  async function guardar() {
    try {
      const { data } = await api.post<PostulacionDetalle>(`/postulaciones/${postulacion.id}/verificar/`, { resultado, observacion });
      onHecho(data);
    } catch (e) {
      setErrores(leerErrores(e));
    }
  }

  return (
    <Dialog open={abierto} onClose={onCerrar} fullWidth maxWidth="sm">
      <DialogTitle>Verificación de requisitos</DialogTitle>
      <DialogContent>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Registra el resultado de la revisión en persona con {postulacion.estudiante.nombre}: habilitación, créditos y documentos (RF-62a).
        </Typography>
        {errores.general && <Alert severity="error" sx={{ mb: 2 }}>{errores.general}</Alert>}
        <RadioGroup value={resultado} onChange={(e) => setResultado(e.target.value)} sx={{ mb: 2 }}>
          <FormControlLabel value="CUMPLE" control={<Radio />} label="Cumple los requisitos" />
          <FormControlLabel value="NO_CUMPLE" control={<Radio />} label="No cumple (el estudiante verá la observación)" />
        </RadioGroup>
        <TextField
          label={resultado === "NO_CUMPLE" ? "¿Qué le falta?" : "Observación (opcional)"}
          required={resultado === "NO_CUMPLE"}
          value={observacion}
          onChange={(e) => setObservacion(e.target.value)}
          multiline
          minRows={2}
          fullWidth
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onCerrar}>Cancelar</Button>
        <Button variant="contained" onClick={guardar}>Registrar</Button>
      </DialogActions>
    </Dialog>
  );
}

function DialogoLegalizar({ abierto, postulacion, onCerrar, onHecho }: {
  abierto: boolean; postulacion: PostulacionDetalle; onCerrar: () => void; onHecho: (p: PostulacionDetalle) => void;
}) {
  const inicial = () => ({
    fecha_inicio: dayjs().add(15, "day").format("YYYY-MM-DD"),
    fecha_fin: dayjs().add(15, "day").add(6, "month").format("YYYY-MM-DD"),
    tipo_vinculacion: "PRACTICA",
    asesor_nombre: "",
    tutor_empresa_nombre: postulacion.contacto_empresa?.nombre ?? "",
    tutor_empresa_email: postulacion.contacto_empresa?.email ?? "",
  });
  const [form, setForm] = useState(inicial);
  const [documento, setDocumento] = useState<File | null>(null);
  const [errores, setErrores] = useState<Errores>(SIN_ERRORES);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (abierto) { setForm(inicial()); setDocumento(null); setErrores(SIN_ERRORES); }
  }, [abierto]);

  const campo = (nombre: keyof ReturnType<typeof inicial>) => ({
    value: form[nombre],
    onChange: (e: { target: { value: string } }) => setForm({ ...form, [nombre]: e.target.value }),
    error: Boolean(errores.campos[nombre]),
    helperText: errores.campos[nombre],
    fullWidth: true,
  });

  async function legalizar() {
    const datos = new FormData();
    Object.entries(form).forEach(([clave, valor]) => datos.append(clave, valor));
    if (documento) datos.append("documento_soporte", documento);
    setEnviando(true);
    try {
      const { data } = await api.post<PostulacionDetalle>(`/postulaciones/${postulacion.id}/legalizar/`, datos);
      onHecho(data);
    } catch (e) {
      setErrores(leerErrores(e));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Dialog open={abierto} onClose={onCerrar} fullWidth maxWidth="sm">
      <DialogTitle>Legalizar práctica</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          <Alert severity="info">
            Al legalizar, {postulacion.estudiante.nombre} queda ubicado, sus otras postulaciones activas se cierran (RN-08) y,
            si se completan los cupos, la convocatoria se cierra (RN-09).
          </Alert>
          {errores.general && <Alert severity="error">{errores.general}</Alert>}
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField label="Inicio" type="date" required slotProps={{ inputLabel: { shrink: true } }} {...campo("fecha_inicio")} />
            <TextField label="Fin" type="date" required slotProps={{ inputLabel: { shrink: true } }} {...campo("fecha_fin")} />
          </Stack>
          <TextField select label="Tipo de vinculación" {...campo("tipo_vinculacion")}>
            {TIPOS_VINCULACION.map((t) => <MenuItem key={t.valor} value={t.valor}>{t.etiqueta}</MenuItem>)}
          </TextField>
          <TextField label="Docente asesor" required {...campo("asesor_nombre")} />
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField label="Tutor en la empresa" required {...campo("tutor_empresa_nombre")} />
            <TextField label="Correo del tutor" type="email" {...campo("tutor_empresa_email")} />
          </Stack>
          <Box>
            <Button component="label" variant="outlined" startIcon={<UploadFileIcon />}>
              {documento ? "Cambiar PDF" : "Adjuntar acta o contrato (PDF, opcional)"}
              <input hidden type="file" accept="application/pdf,.pdf" onChange={(e) => setDocumento(e.target.files?.[0] ?? null)} />
            </Button>
            {documento && <Typography variant="body2" sx={{ mt: 1 }}>{documento.name}</Typography>}
            {errores.campos.documento_soporte && <Typography variant="body2" color="error" sx={{ mt: 1 }}>{errores.campos.documento_soporte}</Typography>}
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCerrar} disabled={enviando}>Cancelar</Button>
        <Button variant="contained" onClick={legalizar} disabled={enviando}>Legalizar</Button>
      </DialogActions>
    </Dialog>
  );
}

/** M7 en la postulación: verificación en persona (RF-62a) y legalización (RF-64). Solo la oficina. */
export function Legalizacion({ postulacion, onCambio }: { postulacion: PostulacionDetalle; onCambio: (p: PostulacionDetalle, mensaje: string) => void }) {
  const [dialogo, setDialogo] = useState<null | "verificar" | "legalizar">(null);
  const ultima = postulacion.verificaciones[0];

  return (
    <Card sx={{ borderColor: "primary.main", borderWidth: 2 }}>
      <CardHeader title="Verificación y legalización" subheader="Trámite de la oficina de prácticas" slotProps={{ title: { variant: "h6" } }} />
      <CardContent sx={{ pt: 0 }}>
        {!ultima && <Typography variant="body2" sx={{ mb: 2 }}>Cita al estudiante, revisa sus requisitos en persona y registra el resultado.</Typography>}
        {postulacion.verificaciones.length > 0 && (
          <List dense disablePadding sx={{ mb: 2 }}>
            {postulacion.verificaciones.map((v) => (
              <ListItem key={v.id} disableGutters>
                <ListItemText
                  primary={<EstadoChip estado={v.resultado} etiqueta={v.resultado_nombre} />}
                  secondary={`${fechaHora(v.creado_en)} · ${v.funcionario}${v.observacion ? ` · ${v.observacion}` : ""}`}
                />
              </ListItem>
            ))}
          </List>
        )}
        <Stack direction="row" spacing={1}>
          <Button variant={postulacion.acciones.legalizar ? "outlined" : "contained"} onClick={() => setDialogo("verificar")}>
            {ultima ? "Nueva verificación" : "Registrar verificación"}
          </Button>
          {postulacion.acciones.legalizar && <Button variant="contained" onClick={() => setDialogo("legalizar")}>Legalizar práctica</Button>}
        </Stack>
      </CardContent>

      <DialogoVerificacion
        abierto={dialogo === "verificar"}
        postulacion={postulacion}
        onCerrar={() => setDialogo(null)}
        onHecho={(p) => { setDialogo(null); onCambio(p, "Verificación registrada."); }}
      />
      <DialogoLegalizar
        abierto={dialogo === "legalizar"}
        postulacion={postulacion}
        onCerrar={() => setDialogo(null)}
        onHecho={(p) => { setDialogo(null); onCambio(p, "Práctica legalizada. Se notificó al estudiante y a la empresa."); }}
      />
    </Card>
  );
}
