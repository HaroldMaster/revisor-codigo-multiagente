import { ErrorValidacion } from '../errores';

export class Contenedor {
  private readonly fabricas = new Map<string, () => unknown>();
  private readonly instancias = new Map<string, unknown>();

  registrar<T>(token: string, fabrica: (contenedor: Contenedor) => T): void {
    this.fabricas.set(token, () => fabrica(this));
  }

  resolver<T>(token: string): T {
    if (!this.instancias.has(token)) {
      const fabrica = this.fabricas.get(token);
      if (fabrica === undefined) {
        throw new ErrorValidacion(`No hay nada registrado como ${token}`);
      }
      this.instancias.set(token, fabrica());
    }
    return this.instancias.get(token) as T;
  }
}
