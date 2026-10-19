export type Rol = "ESTUDIANTE" | "EMPRESA" | "OFICINA" | "SUPERADMIN";

export interface Habilitacion {
  accion: "HABILITADO" | "DESHABILITADO";
  periodo: string;
  fecha: string;
  observacion: string;
}

export interface DatosEstudiante {
  id: number;
  programa: number;
  programa_nombre: string;
  estado: "NO_HABILITADO" | "HABILITADO" | "UBICADO" | "EN_PRACTICA" | "PRACTICA_FINALIZADA";
  estado_nombre: string;
  habilitacion: Habilitacion | null;
}

export interface DatosEmpresa {
  id: number;
  razon_social: string;
  estado: "PENDIENTE" | "ALIADA" | "RECHAZADA" | "CONVENIO_VENCIDO" | "SUSPENDIDA";
  estado_nombre: string;
  puede_publicar: boolean;
}

export interface Usuario {
  id: number;
  email: string;
  nombres: string;
  apellidos: string;
  telefono: string;
  foto: string | null;
  rol: Rol;
  rol_nombre: string;
  estudiante: DatosEstudiante | null;
  empresa: DatosEmpresa | null;
}

export interface Programa {
  id: number;
  nombre: string;
  nivel: string;
  nivel_nombre: string;
  facultad: string;
}

export interface ItemCatalogo {
  id: number;
  nombre: string;
  departamento?: string;
}

export interface Notificacion {
  id: number;
  tipo: string;
  titulo: string;
  mensaje: string;
  url_destino: string;
  leida: boolean;
  creado_en: string;
}

export interface Paginado<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export type EstadoEmpresa = DatosEmpresa["estado"];
export type EstadoEstudiante = DatosEstudiante["estado"];
export type EstadoConvocatoria = "BORRADOR" | "EN_REVISION" | "DEVUELTA" | "PUBLICADA" | "CERRADA" | "CANCELADA";
export type Resumen = Record<string, number>;

export interface Convenio {
  id: number;
  numero: string;
  fecha_inicio: string;
  fecha_fin: string;
  vigente: boolean;
  tiene_documento: boolean;
  registrado_por_nombre: string;
  creado_en: string;
}

export interface EmpresaOficina {
  id: number;
  razon_social: string;
  nit: string;
  sector_nombre: string;
  ciudad_nombre: string;
  estado: EstadoEmpresa;
  estado_nombre: string;
  motivo_estado: string;
  convenio_vigente: { numero: string; fecha_fin: string } | null;
  puede_publicar: boolean;
  creada_por_oficina: boolean;
  contacto_nombre: string;
  contacto_email: string;
  contacto_telefono: string;
  creado_en: string;
}

export interface EmpresaDetalle extends EmpresaOficina {
  descripcion: string;
  sitio_web: string;
  direccion: string;
  tamano: string | null;
  tamano_nombre: string | null;
  convenios: Convenio[];
  usuarios: { nombre: string; email: string; cargo: string; activo: boolean }[];
}

export interface HabilitacionHistorial {
  id: number;
  accion: "HABILITADO" | "DESHABILITADO";
  accion_nombre: string;
  periodo: string;
  funcionario: string;
  observacion: string;
  creado_en: string;
}

export interface EstudianteOficina {
  id: number;
  nombre: string;
  email: string;
  telefono: string;
  correo_verificado: boolean;
  programa: number;
  programa_nombre: string;
  semestre: number | null;
  estado: EstadoEstudiante;
  estado_nombre: string;
  ultima_habilitacion: HabilitacionHistorial | null;
  historial?: HabilitacionHistorial[];
}

export type AccionConvocatoria = "editar" | "enviar_revision" | "aprobar" | "devolver" | "cerrar" | "eliminar" | "duplicar";

export interface Convocatoria {
  id: number;
  empresa: number;
  empresa_nombre: string;
  titulo: string;
  descripcion: string;
  funciones: string;
  nivel_formacion: string;
  nivel_formacion_nombre: string;
  modalidad: string;
  modalidad_nombre: string;
  ciudad: number | null;
  ciudad_nombre: string | null;
  tipo_vinculacion: string;
  tipo_vinculacion_nombre: string;
  apoyo_economico: string | null;
  cupos: number;
  fecha_inicio: string;
  duracion_meses: number;
  fecha_cierre: string;
  estado: EstadoConvocatoria;
  estado_nombre: string;
  observacion_revision: string;
  motivo_cierre: string | null;
  motivo_cierre_nombre: string | null;
  publicada_en: string | null;
  programas: number[];
  programas_detalle: { id: number; nombre: string }[];
  habilidades: number[];
  habilidades_detalle: { id: number; nombre: string }[];
  creada_por_nombre: string;
  creada_por_oficina: boolean;
  acciones: AccionConvocatoria[];
  postulantes: number | null;
  para_estudiante: ParaEstudiante | null;
  creado_en: string;
  actualizado_en: string;
}

export interface Afinidad {
  total: number;
  es_afin: boolean;
  habilidades_coinciden: string[];
  habilidades_faltan: string[];
  modalidad: boolean;
  disponibilidad: boolean;
}

export interface ParaEstudiante {
  afinidad: Afinidad;
  guardada: boolean;
  postulacion: { id: number; estado: EstadoPostulacion; estado_nombre: string } | null;
  puede_postularse: boolean;
  motivo_no_postular: string | null;
}

export type EstadoPostulacion =
  | "POSTULADO" | "EN_REVISION" | "PRESELECCIONADO" | "ENTREVISTA" | "SELECCIONADO" | "NO_SELECCIONADO" | "RETIRADO"
  | "LEGALIZADO" | "CERRADO_SISTEMA";

export interface Entrevista {
  id: number;
  fecha_hora: string;
  modalidad: string;
  modalidad_nombre: string;
  lugar_o_enlace: string;
  notas: string;
  estado: string;
  estado_nombre: string;
}

export interface PostulacionResumen {
  id: number;
  estado: EstadoPostulacion;
  estado_nombre: string;
  afinidad: number;
  motivo_no_seleccion: string;
  convocatoria: { id: number; titulo: string; empresa: string; estado: EstadoConvocatoria; estado_nombre: string };
  estudiante: { id: number; nombre: string; programa: string; semestre: number | null };
  proxima_entrevista: Entrevista | null;
  creado_en: string;
  actualizado_en: string;
}

export interface EntradaSeguimiento {
  id: number;
  tipo: "MENSAJE" | "CONTACTO_EXTERNO" | "NOTA_INTERNA";
  tipo_nombre: string;
  canal: string | null;
  canal_nombre: string | null;
  fecha_contacto: string | null;
  texto: string;
  autor: string;
  autor_rol: string;
  creado_en: string;
}

export interface PostulacionDetalle extends PostulacionResumen {
  mensaje_presentacion: string;
  historial: { id: number; estado_nuevo: EstadoPostulacion; estado_nuevo_nombre: string; usuario: string; comentario: string; creado_en: string }[];
  entrevistas: Entrevista[];
  seguimiento: EntradaSeguimiento[];
  contacto_empresa: { nombre: string; email: string; telefono: string } | null;
  perfil_estudiante: PerfilProfesional | null;
  afinidad_detalle: Afinidad;
  acciones: {
    estados: EstadoPostulacion[];
    programar_entrevista: boolean;
    retirar: boolean;
    seguimiento: EntradaSeguimiento["tipo"][];
    verificar: boolean;
    legalizar: boolean;
  };
  verificaciones: Verificacion[];
  practica: Practica | null;
}

export interface Verificacion {
  id: number;
  resultado: "CUMPLE" | "NO_CUMPLE";
  resultado_nombre: string;
  observacion: string;
  funcionario: string;
  creado_en: string;
}

export type EstadoPractica = "LEGALIZADA" | "EN_CURSO" | "FINALIZADA" | "CANCELADA";

export interface Practica {
  id: number;
  postulacion: number;
  estado: EstadoPractica;
  estado_nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  tipo_vinculacion: string;
  tipo_vinculacion_nombre: string;
  asesor_nombre: string;
  tutor_empresa_nombre: string;
  tutor_empresa_email: string;
  observacion_cierre: string;
  estudiante: { id: number; nombre: string; programa: string; email: string };
  convocatoria: { id: number; titulo: string; empresa: string };
  legalizada_por: string;
  legalizada_en: string;
  finalizada_en: string | null;
  tiene_documento: boolean;
}

export interface ItemAlerta { id: number; titulo: string; detalle: string; desde: string | null; url: string }

export interface CategoriaAlerta {
  clave: string;
  titulo: string;
  descripcion: string;
  gravedad: "alta" | "media" | "baja";
  total: number;
  items: ItemAlerta[];
}

export interface Alertas { total: number; categorias: CategoriaAlerta[] }

export interface NotaAsesoria { id: number; texto: string; autor: string; creado_en: string }

export interface HabilidadPerfil { id: number; nombre: string; nivel: string; nivel_nombre: string }
export interface Idioma { id: number; idioma: string; nivel: string }
export interface Experiencia { id: number; cargo: string; organizacion: string; fecha_inicio: string; fecha_fin: string | null; descripcion: string }
export interface Proyecto { id: number; titulo: string; descripcion: string; url: string }
export interface Certificacion { id: number; nombre: string; entidad: string; fecha: string | null; url: string }
export interface Enlace { id: number; tipo: string; tipo_nombre: string; url: string }

export interface PerfilProfesional {
  id: number;
  nombre: string;
  email: string;
  telefono: string;
  programa: number;
  programa_nombre: string;
  nivel_programa: string;
  semestre: number | null;
  ciudad: number | null;
  ciudad_nombre: string | null;
  titular: string;
  acerca_de: string;
  fecha_disponible: string | null;
  jornada: string | null;
  jornada_nombre: string | null;
  modalidad_preferida: string | null;
  modalidad_preferida_nombre: string | null;
  estado: EstadoEstudiante;
  estado_nombre: string;
  habilidades: HabilidadPerfil[];
  idiomas: Idioma[];
  experiencias: Experiencia[];
  proyectos: Proyecto[];
  certificaciones: Certificacion[];
  enlaces: Enlace[];
  tiene_hoja_vida: boolean;
}

export interface PerfilPropio extends PerfilProfesional {
  nombres: string;
  apellidos: string;
  documento: string | null;
  abierto_oportunidades: boolean;
  completitud: { porcentaje: number; faltantes: { clave: string; texto: string }[] };
  faltantes_para_postular: string[];
}

export type TipoPublicacion = "CONVOCATORIA" | "OFERTA_EXTERNA" | "EVENTO" | "NOTICIA" | "COMUNICADO";

export interface Publicacion {
  id: number;
  tipo: TipoPublicacion;
  tipo_nombre: string;
  titulo: string;
  texto: string;
  imagen: string | null;
  enlace_url: string;
  fuente_externa: string;
  fecha_evento: string | null;
  lugar_evento: string;
  para_todos_programas: boolean;
  programas_detalle: { id: number; nombre: string }[];
  autor: { nombre: string; rol: string };
  empresa: { id: number; razon_social: string; logo: string | null } | null;
  convocatoria: { id: number; estado: EstadoConvocatoria; estado_nombre: string; fecha_cierre: string; modalidad_nombre: string } | null;
  estado: "PUBLICADA" | "OCULTA" | "ELIMINADA";
  estado_nombre: string;
  motivo_ocultamiento: string;
  reacciones_total: number;
  comentarios_total: number;
  me_interesa: boolean;
  guardada: boolean;
  puede_editar: boolean;
  puede_moderar: boolean;
  creado_en: string;
}

export interface Comentario { id: number; texto: string; autor: string; autor_rol: string; oculto: boolean; creado_en: string }

export interface EmpresaPublica {
  id: number;
  razon_social: string;
  sector: number;
  sector_nombre: string;
  ciudad: number;
  ciudad_nombre: string;
  tamano_nombre: string | null;
  descripcion: string;
  logo: string | null;
  sitio_web: string;
  convocatorias_activas: number;
  seguida: boolean | null;
}

export interface EmpresaPagina extends EmpresaPublica {
  convocatorias: { id: number; titulo: string; modalidad_nombre: string; ciudad_nombre: string | null; fecha_cierre: string; apoyo_economico: string | null; programas: string[] }[];
  publicaciones: { id: number; tipo_nombre: string; titulo: string; texto: string; creado_en: string }[];
}

export interface MiEmpresa {
  id: number;
  razon_social: string;
  nit: string;
  estado: string;
  estado_nombre: string;
  sector: number;
  ciudad: number;
  tamano: string | null;
  descripcion: string;
  sitio_web: string;
  direccion: string;
  contacto_nombre: string;
  contacto_email: string;
  contacto_telefono: string;
  logo: string | null;
}

/** RF-45: perfil que ve la empresa en la búsqueda de talento (sin correo ni teléfono). */
export type PerfilTalento = Omit<PerfilProfesional, "email" | "telefono"> & { coincidencias: number | null };

export interface Indicadores {
  filtros: { periodo: string | null; programa: string | null };
  estudiantes: {
    registrados: number;
    habilitados: number;
    en_busqueda: number;
    ubicados: number;
    porcentaje_ubicacion: number;
    dias_promedio_hasta_ubicacion: number | null;
  };
  oferta: {
    convocatorias_activas: number;
    cupos_ofertados: number;
    postulaciones: number;
    postulaciones_por_cupo: number | null;
    empresas_aliadas: number;
    empresas_pendientes: number;
  };
  embudo: { estado: string; nombre: string; total: number }[];
  por_programa: { programa: string; registrados: number; habilitados: number; ubicados: number; postulaciones: number; porcentaje_ubicacion: number }[];
  tendencia: { mes: string; postulaciones: number; legalizaciones: number }[];
}

export interface ResumenConvocatoriaEmpresa {
  id: number;
  titulo: string;
  estado: EstadoConvocatoria;
  estado_nombre: string;
  cupos: number;
  total: number;
  por_revisar: number;
  en_proceso: number;
  seleccionados: number;
}
