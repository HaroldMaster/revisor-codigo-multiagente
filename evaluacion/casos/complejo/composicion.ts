import { Contenedor } from './contenedor';
import {
  DescuentoDeTemporada,
  DescuentoPorVolumen,
  type EstrategiaDeDescuento,
  RebajaPorUnidad,
} from './estrategias';
import { ServicioDePrecios } from './servicio';

const TOKEN = {
  volumen: 'estrategia.volumen',
  temporada: 'estrategia.temporada',
  unidad: 'estrategia.unidad',
  precios: 'servicio.precios',
} as const;

function crearContenedor(temporadaActiva: () => boolean): Contenedor {
  const contenedor = new Contenedor();
  const activa = temporadaActiva();
  contenedor.registrar(TOKEN.volumen, () => new DescuentoPorVolumen());
  contenedor.registrar(TOKEN.temporada, () => new DescuentoDeTemporada(() => activa));
  contenedor.registrar(TOKEN.unidad, () => new RebajaPorUnidad());
  contenedor.registrar(
    TOKEN.precios,
    (dependencias) =>
      new ServicioDePrecios([
        dependencias.resolver<EstrategiaDeDescuento>(TOKEN.volumen),
        dependencias.resolver<EstrategiaDeDescuento>(TOKEN.temporada),
        dependencias.resolver<EstrategiaDeDescuento>(TOKEN.unidad),
      ]),
  );
  return contenedor;
}

export function crearServicioDePrecios(temporadaActiva: () => boolean): ServicioDePrecios {
  return crearContenedor(temporadaActiva).resolver<ServicioDePrecios>(TOKEN.precios);
}
