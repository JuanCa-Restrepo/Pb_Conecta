import { Box, Stack, Tooltip, Typography } from "@mui/material";

import { grafico } from "../../theme";

export interface Serie {
  clave: string;
  nombre: string;
  color: string;
}

const ALTO = 160;

/**
 * Barras verticales agrupadas por categoría (p. ej., meses) para dos o tres series con la misma escala.
 * Una sola escala; leyenda siempre visible; tooltip por barra; 2 px de separación entre barras vecinas.
 */
export function BarrasAgrupadas({ categorias, series, datos }: {
  categorias: { clave: string; etiqueta: string }[];
  series: Serie[];
  datos: Record<string, Record<string, number>>;
}) {
  const maximo = Math.max(1, ...categorias.flatMap((c) => series.map((s) => datos[c.clave]?.[s.clave] ?? 0)));
  const marcas = [0, Math.ceil(maximo / 2), maximo];

  return (
    <Box>
      <Stack direction="row" spacing={2} sx={{ mb: 1.5 }} role="list" aria-label="Leyenda">
        {series.map((s) => (
          <Stack key={s.clave} direction="row" spacing={0.75} sx={{ alignItems: "center" }} role="listitem">
            <Box sx={{ width: 12, height: 12, borderRadius: "3px", bgcolor: s.color }} />
            <Typography variant="body2" sx={{ color: grafico.tintaSecundaria }}>{s.nombre}</Typography>
          </Stack>
        ))}
      </Stack>

      <Box sx={{ display: "grid", gridTemplateColumns: "32px 1fr", columnGap: 1 }}>
        {/* Eje Y discreto: tres marcas */}
        <Box sx={{ position: "relative", height: ALTO }}>
          {marcas.map((m) => (
            <Typography key={m} variant="caption" sx={{ position: "absolute", right: 0, bottom: `${(100 * m) / maximo}%`, transform: "translateY(50%)", color: grafico.tintaTenue, fontVariantNumeric: "tabular-nums" }}>
              {m}
            </Typography>
          ))}
        </Box>
        <Box sx={{ position: "relative", height: ALTO, borderBottom: `1px solid ${grafico.base}` }}>
          {marcas.slice(1).map((m) => (
            <Box key={m} sx={{ position: "absolute", left: 0, right: 0, bottom: `${(100 * m) / maximo}%`, borderTop: `1px solid ${grafico.rejilla}` }} />
          ))}
          <Stack direction="row" sx={{ position: "absolute", inset: 0, alignItems: "flex-end", justifyContent: "space-around" }}>
            {categorias.map((c) => (
              <Stack key={c.clave} direction="row" sx={{ height: "100%", alignItems: "flex-end", gap: "2px" }}>
                {series.map((s) => {
                  const valor = datos[c.clave]?.[s.clave] ?? 0;
                  return (
                    <Tooltip key={s.clave} placement="top" title={`${c.etiqueta} · ${s.nombre}: ${valor}`}>
                      {/* Columna completa como área de hover; la barra es la parte coloreada */}
                      <Box sx={{ height: "100%", width: 22, display: "flex", alignItems: "flex-end", cursor: "default" }}>
                        <Box sx={{ width: "100%", height: `${(100 * valor) / maximo}%`, minHeight: valor ? 4 : 0, bgcolor: s.color, borderRadius: "4px 4px 0 0" }} />
                      </Box>
                    </Tooltip>
                  );
                })}
              </Stack>
            ))}
          </Stack>
        </Box>
        <Box />
        <Stack direction="row" sx={{ justifyContent: "space-around", mt: 0.5 }}>
          {categorias.map((c) => (
            <Typography key={c.clave} variant="caption" sx={{ color: grafico.tintaTenue }}>{c.etiqueta}</Typography>
          ))}
        </Stack>
      </Box>
    </Box>
  );
}
