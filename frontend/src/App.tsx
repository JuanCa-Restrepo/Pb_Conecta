import { Navigate, Route, Routes } from "react-router-dom";

import { RutaProtegida } from "./auth/RutaProtegida";
import { AppLayout } from "./layouts/AppLayout";
import { PublicoLayout } from "./layouts/PublicoLayout";
import DetalleConvocatoria from "./pages/convocatorias/DetalleConvocatoria";
import FormularioConvocatoria from "./pages/convocatorias/FormularioConvocatoria";
import ListaConvocatorias from "./pages/convocatorias/ListaConvocatorias";
import InicioEmpresa from "./pages/empresa/InicioEmpresa";
import PerfilEmpresa from "./pages/empresa/PerfilEmpresa";
import TalentoEmpresa from "./pages/empresa/TalentoEmpresa";
import DirectorioEmpresas from "./pages/empresas/DirectorioEmpresas";
import PaginaEmpresa from "./pages/empresas/PaginaEmpresa";
import ConvocatoriaEstudiante from "./pages/estudiante/ConvocatoriaEstudiante";
import ConvocatoriasEstudiante from "./pages/estudiante/ConvocatoriasEstudiante";
import InicioEstudiante from "./pages/estudiante/InicioEstudiante";
import MiPerfil from "./pages/estudiante/MiPerfil";
import Muro from "./pages/muro/Muro";
import Notificaciones from "./pages/Notificaciones";
import EmpresaDetalleOficina from "./pages/oficina/EmpresaDetalleOficina";
import EmpresasOficina from "./pages/oficina/EmpresasOficina";
import EstudiantesOficina from "./pages/oficina/EstudiantesOficina";
import AlertasOficina from "./pages/oficina/AlertasOficina";
import InicioOficina from "./pages/oficina/InicioOficina";
import PracticaDetalleOficina from "./pages/oficina/PracticaDetalleOficina";
import PracticasOficina from "./pages/oficina/PracticasOficina";
import IniciarSesion from "./pages/publico/IniciarSesion";
import Inicio from "./pages/publico/Inicio";
import RecuperarClave from "./pages/publico/RecuperarClave";
import RegistroEmpresa from "./pages/publico/RegistroEmpresa";
import RegistroEstudiante from "./pages/publico/RegistroEstudiante";
import RestablecerClave from "./pages/publico/RestablecerClave";
import VerificarCorreo from "./pages/publico/VerificarCorreo";
import DetallePostulacion from "./pages/postulaciones/DetallePostulacion";
import ListaPostulaciones from "./pages/postulaciones/ListaPostulaciones";

// Las pantallas de convocatorias son las mismas para la empresa y la oficina; cada una se adapta al rol
const rutasConvocatorias = (
  <>
    <Route path="convocatorias" element={<ListaConvocatorias />} />
    <Route path="convocatorias/nueva" element={<FormularioConvocatoria />} />
    <Route path="convocatorias/:id" element={<DetalleConvocatoria />} />
    <Route path="convocatorias/:id/editar" element={<FormularioConvocatoria />} />
  </>
);

export default function App() {
  return (
    <Routes>
      <Route element={<PublicoLayout />}>
        <Route index element={<Inicio />} />
        <Route path="iniciar-sesion" element={<IniciarSesion />} />
        <Route path="registro/estudiante" element={<RegistroEstudiante />} />
        <Route path="registro/empresa" element={<RegistroEmpresa />} />
        <Route path="verificar-correo" element={<VerificarCorreo />} />
        <Route path="recuperar-clave" element={<RecuperarClave />} />
        <Route path="restablecer-clave" element={<RestablecerClave />} />
        <Route path="empresas" element={<DirectorioEmpresas />} />
        <Route path="empresas/:id" element={<PaginaEmpresa />} />
      </Route>

      <Route element={<RutaProtegida />}>
        <Route element={<AppLayout />}>
          <Route path="notificaciones" element={<Notificaciones />} />
        </Route>
      </Route>

      <Route path="estudiante" element={<RutaProtegida roles={["ESTUDIANTE"]} />}>
        <Route element={<AppLayout />}>
          <Route index element={<InicioEstudiante />} />
          <Route path="perfil" element={<MiPerfil />} />
          <Route path="convocatorias" element={<ConvocatoriasEstudiante />} />
          <Route path="convocatorias/:id" element={<ConvocatoriaEstudiante />} />
          <Route path="postulaciones" element={<ListaPostulaciones />} />
          <Route path="postulaciones/:id" element={<DetallePostulacion />} />
          <Route path="muro" element={<Muro />} />
          <Route path="empresas" element={<DirectorioEmpresas base="/estudiante" />} />
          <Route path="empresas/:id" element={<PaginaEmpresa base="/estudiante" />} />
        </Route>
      </Route>

      <Route path="empresa" element={<RutaProtegida roles={["EMPRESA"]} />}>
        <Route element={<AppLayout />}>
          <Route index element={<InicioEmpresa />} />
          {rutasConvocatorias}
          <Route path="postulaciones/:id" element={<DetallePostulacion />} />
          <Route path="muro" element={<Muro />} />
          <Route path="perfil" element={<PerfilEmpresa />} />
          <Route path="talento" element={<TalentoEmpresa />} />
        </Route>
      </Route>

      <Route path="oficina" element={<RutaProtegida roles={["OFICINA", "SUPERADMIN"]} />}>
        <Route element={<AppLayout />}>
          <Route index element={<InicioOficina />} />
          <Route path="estudiantes" element={<EstudiantesOficina />} />
          <Route path="empresas" element={<EmpresasOficina />} />
          <Route path="empresas/:id" element={<EmpresaDetalleOficina />} />
          {rutasConvocatorias}
          <Route path="postulaciones" element={<ListaPostulaciones />} />
          <Route path="postulaciones/:id" element={<DetallePostulacion />} />
          <Route path="practicas" element={<PracticasOficina />} />
          <Route path="practicas/:id" element={<PracticaDetalleOficina />} />
          <Route path="alertas" element={<AlertasOficina />} />
          <Route path="muro" element={<Muro />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
