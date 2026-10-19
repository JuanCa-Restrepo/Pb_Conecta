import LogoutIcon from "@mui/icons-material/Logout";
import MenuIcon from "@mui/icons-material/Menu";
import NotificationsIcon from "@mui/icons-material/Notifications";
import {
  AppBar, Avatar, Badge, Box, Divider, Drawer, IconButton, List, ListItemButton, ListItemIcon, ListItemText, Menu, MenuItem,
  Toolbar, Tooltip, Typography, useMediaQuery, useTheme,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { api } from "../api/cliente";
import { useAuth } from "../auth/AuthContext";
import { DialogoCambiarClave } from "../components/DialogoCambiarClave";
import { menuPorRol } from "./menus";

const ANCHO_MENU = 248;

function Campana() {
  const navegar = useNavigate();
  const { data } = useQuery({
    queryKey: ["notificaciones", "conteo"],
    queryFn: async () => (await api.get<{ no_leidas: number }>("/notificaciones/no-leidas/conteo/")).data,
    refetchInterval: 60_000,
  });
  return (
    <Tooltip title="Notificaciones">
      <IconButton color="inherit" onClick={() => navegar("/notificaciones")} aria-label="Notificaciones">
        <Badge badgeContent={data?.no_leidas ?? 0} color="secondary">
          <NotificationsIcon />
        </Badge>
      </IconButton>
    </Tooltip>
  );
}

export function AppLayout() {
  const { usuario, cerrarSesion } = useAuth();
  const tema = useTheme();
  const esMovil = useMediaQuery(tema.breakpoints.down("md"));
  const [abierto, setAbierto] = useState(false);
  const [menuCuenta, setMenuCuenta] = useState<HTMLElement | null>(null);
  const [cambiandoClave, setCambiandoClave] = useState(false);
  const navegar = useNavigate();

  if (!usuario) return null;
  const items = menuPorRol(usuario.rol);

  const menu = (
    <Box sx={{ width: "100%", overflowX: "hidden" }}>
      <Toolbar />
      <Box sx={{ px: 2, py: 1.5 }}>
        <Typography variant="subtitle2" noWrap>{usuario.nombres} {usuario.apellidos}</Typography>
        <Typography variant="caption" color="text.secondary">{usuario.rol_nombre}</Typography>
      </Box>
      <Divider />
      <List dense>
        {items.map((item) => (
          <ListItemButton
            key={item.ruta}
            component={NavLink}
            to={item.ruta}
            end={item.ruta.split("/").length === 2}
            onClick={() => setAbierto(false)}
            sx={{ "&.active": { bgcolor: "action.selected", color: "primary.main", "& .MuiListItemIcon-root": { color: "primary.main" } } }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>{item.icono}</ListItemIcon>
            <ListItemText primary={item.texto} />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
        <Toolbar>
          {esMovil && (
            <IconButton color="inherit" edge="start" onClick={() => setAbierto(true)} aria-label="Abrir menú" sx={{ mr: 1 }}>
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700 }}>PB Conecta</Typography>
          <Campana />
          <Tooltip title="Cerrar sesión">
            <IconButton color="inherit" aria-label="Cerrar sesión" onClick={() => { cerrarSesion(); navegar("/"); }}>
              <LogoutIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Mi cuenta">
            <IconButton aria-label="Mi cuenta" onClick={(e) => setMenuCuenta(e.currentTarget)} sx={{ ml: 0.5, p: 0.5 }}>
              <Avatar sx={{ width: 32, height: 32, bgcolor: "secondary.main", color: "primary.main", fontSize: 14 }}>
                {usuario.nombres[0]}{usuario.apellidos[0]}
              </Avatar>
            </IconButton>
          </Tooltip>
          <Menu anchorEl={menuCuenta} open={Boolean(menuCuenta)} onClose={() => setMenuCuenta(null)}>
            <MenuItem disabled sx={{ opacity: "1 !important" }}>
              <ListItemText primary={`${usuario.nombres} ${usuario.apellidos}`} secondary={usuario.email} />
            </MenuItem>
            <Divider />
            <MenuItem onClick={() => { setMenuCuenta(null); setCambiandoClave(true); }}>Cambiar contraseña</MenuItem>
            <MenuItem onClick={() => { cerrarSesion(); navegar("/"); }}>Cerrar sesión</MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>
      <DialogoCambiarClave abierto={cambiandoClave} onCerrar={() => setCambiandoClave(false)} />

      <Drawer
        variant={esMovil ? "temporary" : "permanent"}
        open={esMovil ? abierto : true}
        onClose={() => setAbierto(false)}
        sx={{ width: ANCHO_MENU, flexShrink: 0, "& .MuiDrawer-paper": { width: ANCHO_MENU, boxSizing: "border-box" } }}
      >
        {menu}
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, minWidth: 0, p: { xs: 2, md: 3 } }}>
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}
