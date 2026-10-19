import { Box, CircularProgress } from "@mui/material";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import type { Rol } from "../api/tipos";
import { rutaInicio, useAuth } from "./AuthContext";

/** Deja pasar solo a usuarios con sesión y con uno de los roles indicados (RF-07). */
export function RutaProtegida({ roles }: { roles?: Rol[] }) {
  const { usuario, cargando } = useAuth();
  const ubicacion = useLocation();

  if (cargando) {
    return (
      <Box sx={{ display: "grid", placeItems: "center", minHeight: "100vh" }}>
        <CircularProgress />
      </Box>
    );
  }
  if (!usuario) return <Navigate to="/iniciar-sesion" replace state={{ desde: ubicacion.pathname }} />;
  if (roles && !roles.includes(usuario.rol)) return <Navigate to={rutaInicio(usuario.rol)} replace />;
  return <Outlet />;
}
