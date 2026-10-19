import { Divider, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { api, leerErrores } from "../../api/cliente";
import type { ItemCatalogo } from "../../api/tipos";
import { FormularioRegistro } from "../../components/FormularioRegistro";

export default function RegistroEmpresa() {
  const { data: sectores = [] } = useQuery({
    queryKey: ["catalogos", "sectores"],
    queryFn: async () => (await api.get<ItemCatalogo[]>("/catalogos/sectores/")).data,
  });
  const { data: ciudades = [] } = useQuery({
    queryKey: ["catalogos", "ciudades"],
    queryFn: async () => (await api.get<ItemCatalogo[]>("/catalogos/ciudades/")).data,
  });

  const [form, setForm] = useState({
    razon_social: "", nit: "", sector: "", ciudad: "", sitio_web: "", descripcion: "",
    nombres: "", apellidos: "", cargo: "", email: "", telefono: "", password: "",
  });
  const [acepta, setAcepta] = useState(false);
  const [errores, setErrores] = useState<{ general: string; campos: Record<string, string> }>({ general: "", campos: {} });
  const [enviando, setEnviando] = useState(false);
  const [exito, setExito] = useState("");

  const campo = (nombre: keyof typeof form) => ({
    value: form[nombre],
    onChange: (e: { target: { value: string } }) => setForm({ ...form, [nombre]: e.target.value }),
    error: Boolean(errores.campos[nombre]),
    helperText: errores.campos[nombre],
  });

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setEnviando(true);
    setErrores({ general: "", campos: {} });
    try {
      const { data } = await api.post("/auth/registro/empresa/", {
        ...form,
        email: form.email.trim(),
        sector: form.sector ? Number(form.sector) : null,
        ciudad: form.ciudad ? Number(form.ciudad) : null,
        acepta_politica: acepta,
      });
      setExito(data.detalle);
    } catch (e) {
      setErrores(leerErrores(e));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <FormularioRegistro
      titulo="Solicitud de registro de empresa"
      descripcion="La oficina de prácticas revisará la solicitud y registrará el convenio. Solo las empresas aliadas con convenio vigente pueden publicar convocatorias."
      errorGeneral={errores.general}
      errorPolitica={errores.campos.acepta_politica}
      aceptaPolitica={acepta}
      onAceptaPolitica={setAcepta}
      enviando={enviando}
      exito={exito}
      onEnviar={enviar}
    >
      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Datos de la empresa</Typography>
      <TextField label="Razón social" required {...campo("razon_social")} />
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <TextField label="NIT" placeholder="900123456-7" fullWidth required {...campo("nit")} />
        <TextField select label="Sector" fullWidth required {...campo("sector")}>
          {sectores.map((s) => <MenuItem key={s.id} value={String(s.id)}>{s.nombre}</MenuItem>)}
        </TextField>
      </Stack>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <TextField select label="Ciudad" fullWidth required {...campo("ciudad")}>
          {ciudades.map((c) => <MenuItem key={c.id} value={String(c.id)}>{c.nombre} ({c.departamento})</MenuItem>)}
        </TextField>
        <TextField label="Sitio web" placeholder="https://" fullWidth {...campo("sitio_web")} />
      </Stack>
      <TextField label="Descripción" multiline minRows={2} {...campo("descripcion")} />

      <Divider />
      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Persona de contacto (usuario reclutador)</Typography>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <TextField label="Nombres" fullWidth required {...campo("nombres")} />
        <TextField label="Apellidos" fullWidth required {...campo("apellidos")} />
      </Stack>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <TextField label="Cargo" fullWidth {...campo("cargo")} />
        <TextField label="Teléfono" fullWidth {...campo("telefono")} />
      </Stack>
      <TextField label="Correo corporativo" type="email" required {...campo("email")} />
      <TextField label="Contraseña" type="password" autoComplete="new-password" required
        {...campo("password")} helperText={errores.campos.password ?? "Mínimo 8 caracteres, no solo números."} />
    </FormularioRegistro>
  );
}
