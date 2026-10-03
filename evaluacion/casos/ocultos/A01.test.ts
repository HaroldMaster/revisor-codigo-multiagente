import { expect, it } from 'vitest';
import { Carrito } from '../carrito/carrito';

it('rechaza una cantidad negativa', () => {
  const carrito = new Carrito();
  expect(() => carrito.agregar({ id: 'teclado', nombre: 'Teclado', precioCentavos: 2500 }, -1)).toThrow();
  expect(carrito.estaVacio()).toBe(true);
});
