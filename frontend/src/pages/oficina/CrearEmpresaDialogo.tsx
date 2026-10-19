import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, Divider, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api, leerErrores } from "../../api/cliente";
import type { EmpresaDetalle, ItemCatalogo } from "../../api/tipos";
import { agregarConvenio, CamposConvenio, convenioInicial } from "../../components/CamposConvenio";

const VACIO = {
  razon_social: "", nit: "", sector: "", ciudad: "", contacto_nombre: "", contacto_email: "", contacto_telefono: "", sitio_web: "",
};

/** RF-24: la oficina registra una empresa aliada con su convenio en un solo paso. */
export function CrearEmpresaDialogo({ abierto, onCerrar, onCreada }: { abierto: boolean; onCerrar: () => void; onCreada: (e: EmpresaDetalle) => void }) {
  const { data: sectores = [] } = useQuery({ queryKey: ["catalogos", "sectores"], queryFn: async () => (await api.get<ItemCatalogo[]>("/catalogos/sectores/")).data });
  const { data: ciudades = [] } = useQuery({ queryKey: ["catalogos", "ciudades"], queryFn: async () => (await api.get<ItemCatalogo[]>("/catalogos/ciudades/")).data });

  const [form, setForm] = useState(VACIO);
  const [convenio, setConvenio] = useState(convenioInicial);
  const [errores, setErrores] = useState<{ general: string; campos: Record<string, string> }>({ general: "", campos: {} });
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (abierto) {
      setForm(VACIO);
      setConvenio(convenioInicial());
      setErrores({ general: "", campos: {} });
    }
  }, [abierto]);

  const campo = (nombre: keyof typeof VACIO) => ({
    value: form[nombre],
    onChange: (e: { target: { value: string } }) => setForm({ ...form, [nombre]: e.target.value }),
    error: Boolean(errores.campos[nombre]),
    helperText: errores.campos[nombre],
  });

  async function guardar() {
    setEnviando(true);
    const datos = new FormData();
    Object.entries(form).forEach(([clave, valor]) => datos.append(clave, valor.trim()));
    agregarConvenio(datos, convenio);
    try {
      const { data } = await api.post<EmpresaDetalle>("/oficina/empresas/", datos);
      onCreada(data);
    } catch (e) {
      setErrores(leerErrores(e));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Dialog open={abierto} onClose={onCerrar} fullWidth maxWidth="md">
      <DialogTitle>Registrar empresa aliada</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          <Typography color="text.secondary">
            Para empresas que llegaron por otros canales. Queda aliada de inmediato y la oficina puede publicar convocatorias en su nombre.
          </Typography>
          {errores.general && <Alert severity="error">{errores.general}</Alert>}
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField label="Razón social" fullWidth required {...campo("razon_social")} />
            <TextField label="NIT" placeholder="900123456-7" fullWidth required {...campo("nit")} />
          </Stack>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField select label="Sector" fullWidth required {...campo("sector")}>
              {sectores.map((s) => <MenuItem key={s.id} value={String(s.id)}>{s.nombre}</MenuItem>)}
            </TextField>
            <TextField select label="Ciudad" fullWidth required {...campo("ciudad")}>
              {ciudades.map((c) => <MenuItem key={c.id} value={String(c.id)}>{c.nombre}</MenuItem>)}
            </TextField>
          </Stack>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField label="Persona de contacto" fullWidth required {...campo("contacto_nombre")} />
            <TextField label="Correo de contacto" type="email" fullWidth required {...campo("contacto_email")} />
          </Stack>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField label="Teléfono" fullWidth {...campo("contacto_telefono")} />
            <TextField label="Sitio web" placeholder="https://" fullWidth {...campo("sitio_web")} />
          </Stack>
          <Divider />
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Convenio</Typography>
          <CamposConvenio valor={convenio} onCambio={setConvenio} errores={errores.campos} />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCerrar} disabled={enviando}>Cancelar</Button>
        <Button variant="contained" onClick={guardar} disabled={enviando}>Registrar empresa</Button>
      </DialogActions>
    </Dialog>
  );
}
