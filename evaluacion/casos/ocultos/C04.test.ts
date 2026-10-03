import { expect, it } from 'vitest';
import { Carrito } from '../carrito/carrito';
import { Inventario } from '../inventario/inventario';
import { crearPedido } from '../pedidos/pedidos';

it('no deja stock reservado cuando el pedido falla a la mitad', () => {
  const inventario = new Inventario();
  inventario.registrar('teclado', 5);
  inventario.registrar('raton', 2);
  const carrito = new Carrito();
  carrito.agregar({ id: 'teclado', nombre: 'Teclado', precioCentavos: 2500 }, 2);
  carrito.agregar({ id: 'raton', nombre: 'Ratón', precioCentavos: 1200 }, 3);
  expect(() => crearPedido('P-1', carrito, inventario)).toThrow();
  expect(inventario.disponible('teclado')).toBe(5);
});
