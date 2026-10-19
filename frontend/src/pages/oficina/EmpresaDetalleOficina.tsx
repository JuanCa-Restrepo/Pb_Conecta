import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import {
  Alert, Box, Button, Card, CardContent, CardHeader, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Divider,
  IconButton, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Tooltip, Typography,
} from "@mui/material";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";
import { Link as RouterLink, useParams } from "react-router-dom";

import { api, leerErrores } from "../../api/cliente";
import { abrirArchivoProtegido } from "../../api/descargas";
import type { EmpresaDetalle } from "../../api/tipos";
import { useAviso } from "../../components/Avisos";
import { agregarConvenio, CamposConvenio, convenioInicial } from "../../components/CamposConvenio";
import { DialogoTexto } from "../../components/DialogoTexto";
import { EstadoChip } from "../../components/EstadoChip";
import { fecha } from "../../utilidades/formato";

type Dialogo = null | "aprobar" | "convenio" | "rechazar" | "suspender" | "reactivar";

function DialogoConvenio({ abierto, titulo, descripcion, textoConfirmar, onCerrar, onConfirmar }: {
  abierto: boolean; titulo: string; descripcion: string; textoConfirmar: string; onCerrar: () => void; onConfirmar: (datos: FormData) => Promise<unknown>;
}) {
  const [convenio, setConvenio] = useState(convenioInicial);
  const [errores, setErrores] = useState<{ general: string; campos: Record<string, string> }>({ general: "", campos: {} });
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (abierto) {
      setConvenio(convenioInicial());
      setErrores({ general: "", campos: {} });
    }
  }, [abierto]);

  async function confirmar() {
    const datos = new FormData();
    agregarConvenio(datos, convenio);
    setEnviando(true);
    try {
      await onConfirmar(datos);
      onCerrar();
    } catch (e) {
      setErrores(leerErrores(e));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Dialog open={abierto} onClose={onCerrar} fullWidth maxWidth="sm">
      <DialogTitle>{titulo}</DialogTitle>
      <DialogContent>
        <Typography color="text.secondary" sx={{ mb: 2 }}>{descripcion}</Typography>
        {errores.general && <Alert severity="error" sx={{ mb: 2 }}>{errores.general}</Alert>}
        <CamposConvenio valor={convenio} onCambio={setConvenio} errores={errores.campos} />
      </DialogContent>
      <DialogActions>
        <Button onClick={onCerrar} disabled={enviando}>Cancelar</Button>
        <Button variant="contained" onClick={confirmar} disabled={enviando}>{textoConfirmar}</Button>
      </DialogActions>
    </Dialog>
  );
}

function Dato({ etiqueta, children }: { etiqueta: string; children: ReactNode }) {
  return (
    <Box sx={{ minWidth: 180, flex: "1 1 180px" }}>
      <Typography variant="caption" color="text.secondary">{etiqueta}</Typography>
      <Typography variant="body2">{children || "—"}</Typography>
    </Box>
  );
}

export default function EmpresaDetalleOficina() {
  const { id } = useParams();
  const cliente = useQueryClient();
  const avisar = useAviso();
  const [dialogo, setDialogo] = useState<Dialogo>(null);

  const { data: empresa } = useQuery({
    queryKey: ["oficina", "empresa", id],
    queryFn: async () => (await api.get<EmpresaDetalle>(`/oficina/empresas/${id}/`)).data,
  });

  async function ejecutar(accion: string, datos: FormData | object, mensaje: string) {
    const { data } = await api.post<EmpresaDetalle>(`/oficina/empresas/${id}/${accion}/`, datos);
    cliente.setQueryData(["oficina", "empresa", id], data);
    cliente.invalidateQueries({ queryKey: ["oficina", "empresas"] });
    avisar(mensaje);
  }

  if (!empresa) return null;
  const { estado } = empresa;

  return (
    <Stack spacing={2}>
      <Button component={RouterLink} to="/oficina/empresas" startIcon={<ArrowBackIcon />} sx={{ alignSelf: "flex-start" }}>Empresas</Button>

      <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ justifyContent: "space-between" }}>
        <div>
          <Typography variant="h5" component="h1">{empresa.razon_social}</Typography>
          <Stack direction="row" spacing={1} sx={{ mt: 1, alignItems: "center", flexWrap: "wrap" }}>
            <EstadoChip estado={estado} etiqueta={empresa.estado_nombre} />
            <Typography variant="body2" color="text.secondary">NIT {empresa.nit}</Typography>
            {empresa.creada_por_oficina && <Chip size="small" variant="outlined" label="Registrada por la oficina" />}
          </Stack>
        </div>
        <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap", alignItems: "flex-start" }}>
          {estado === "PENDIENTE" && (
            <>
              <Button variant="contained" onClick={() => setDialogo("aprobar")}>Aprobar y registrar convenio</Button>
              <Button color="error" variant="outlined" onClick={() => setDialogo("rechazar")}>Rechazar</Button>
            </>
          )}
          {(estado === "ALIADA" || estado === "CONVENIO_VENCIDO") && (
            <>
              <Button variant="contained" onClick={() => setDialogo("convenio")}>{estado === "CONVENIO_VENCIDO" ? "Renovar convenio" : "Registrar convenio"}</Button>
              <Button color="error" variant="outlined" onClick={() => setDialogo("suspender")}>Suspender</Button>
            </>
          )}
          {estado === "SUSPENDIDA" && <Button variant="contained" onClick={() => setDialogo("reactivar")}>Reactivar</Button>}
        </Stack>
      </Stack>

      {empresa.motivo_estado && <Alert severity={estado === "RECHAZADA" || estado === "SUSPENDIDA" ? "error" : "info"}>Motivo: {empresa.motivo_estado}</Alert>}
      {estado === "CONVENIO_VENCIDO" && <Alert severity="warning">El convenio venció: la empresa no puede crear convocatorias nuevas hasta que se registre uno vigente (RN-02).</Alert>}

      <Card>
        <CardHeader title="Datos de la empresa" slotProps={{ title: { variant: "h6" } }} />
        <CardContent sx={{ pt: 0 }}>
          <Stack direction="row" useFlexGap spacing={2} sx={{ flexWrap: "wrap" }}>
            <Dato etiqueta="Sector">{empresa.sector_nombre}</Dato>
            <Dato etiqueta="Ciudad">{empresa.ciudad_nombre}</Dato>
            <Dato etiqueta="Tamaño">{empresa.tamano_nombre}</Dato>
            <Dato etiqueta="Sitio web">{empresa.sitio_web}</Dato>
            <Dato etiqueta="Contacto">{empresa.contacto_nombre}</Dato>
            <Dato etiqueta="Correo">{empresa.contacto_email}</Dato>
            <Dato etiqueta="Teléfono">{empresa.contacto_telefono}</Dato>
            <Dato etiqueta="Solicitud">{fecha(empresa.creado_en)}</Dato>
          </Stack>
          {empresa.descripcion && (<><Divider sx={{ my: 2 }} /><Typography variant="body2">{empresa.descripcion}</Typography></>)}
        </CardContent>
      </Card>

      <Card>
        <CardHeader title="Convenios" slotProps={{ title: { variant: "h6" } }} />
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Número</TableCell><TableCell>Inicio</TableCell><TableCell>Fin</TableCell>
                <TableCell>Estado</TableCell><TableCell>Registrado por</TableCell><TableCell align="right">Documento</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {empresa.convenios.map((c) => (
                <TableRow key={c.id}>
                  <TableCell>{c.numero}</TableCell>
                  <TableCell>{fecha(c.fecha_inicio)}</TableCell>
                  <TableCell>{fecha(c.fecha_fin)}</TableCell>
                  <TableCell>{c.vigente ? <Chip size="small" color="success" label="Vigente" /> : <Chip size="small" label="No vigente" />}</TableCell>
                  <TableCell>{c.registrado_por_nombre}</TableCell>
                  <TableCell align="right">
                    {c.tiene_documento ? (
                      <Tooltip title="Ver PDF">
                        <IconButton
                          size="small"
                          aria-label={`Ver PDF del convenio ${c.numero}`}
                          onClick={() => abrirArchivoProtegido(`/oficina/empresas/${empresa.id}/convenios/${c.id}/documento/`).catch((e) => avisar(leerErrores(e).general, "error"))}
                        >
                          <PictureAsPdfIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    ) : "—"}
                  </TableCell>
                </TableRow>
              ))}
              {empresa.convenios.length === 0 && (
                <TableRow><TableCell colSpan={6} sx={{ py: 3, textAlign: "center", color: "text.secondary" }}>Aún no hay convenios registrados.</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      <Card>
        <CardHeader title="Usuarios de la empresa" slotProps={{ title: { variant: "h6" } }} />
        <CardContent sx={{ pt: 0 }}>
          {empresa.usuarios.length === 0 ? (
            <Typography color="text.secondary">Sin usuarios: la oficina publica las convocatorias en su nombre.</Typography>
          ) : (
            empresa.usuarios.map((u) => (
              <Typography key={u.email} variant="body2">
                {u.nombre}{u.cargo ? ` · ${u.cargo}` : ""} · {u.email}{u.activo ? "" : " (correo sin verificar)"}
              </Typography>
            ))
          )}
        </CardContent>
      </Card>

      <DialogoConvenio
        abierto={dialogo === "aprobar"}
        titulo="Aprobar empresa"
        descripcion="Registra el convenio firmado. Debe estar vigente hoy para que la empresa quede como aliada."
        textoConfirmar="Aprobar"
        onCerrar={() => setDialogo(null)}
        onConfirmar={(datos) => ejecutar("aprobar", datos, "Empresa aprobada. Se notificó a sus usuarios.")}
      />
      <DialogoConvenio
        abierto={dialogo === "convenio"}
        titulo={estado === "CONVENIO_VENCIDO" ? "Renovar convenio" : "Registrar convenio"}
        descripcion="Si la empresa tenía el convenio vencido y este está vigente, vuelve a quedar como aliada."
        textoConfirmar="Guardar convenio"
        onCerrar={() => setDialogo(null)}
        onConfirmar={(datos) => ejecutar("convenios", datos, "Convenio registrado.")}
      />
      <DialogoTexto
        abierto={dialogo === "rechazar"}
        titulo="Rechazar solicitud"
        descripcion="La empresa verá este motivo."
        etiqueta="Motivo del rechazo"
        obligatorio
        textoConfirmar="Rechazar"
        colorConfirmar="error"
        onCerrar={() => setDialogo(null)}
        onConfirmar={(motivo) => ejecutar("rechazar", { motivo }, "Solicitud rechazada.")}
      />
      <DialogoTexto
        abierto={dialogo === "suspender"}
        titulo="Suspender empresa"
        descripcion="La empresa no podrá publicar convocatorias mientras esté suspendida."
        etiqueta="Motivo de la suspensión"
        obligatorio
        textoConfirmar="Suspender"
        colorConfirmar="error"
        onCerrar={() => setDialogo(null)}
        onConfirmar={(motivo) => ejecutar("suspender", { motivo }, "Empresa suspendida.")}
      />
      <DialogoTexto
        abierto={dialogo === "reactivar"}
        titulo="Reactivar empresa"
        descripcion="Volverá a ser aliada si tiene un convenio vigente; si no, quedará con el convenio vencido."
        textoConfirmar="Reactivar"
        onCerrar={() => setDialogo(null)}
        onConfirmar={() => ejecutar("reactivar", {}, "Empresa reactivada.")}
      />
    </Stack>
  );
}
