import { Alert, Box, Button, CircularProgress } from "@mui/material";
import { useEffect, useRef, useState } from "react";
import { Link as RouterLink, useSearchParams } from "react-router-dom";

import { api, leerErrores } from "../../api/cliente";

export default function VerificarCorreo() {
  const [parametros] = useSearchParams();
  const [estado, setEstado] = useState<{ tipo: "cargando" | "ok" | "error"; mensaje: string }>({ tipo: "cargando", mensaje: "" });
  const enviado = useRef(false);

  useEffect(() => {
    if (enviado.current) return; // Evita el doble envío del modo estricto de React
    enviado.current = true;
    const token = parametros.get("token");
    if (!token) {
      setEstado({ tipo: "error", mensaje: "El enlace no tiene token de verificación." });
      return;
    }
    api
      .post("/auth/verificar-correo/", { token })
      .then(({ data }) => setEstado({ tipo: "ok", mensaje: data.detalle }))
      .catch((e) => {
        const { general, campos } = leerErrores(e);
        setEstado({ tipo: "error", mensaje: campos.token ?? general });
      });
  }, [parametros]);

  return (
    <Box sx={{ maxWidth: 480, mx: "auto", textAlign: "center" }}>
      {estado.tipo === "cargando" ? (
        <CircularProgress />
      ) : (
        <>
          <Alert severity={estado.tipo === "ok" ? "success" : "error"} sx={{ mb: 2, textAlign: "left" }}>{estado.mensaje}</Alert>
          <Button variant="contained" component={RouterLink} to="/iniciar-sesion">Iniciar sesión</Button>
        </>
      )}
    </Box>
  );
}
