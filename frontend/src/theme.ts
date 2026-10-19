import { esES } from "@mui/material/locale";
import { createTheme } from "@mui/material/styles";

// Paleta institucional (RNF-12). Ajustar con los valores exactos del manual de marca del Pascual Bravo.
export const colores = {
  primario: "#0b3b7a",
  secundario: "#f2a900",
  fondo: "#f3f5f9",
};

// Colores de los gráficos (validados con el validador de paletas: contraste, daltonismo y visión normal sobre blanco)
export const grafico = {
  serie1: "#2a78d6",
  serie2: "#eb6834",
  tintaSecundaria: "#52514e",
  tintaTenue: "#898781",
  rejilla: "#e1e0d9",
  base: "#c3c2b7",
};

// esES traduce los textos internos de MUI (paginación, botones de las tablas, etc.)
export const tema = createTheme({
  palette: {
    primary: { main: colores.primario },
    secondary: { main: colores.secundario },
    background: { default: colores.fondo },
  },
  shape: { borderRadius: 8 },
  typography: {
    fontFamily: '"Roboto", "Segoe UI", Arial, sans-serif',
    h4: { fontWeight: 700 },
    h5: { fontWeight: 700 },
    h6: { fontWeight: 600 },
  },
  components: {
    MuiButton: { defaultProps: { disableElevation: true }, styleOverrides: { root: { textTransform: "none" } } },
    MuiCard: { defaultProps: { variant: "outlined" } },
    MuiTab: { styleOverrides: { root: { textTransform: "none", fontWeight: 600 } } },
    MuiToggleButton: { styleOverrides: { root: { textTransform: "none", fontWeight: 600 } } },
  },
}, esES);
