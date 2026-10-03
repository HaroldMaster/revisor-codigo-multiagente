export interface Producto {
  readonly id: string;
  readonly nombre: string;
  readonly precioCentavos: number;
}

export interface LineaCarrito {
  readonly producto: Producto;
  readonly cantidad: number;
}

export interface CuponPorcentaje {
  readonly codigo: string;
  readonly tipo: 'porcentaje';
  readonly porcentaje: number;
  readonly minimoCentavos: number;
}

export interface CuponFijo {
  readonly codigo: string;
  readonly tipo: 'fijo';
  readonly montoCentavos: number;
  readonly minimoCentavos: number;
}

export type Cupon = CuponPorcentaje | CuponFijo;

export interface Pedido {
  readonly id: string;
  readonly lineas: readonly LineaCarrito[];
  readonly subtotalCentavos: number;
  readonly descuentoCentavos: number;
  readonly impuestoCentavos: number;
  readonly totalCentavos: number;
}
