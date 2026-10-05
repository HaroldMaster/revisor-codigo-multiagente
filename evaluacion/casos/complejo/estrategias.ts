import { porcentajeDe } from '../utils/dinero';
import { asegurarEnteroNoNegativo } from '../utils/validacion';

const CANTIDAD_MINIMA_VOLUMEN = 10;
const PORCENTAJE_VOLUMEN = 5;
const PORCENTAJE_TEMPORADA = 12;
const REBAJA_POR_UNIDAD_CENTAVOS = 150;

export abstract class EstrategiaDeDescuento {
  abstract readonly nombre: string;

  descuentoPara(subtotalCentavos: number, cantidadTotal: number): number {
    asegurarEnteroNoNegativo(subtotalCentavos, 'subtotalCentavos');
    asegurarEnteroNoNegativo(cantidadTotal, 'cantidadTotal');
    const descuento = this.calcular(subtotalCentavos, cantidadTotal);
    return Math.min(Math.max(descuento, 0), subtotalCentavos);
  }

  protected abstract calcular(subtotalCentavos: number, cantidadTotal: number): number;
}

export class DescuentoPorVolumen extends EstrategiaDeDescuento {
  readonly nombre = 'volumen';

  protected calcular(subtotalCentavos: number, cantidadTotal: number): number {
    return cantidadTotal >= CANTIDAD_MINIMA_VOLUMEN
      ? porcentajeDe(subtotalCentavos, PORCENTAJE_VOLUMEN)
      : 0;
  }
}

export class DescuentoDeTemporada extends EstrategiaDeDescuento {
  readonly nombre = 'temporada';

  constructor(private readonly estaActiva: () => boolean) {
    super();
  }

  protected calcular(subtotalCentavos: number): number {
    return this.estaActiva() ? porcentajeDe(subtotalCentavos, PORCENTAJE_TEMPORADA) : 0;
  }
}

export class RebajaPorUnidad extends EstrategiaDeDescuento {
  readonly nombre = 'unidad';

  override descuentoPara(subtotalCentavos: number, cantidadTotal: number): number {
    return this.calcular(subtotalCentavos, cantidadTotal);
  }

  protected calcular(_subtotalCentavos: number, cantidadTotal: number): number {
    return cantidadTotal * REBAJA_POR_UNIDAD_CENTAVOS;
  }
}
