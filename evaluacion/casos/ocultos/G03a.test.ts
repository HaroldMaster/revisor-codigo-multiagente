import { expect, it } from 'vitest';
import { RebajaPorUnidad } from '../precios/estrategias';

it('ninguna estrategia descuenta más que el subtotal', () => {
  expect(new RebajaPorUnidad().descuentoPara(1000, 20)).toBeLessThanOrEqual(1000);
});
