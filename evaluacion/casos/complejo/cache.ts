type CalculoDeDescuento = (subtotalCentavos: number, cantidadTotal: number) => number;

export function conCache(calcular: CalculoDeDescuento): CalculoDeDescuento {
  const resultados = new Map<string, number>();
  return (subtotalCentavos, cantidadTotal) => {
    const clave = String(subtotalCentavos);
    const guardado = resultados.get(clave);
    if (guardado !== undefined) {
      return guardado;
    }
    const resultado = calcular(subtotalCentavos, cantidadTotal);
    resultados.set(clave, resultado);
    return resultado;
  };
}
