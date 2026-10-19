import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

// Tokens JWT (RNF-04). En el prototipo se guardan en localStorage.
const CLAVE_ACCESO = "pbc_acceso";
const CLAVE_RENOVACION = "pbc_renovacion";

export const tokens = {
  acceso: () => localStorage.getItem(CLAVE_ACCESO),
  renovacion: () => localStorage.getItem(CLAVE_RENOVACION),
  guardar(acceso: string, renovacion?: string) {
    localStorage.setItem(CLAVE_ACCESO, acceso);
    if (renovacion) localStorage.setItem(CLAVE_RENOVACION, renovacion);
  },
  borrar() {
    localStorage.removeItem(CLAVE_ACCESO);
    localStorage.removeItem(CLAVE_RENOVACION);
  },
};

export const api = axios.create({ baseURL: "/api/v1" });

api.interceptors.request.use((config) => {
  const acceso = tokens.acceso();
  if (acceso) config.headers.Authorization = `Bearer ${acceso}`;
  return config;
});

// Si el token de acceso venció, se renueva una sola vez (aunque fallen varias peticiones a la vez) y se reintenta.
let renovando: Promise<string> | null = null;

async function renovarAcceso(): Promise<string> {
  const renovacion = tokens.renovacion();
  if (!renovacion) throw new Error("Sin token de renovación");
  const { data } = await axios.post("/api/v1/auth/token/refrescar/", { refresh: renovacion });
  tokens.guardar(data.access, data.refresh);
  return data.access;
}

api.interceptors.response.use(
  (respuesta) => respuesta,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _reintento?: boolean }) | undefined;
    const esAuth = original?.url?.startsWith("/auth/token");
    if (error.response?.status !== 401 || !original || original._reintento || esAuth || !tokens.renovacion()) {
      throw error;
    }
    original._reintento = true;
    try {
      renovando ??= renovarAcceso().finally(() => (renovando = null));
      const acceso = await renovando;
      original.headers.Authorization = `Bearer ${acceso}`;
      return api(original);
    } catch {
      tokens.borrar();
      window.location.assign("/iniciar-sesion");
      throw error;
    }
  },
);

/** Convierte los errores de DRF en un mensaje general y errores por campo. */
export function leerErrores(error: unknown): { general: string; campos: Record<string, string> } {
  const campos: Record<string, string> = {};
  if (!axios.isAxiosError(error) || !error.response) {
    return { general: "No fue posible conectarse con el servidor. Intenta de nuevo.", campos };
  }
  const datos = error.response.data as Record<string, unknown> | undefined;
  let general = "";
  if (datos && typeof datos === "object") {
    for (const [campo, valor] of Object.entries(datos)) {
      const texto = Array.isArray(valor) ? valor.join(" ") : String(valor);
      if (campo === "detail" || campo === "non_field_errors") general = texto;
      else campos[campo] = texto;
    }
  }
  if (!general && Object.keys(campos).length === 0) general = "Ocurrió un error inesperado.";
  if (!general) general = "Revisa los campos marcados.";
  return { general, campos };
}
