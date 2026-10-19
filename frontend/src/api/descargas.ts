import { api } from "./cliente";

/** Abre un archivo protegido (convenios, hojas de vida): se pide con el token JWT y se muestra en una pestaña nueva. */
export async function abrirArchivoProtegido(ruta: string) {
  const ventana = window.open("", "_blank"); // Se abre antes de la petición para que el navegador no la bloquee
  try {
    const { data } = await api.get<Blob>(ruta, { responseType: "blob" });
    const url = URL.createObjectURL(data);
    if (ventana) ventana.location.href = url;
    else window.location.assign(url);
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  } catch (error) {
    ventana?.close();
    throw error;
  }
}

/** Descarga un archivo de la API (p. ej., un CSV) con el nombre que envía el servidor. */
export async function descargarArchivo(ruta: string, nombrePorDefecto: string) {
  const respuesta = await api.get<Blob>(ruta, { responseType: "blob" });
  const disposicion = String(respuesta.headers["content-disposition"] ?? "");
  const nombre = /filename="([^"]+)"/.exec(disposicion)?.[1] ?? nombrePorDefecto;
  const url = URL.createObjectURL(respuesta.data);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombre;
  enlace.click();
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}
