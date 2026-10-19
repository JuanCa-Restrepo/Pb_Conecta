// Listas de valores de la API (mismos códigos que los TextChoices de Django)
export const MODALIDADES = [
  { valor: "PRESENCIAL", etiqueta: "Presencial" },
  { valor: "REMOTA", etiqueta: "Remota" },
  { valor: "HIBRIDA", etiqueta: "Híbrida" },
];

export const TIPOS_VINCULACION = [
  { valor: "PRACTICA", etiqueta: "Práctica" },
  { valor: "PASANTIA", etiqueta: "Pasantía" },
  { valor: "CONTRATO_APRENDIZAJE", etiqueta: "Contrato de aprendizaje" },
  { valor: "VINCULO_LABORAL", etiqueta: "Vínculo laboral" },
];

export const NIVELES_FORMACION = [
  { valor: "CUALQUIERA", etiqueta: "Cualquier nivel" },
  { valor: "TECNICO", etiqueta: "Técnico profesional" },
  { valor: "TECNOLOGICO", etiqueta: "Tecnológico" },
  { valor: "PROFESIONAL", etiqueta: "Profesional" },
];

export const JORNADAS = [
  { valor: "COMPLETA", etiqueta: "Tiempo completo" },
  { valor: "MEDIA", etiqueta: "Medio tiempo" },
  { valor: "FLEXIBLE", etiqueta: "Flexible" },
];

export const NIVELES_HABILIDAD = [
  { valor: "BASICO", etiqueta: "Básico" },
  { valor: "INTERMEDIO", etiqueta: "Intermedio" },
  { valor: "AVANZADO", etiqueta: "Avanzado" },
];

export const NIVELES_IDIOMA = ["A1", "A2", "B1", "B2", "C1", "C2", "NATIVO"].map((n) => ({ valor: n, etiqueta: n === "NATIVO" ? "Nativo" : n }));

export const TIPOS_ENLACE = [
  { valor: "LINKEDIN", etiqueta: "LinkedIn" },
  { valor: "GITHUB", etiqueta: "GitHub" },
  { valor: "PORTAFOLIO", etiqueta: "Portafolio" },
  { valor: "OTRO", etiqueta: "Otro" },
];

export const MODALIDADES_ENTREVISTA = [
  { valor: "VIRTUAL", etiqueta: "Virtual" },
  { valor: "PRESENCIAL", etiqueta: "Presencial" },
  { valor: "TELEFONICA", etiqueta: "Telefónica" },
];

export const CANALES_CONTACTO = [
  { valor: "LLAMADA", etiqueta: "Llamada" },
  { valor: "CORREO", etiqueta: "Correo" },
  { valor: "WHATSAPP", etiqueta: "WhatsApp" },
  { valor: "PRESENCIAL", etiqueta: "Presencial" },
  { valor: "OTRO", etiqueta: "Otro" },
];

// Etiqueta del botón que lleva una postulación a cada estado (empresa y oficina)
export const ACCION_ESTADO: Record<string, string> = {
  EN_REVISION: "Marcar en revisión",
  PRESELECCIONADO: "Preseleccionar",
  SELECCIONADO: "Seleccionar",
  NO_SELECCIONADO: "No seleccionar",
};

export const TIPOS_PUBLICACION: { valor: string; etiqueta: string }[] = [
  { valor: "CONVOCATORIA", etiqueta: "Convocatorias" },
  { valor: "OFERTA_EXTERNA", etiqueta: "Ofertas externas" },
  { valor: "EVENTO", etiqueta: "Eventos" },
  { valor: "NOTICIA", etiqueta: "Noticias" },
  { valor: "COMUNICADO", etiqueta: "Comunicados" },
];

export const NOMBRE_TIPO_PUBLICACION: Record<string, string> = {
  OFERTA_EXTERNA: "Oferta externa / bolsa de empleo",
  EVENTO: "Evento",
  NOTICIA: "Noticia",
  COMUNICADO: "Comunicado de la oficina",
};

export const TAMANOS_EMPRESA = [
  { valor: "MICRO", etiqueta: "Microempresa" },
  { valor: "PEQUENA", etiqueta: "Pequeña" },
  { valor: "MEDIANA", etiqueta: "Mediana" },
  { valor: "GRANDE", etiqueta: "Grande" },
];
