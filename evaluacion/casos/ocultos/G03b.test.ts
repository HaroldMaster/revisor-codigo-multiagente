import { expect, it } from 'vitest';
import { crearServicioDePrecios } from '../precios/composicion';

it('la temporada se puede activar después de crear el servicio', () => {
  let activa = false;
  const servicio = crearServicioDePrecios(() => activa);
  activa = true;
  expect(servicio.mejorDescuento(10000, 1)).toBe(1200);
});
