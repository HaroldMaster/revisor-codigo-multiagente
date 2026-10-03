export class ErrorDominio extends Error {
  constructor(mensaje: string) {
    super(mensaje);
    this.name = new.target.name;
  }
}

export class ErrorValidacion extends ErrorDominio {}

export class ErrorProductoDesconocido extends ErrorDominio {}

export class ErrorStockInsuficiente extends ErrorDominio {}

export class ErrorCuponInvalido extends ErrorDominio {}
