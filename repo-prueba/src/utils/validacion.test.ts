import { describe, expect, it } from 'vitest';
import { ErrorValidacion } from '../errores';
import { asegurarEnteroNoNegativo, asegurarEnteroPositivo } from './validacion';

describe('asegurarEnteroPositivo', () => {
  it('acepta enteros mayores que cero', () => {
    expect(() => asegurarEnteroPositivo(3, 'cantidad')).not.toThrow();
  });

  it.each([0, -1, 1.5, Number.NaN])('rechaza %s', (valor) => {
    expect(() => asegurarEnteroPositivo(valor, 'cantidad')).toThrow(ErrorValidacion);
  });
});

describe('asegurarEnteroNoNegativo', () => {
  it('acepta el cero', () => {
    expect(() => asegurarEnteroNoNegativo(0, 'cantidad')).not.toThrow();
  });

  it.each([-1, 2.5])('rechaza %s', (valor) => {
    expect(() => asegurarEnteroNoNegativo(valor, 'cantidad')).toThrow(ErrorValidacion);
  });
});
