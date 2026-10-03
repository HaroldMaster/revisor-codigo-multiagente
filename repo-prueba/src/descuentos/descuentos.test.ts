import { describe, expect, it } from 'vitest';
import { ErrorCuponInvalido } from '../errores';
import type { Cupon } from '../tipos';
import { calcularDescuento, mejorCupon } from './descuentos';

const diezPorCiento: Cupon = {
  codigo: 'DIEZ',
  tipo: 'porcentaje',
  porcentaje: 10,
  minimoCentavos: 5000,
};
const cincoDolares: Cupon = {
  codigo: 'CINCO',
  tipo: 'fijo',
  montoCentavos: 500,
  minimoCentavos: 0,
};

describe('calcularDescuento', () => {
  it('aplica el porcentaje sobre el subtotal', () => {
    expect(calcularDescuento(8000, diezPorCiento)).toBe(800);
  });

  it('aplica el cupón cuando el subtotal es exactamente el mínimo', () => {
    expect(calcularDescuento(5000, diezPorCiento)).toBe(500);
  });

  it('no descuenta nada por debajo del mínimo de compra', () => {
    expect(calcularDescuento(4999, diezPorCiento)).toBe(0);
  });

  it('nunca descuenta más que el subtotal', () => {
    expect(calcularDescuento(300, cincoDolares)).toBe(300);
  });

  it('rechaza un porcentaje fuera de rango', () => {
    const invalido: Cupon = { ...diezPorCiento, porcentaje: 120 };
    expect(() => calcularDescuento(8000, invalido)).toThrow(ErrorCuponInvalido);
  });

  it('rechaza un monto fijo que no es positivo', () => {
    const invalido: Cupon = { ...cincoDolares, montoCentavos: 0 };
    expect(() => calcularDescuento(8000, invalido)).toThrow(ErrorCuponInvalido);
  });
});

describe('mejorCupon', () => {
  it('elige el cupón que más descuenta para ese subtotal', () => {
    expect(mejorCupon(8000, [cincoDolares, diezPorCiento])).toBe(diezPorCiento);
    expect(mejorCupon(4000, [cincoDolares, diezPorCiento])).toBe(cincoDolares);
  });

  it('devuelve undefined si no hay cupones', () => {
    expect(mejorCupon(8000, [])).toBeUndefined();
  });
});
