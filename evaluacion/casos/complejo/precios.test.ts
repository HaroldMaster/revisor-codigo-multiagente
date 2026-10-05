import { describe, expect, it } from 'vitest';
import { ErrorValidacion } from '../errores';
import { conCache } from './cache';
import { crearServicioDePrecios } from './composicion';
import { Contenedor } from './contenedor';
import { DescuentoDeTemporada, DescuentoPorVolumen, RebajaPorUnidad } from './estrategias';

describe('estrategias de descuento', () => {
  it('volumen da el 5 % desde 10 unidades', () => {
    const volumen = new DescuentoPorVolumen();
    expect(volumen.descuentoPara(10000, 10)).toBe(500);
    expect(volumen.descuentoPara(10000, 9)).toBe(0);
  });

  it('temporada da el 12 % solo si está activa', () => {
    expect(new DescuentoDeTemporada(() => true).descuentoPara(10000, 1)).toBe(1200);
    expect(new DescuentoDeTemporada(() => false).descuentoPara(10000, 1)).toBe(0);
  });

  it('la rebaja por unidad multiplica por la cantidad', () => {
    expect(new RebajaPorUnidad().descuentoPara(10000, 3)).toBe(450);
  });
});

describe('Contenedor', () => {
  it('devuelve siempre la misma instancia para un token', () => {
    const contenedor = new Contenedor();
    contenedor.registrar('lista', () => []);
    expect(contenedor.resolver('lista')).toBe(contenedor.resolver('lista'));
  });

  it('falla con un token que nadie registró', () => {
    expect(() => new Contenedor().resolver('nada')).toThrow(ErrorValidacion);
  });
});

describe('conCache', () => {
  it('no vuelve a calcular para los mismos argumentos', () => {
    let llamadas = 0;
    const calcular = conCache((subtotalCentavos, cantidadTotal) => {
      llamadas += 1;
      return subtotalCentavos + cantidadTotal;
    });
    expect(calcular(100, 2)).toBe(102);
    expect(calcular(100, 2)).toBe(102);
    expect(llamadas).toBe(1);
  });
});

describe('ServicioDePrecios', () => {
  it('elige el mayor descuento entre las estrategias', () => {
    const servicio = crearServicioDePrecios(() => true);
    expect(servicio.mejorDescuento(10000, 2)).toBe(1200);
    expect(servicio.totalConDescuento(10000, 2)).toBe(8800);
  });
});
