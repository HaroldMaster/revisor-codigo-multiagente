export { Carrito } from './carrito/carrito';
export { calcularDescuento, mejorCupon } from './descuentos/descuentos';
export {
  ErrorCuponInvalido,
  ErrorDominio,
  ErrorProductoDesconocido,
  ErrorStockInsuficiente,
  ErrorValidacion,
} from './errores';
export { Inventario } from './inventario/inventario';
export { IMPUESTO_PORCENTAJE, crearPedido } from './pedidos/pedidos';
export type { Cupon, CuponFijo, CuponPorcentaje, LineaCarrito, Pedido, Producto } from './tipos';
export { formatearPrecio } from './utils/dinero';
