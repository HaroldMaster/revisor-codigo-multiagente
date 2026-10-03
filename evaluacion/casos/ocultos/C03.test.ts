import { expect, it } from 'vitest';
import { descuentoPorVolumen } from '../descuentos/descuentos';

it('aplica el descuento con exactamente 10 unidades', () => {
  expect(descuentoPorVolumen(10, 20000)).toBe(1000);
});
