import { beforeEach, describe, expect, it } from 'vitest';
import { ErrorProductoDesconocido, ErrorStockInsuficiente } from '../errores';
import { Inventario } from './inventario';

describe('Inventario', () => {
  let inventario: Inventario;

  beforeEach(() => {
    inventario = new Inventario();
    inventario.registrar('teclado', 5);
  });

  it('informa el stock disponible de un producto registrado', () => {
    expect(inventario.disponible('teclado')).toBe(5);
  });

  it('falla al consultar un producto que no existe', () => {
    expect(() => inventario.disponible('monitor')).toThrow(ErrorProductoDesconocido);
  });

  it('descuenta lo reservado del disponible', () => {
    inventario.reservar('teclado', 2);
    expect(inventario.disponible('teclado')).toBe(3);
  });

  it('permite reservar exactamente todo el stock', () => {
    inventario.reservar('teclado', 5);
    expect(inventario.disponible('teclado')).toBe(0);
  });

  it('rechaza una reserva mayor que el disponible y no cambia el stock', () => {
    expect(() => inventario.reservar('teclado', 6)).toThrow(ErrorStockInsuficiente);
    expect(inventario.disponible('teclado')).toBe(5);
  });

  it('devuelve al disponible lo que se libera', () => {
    inventario.reservar('teclado', 4);
    inventario.liberar('teclado', 3);
    expect(inventario.disponible('teclado')).toBe(4);
  });

  it('rechaza liberar más de lo reservado', () => {
    inventario.reservar('teclado', 1);
    expect(() => inventario.liberar('teclado', 2)).toThrow(ErrorStockInsuficiente);
  });

  it('conserva las reservas cuando se vuelve a registrar el stock', () => {
    inventario.reservar('teclado', 2);
    inventario.registrar('teclado', 10);
    expect(inventario.disponible('teclado')).toBe(8);
  });
});
