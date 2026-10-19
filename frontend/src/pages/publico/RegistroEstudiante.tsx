import { MenuItem, Stack, TextField } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { api, leerErrores } from "../../api/cliente";
import type { Programa } from "../../api/tipos";
import { FormularioRegistro } from "../../components/FormularioRegistro";

const DOMINIO = "pascualbravo.edu.co";

export default function RegistroEstudiante() {
  const { data: programas = [] } = useQuery({
    queryKey: ["catalogos", "programas"],
    queryFn: async () => (await api.get<Programa[]>("/catalogos/programas/")).data,
  });

  const [form, setForm] = useState({
    nombres: "", apellidos: "", email: "", telefono: "", programa: "", semestre: "", documento: "", password: "",
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
      const { data } = await api.post("/auth/registro/estudiante/", {
        ...form,
        email: form.email.trim(),
        programa: form.programa ? Number(form.programa) : null,
        semestre: form.semestre ? Number(form.semestre) : null,
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
      titulo="Registro de estudiante"
      descripcion={`Usa tu correo institucional @${DOMINIO}. La oficina de prácticas te habilitará cuando cumplas los requisitos.`}
      errorGeneral={errores.general}
      errorPolitica={errores.campos.acepta_politica}
      aceptaPolitica={acepta}
      onAceptaPolitica={setAcepta}
      enviando={enviando}
      exito={exito}
      onEnviar={enviar}
    >
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <TextField label="Nombres" fullWidth required {...campo("nombres")} />
        <TextField label="Apellidos" fullWidth required {...campo("apellidos")} />
      </Stack>
      <TextField label="Correo institucional" type="email" placeholder={`nombre.apellido@${DOMINIO}`} required {...campo("email")} />
      <TextField select label="Programa académico" required {...campo("programa")}>
        {programas.map((p) => (
          <MenuItem key={p.id} value={String(p.id)}>{p.nombre} · {p.nivel_nombre}</MenuItem>
        ))}
      </TextField>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <TextField label="Semestre" type="number" fullWidth slotProps={{ htmlInput: { min: 1, max: 12 } }} {...campo("semestre")} />
        <TextField label="Teléfono" fullWidth {...campo("telefono")} />
        <TextField label="Documento (opcional)" fullWidth {...campo("documento")} />
      </Stack>
      <TextField label="Contraseña" type="password" autoComplete="new-password" required
        {...campo("password")} helperText={errores.campos.password ?? "Mínimo 8 caracteres, no solo números."} />
    </FormularioRegistro>
  );
}
