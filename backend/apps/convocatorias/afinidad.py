"""Índice de afinidad estudiante–convocatoria, de 0 a 100 (RF-42, RF-53 · docs/02-arquitectura.md, sección 3.7).

| Componente     | Puntos | Regla                                                                  |
|----------------|--------|------------------------------------------------------------------------|
| Programa afín  | 50     | Si el programa del estudiante no es afín, la afinidad total es 0       |
| Habilidades    | 0–35   | 35 × (requeridas que tiene ÷ requeridas); 35 si no pide habilidades    |
| Modalidad      | 0–10   | Coincide con la preferida, o el estudiante prefiere híbrida            |
| Disponibilidad | 0–5    | Disponible en o antes de la fecha de inicio de la práctica             |
"""

PUNTOS_PROGRAMA, PUNTOS_HABILIDADES, PUNTOS_MODALIDAD, PUNTOS_DISPONIBILIDAD = 50, 35, 10, 5


def calcular(perfil, convocatoria, habilidades_estudiante=None):
    """`habilidades_estudiante` (ids) evita una consulta por convocatoria cuando se calcula para un listado."""
    if habilidades_estudiante is None:
        habilidades_estudiante = set(perfil.habilidades.values_list("id", flat=True))

    es_afin = perfil.programa_id in {p.id for p in convocatoria.programas.all()}
    requeridas = {h.id: h.nombre for h in convocatoria.habilidades.all()}
    coinciden = [nombre for id_, nombre in requeridas.items() if id_ in habilidades_estudiante]
    faltan = [nombre for id_, nombre in requeridas.items() if id_ not in habilidades_estudiante]

    puntos_habilidades = round(PUNTOS_HABILIDADES * len(coinciden) / len(requeridas)) if requeridas else PUNTOS_HABILIDADES
    modalidad_ok = perfil.modalidad_preferida in (convocatoria.modalidad, "HIBRIDA")
    disponibilidad_ok = bool(perfil.fecha_disponible and perfil.fecha_disponible <= convocatoria.fecha_inicio)

    total = 0
    if es_afin:
        total = (
            PUNTOS_PROGRAMA + puntos_habilidades
            + (PUNTOS_MODALIDAD if modalidad_ok else 0)
            + (PUNTOS_DISPONIBILIDAD if disponibilidad_ok else 0)
        )
    return {
        "total": total,
        "es_afin": es_afin,
        "habilidades_coinciden": coinciden,
        "habilidades_faltan": faltan,
        "modalidad": modalidad_ok,
        "disponibilidad": disponibilidad_ok,
    }
