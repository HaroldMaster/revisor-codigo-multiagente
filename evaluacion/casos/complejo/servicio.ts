import { conCache } from './cache';
import type { EstrategiaDeDescuento } from './estrategias';

export class ServicioDePrecios {
  private readonly descuentoConCache: (subtotalCentavos: number, cantidadTotal: number) => number;

  constructor(private readonly estrategias: readonly EstrategiaDeDescuento[]) {
    this.descuentoConCache = conCache((subtotalCentavos, cantidadTotal) =>
      this.calcularMejor(subtotalCentavos, cantidadTotal),
    );
  }

  mejorDescuento(subtotalCentavos: number, cantidadTotal: number): number {
    return this.descuentoConCache(subtotalCentavos, cantidadTotal);
  }

  totalConDescuento(subtotalCentavos: number, cantidadTotal: number): number {
    return subtotalCentavos - this.mejorDescuento(subtotalCentavos, cantidadTotal);
  }

  private calcularMejor(subtotalCentavos: number, cantidadTotal: number): number {
    return Math.max(
      0,
      ...this.estrategias.map((estrategia) =>
        estrategia.descuentoPara(subtotalCentavos, cantidadTotal),
      ),
    );
  }
}
