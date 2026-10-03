import { describe, expect, it } from 'vitest';
import { ErrorValidacion } from '../errores';
import type { Producto } from '../tipos';
import { Carrito } from './carrito';

const teclado: Producto = { id: 'teclado', nombre: 'Teclado', precioCentavos: 2500 };
const raton: Producto = { id: 'raton', nombre: 'Ratón', precioCentavos: 1200 };

describe('Carrito', () => {
  it('empieza vacío y con subtotal cero', () => {
    const carrito = new Carrito();
    expect(carrito.estaVacio()).toBe(true);
    expect(carrito.subtotalCentavos()).toBe(0);
  });

  it('acumula la cantidad cuando se agrega el mismo producto dos veces', () => {
    const carrito = new Carrito();
    carrito.agregar(teclado, 1);
    carrito.agregar(teclado, 2);
    expect(carrito.lineas()).toEqual([{ producto: teclado, cantidad: 3 }]);
  });

  it('calcula el subtotal con precio por cantidad de cada línea', () => {
    const carrito = new Carrito();
    carrito.agregar(teclado, 2);
    carrito.agregar(raton, 3);
    expect(carrito.subtotalCentavos()).toBe(8600);
  });

  it('quita la línea completa de un producto', () => {
    const carrito = new Carrito();
    carrito.agregar(teclado, 2);
    carrito.agregar(raton, 1);
    carrito.quitar('teclado');
    expect(carrito.lineas()).toEqual([{ producto: raton, cantidad: 1 }]);
  });

  it('rechaza cantidades que no son enteros positivos', () => {
    const carrito = new Carrito();
    expect(() => carrito.agregar(teclado, 0)).toThrow(ErrorValidacion);
    expect(carrito.estaVacio()).toBe(true);
  });
});
