import type { Carrito } from '../carrito/carrito';
import { calcularDescuento } from '../descuentos/descuentos';
import { ErrorValidacion } from '../errores';
import type { Inventario } from '../inventario/inventario';
import type { Cupon, LineaCarrito, Pedido } from '../tipos';
import { porcentajeDe } from '../utils/dinero';

export const IMPUESTO_PORCENTAJE = 15;

export function crearPedido(
  id: string,
  carrito: Carrito,
  inventario: Inventario,
  cupon?: Cupon,
): Pedido {
  if (carrito.estaVacio()) {
    throw new ErrorValidacion('No se puede crear un pedido con el carrito vacío');
  }
  const lineas = carrito.lineas();
  reservarTodo(lineas, inventario);

  const subtotalCentavos = carrito.subtotalCentavos();
  const descuentoCentavos = cupon ? calcularDescuento(subtotalCentavos, cupon) : 0;
  const baseCentavos = subtotalCentavos - descuentoCentavos;
  const impuestoCentavos = porcentajeDe(baseCentavos, IMPUESTO_PORCENTAJE);

  return {
    id,
    lineas,
    subtotalCentavos,
    descuentoCentavos,
    impuestoCentavos,
    totalCentavos: baseCentavos + impuestoCentavos,
  };
}

function reservarTodo(lineas: readonly LineaCarrito[], inventario: Inventario): void {
  const reservadas: LineaCarrito[] = [];
  try {
    for (const linea of lineas) {
      inventario.reservar(linea.producto.id, linea.cantidad);
      reservadas.push(linea);
    }
  } catch (error) {
    for (const linea of reservadas) {
      inventario.liberar(linea.producto.id, linea.cantidad);
    }
    throw error;
  }
}
