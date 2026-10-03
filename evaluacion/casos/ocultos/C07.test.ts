import { expect, it } from 'vitest';
import { ordenarPorDescuento } from '../descuentos/descuentos';
import type { Cupon } from '../tipos';

it('no cambia el orden de la lista que recibe', () => {
  const fijo: Cupon = { codigo: 'CINCO', tipo: 'fijo', montoCentavos: 500, minimoCentavos: 0 };
  const diez: Cupon = { codigo: 'DIEZ', tipo: 'porcentaje', porcentaje: 10, minimoCentavos: 0 };
  const cupones = [fijo, diez];
  ordenarPorDescuento(8000, cupones);
  expect(cupones).toEqual([fijo, diez]);
});
