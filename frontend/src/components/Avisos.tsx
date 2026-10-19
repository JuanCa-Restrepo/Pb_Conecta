import { Alert, Snackbar, type AlertColor } from "@mui/material";
import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

type Mostrar = (mensaje: string, tipo?: AlertColor) => void;

const Contexto = createContext<Mostrar>(() => {});

/** Mensajes breves de confirmación o error después de una acción (barra inferior). */
export function AvisosProvider({ children }: { children: ReactNode }) {
  const [aviso, setAviso] = useState<{ mensaje: string; tipo: AlertColor; clave: number } | null>(null);
  const mostrar = useCallback<Mostrar>((mensaje, tipo = "success") => setAviso({ mensaje, tipo, clave: Date.now() }), []);

  return (
    <Contexto.Provider value={mostrar}>
      {children}
      <Snackbar
        key={aviso?.clave}
        open={Boolean(aviso)}
        autoHideDuration={5000}
        onClose={() => setAviso(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        {aviso ? <Alert severity={aviso.tipo} variant="filled" onClose={() => setAviso(null)}>{aviso.mensaje}</Alert> : undefined}
      </Snackbar>
    </Contexto.Provider>
  );
}

export const useAviso = () => useContext(Contexto);
