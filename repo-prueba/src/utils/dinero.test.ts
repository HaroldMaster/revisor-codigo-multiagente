import { describe, expect, it } from 'vitest';
import { formatearPrecio, porcentajeDe, sumarCentavos } from './dinero';

describe('sumarCentavos', () => {
  it('suma todos los valores', () => {
    expect(sumarCentavos([150, 250, 100])).toBe(500);
  });

  it('devuelve 0 con una lista vacía', () => {
    expect(sumarCentavos([])).toBe(0);
  });
});

describe('porcentajeDe', () => {
  it('calcula el porcentaje en centavos enteros', () => {
    expect(porcentajeDe(1000, 15)).toBe(150);
  });

  it('redondea al centavo más cercano', () => {
    expect(porcentajeDe(999, 15)).toBe(150);
    expect(porcentajeDe(333, 10)).toBe(33);
  });
});

describe('formatearPrecio', () => {
  it('muestra dos decimales', () => {
    expect(formatearPrecio(1205)).toBe('$12.05');
  });

  it('muestra el signo delante en valores negativos', () => {
    expect(formatearPrecio(-250)).toBe('-$2.50');
  });
});
