import type { LineaCarrito, Producto } from '../tipos';
import { sumarCentavos } from '../utils/dinero';
import { asegurarEnteroPositivo } from '../utils/validacion';

export class Carrito {
  private readonly lineasPorProducto = new Map<string, LineaCarrito>();

  agregar(producto: Producto, cantidad: number): void {
    asegurarEnteroPositivo(cantidad, 'cantidad');
    const existente = this.lineasPorProducto.get(producto.id);
    const cantidadTotal = (existente?.cantidad ?? 0) + cantidad;
    this.lineasPorProducto.set(producto.id, { producto, cantidad: cantidadTotal });
  }

  quitar(productoId: string): void {
    this.lineasPorProducto.delete(productoId);
  }

  lineas(): readonly LineaCarrito[] {
    return [...this.lineasPorProducto.values()];
  }

  estaVacio(): boolean {
    return this.lineasPorProducto.size === 0;
  }

  subtotalCentavos(): number {
    return sumarCentavos(
      this.lineas().map((linea) => linea.producto.precioCentavos * linea.cantidad),
    );
  }
}
