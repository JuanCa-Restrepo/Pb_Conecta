import { Box, Stack, Tooltip, Typography } from "@mui/material";

import { grafico } from "../../theme";

export interface Barra {
  etiqueta: string;
  valor: number;
}

/**
 * Una sola serie en barras horizontales (p. ej., el embudo de postulaciones). Sin leyenda: el título nombra la serie.
 * El valor va escrito al final de cada barra, así la cifra nunca depende solo de la longitud (vale como tabla).
 */
export function BarrasHorizontales({ datos, color = grafico.serie1, sufijo = "" }: { datos: Barra[]; color?: string; sufijo?: string }) {
  const maximo = Math.max(1, ...datos.map((d) => d.valor));
  const total = datos.reduce((suma, d) => suma + d.valor, 0);

  return (
    <Stack spacing={0.25} role="list">
      {datos.map((d) => (
        <Tooltip
          key={d.etiqueta}
          placement="top"
          title={`${d.etiqueta}: ${d.valor}${sufijo}${total ? ` · ${Math.round((100 * d.valor) / total)} % del total` : ""}`}
        >
          {/* La fila completa es el área de hover: más grande que la barra */}
          <Box role="listitem" sx={{ display: "grid", gridTemplateColumns: "minmax(110px, 38%) 1fr", gap: 1.5, alignItems: "center", py: 0.5, borderRadius: 1, "&:hover": { bgcolor: "action.hover" } }}>
            <Typography variant="body2" sx={{ color: grafico.tintaSecundaria, textAlign: "right" }} noWrap>{d.etiqueta}</Typography>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center", minWidth: 0 }}>
              <Box
                sx={{
                  height: 14,
                  width: `${(100 * d.valor) / maximo}%`,
                  minWidth: d.valor ? 4 : 0,
                  bgcolor: color,
                  borderRadius: "0 4px 4px 0", // Extremo redondeado; el inicio queda anclado a la base
                  transition: "width 200ms",
                }}
              />
              <Typography variant="body2" sx={{ fontVariantNumeric: "tabular-nums", color: d.valor ? "text.primary" : grafico.tintaTenue }}>
                {d.valor}{sufijo}
              </Typography>
            </Stack>
          </Box>
        </Tooltip>
      ))}
    </Stack>
  );
}
