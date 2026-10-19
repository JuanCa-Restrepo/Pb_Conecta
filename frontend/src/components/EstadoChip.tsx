import { Chip, type ChipProps } from "@mui/material";

// Un solo mapa de colores para los estados de empresas, estudiantes y convocatorias
const COLORES: Record<string, ChipProps["color"]> = {
  PENDIENTE: "info",
  ALIADA: "success",
  RECHAZADA: "error",
  CONVENIO_VENCIDO: "warning",
  SUSPENDIDA: "error",
  NO_HABILITADO: "warning",
  HABILITADO: "success",
  UBICADO: "primary",
  EN_PRACTICA: "primary",
  PRACTICA_FINALIZADA: "default",
  BORRADOR: "default",
  EN_REVISION: "info",
  DEVUELTA: "warning",
  PUBLICADA: "success",
  CERRADA: "default",
  CANCELADA: "error",
  POSTULADO: "info",
  PRESELECCIONADO: "primary",
  ENTREVISTA: "secondary",
  SELECCIONADO: "success",
  NO_SELECCIONADO: "error",
  RETIRADO: "default",
  LEGALIZADO: "success",
  CERRADO_SISTEMA: "default",
  LEGALIZADA: "primary",
  EN_CURSO: "success",
  FINALIZADA: "default",
  CUMPLE: "success",
  NO_CUMPLE: "error",
};

export function EstadoChip({ estado, etiqueta, size = "small" }: { estado: string; etiqueta: string; size?: ChipProps["size"] }) {
  return <Chip size={size} label={etiqueta} color={COLORES[estado] ?? "default"} />;
}
