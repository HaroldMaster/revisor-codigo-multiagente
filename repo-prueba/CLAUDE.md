# Reglas del repositorio: mini tienda

Mini tienda en TypeScript puro: carrito, descuentos, inventario y pedidos. Este archivo es la fuente de las reglas que debe cumplir todo cambio. Cada regla tiene un identificador estable para poder citarla en un review.

## Comandos

- `npm run lint`: ESLint.
- `npm test`: Vitest.
- `npm run tipos`: comprobación de tipos con `tsc --noEmit`.

Un cambio solo está listo si los tres pasan.

## Estructura

- `src/tipos.ts`: tipos del dominio.
- `src/errores.ts`: errores del dominio.
- `src/utils/`: funciones compartidas de dinero y validación.
- `src/inventario/`, `src/carrito/`, `src/descuentos/`, `src/pedidos/`: un módulo por carpeta, con su test al lado.
- `src/index.ts`: lo único que se expone hacia fuera.

Dependencias permitidas: `pedidos` usa `carrito`, `descuentos` e `inventario`. Ningún otro módulo importa a otro; todos pueden usar `tipos`, `errores` y `utils`.

## Reglas

### R1. El dinero va en centavos enteros

Todo importe es un `number` entero en centavos y su nombre termina en `Centavos`. No se usan decimales para dinero ni se redondea a mano: los porcentajes se calculan con `porcentajeDe` y las sumas con `sumarCentavos`, de `src/utils/dinero.ts`.

Por qué: los decimales en coma flotante acumulan errores de un centavo que después no cuadran con el total.

### R2. Prohibido `any`

No se usa `any`, ni explícito ni con `as any`. Si el tipo no se conoce, se usa `unknown` y se estrecha antes de usarlo.

Por qué: `any` apaga el compilador justo donde más falta hace.

### R3. Los fallos se lanzan como errores del dominio

Un fallo se comunica lanzando una subclase de `ErrorDominio` de `src/errores.ts`. No se lanza `Error` genérico, no se devuelve `null` ni `-1` para señalar un fallo, y no se atrapa un error para ignorarlo.

Por qué: quien llama distingue los casos por la clase del error; un `null` silencioso se convierte en un bug lejos de su origen.

### R4. Sin `console` en `src`

No se deja `console.log`, `console.error` ni similares en el código de `src`.

Por qué: esta librería no decide dónde se registran los mensajes; eso es de quien la usa.

### R5. Las funciones no modifican sus argumentos

Las funciones reciben listas y objetos como `readonly` y devuelven valores nuevos. `descuentos` solo contiene funciones puras: mismo resultado para las mismas entradas y ningún efecto fuera.

Por qué: un argumento modificado por dentro cambia datos que otro módulo sigue usando.

### R6. Todo código nuevo lleva un test que comprueba su comportamiento

Cada función o método exportado nuevo, y cada rama nueva de uno existente, tiene un test que afirma el resultado esperado. Un test que solo comprueba que la función existe o que no lanza no cuenta. Los casos borde se prueban: lista vacía, cero, el valor exacto del límite.

Por qué: un test que no afirma nada pasa también cuando el código está mal.

### R7. Las cantidades se validan en la entrada pública

Todo método público que recibe una cantidad la valida con `asegurarEnteroPositivo` o `asegurarEnteroNoNegativo` antes de cambiar ningún estado.

Por qué: una cantidad negativa o decimal que entra sin validar corrompe el stock y los totales.

### R8. El stock solo cambia a través de `Inventario`

Los mapas internos de `Inventario` son privados. Fuera de la clase, el stock solo se consulta con `disponible` y solo se cambia con `registrar`, `reservar` y `liberar`. Una operación que reserva varias líneas y falla a la mitad libera lo que ya había reservado.

Por qué: una reserva que queda a medias deja stock bloqueado que nadie va a liberar.

### R9. Nombres en español y sin abreviaturas

Funciones y variables en `camelCase`, tipos y clases en `PascalCase`, constantes en `MAYUSCULAS_CON_GUION`. Los nombres van en español y completos: `cantidad`, no `cant` ni `qty`.

Por qué: el dominio está en español y un nombre abreviado obliga a adivinar.

### R10. No se duplica ni se deja código sin uso

Antes de escribir una función auxiliar se comprueba si ya existe en `src/utils`. No se exporta nada que no tenga un consumidor en `src` o en `src/index.ts`, y no se deja código comentado.

Por qué: dos funciones que hacen lo mismo divergen con el tiempo, y el código sin uso se mantiene sin que nadie lo ejecute.

### R11. Los tipos del dominio son de solo lectura

Las propiedades de los tipos de `src/tipos.ts` son `readonly`. Para cambiar un valor se crea un objeto nuevo.

Por qué: un pedido ya creado no debe poder cambiar de total.

### R12. El impuesto se calcula después del descuento

El impuesto se aplica sobre el subtotal menos el descuento, con la constante `IMPUESTO_PORCENTAJE`. El porcentaje no se escribe como número suelto en ningún otro sitio.

Por qué: calcularlo antes cobra impuesto sobre dinero que el cliente no paga.
