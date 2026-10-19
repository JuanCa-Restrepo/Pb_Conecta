import { Card, CardContent, CardHeader, Chip, Divider, Link, Stack, Typography } from "@mui/material";

import type { PerfilProfesional, PerfilTalento } from "../../api/tipos";
import { fecha } from "../../utilidades/formato";

/** RF-16: lo que ve la empresa del estudiante (sin documento). En la búsqueda de talento tampoco trae contacto (RF-45). */
export function PerfilProfesionalCard({ perfil }: { perfil: PerfilProfesional | PerfilTalento }) {
  const disponibilidad = [
    perfil.fecha_disponible && `desde el ${fecha(perfil.fecha_disponible)}`,
    perfil.jornada_nombre?.toLowerCase(),
    perfil.modalidad_preferida_nombre && `prefiere ${perfil.modalidad_preferida_nombre.toLowerCase()}`,
  ].filter(Boolean).join(" · ");

  return (
    <Card>
      <CardHeader
        title={perfil.nombre}
        subheader={`${perfil.programa_nombre}${perfil.semestre ? ` · semestre ${perfil.semestre}` : ""}${perfil.ciudad_nombre ? ` · ${perfil.ciudad_nombre}` : ""}`}
        slotProps={{ title: { variant: "h6" } }}
      />
      <CardContent sx={{ pt: 0 }}>
        <Stack spacing={2}>
          {"email" in perfil && (
            <Typography variant="body2">
              <Link href={`mailto:${perfil.email}`}>{perfil.email}</Link>{perfil.telefono && ` · ${perfil.telefono}`}
            </Typography>
          )}
          {perfil.titular && <Typography variant="subtitle2">{perfil.titular}</Typography>}
          {perfil.acerca_de && <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>{perfil.acerca_de}</Typography>}
          {disponibilidad && <Typography variant="body2" color="text.secondary">Disponibilidad: {disponibilidad}</Typography>}

          {perfil.habilidades.length > 0 && (
            <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
              {perfil.habilidades.map((h) => <Chip key={h.id} size="small" label={`${h.nombre} · ${h.nivel_nombre}`} />)}
            </Stack>
          )}

          {perfil.experiencias.length > 0 && (
            <>
              <Divider />
              <Typography variant="subtitle2">Experiencia</Typography>
              {perfil.experiencias.map((e) => (
                <div key={e.id}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>{e.cargo} · {e.organizacion}</Typography>
                  <Typography variant="caption" color="text.secondary">{fecha(e.fecha_inicio)} – {e.fecha_fin ? fecha(e.fecha_fin) : "actual"}</Typography>
                  {e.descripcion && <Typography variant="body2">{e.descripcion}</Typography>}
                </div>
              ))}
            </>
          )}
          {perfil.proyectos.length > 0 && (
            <>
              <Divider />
              <Typography variant="subtitle2">Proyectos</Typography>
              {perfil.proyectos.map((p) => (
                <Typography key={p.id} variant="body2">
                  <strong>{p.titulo}</strong>{p.descripcion && ` · ${p.descripcion}`}{" "}
                  {p.url && <Link href={p.url} target="_blank" rel="noreferrer">ver</Link>}
                </Typography>
              ))}
            </>
          )}
          {(perfil.idiomas.length > 0 || perfil.certificaciones.length > 0 || perfil.enlaces.length > 0) && <Divider />}
          {perfil.idiomas.length > 0 && <Typography variant="body2">Idiomas: {perfil.idiomas.map((i) => `${i.idioma} (${i.nivel})`).join(", ")}</Typography>}
          {perfil.certificaciones.length > 0 && <Typography variant="body2">Certificaciones: {perfil.certificaciones.map((c) => `${c.nombre} – ${c.entidad}`).join("; ")}</Typography>}
          {perfil.enlaces.length > 0 && (
            <Stack direction="row" spacing={2} useFlexGap sx={{ flexWrap: "wrap" }}>
              {perfil.enlaces.map((e) => <Link key={e.id} href={e.url} target="_blank" rel="noreferrer" variant="body2">{e.tipo_nombre}</Link>)}
            </Stack>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
