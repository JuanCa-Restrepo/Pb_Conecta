import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, tokens } from "../api/cliente";
import type { Rol, Usuario } from "../api/tipos";

interface ContextoAuth {
  usuario: Usuario | null;
  cargando: boolean;
  iniciarSesion: (email: string, password: string) => Promise<Usuario>;
  cerrarSesion: () => void;
  recargarUsuario: () => Promise<void>;
}

const Contexto = createContext<ContextoAuth | null>(null);

export function rutaInicio(rol: Rol): string {
  switch (rol) {
    case "ESTUDIANTE":
      return "/estudiante";
    case "EMPRESA":
      return "/empresa";
    default:
      return "/oficina";
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [cargando, setCargando] = useState(true);

  const recargarUsuario = useCallback(async () => {
    const { data } = await api.get<Usuario>("/auth/yo/");
    setUsuario(data);
  }, []);

  useEffect(() => {
    if (!tokens.acceso()) {
      setCargando(false);
      return;
    }
    recargarUsuario()
      .catch(() => tokens.borrar())
      .finally(() => setCargando(false));
  }, [recargarUsuario]);

  const iniciarSesion = useCallback(async (email: string, password: string) => {
    const { data } = await api.post("/auth/token/", { email, password });
    tokens.guardar(data.access, data.refresh);
    const { data: yo } = await api.get<Usuario>("/auth/yo/");
    setUsuario(yo);
    return yo;
  }, []);

  const cerrarSesion = useCallback(() => {
    tokens.borrar();
    setUsuario(null);
  }, []);

  const valor = useMemo(
    () => ({ usuario, cargando, iniciarSesion, cerrarSesion, recargarUsuario }),
    [usuario, cargando, iniciarSesion, cerrarSesion, recargarUsuario],
  );
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useAuth() {
  const contexto = useContext(Contexto);
  if (!contexto) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return contexto;
}
