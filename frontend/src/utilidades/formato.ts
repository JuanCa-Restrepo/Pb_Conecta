import dayjs from "dayjs";

// Formatos de Colombia (RNF-17)
export const fecha = (valor?: string | null) => (valor ? dayjs(valor).format("DD/MM/YYYY") : "—");
export const fechaHora = (valor?: string | null) => (valor ? dayjs(valor).format("DD/MM/YYYY HH:mm") : "—");
export const hoyISO = () => dayjs().format("YYYY-MM-DD");
export const enDiasISO = (dias: number) => dayjs().add(dias, "day").format("YYYY-MM-DD");

const formatoPesos = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
export const pesos = (valor?: string | number | null) => (valor === null || valor === undefined || valor === "" ? "Sin apoyo económico" : formatoPesos.format(Number(valor)));
