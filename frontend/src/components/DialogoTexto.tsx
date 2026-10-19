import { Alert, Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, TextField, type ButtonProps } from "@mui/material";
import { useEffect, useState } from "react";

import { leerErrores } from "../api/cliente";

interface Props {
  abierto: boolean;
  titulo: string;
  descripcion?: string;
  /** Sin etiqueta el diálogo es solo de confirmación. */
  etiqueta?: string;
  obligatorio?: boolean;
  textoConfirmar: string;
  colorConfirmar?: ButtonProps["color"];
  onCerrar: () => void;
  onConfirmar: (texto: string) => Promise<unknown>;
}

/** Confirmación con un campo de texto opcional u obligatorio (motivos y observaciones, RN-11). */
export function DialogoTexto(props: Props) {
  const [texto, setTexto] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (props.abierto) {
      setTexto("");
      setError("");
    }
  }, [props.abierto]);

  async function confirmar() {
    if (props.etiqueta && props.obligatorio && !texto.trim()) {
      setError("Este campo es obligatorio.");
      return;
    }
    setEnviando(true);
    try {
      await props.onConfirmar(texto.trim());
      props.onCerrar();
    } catch (e) {
      setError(leerErrores(e).general);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Dialog open={props.abierto} onClose={props.onCerrar} fullWidth maxWidth="sm">
      <DialogTitle>{props.titulo}</DialogTitle>
      <DialogContent>
        {props.descripcion && <DialogContentText sx={{ mb: 2 }}>{props.descripcion}</DialogContentText>}
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {props.etiqueta && (
          <TextField
            label={props.etiqueta}
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            required={props.obligatorio}
            multiline
            minRows={3}
            fullWidth
            autoFocus
          />
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={props.onCerrar} disabled={enviando}>Cancelar</Button>
        <Button variant="contained" color={props.colorConfirmar ?? "primary"} onClick={confirmar} disabled={enviando}>
          {props.textoConfirmar}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
