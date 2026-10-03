import { beforeEach, describe, expect, it } from 'vitest';
import { Carrito } from '../carrito/carrito';
import { ErrorStockInsuficiente, ErrorValidacion } from '../errores';
import { Inventario } from '../inventario/inventario';
import type { Cupon, Producto } from '../tipos';
import { crearPedido } from './pedidos';

const teclado: Producto = { id: 'teclado', nombre: 'Teclado', precioCentavos: 2500 };
const raton: Producto = { id: 'raton', nombre: 'Ratón', precioCentavos: 1200 };
const diezPorCiento: Cupon = {
  codigo: 'DIEZ',
  tipo: 'porcentaje',
  porcentaje: 10,
  minimoCentavos: 0,
};

describe('crearPedido', () => {
  let inventario: Inventario;
  let carrito: Carrito;

  beforeEach(() => {
    inventario = new Inventario();
    inventario.registrar('teclado', 5);
    inventario.registrar('raton', 2);
    carrito = new Carrito();
  });

  it('calcula subtotal, impuesto y total sin cupón', () => {
    carrito.agregar(teclado, 2);
    const pedido = crearPedido('P-1', carrito, inventario);
    expect(pedido).toMatchObject({
      subtotalCentavos: 5000,
      descuentoCentavos: 0,
      impuestoCentavos: 750,
      totalCentavos: 5750,
    });
  });

  it('calcula el impuesto después de restar el descuento', () => {
    carrito.agregar(teclado, 2);
    const pedido = crearPedido('P-2', carrito, inventario, diezPorCiento);
    expect(pedido).toMatchObject({
      descuentoCentavos: 500,
      impuestoCentavos: 675,
      totalCentavos: 5175,
    });
  });

  it('reserva en el inventario lo que se pidió', () => {
    carrito.agregar(teclado, 2);
    carrito.agregar(raton, 1);
    crearPedido('P-3', carrito, inventario);
    expect(inventario.disponible('teclado')).toBe(3);
    expect(inventario.disponible('raton')).toBe(1);
  });

  it('rechaza un carrito vacío', () => {
    expect(() => crearPedido('P-4', carrito, inventario)).toThrow(ErrorValidacion);
  });

  it('deshace las reservas ya hechas si una línea no tiene stock', () => {
    carrito.agregar(teclado, 2);
    carrito.agregar(raton, 3);
    expect(() => crearPedido('P-5', carrito, inventario)).toThrow(ErrorStockInsuficiente);
    expect(inventario.disponible('teclado')).toBe(5);
    expect(inventario.disponible('raton')).toBe(2);
  });
});
