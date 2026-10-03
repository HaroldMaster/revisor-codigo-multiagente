export function sumarCentavos(valores: readonly number[]): number {
  return valores.reduce((acumulado, valor) => acumulado + valor, 0);
}

export function porcentajeDe(centavos: number, porcentaje: number): number {
  return Math.round((centavos * porcentaje) / 100);
}

export function formatearPrecio(centavos: number): string {
  const signo = centavos < 0 ? '-' : '';
  const absoluto = Math.abs(centavos);
  const unidades = Math.floor(absoluto / 100);
  const fraccion = String(absoluto % 100).padStart(2, '0');
  return `${signo}$${unidades}.${fraccion}`;
}
