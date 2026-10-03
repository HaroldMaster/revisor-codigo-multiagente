const CENTAVOS_POR_UNIDAD = 100;
const PORCENTAJE_TOTAL = 100;
const DIGITOS_DE_CENTAVOS = 2;

export function sumarCentavos(valores: readonly number[]): number {
  return valores.reduce((acumulado, valor) => acumulado + valor, 0);
}

export function porcentajeDe(centavos: number, porcentaje: number): number {
  return Math.round((centavos * porcentaje) / PORCENTAJE_TOTAL);
}

export function formatearPrecio(centavos: number): string {
  const signo = centavos < 0 ? '-' : '';
  const absoluto = Math.abs(centavos);
  const unidades = Math.floor(absoluto / CENTAVOS_POR_UNIDAD);
  const fraccion = String(absoluto % CENTAVOS_POR_UNIDAD).padStart(DIGITOS_DE_CENTAVOS, '0');
  return `${signo}$${unidades}.${fraccion}`;
}
