import ApartmentIcon from "@mui/icons-material/Apartment";
import AssignmentIndIcon from "@mui/icons-material/AssignmentInd";
import BarChartIcon from "@mui/icons-material/BarChart";
import BusinessCenterIcon from "@mui/icons-material/BusinessCenter";
import DashboardIcon from "@mui/icons-material/Dashboard";
import DynamicFeedIcon from "@mui/icons-material/DynamicFeed";
import FactCheckIcon from "@mui/icons-material/FactCheck";
import NotificationImportantIcon from "@mui/icons-material/NotificationImportant";
import PersonIcon from "@mui/icons-material/Person";
import PersonSearchIcon from "@mui/icons-material/PersonSearch";
import SchoolIcon from "@mui/icons-material/School";
import WorkIcon from "@mui/icons-material/Work";
import type { ReactElement } from "react";

import type { Rol } from "../api/tipos";

export interface ItemMenu {
  texto: string;
  ruta: string;
  icono: ReactElement;
}

// Mapa de pantallas por rol (docs/02-arquitectura.md, sección 4.3)
const ESTUDIANTE: ItemMenu[] = [
  { texto: "Inicio", ruta: "/estudiante", icono: <DashboardIcon /> },
  { texto: "Muro", ruta: "/estudiante/muro", icono: <DynamicFeedIcon /> },
  { texto: "Convocatorias", ruta: "/estudiante/convocatorias", icono: <WorkIcon /> },
  { texto: "Mis postulaciones", ruta: "/estudiante/postulaciones", icono: <AssignmentIndIcon /> },
  { texto: "Empresas", ruta: "/estudiante/empresas", icono: <ApartmentIcon /> },
  { texto: "Mi perfil", ruta: "/estudiante/perfil", icono: <PersonIcon /> },
];

const EMPRESA: ItemMenu[] = [
  { texto: "Inicio", ruta: "/empresa", icono: <DashboardIcon /> },
  { texto: "Muro", ruta: "/empresa/muro", icono: <DynamicFeedIcon /> },
  { texto: "Mis convocatorias", ruta: "/empresa/convocatorias", icono: <WorkIcon /> },
  { texto: "Buscar talento", ruta: "/empresa/talento", icono: <PersonSearchIcon /> },
  { texto: "Perfil de la empresa", ruta: "/empresa/perfil", icono: <ApartmentIcon /> },
];

const OFICINA: ItemMenu[] = [
  { texto: "Indicadores", ruta: "/oficina", icono: <BarChartIcon /> },
  { texto: "Alertas de seguimiento", ruta: "/oficina/alertas", icono: <NotificationImportantIcon /> },
  { texto: "Estudiantes y habilitación", ruta: "/oficina/estudiantes", icono: <SchoolIcon /> },
  { texto: "Empresas y convenios", ruta: "/oficina/empresas", icono: <ApartmentIcon /> },
  { texto: "Convocatorias", ruta: "/oficina/convocatorias", icono: <FactCheckIcon /> },
  { texto: "Postulaciones", ruta: "/oficina/postulaciones", icono: <AssignmentIndIcon /> },
  { texto: "Prácticas", ruta: "/oficina/practicas", icono: <BusinessCenterIcon /> },
  { texto: "Muro", ruta: "/oficina/muro", icono: <DynamicFeedIcon /> },
];

export function menuPorRol(rol: Rol): ItemMenu[] {
  if (rol === "ESTUDIANTE") return ESTUDIANTE;
  if (rol === "EMPRESA") return EMPRESA;
  return OFICINA;
}
