import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { Button, Stack, Typography } from "@mui/material";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link as RouterLink, useParams } from "react-router-dom";

import { api } from "../../api/cliente";
import type { Practica } from "../../api/tipos";
import { useAviso } from "../../components/Avisos";
import { DialogoTexto } from "../../components/DialogoTexto";
import { TarjetaPractica } from "../../components/practicas/TarjetaPractica";

export default function PracticaDetalleOficina() {
  const { id } = useParams();
  const cliente = useQueryClient();
  const avisar = useAviso();
  const [dialogo, setDialogo] = useState<null | "finalizar" | "cancelar">(null);
  const { data: practica } = useQuery({ queryKey: ["practica", id], queryFn: async () => (await api.get<Practica>(`/practicas/${id}/`)).data });

  async function ejecutar(accion: "finalizar" | "cancelar", observacion: string) {
    const { data } = await api.post<Practica>(`/practicas/${id}/${accion}/`, { observacion });
    cliente.setQueryData(["practica", id], data);
    cliente.invalidateQueries({ queryKey: ["practicas"] });
    avisar(accion === "finalizar" ? "Práctica finalizada." : "Práctica cancelada: el estudiante vuelve a quedar habilitado.");
  }

  if (!practica) return null;
  const activa = practica.estado === "LEGALIZADA" || practica.estado === "EN_CURSO";

  return (
    <Stack spacing={2}>
      <Button component={RouterLink} to="/oficina/practicas" startIcon={<ArrowBackIcon />} sx={{ alignSelf: "flex-start" }}>Prácticas</Button>
      <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ justifyContent: "space-between" }}>
        <div>
          <Typography variant="h5" component="h1">{practica.estudiante.nombre}</Typography>
          <Typography color="text.secondary">{practica.convocatoria.titulo} · {practica.convocatoria.empresa}</Typography>
        </div>
        <Stack direction="row" spacing={1} sx={{ alignItems: "flex-start" }}>
          <Button variant="outlined" component={RouterLink} to={`/oficina/postulaciones/${practica.postulacion}`}>Ver postulación</Button>
          {activa && <Button variant="contained" onClick={() => setDialogo("finalizar")}>Finalizar práctica</Button>}
          {activa && <Button color="error" onClick={() => setDialogo("cancelar")}>Cancelar</Button>}
        </Stack>
      </Stack>
      <TarjetaPractica practica={practica} />

      <DialogoTexto
        abierto={dialogo === "finalizar"}
        titulo="Finalizar práctica"
        descripcion="Registra el cierre: el estudiante queda con la práctica finalizada (RF-65)."
        etiqueta="Observación de cierre"
        obligatorio
        textoConfirmar="Finalizar"
        onCerrar={() => setDialogo(null)}
        onConfirmar={(texto) => ejecutar("finalizar", texto)}
      />
      <DialogoTexto
        abierto={dialogo === "cancelar"}
        titulo="Cancelar práctica"
        descripcion="Úsalo si la práctica no se realizó o se interrumpió. El estudiante vuelve a quedar habilitado para buscar otra."
        etiqueta="Motivo"
        obligatorio
        textoConfirmar="Cancelar práctica"
        colorConfirmar="error"
        onCerrar={() => setDialogo(null)}
        onConfirmar={(texto) => ejecutar("cancelar", texto)}
      />
    </Stack>
  );
}
