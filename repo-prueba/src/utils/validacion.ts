import { ErrorValidacion } from '../errores';

export function asegurarEnteroPositivo(valor: number, nombre: string): void {
  if (!Number.isInteger(valor) || valor <= 0) {
    throw new ErrorValidacion(`${nombre} debe ser un entero positivo, se recibió ${valor}`);
  }
}

export function asegurarEnteroNoNegativo(valor: number, nombre: string): void {
  if (!Number.isInteger(valor) || valor < 0) {
    throw new ErrorValidacion(`${nombre} debe ser un entero no negativo, se recibió ${valor}`);
  }
}
