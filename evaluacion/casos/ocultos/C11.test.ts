import { expect, it } from 'vitest';
import { Carrito } from '../carrito/carrito';
import { Inventario } from '../inventario/inventario';
import { crearPedido } from '../pedidos/pedidos';

it('el impuesto de un pedido se redondea al centavo más cercano', () => {
  const inventario = new Inventario();
  inventario.registrar('cable', 5);
  const carrito = new Carrito();
  carrito.agregar({ id: 'cable', nombre: 'Cable', precioCentavos: 999 }, 1);
  expect(crearPedido('P-1', carrito, inventario).impuestoCentavos).toBe(150);
});
