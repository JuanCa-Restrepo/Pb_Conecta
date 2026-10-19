import UploadFileIcon from "@mui/icons-material/UploadFile";
import { Alert, Avatar, Button, Card, CardContent, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link as RouterLink } from "react-router-dom";

import { api, leerErrores } from "../../api/cliente";
import { TAMANOS_EMPRESA } from "../../api/opciones";
import type { ItemCatalogo, MiEmpresa } from "../../api/tipos";
import { useAviso } from "../../components/Avisos";

const CAMPOS = ["sector", "ciudad", "tamano", "descripcion", "sitio_web", "direccion", "contacto_nombre", "contacto_email", "contacto_telefono"] as const;

/** RF-20: la empresa mantiene su perfil. La razón social y el NIT los corrige la oficina. */
export default function PerfilEmpresa() {
  const cliente = useQueryClient();
  const avisar = useAviso();
  const { data: empresa } = useQuery({ queryKey: ["empresa", "yo"], queryFn: async () => (await api.get<MiEmpresa>("/empresas/yo/")).data });
  const { data: sectores = [] } = useQuery({ queryKey: ["catalogos", "sectores"], queryFn: async () => (await api.get<ItemCatalogo[]>("/catalogos/sectores/")).data });
  const { data: ciudades = [] } = useQuery({ queryKey: ["catalogos", "ciudades"], queryFn: async () => (await api.get<ItemCatalogo[]>("/catalogos/ciudades/")).data });
  const [form, setForm] = useState<Record<string, string>>({});
  const [errores, setErrores] = useState<{ general: string; campos: Record<string, string> }>({ general: "", campos: {} });

  useEffect(() => {
    if (empresa) setForm(Object.fromEntries(CAMPOS.map((c) => [c, empresa[c] === null ? "" : String(empresa[c])])));
  }, [empresa]);

  const campo = (nombre: (typeof CAMPOS)[number]) => ({
    value: form[nombre] ?? "",
    onChange: (e: { target: { value: string } }) => setForm({ ...form, [nombre]: e.target.value }),
    error: Boolean(errores.campos[nombre]),
    helperText: errores.campos[nombre],
    fullWidth: true,
  });

  async function guardar() {
    setErrores({ general: "", campos: {} });
    try {
      const { data } = await api.patch<MiEmpresa>("/empresas/yo/", { ...form, tamano: form.tamano || null, sector: Number(form.sector), ciudad: Number(form.ciudad) });
      cliente.setQueryData(["empresa", "yo"], data);
      avisar("Perfil actualizado.");
    } catch (e) {
      setErrores(leerErrores(e));
    }
  }

  async function subirLogo(archivo: File | undefined) {
    if (!archivo) return;
    const datos = new FormData();
    datos.append("logo", archivo);
    try {
      const { data } = await api.post<MiEmpresa>("/empresas/yo/logo/", datos);
      cliente.setQueryData(["empresa", "yo"], data);
      avisar("Logo actualizado.");
    } catch (e) {
      const { general, campos } = leerErrores(e);
      avisar(campos.logo ?? general, "error");
    }
  }

  if (!empresa) return null;
  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ justifyContent: "space-between", alignItems: { sm: "center" } }}>
        <div>
          <Typography variant="h5" component="h1">Perfil de la empresa</Typography>
          <Typography color="text.secondary">Así te ven los estudiantes en el directorio de empresas aliadas.</Typography>
        </div>
        {empresa.estado === "ALIADA" && <Button variant="outlined" component={RouterLink} to={`/empresas/${empresa.id}`}>Ver página pública</Button>}
      </Stack>

      <Card>
        <CardContent>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ alignItems: { sm: "center" } }}>
            <Avatar src={empresa.logo ?? undefined} variant="rounded" sx={{ width: 80, height: 80, bgcolor: "primary.main", fontSize: 32 }}>{empresa.razon_social[0]}</Avatar>
            <Stack sx={{ flex: 1 }}>
              <Typography variant="h6">{empresa.razon_social}</Typography>
              <Typography variant="body2" color="text.secondary">NIT {empresa.nit} · {empresa.estado_nombre}</Typography>
            </Stack>
            <Button component="label" variant="outlined" startIcon={<UploadFileIcon />}>
              {empresa.logo ? "Cambiar logo" : "Subir logo"}
              <input hidden type="file" accept="image/png,image/jpeg,image/webp" onChange={(e) => { subirLogo(e.target.files?.[0]); e.target.value = ""; }} />
            </Button>
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Stack spacing={2}>
            {errores.general && <Alert severity="error">{errores.general}</Alert>}
            <TextField label="Descripción" multiline minRows={4} {...campo("descripcion")} placeholder="¿A qué se dedica la empresa? ¿Qué aprende un practicante allí?" />
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField select label="Sector" {...campo("sector")}>
                {sectores.map((s) => <MenuItem key={s.id} value={String(s.id)}>{s.nombre}</MenuItem>)}
              </TextField>
              <TextField select label="Ciudad" {...campo("ciudad")}>
                {ciudades.map((c) => <MenuItem key={c.id} value={String(c.id)}>{c.nombre}</MenuItem>)}
              </TextField>
              <TextField select label="Tamaño" {...campo("tamano")}>
                <MenuItem value="">Sin especificar</MenuItem>
                {TAMANOS_EMPRESA.map((t) => <MenuItem key={t.valor} value={t.valor}>{t.etiqueta}</MenuItem>)}
              </TextField>
            </Stack>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField label="Sitio web" type="url" placeholder="https://" {...campo("sitio_web")} />
              <TextField label="Dirección" {...campo("direccion")} />
            </Stack>
            <Typography variant="subtitle2">Contacto para los practicantes</Typography>
            <Typography variant="caption" color="text.secondary">Lo ven los estudiantes desde que los preseleccionas (RF-58).</Typography>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField label="Nombre" {...campo("contacto_nombre")} />
              <TextField label="Correo" type="email" {...campo("contacto_email")} />
              <TextField label="Teléfono" {...campo("contacto_telefono")} />
            </Stack>
            <Button variant="contained" onClick={guardar} sx={{ alignSelf: "flex-end" }}>Guardar</Button>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}
