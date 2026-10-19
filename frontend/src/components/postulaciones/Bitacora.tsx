import { alpha, Alert, Box, Button, Card, CardContent, CardHeader, Chip, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { useState } from "react";

import { api, leerErrores } from "../../api/cliente";
import { CANALES_CONTACTO } from "../../api/opciones";
import type { EntradaSeguimiento } from "../../api/tipos";
import { fechaHora } from "../../utilidades/formato";

const TIPOS = {
  MENSAJE: { etiqueta: "Mensaje", color: "default" as const },
  CONTACTO_EXTERNO: { etiqueta: "Contacto por fuera", color: "info" as const },
  NOTA_INTERNA: { etiqueta: "Nota interna (solo oficina)", color: "warning" as const },
};

const ahoraLocal = () => {
  const ahora = new Date();
  ahora.setMinutes(ahora.getMinutes() - ahora.getTimezoneOffset());
  return ahora.toISOString().slice(0, 16);
};

/** RF-57: bitácora compartida entre estudiante, empresa y oficina. Los contactos hechos por fuera también se registran. */
export function Bitacora({ postulacionId, entradas, tipos, onNueva }: {
  postulacionId: number; entradas: EntradaSeguimiento[]; tipos: EntradaSeguimiento["tipo"][]; onNueva: () => void;
}) {
  const [tipo, setTipo] = useState<EntradaSeguimiento["tipo"]>("MENSAJE");
  const [texto, setTexto] = useState("");
  const [canal, setCanal] = useState("LLAMADA");
  const [cuando, setCuando] = useState(ahoraLocal);
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  async function enviar() {
    if (!texto.trim()) return;
    setEnviando(true);
    setError("");
    try {
      const externo = tipo === "CONTACTO_EXTERNO";
      await api.post(`/postulaciones/${postulacionId}/seguimiento/`, {
        tipo, texto, canal: externo ? canal : null, fecha_contacto: externo ? new Date(cuando).toISOString() : null,
      });
      setTexto("");
      onNueva();
    } catch (e) {
      setError(leerErrores(e).general);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Card>
      <CardHeader
        title="Bitácora de seguimiento"
        subheader="Mensajes entre el estudiante, la empresa y la oficina, y registro de contactos hechos por fuera."
        slotProps={{ title: { variant: "h6" } }}
      />
      <CardContent sx={{ pt: 0 }}>
        <Stack spacing={1.5} sx={{ mb: 2 }}>
          {entradas.length === 0 && <Typography variant="body2" color="text.secondary">Aún no hay entradas.</Typography>}
          {entradas.map((e) => (
            <Box key={e.id} sx={{ p: 1.5, borderRadius: 1, bgcolor: (t) => (e.tipo === "NOTA_INTERNA" ? alpha(t.palette.warning.main, 0.08) : t.palette.action.hover), border: 1, borderColor: "divider" }}>
              <Stack direction="row" spacing={1} useFlexGap sx={{ alignItems: "center", flexWrap: "wrap", mb: 0.5 }}>
                <Typography variant="subtitle2">{e.autor}</Typography>
                <Typography variant="caption" color="text.secondary">{e.autor_rol} · {fechaHora(e.creado_en)}</Typography>
                {e.tipo !== "MENSAJE" && <Chip size="small" color={TIPOS[e.tipo].color} label={e.tipo === "CONTACTO_EXTERNO" ? `${e.canal_nombre} · ${fechaHora(e.fecha_contacto)}` : TIPOS[e.tipo].etiqueta} />}
              </Stack>
              <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>{e.texto}</Typography>
            </Box>
          ))}
        </Stack>

        <Stack spacing={1.5}>
          {error && <Alert severity="error">{error}</Alert>}
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
            {tipos.length > 1 && (
              <TextField select size="small" label="Tipo" value={tipo} onChange={(e) => setTipo(e.target.value as EntradaSeguimiento["tipo"])} sx={{ minWidth: 200 }}>
                {tipos.map((t) => <MenuItem key={t} value={t}>{TIPOS[t].etiqueta}</MenuItem>)}
              </TextField>
            )}
            {tipo === "CONTACTO_EXTERNO" && (
              <>
                <TextField select size="small" label="Canal" value={canal} onChange={(e) => setCanal(e.target.value)} sx={{ minWidth: 150 }}>
                  {CANALES_CONTACTO.map((c) => <MenuItem key={c.valor} value={c.valor}>{c.etiqueta}</MenuItem>)}
                </TextField>
                <TextField size="small" type="datetime-local" label="Cuándo" value={cuando} onChange={(e) => setCuando(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
              </>
            )}
          </Stack>
          <TextField
            label={tipo === "CONTACTO_EXTERNO" ? "¿Qué se habló?" : tipo === "NOTA_INTERNA" ? "Nota interna" : "Escribe un mensaje"}
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            multiline
            minRows={2}
            fullWidth
          />
          <Button variant="contained" onClick={enviar} disabled={enviando || !texto.trim()} sx={{ alignSelf: "flex-end" }}>
            {tipo === "MENSAJE" ? "Enviar" : "Registrar"}
          </Button>
        </Stack>
      </CardContent>
    </Card>
  );
}
