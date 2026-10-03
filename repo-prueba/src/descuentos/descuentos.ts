import { ErrorCuponInvalido } from '../errores';
import type { Cupon } from '../tipos';
import { porcentajeDe } from '../utils/dinero';

const PORCENTAJE_MAXIMO = 100;

export function calcularDescuento(subtotalCentavos: number, cupon: Cupon): number {
  validarCupon(cupon);
  if (subtotalCentavos < cupon.minimoCentavos) {
    return 0;
  }
  const descuento =
    cupon.tipo === 'porcentaje'
      ? porcentajeDe(subtotalCentavos, cupon.porcentaje)
      : cupon.montoCentavos;
  return Math.min(descuento, subtotalCentavos);
}

export function mejorCupon(subtotalCentavos: number, cupones: readonly Cupon[]): Cupon | undefined {
  let mejor: Cupon | undefined;
  let mejorDescuento = 0;
  for (const cupon of cupones) {
    const descuento = calcularDescuento(subtotalCentavos, cupon);
    if (descuento > mejorDescuento) {
      mejor = cupon;
      mejorDescuento = descuento;
    }
  }
  return mejor;
}

function validarCupon(cupon: Cupon): void {
  if (cupon.tipo === 'porcentaje' && (cupon.porcentaje <= 0 || cupon.porcentaje > PORCENTAJE_MAXIMO)) {
    throw new ErrorCuponInvalido(`El cupón ${cupon.codigo} tiene un porcentaje fuera de 1 a 100`);
  }
  if (cupon.tipo === 'fijo' && cupon.montoCentavos <= 0) {
    throw new ErrorCuponInvalido(`El cupón ${cupon.codigo} tiene un monto que no es positivo`);
  }
}
