import { expect, it } from 'vitest';
import { conCache } from '../precios/cache';

it('la caché distingue dos cantidades con el mismo subtotal', () => {
  const calcular = conCache((subtotalCentavos, cantidadTotal) => subtotalCentavos + cantidadTotal);
  calcular(100, 1);
  expect(calcular(100, 2)).toBe(102);
});
