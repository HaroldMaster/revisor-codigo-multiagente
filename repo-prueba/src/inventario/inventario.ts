import { ErrorProductoDesconocido, ErrorStockInsuficiente } from '../errores';
import { asegurarEnteroNoNegativo, asegurarEnteroPositivo } from '../utils/validacion';

export class Inventario {
  private readonly existencias = new Map<string, number>();
  private readonly reservas = new Map<string, number>();

  registrar(productoId: string, cantidad: number): void {
    asegurarEnteroNoNegativo(cantidad, 'cantidad');
    this.existencias.set(productoId, cantidad);
    if (!this.reservas.has(productoId)) {
      this.reservas.set(productoId, 0);
    }
  }

  disponible(productoId: string): number {
    const existencia = this.existencias.get(productoId);
    if (existencia === undefined) {
      throw new ErrorProductoDesconocido(`No existe el producto ${productoId} en el inventario`);
    }
    return existencia - this.reservado(productoId);
  }

  reservar(productoId: string, cantidad: number): void {
    asegurarEnteroPositivo(cantidad, 'cantidad');
    const disponible = this.disponible(productoId);
    if (cantidad > disponible) {
      throw new ErrorStockInsuficiente(
        `Se pidieron ${cantidad} de ${productoId} y solo hay ${disponible} disponibles`,
      );
    }
    this.reservas.set(productoId, this.reservado(productoId) + cantidad);
  }

  liberar(productoId: string, cantidad: number): void {
    asegurarEnteroPositivo(cantidad, 'cantidad');
    const reservado = this.reservado(productoId);
    if (cantidad > reservado) {
      throw new ErrorStockInsuficiente(
        `Se quieren liberar ${cantidad} de ${productoId} y solo hay ${reservado} reservados`,
      );
    }
    this.reservas.set(productoId, reservado - cantidad);
  }

  private reservado(productoId: string): number {
    return this.reservas.get(productoId) ?? 0;
  }
}
