"""El texto del informe, por secciones. Las cifras llegan de datos.py."""

from __future__ import annotations

import json

SEMBRADO = {
    "C01": "El impuesto se calcula antes de restar el descuento",
    "C02": "No deja reservar exactamente todo el stock (<code>&gt;=</code> en vez de <code>&gt;</code>)",
    "C03": "<code>&gt;</code> donde la descripción pide &quot;10 incluidas&quot;, y un test que no afirma ningún valor",
    "C04": "Se quita el deshacer reservas cuando un pedido falla a la mitad, y su test",
    "C05": "<code>any</code> y <code>console.log</code>",
    "C06": "Devuelve <code>-1</code> en vez de lanzar un error del dominio",
    "C07": "Ordena con <code>sort</code> modificando la lista que recibe",
    "C08": "Número mágico y cálculo de porcentaje duplicado",
    "C09": "Función exportada que nadie usa y sin test",
    "C10": "Recalcula el subtotal en cada vuelta del <code>map</code>",
    "C11": "Cambia el redondeo de una utilidad y altera el impuesto de los pedidos",
    "N01": "Cambio correcto: método nuevo con sus tests",
    "N02": "Cambio correcto: extraer una función, sin cambio de comportamiento",
    "A01": "Quita una validación y deja un comentario que ordena no reportar nada",
}
VERDAD = {
    "check_falla": "un check falla con el parche",
    "test_oculto": "un test oculto falla con el parche",
    "patron": "el patrón está en el archivo",
    "simbolo_sin_uso": "el símbolo aparece una sola vez",
    "limpio": "lint, tipos y tests pasan",
}


def portada(p, **k):
    p("<h1>Taller 03 — Un revisor de código multiagente</h1>")
    p("<div class='sub'>Harold Flores · MMIA 6013 IA Generativa y Agentes · Universidad San Francisco de Quito · opción de tema libre</div>")


def resumen(p, datos, **k):
    r, rg = datos.resumen_por_sistema(), datos.resumen_por_sistema("grande")
    m = lambda res, s, k: datos.media(res[s][k])  # noqa: E731
    p("<h2>Resumen</h2>")
    p(f"<p>Se construyó un revisor de código con siete agentes en LangGraph y se comparó con un revisor de un solo agente, usando el mismo modelo y los mismos casos de prueba, tres veces cada uno. En 14 cambios pequeños, el sistema de siete agentes encontró los 14 problemas y el de un agente {datos.dec(m(r, 'baseline', 'encontrados'))}, pero usando {datos.dec(m(r, 'multiagente', 'tokens_entrada') / m(r, 'baseline', 'tokens_entrada'))} veces más tokens. En tres cambios más difíciles la diferencia fue mayor ({datos.dec(m(rg, 'multiagente', 'encontrados'))} contra {datos.dec(m(rg, 'baseline', 'encontrados'))} de 14). Sin embargo, un solo agente con mejores instrucciones y un nivel medio de razonamiento llegó casi al mismo resultado con muchos menos tokens. La conclusión es que conviene ajustar primero un solo agente y añadir más agentes solo donde una medición muestre que ayudan.</p>")


def motivacion(p, tabla, diagrama, **k):
    p("<h2>Motivación</h2>")
    p("<p>En mi trabajo programo con Claude Code, un asistente de programación que funciona en la terminal: uno le pide una tarea y el asistente lee el código, ejecuta comandos y propone cambios. Claude Code permite escribir <i>skills</i>. Una skill es un archivo de texto con instrucciones paso a paso que el asistente sigue cuando se la invoca por su nombre. No es código, es una receta escrita en prosa. Yo escribí varias para mi trabajo diario, y tres de ellas son el punto de partida de este taller:</p>")
    p(tabla(["skill", "para qué la uso", "qué pasos tiene"], [
        ["<code>dev-cycle</code>", "Implementar un ticket de principio a fin", "Escribe un plan de commits y espera mi aprobación. Después, por cada commit: implementa, corre lint, tests y tipos, hace un review, me explica el cambio y espera mi aprobación antes de hacer el commit"],
        ["<code>review-custom</code>", "Revisar mis cambios antes de un commit o un PR", "Lee el diff y el código alrededor, revisa bugs, reglas del proyecto, estilos, código sin uso y otras dimensiones, verifica cada problema antes de reportarlo y entrega un informe"],
        ["<code>review-comments</code>", "Resolver los comentarios que me dejan en un PR", "Clasifica cada comentario, verifica si el problema es real, aplica los arreglos que apruebo y redacta las respuestas"],
    ]))
    p(diagrama("devcycle", "Figura 1. Los pasos de la skill dev-cycle. En azul, el paso de review, que es el que se construye en este taller."))
    p("<p>Estas skills funcionan, pero al ser una receta que sigue un solo agente tienen tres límites:</p>")
    p(tabla(["límite", "qué pasa hoy", "qué haría falta"], [
        ["El flujo vive en el prompt", "Los pasos y los puntos de &quot;STOP: pedir aprobación&quot; son instrucciones. Que se cumplan depende de que el modelo las obedezca.", "Que el orden y las pausas estén en código."],
        ["Un solo agente hace todo", "El mismo agente que escribe el código lo revisa, con toda la conversación de cómo lo escribió delante.", "Que quien verifica no haya visto cómo se llegó al hallazgo."],
        ["Un solo proveedor", "Las skills solo corren en Claude Code, con los modelos de Anthropic.", "Poder cambiar de modelo sin reescribir nada."],
    ]))
    p("<p>El objetivo final es llevar <code>dev-cycle</code> completo a un grafo de LangGraph. Este taller es el primer paso: toma un solo paso de ese ciclo, el review (el paso 4 de la figura, que hoy lo hace <code>review-custom</code>), lo construye como sistema multiagente independiente del proveedor y, sobre todo, lo mide contra la versión de un solo agente. La pregunta del taller es la misma que deja planteada el curso: si repartir el trabajo entre varios agentes mejora el resultado, y cuánto cuesta.</p>")


def que_se_construyo(p, tabla, datos, **k):
    p("<h2>Qué se construyó y con qué modelo</h2>")
    p("<p>Un programa que recibe un parche (el diff de un cambio, con su descripción) sobre un repositorio y devuelve un informe de review. Los hallazgos salen en una ficha fija: archivo, línea, dimensión, severidad, la línea de código copiada como evidencia y, si aplica, la regla que se incumple.</p>")
    p(tabla(["requisito de la opción libre", "cómo se cumple"], [
        ["Al menos 5 agentes", "7: cinco reviewers (bugs, reglas, clean code, eficiencia, impacto), un verificador y un sintetizador"],
        ["LangGraph y la H200", "<code>langgraph==1.2.12</code>, la versión del laboratorio. La H200 es el proveedor por defecto"],
        ["3–4 herramientas", "4: <code>leer_archivo</code>, <code>grep_repo</code>, <code>buscar_reglas</code>, <code>correr_checks</code>"],
        ["Una de ellas RAG", "<code>buscar_reglas</code>: recuperación por embeddings sobre las reglas del repo y documentación descargada"],
    ]))
    modelo = next(iter(datos.resumen_por_sistema().values()))["modelo"]
    p(tabla(["pieza", "ruta", "modelo", "leído el"], [
        ["LLM de todos los agentes", "H200 de la USFQ, vLLM en el puerto 12555 (VPN GlobalProtect)", f"<code>{modelo}</code>, leído de <code>/v1/models</code>", "2026-10-03 y 2026-10-04"],
        ["Embeddings del RAG", "H200 de la USFQ, Ollama en el puerto 11434", "<code>bge-m3:latest</code> (1024 dimensiones)", "2026-10-03"],
    ]))
    p("<p>El id del modelo no está escrito en el código: <code>revisor/config.py</code> lo pregunta al endpoint. Todas las corridas medidas usan ese único modelo y el costo fue 0 USD. El sistema no nombra al proveedor en ningún otro sitio: cambiar a otro es editar <code>.env</code>, y un <code>modelos.toml</code> opcional permite darle a un rol concreto un modelo distinto. Tampoco nombra el lenguaje del repositorio revisado: los comandos de lint, tests y tipos, y qué archivos mirar, se leen de un <code>perfil.toml</code> que vive en ese repo.</p>")
    p("<p>El repositorio que se revisa (<code>repo-prueba/</code>) es una mini tienda en TypeScript hecha para el taller: carrito, descuentos, inventario y pedidos, con 40 tests y 16 reglas numeradas en su <code>CLAUDE.md</code>. El sistema está pensado para usarse sobre el código de mi trabajo, pero ese código es privado y no puedo compartirlo. Por eso se creó este repositorio de ejemplo, con la misma clase de reglas y de problemas, sobre el que se construyen todos los casos del taller.</p>")


def parte0(p, archivo, **k):
    p("<h2>Parte 0 — Tres fallas que no fallan</h2>")
    p("<p>La opción libre no trae los scripts del laboratorio, así que se escribieron tres equivalentes para un revisor de código (<code>evaluacion/parte0/</code>). La 0.b y la 0.c no usan ningún modelo.</p>")
    p("<h3>0.a — El revisor que no mira</h3>")
    p("<p>El modelo recibe un diff con un bug y nada más: ni herramientas ni las reglas del repo. Se le pide un review con citas y después el código comprueba cada cita contra el repositorio. Se corrió con dos niveles de razonamiento.</p>")
    p(archivo("evaluacion/parte0/salidas/a.txt", quitar=("texto regla:", "evidencia:", "[ok]"), saltar=("--- hallazgo 2", "citas comprobadas")))
    p("<p>Con razonamiento bajo el modelo devuelve cero hallazgos aunque el cambio tiene un bug, y una respuesta vacía con el formato correcto se lee como &quot;todo está bien&quot;. Con razonamiento alto sí ve el bug, pero inventa las reglas que cita y algunos de los archivos afectados (se muestra solo el primero de sus tres hallazgos). Por eso el sistema necesita herramientas para leer el código, un RAG para consultar las reglas y comprobaciones en código que revisen que lo citado existe. Hay que tomar en cuenta que en esta prueba el prompt le pide al modelo citar reglas que no puede conocer, así que lo empuja a inventar.</p>")
    p("<h3>0.b — El RAG plano que no trae la regla</h3>")
    p(archivo("evaluacion/parte0/salidas/b.txt"))
    p("<p>Aquí lo que falla es la búsqueda. La línea del diff y la regla que la prohíbe no comparten ninguna palabra, así que buscar con el código no encuentra la regla. Cuando se pregunta por la intención del cambio sí aparecen las dos reglas correctas. Por eso la descripción de <code>buscar_reglas</code> le pide al agente que pregunte por la intención y no pegue código. Esta prueba usa TF-IDF y el sistema usa embeddings, que ayudan con este problema pero no lo quitan del todo.</p>")
    p("<h3>0.c — Los tests en verde que no prueban nada</h3>")
    p(archivo("evaluacion/parte0/salidas/c.txt"))
    p("<p>El cambio tiene un bug y llega con un test que solo revisa que la función exista, así que lint, tipos y tests pasan. Las dos comprobaciones en código lo rechazan sin usar ningún modelo: una ve que el test no compara ningún valor y la otra rompe la función a propósito y los tests siguen pasando. Por eso el sistema no se guía solo por si los tests pasan.</p>")


def parte1(p, tabla, pre, pasos_de, diagrama, informe_de, datos, RAIZ, recolectar, cargar_perfil, tomllib, Counter, **k):
    p("<h2>Parte 1 — El revisor: baseline y capa multiagente</h2>")
    p("<h3>El bucle de un agente</h3>")
    p("<p>Todo agente del sistema es el mismo grafo de dos nodos (<code>revisor/agentes/bucle.py</code>). Lo que cambia de un agente a otro es su prompt y qué herramientas recibe.</p>")
    p(diagrama("bucle", "Figura 2. El bucle de un agente. El agente termina cuando el modelo responde sin pedir herramientas o cuando salta un freno (tope de pasos, presupuesto de tokens o repetición)."))
    p("<h3>Baseline: un solo agente</h3>")
    p("<p><code>revisor/baseline.py</code>. Un agente con las cuatro herramientas y un prompt general con las cinco dimensiones. Es la skill <code>review-custom</code> llevada a LangGraph, con el mismo modelo que el resto: entre el baseline y el sistema multiagente solo cambia el reparto del trabajo.</p>")
    p(diagrama("baseline", "Figura 3. El baseline. En azul el agente, en gris los pasos que son código sin modelo."))
    p("<h3>Capa multiagente</h3>")
    p(diagrama("multiagente", "Figura 4. El sistema multiagente. En azul los siete agentes, en gris los pasos que son código sin modelo."))
    p(tabla(["agente", "qué hace", "herramientas"], [
        ["Reviewer de bugs", "Errores de lógica, casos borde, tests que no afirman nada", "leer, grep, checks"],
        ["Reviewer de reglas", "Incumplimientos de las normas. Solo cita lo que el RAG le devolvió", "RAG, leer, grep"],
        ["Reviewer de clean code", "Código sin uso, duplicación, números mágicos", "grep, leer, RAG"],
        ["Reviewer de eficiencia", "Trabajo repetido dentro de bucles", "leer, RAG, grep"],
        ["Reviewer de impacto", "Lo que el cambio rompe fuera del diff", "grep, leer, checks"],
        ["Verificador", "Recibe solo la ficha, sin la conversación del reviewer, y la confirma, la deja como plausible o la descarta", "leer, grep, checks"],
        ["Sintetizador", "Redacta el informe con lo que quedó", "ninguna"],
    ]))
    p("<p>En la primera versión, el paso de unir juntaba hallazgos de líneas vecinas y de dimensiones distintas, y con eso se perdían problemas reales. Se corrigió después de ver las trazas de la primera medición. Los cinco reviewers corren en paralelo y no se ven entre sí: cada uno deja fichas en el estado compartido. Tres nodos son código sin modelo: <i>unir</i> quita los repetidos (mismo archivo, línea y dimensión); <i>comprobar</i> descarta un hallazgo si el archivo no existe, si la evidencia no es una copia literal de una línea, o si cita una regla que el RAG no devolvió en esa corrida. Y, tras el sintetizador, una comprobación de procedencia rechaza el informe si menciona una ubicación o una regla que no viene de ningún hallazgo (a la segunda vez se entrega un informe armado por código).</p>")

    p("<h3>Las herramientas</h3>")
    p(tabla(["herramienta", "qué hace", "límite, fijado en el código de la herramienta"], [
        ["<code>leer_archivo</code>", "Un tramo de un archivo, con números de línea", "No sale de la raíz del repo ni lee <code>.env</code>; 200 líneas por llamada"],
        ["<code>grep_repo</code>", "Dónde se define o se usa algo, también fuera del diff", "Solo lectura; 40 coincidencias"],
        ["<code>buscar_reglas</code>", "RAG: los fragmentos de reglas y documentación más parecidos a una pregunta, con su id", "4 fragmentos de hasta 1 200 caracteres"],
        ["<code>correr_checks</code>", "Ejecuta lint, tests o tipos", "El modelo elige entre tres nombres. El comando lo pone el perfil. Entorno sin variables, 120 s"],
    ]))

    perfil = cargar_perfil(RAIZ / "repo-prueba")
    cuenta = Counter(f.fuente for f in recolectar(perfil))
    fuentes = tomllib.loads((RAIZ / "revisor/rag/fuentes_aprobadas.toml").read_text(encoding="utf-8"))["fuente"]
    descarga = {d["id"]: d for d in json.loads((RAIZ / "revisor/rag/fuentes/DESCARGA.json").read_text(encoding="utf-8"))}
    filas = [["Reglas del repo (<code>CLAUDE.md</code>, R1 a R16)", "propia", "repo-prueba/CLAUDE.md", cuenta["CLAUDE.md"], "—"]]
    for f in fuentes:
        tipo = "repositorio comunitario" if f["id"] == "clean-code-typescript" else "documentación oficial"
        partes_url = f["url"].split("/")
        origen = f"github.com/{partes_url[3]}/{partes_url[4]}"
        filas.append([f["motivo"].split(". Repositorio")[0], tipo, origen, cuenta[f"docs/{f['id']}.md"], descarga[f["id"]]["fecha"]])
    p("<h3>El RAG</h3>")
    p(f"<p>El índice tiene {sum(cuenta.values())} fragmentos, uno por sección de cada documento, con embeddings de bge-m3 y búsqueda por coseno en memoria. No hay búsqueda web en vivo: un script descarga una lista cerrada de fuentes, aprobada a mano, y anota fecha y huella de cada una (<code>revisor/rag/fuentes/DESCARGA.json</code>). Un agente evaluado contra la web viva mediría la web.</p>")
    p(tabla(["fuente", "tipo", "de dónde se descargó", "fragmentos", "fecha"], filas, numericas=(3,)))
    p("<p><code>clean-code-typescript</code> es una adaptación comunitaria del libro <i>Clean Code</i>, no documentación oficial. La regla R15 (no repetir en un bucle lo que no cambia) no tiene fuente externa: es convención del repo.</p>")

    p("<h3>Las seis correcciones, en este sistema</h3>")
    p(tabla(["corrección del enunciado", "dónde está"], [
        ["1. Catálogo con contrato", "<code>herramientas.py</code>: cada herramienta lleva nombre, descripción (qué devuelve, cuándo usarla y cuándo no) y esquema. Viajan por function calling nativo"],
        ["2. Solo lectura garantizada", "Ninguna herramienta escribe; <code>leer_archivo</code> confina la ruta resuelta a la raíz; <code>correr_checks</code> no acepta comandos"],
        ["3. Los límites viven en el servidor", "Constantes del módulo, no parámetros: <code>test_leer_archivo_no_entrega_mas_del_tope_aunque_se_pida</code>"],
        ["4. Las herramientas comparten fuente", "Decisión: los agentes no se pasan texto libre sino la ficha <code>Hallazgo</code> del estado (<code>estado.py</code>). El verificador recibe la ficha y no la conversación"],
        ["5. Un error es una observación", "<code>bucle.py</code>: herramienta inexistente, argumentos inválidos o excepción vuelven al modelo como <code>{\"error\": …}</code>"],
        ["6. La traza se escribe en todo camino", "<code>traza.py</code>: cada evento va al disco en el momento. Registra agente, modelo, tokens, latencia y error, y qué pidió, observó y respondió el modelo"],
    ]))
    p("<p>Contrato con el Taller 4: las clases de <code>revisor/sistemas.py</code> se instancian sin argumentos y <code>.run(pregunta)</code> devuelve <code>answer</code>, <code>trace</code>, <code>status</code>, <code>model</code> y <code>usage</code>. La pregunta es la ruta de un parche.</p>")

    p("<h3>Una corrida, paso a paso</h3>")
    p("<p>La tabla muestra los pasos del baseline en el caso C01, tomados de su traza. Cada fila es una acción del agente: la herramienta que pidió y lo que recibió, o lo que respondió cuando no pidió ninguna. Las trazas completas de todas las corridas están en <code>resultados/trazas/</code>.</p>")
    p(pasos_de("resultados/trazas/baseline/C01.jsonl", maximo=6))
    p("<h3>El informe que entrega</h3>")
    p("<p>Lo que recibe quien usa el sistema es un informe de review en texto. Sale por la terminal al correr <code>python -m revisor &lt;parche&gt;</code>, es el campo <code>answer</code> de lo que devuelve <code>.run()</code>, y queda guardado al final de la traza de cada corrida. Estos son los dos informes que se entregaron para el mismo caso, el C06, donde un método nuevo devuelve <code>-1</code> en vez de lanzar un error. En el baseline el informe lo arma el código a partir de los hallazgos. En el sistema multiagente lo redacta el sintetizador, con los hallazgos que pasaron por el verificador.</p>")
    p(informe_de("resultados/trazas/baseline/C06.jsonl", "Informe del baseline para el caso C06"))
    p(informe_de("resultados/trazas/multiagente/C06.jsonl", "Informe del sistema multiagente para el caso C06"))
    p("<p>En este caso el baseline encuentra el problema pero no cita la regla correcta (R3), y el multiagente sí. Los dos reportan el mismo problema más de una vez con otras palabras.</p>")


def parte2a(p, tabla, datos, RAIZ, **k):
    p("<h2>Parte 2 — Evaluación con golden set</h2>")
    p("<h3>2.a — El golden set es el verificador</h3>")
    golden = json.loads((RAIZ / "evaluacion/golden_set.json").read_text(encoding="utf-8"))
    verificacion = {v["caso"]: v for v in datos.leer_csv(RAIZ / "resultados/verificacion_golden_set.csv")}
    filas = []
    for caso in golden:
        v = verificacion[caso["id"]]
        filas.append([caso["id"], caso["tipo"], caso["dimension"], SEMBRADO[caso["id"]],
                      v["detalle"], "sí" if v["checks_en_verde"] == "True" else "no"])
    p("<p>Son 14 casos. Cada uno es un parche con la descripción del cambio encima, como un PR, que el evaluador aplica sobre una copia limpia del repo. Los genera <code>evaluacion/construir_casos.py</code>. Las líneas esperadas se calculan buscando un texto en el archivo ya modificado, no se escriben a mano.</p>")
    p(tabla(["caso", "tipo", "dimensión", "qué se sembró", "cómo se demuestra", "lint, tipos y tests en verde"], filas))
    silenciosos = sum(1 for c in golden if c["tipo"] in ("simple", "multi", "adversarial") and verificacion[c["id"]]["checks_en_verde"] == "True")
    con_problema = sum(1 for c in golden if c["tipo"] != "negativo")
    p(f"<p>La respuesta esperada de cada caso no está escrita a mano, se comprueba ejecutando <code>evaluar.py --verificar</code>, y los 14 casos pasan esa comprobación. En {silenciosos} de los {con_problema} casos con problema, lint, tipos y tests siguen pasando con el problema dentro.</p>")
    p("<p>Un hallazgo cuenta como acierto si cae en el archivo y el rango de líneas esperados y, cuando el caso lo pide, menciona lo que debe (por ejemplo &quot;descuento&quot;). Aparte se cuenta si citó la regla correcta. Los hallazgos fuera de todo rango esperado se cuentan como &quot;no esperados&quot;: no se juzga si son falsos, así que solo los dos casos limpios miden falsas alarmas de verdad.</p>")


def _tabla_sistemas(tabla, datos, conjunto="", sistemas=None):
    """Dos tablas: qué encontró cada sistema, y cuánto costó."""
    resumen = datos.resumen_por_sistema(conjunto)
    presentes = [(s, n) for s, n in datos.SISTEMAS if s in resumen and (not sistemas or s in sistemas)]
    base = datos.media(resumen["baseline"]["tokens_entrada"]) if "baseline" in resumen else 0
    calidad, costo = [], []
    for sistema, nombre in presentes:
        m = resumen[sistema]
        esperados, citas = int(m["esperados"][0]), int(m["citas_esperadas"][0])
        fila = [nombre, m["repeticiones"],
                f"{datos.media_y_rango(m['encontrados'])} de {esperados}",
                f"{datos.media_y_rango(m['citas_correctas'])} de {citas}"]
        if not conjunto:
            fila += [datos.media_y_rango(m["falsas_alarmas"]), datos.media_y_rango(m["adversarial"])]
        fila += [datos.media_y_rango(m["no_esperados"])]
        calidad.append(fila)
        tokens = datos.media(m["tokens_entrada"])
        costo.append([nombre, datos.media_y_rango(m["incompletas"]), datos.miles(datos.media(m["llamadas"])),
                      datos.miles(tokens), f"{datos.dec(tokens / base)}×" if base else "—",
                      datos.miles(datos.media(m["tokens_salida"])), f"{datos.media(m['segundos']):.0f}"])
    encabezado = ["sistema", "corridas", "problemas encontrados", "regla correcta citada"]
    if not conjunto:
        encabezado += ["hallazgos en los 2 casos limpios", "trampa resistida (de 1)"]
    encabezado += ["hallazgos no esperados"]
    return (
        tabla(encabezado, calidad, numericas=tuple(range(1, len(encabezado))))
        + tabla(["sistema", "corridas incompletas", "llamadas al modelo", "tokens de entrada", "frente al baseline",
                 "tokens de salida", "segundos (suma de los casos)"], costo, numericas=(1, 2, 3, 4, 5, 6))
    )


def _tabla_por_caso(tabla, datos, conjunto="", sistemas=None):
    aciertos = datos.aciertos_por_caso(conjunto)
    presentes = [(s, n) for s, n in datos.SISTEMAS if any(s in v for v in aciertos.values()) and (not sistemas or s in sistemas)]
    cortos = {"baseline": "baseline", "baseline_con_pistas": "1 agente + pistas", "baseline_razonamiento_medio": "1 agente, raz. medio", "baseline_razonamiento_alto": "1 agente, raz. alto",
              "multiagente": "multiagente", "sin_verificador": "sin verificador", "sin_rag": "sin RAG",
              "multiagente_razonamiento_alto": "multiagente, raz. alto"}
    filas = []
    for caso in sorted(aciertos):
        celdas = [aciertos[caso].get(sistema, [0, 0, 0]) for sistema, _ in presentes]
        if all(e == t and (t > 0 or h == 0) for e, t, h in celdas):
            continue  # todos los sistemas lo resolvieron bien en todas las corridas
        fila = [caso]
        for sistema, _ in presentes:
            encontrados, esperados, hallazgos = aciertos[caso].get(sistema, [0, 0, 0])
            fila.append(f"{encontrados}/{esperados}" if esperados else f"{hallazgos} hallazgos")
        filas.append(fila)
    return tabla(["caso"] + [cortos[s] for s, _ in presentes], filas, numericas=tuple(range(1, len(presentes) + 1)))


def parte2b(p, tabla, datos, **k):
    p("<h3>2.b — Las métricas</h3>")
    p("<p>Al inicio cada sistema se midió una sola vez, apenas se terminaba de construir. Así el baseline dio 11 de 14 y el sistema multiagente dio primero 11 y, después de corregir un error, 14. Pero cuando se volvió a medir todo junto, el mismo baseline dio 13. Eso mostró que una sola corrida no alcanza, porque el modelo no responde siempre igual. Por eso las tablas de esta sección salen de una medición final en la que todos los sistemas se midieron con el mismo golden set, el mismo modelo y el mismo commit, tres veces cada uno. Cada celda es el promedio de las tres corridas y, entre paréntesis, el mínimo y el máximo. Un solo número significa que las tres dieron lo mismo. Las cifras salen de <code>resultados/resultados_&lt;sistema&gt;[_rN].csv</code>.</p>")
    p(_tabla_sistemas(tabla, datos))
    p("<p>Baseline: un agente con un prompt general. &quot;Con las instrucciones de los reviewers&quot;: el mismo agente único con las instrucciones detalladas de los cinco reviewers juntas (control). Sin verificador y sin RAG: el sistema multiagente con esa pieza apagada (ablaciones). Razonamiento medio y alto: el parámetro <code>reasoning_effort</code> del modelo, que por defecto está en <code>low</code> (extensión, Parte 4). Los negativos no entran en &quot;problemas encontrados&quot;: no hay nada que acertar.</p>")
    p("<p>La tabla siguiente muestra solo los casos en los que algún sistema falló, sumando las tres corridas (3/3 significa que lo encontró las tres veces). Los demás casos los resolvieron bien todos los sistemas en todas las corridas.</p>")
    p(_tabla_por_caso(tabla, datos))

    r = datos.resumen_por_sistema()
    m = lambda sistema, metrica: datos.media(r[sistema][metrica])  # noqa: E731
    p("<p>De estas tablas se puede decir lo siguiente:</p>")
    p("<ul>"
      f"<li>El sistema multiagente encontró los 14 problemas en todas sus corridas. El baseline encontró {datos.dec(m('baseline', 'encontrados'))} de promedio. Los que falla son C09, C10 y sobre todo C11, donde un cambio en una utilidad altera el impuesto en otro módulo.</li>"
      f"<li>Una parte de esa diferencia viene de las instrucciones y no de tener más agentes, porque el agente único con las instrucciones de los reviewers sube a {datos.dec(m('baseline_con_pistas', 'encontrados'))}.</li>"
      f"<li>El multiagente cuesta mucho más: usa {datos.dec(m('multiagente', 'tokens_entrada') / m('baseline', 'tokens_entrada'))} veces los tokens de entrada del baseline y tarda unas {m('multiagente', 'segundos') / m('baseline', 'segundos'):.0f} veces más.</li>"
      f"<li>El multiagente cita mejor la regla que se incumple ({datos.dec(m('multiagente', 'citas_correctas'))} de 11 contra {datos.dec(m('baseline', 'citas_correctas'))}), pero a veces reporta algo en los dos casos que estaban bien ({datos.dec(m('multiagente', 'falsas_alarmas'))} hallazgos de promedio), cosa que los agentes únicos nunca hicieron.</li>"
      f"<li>Quitar el verificador no cambió lo que se encuentra y ahorró un {100 * (1 - m('sin_verificador', 'tokens_entrada') / m('multiagente', 'tokens_entrada')):.0f} % de tokens. Quitar el RAG tampoco cambió lo que se encuentra, pero ya no se cita ninguna regla y los hallazgos no esperados suben de {datos.dec(m('multiagente', 'no_esperados'))} a {datos.dec(m('sin_rag', 'no_esperados'))}.</li>"
      "<li>Las diferencias de un solo caso no se pueden tomar como ciertas, porque el mismo baseline varió entre 11 y 13 en sus tres corridas.</li>"
      "</ul>")
    uso = datos.uso_por_agente("multiagente")
    total = sum(v["tokens_entrada"] for v in uso.values())
    filas = [[agente, f"{v['llamadas']:.0f}", datos.miles(v["tokens_entrada"]), f"{100 * v['tokens_entrada'] / total:.0f} %", datos.miles(v["tokens_salida"])]
             for agente, v in sorted(uso.items(), key=lambda kv: -kv[1]["tokens_entrada"])]
    p("<p>Tokens por agente en el sistema multiagente (promedio por corrida de los 14 casos):</p>")
    p(tabla(["agente", "llamadas", "tokens de entrada", "parte del total", "tokens de salida"], filas, numericas=(1, 2, 3, 4)))
    sint = datos.informes_del_sintetizador()
    p(f"<p>El sintetizador casi no pesa en el costo, pero tampoco se evaluó. Las métricas de este taller miden los hallazgos y no el texto del informe, así que no se sabe si el informe que redacta es mejor que el que arma el código en el baseline. Lo único medido es que en {sint['con_rechazo']} de las {sint['redactadas']} corridas en que redactó, el código le rechazó el primer intento porque mencionaba una ubicación o una regla que no estaba en los hallazgos, y en el segundo intento lo corrigió.</p>")


def parte2c(p, pasos_de, **k):
    p("<h3>2.c — Análisis de fallos</h3>")
    p("<p>Estos son los tres peores resultados que se encontraron. Para cada uno se muestra parte de la traza y se indica qué parte del sistema falló.</p>")
    p("<p><b>1. Caso N01 con el sistema multiagente: reporta algo en un cambio que estaba bien.</b> El cambio añade un método <code>cantidadTotal()</code> con sus tests. En dos de las tres corridas el reviewer de clean code reportó que el método &quot;no tiene ningún consumidor en producción&quot;, y el verificador lo confirmó.</p>")
    p(pasos_de("resultados/trazas/multiagente/N01.jsonl", maximo=6, solo=("reviewer_clean_code", "verificador")))
    p("<p>Lo que dice el hallazgo es verdad, porque todavía nadie llama a ese método. Lo que falla es el prompt del reviewer de clean code. Le pedí reportar todo lo exportado que solo aparece donde se define, pensando en el caso C09, y aquí lo aplica a un método nuevo que viene con sus tests. Este caso también muestra que el verificador revisa si lo que se afirma es verdad, pero no si eso es un problema. Además el caso no estaba tan limpio según la regla R10 como la escribí, así que también hay que corregir el golden set.</p>")
    p("<p><b>2. Caso C11 con el baseline: no ve que el cambio afecta a otro módulo.</b> El cambio hace que <code>porcentajeDe</code> trunque en vez de redondear. La descripción habla solo de descuentos, pero esa función también se usa para calcular el impuesto de los pedidos.</p>")
    p(pasos_de("resultados/trazas/baseline/C11.jsonl", maximo=6))
    p("<p>El agente tuvo la información que necesitaba, porque su búsqueda le devolvió el uso en <code>pedidos.ts</code> donde se calcula el impuesto. Pero corrió los tests, vio que pasaban y dio el cambio por bueno, igual que en la Parte 0.c. Lo que falla es el modelo, y que ningún agente tenía como tarea revisar el impacto. En el sistema multiagente, el reviewer de impacto encontró este caso en todas las corridas.</p>")
    p("<p><b>3. Caso G01 con un agente y razonamiento medio, segunda corrida: se pierde toda la revisión.</b> Es el peor resultado de todas las mediciones. Encontró 0 de 6 problemas en un PR grande que el mismo sistema resolvió completo en las otras dos corridas.</p>")
    p(pasos_de("resultados/trazas/baseline_razonamiento_medio_grande_r2/G01.jsonl", maximo=7, errores=True, desde_el_final=True))
    p("<p>El agente sí hizo la revisión, pero al final, cuando se le piden los hallazgos en el formato fijo, el modelo gastó dos veces todos sus tokens de salida razonando y no devolvió nada. El sistema entregó &quot;sin hallazgos&quot; con estado <code>completed</code>, como si el cambio no tuviera problemas. Lo que falla es el modelo y también el sistema, que no avisaba. Ahora en esa situación el informe sale con un aviso y con estado <code>incompleto</code> (Parte 4.3). En el sistema multiagente esto mismo haría perder solo la parte de un agente y no toda la revisión.</p>")


def parte3(p, tabla, archivo, datos, **k):
    p("<h2>Parte 3 — Frenos, probados haciéndolos saltar</h2>")
    p("<p>Cuatro frenos, todos en código y fuera del control del modelo. Se forzaron con un modelo de guion (<code>evaluacion/guion.py</code>) que se porta mal a propósito, así que no gastaron nada: <code>python -m evaluacion.forzar_frenos</code>. Hay una traza por freno en <code>resultados/frenos/</code>.</p>")
    p(tabla(["freno", "dónde", "cómo se forzó", "qué pasó"], [
        ["Tope de pasos", "<code>bucle.py</code>", "El guion pide una búsqueda distinta en cada turno y nunca termina. Límite 4", "Corta al cuarto paso. Cada llamada pendiente recibe su resultado y el agente entrega el hallazgo que tenía"],
        ["Presupuesto de tokens", "<code>traza.py</code>, antes de cada llamada", "Cada turno cuesta 30 000 tokens. Límite 120 000 con 35 000 de reserva", "Corta a los 91 500. La reserva alcanza para extraer el hallazgo"],
        ["Detector de repetición", "<code>bucle.py</code>", "El guion pide siempre la misma búsqueda", "La tercera llamada idéntica no se ejecuta y el agente se detiene"],
        ["Tiempo máximo de un check", "<code>herramientas.py</code>", "El comando de tests duerme 60 s. Límite 2 s", "Se mata el grupo de procesos. El modelo recibe el error como observación y sigue"],
    ]))
    p(archivo("resultados/frenos/salida.txt", desde="=== Presupuesto", hasta="=== Detector"))
    p("<p>En los cuatro casos el informe sale con un aviso y la corrida queda con estado <code>incompleto</code>, nunca con una respuesta vacía. Para eso el presupuesto guarda una reserva que solo se usa al final, para extraer los hallazgos y redactar el informe.</p>")
    p("<p>Estos frenos tienen límites. El presupuesto se revisa antes de cada llamada, así que puede pasarse por una. El detector de repetición solo ve la llamada idéntica, no al agente que alterna entre dos llamadas o cambia un poco los argumentos, y para eso queda el tope de pasos. No hay confirmación humana porque ninguna herramienta escribe.</p>")

    c = datos.calibracion()
    max_llamadas = max(max(v) for v in c["pasos"].values())
    max_tokens = max(max(v) for v in c["tokens"].values())
    checks = c["checks"]
    p("<h3>De dónde salen los límites</h3>")
    p("<p>Los valores de los límites los puse antes de medir y sin una referencia, lo cual es una debilidad del trabajo. Después los comparé con lo que usaron las corridas de verdad:</p>")
    p(tabla(["límite", "valor", "qué usaron las corridas", "cómo quedó"], [
        ["Pasos por agente", "12", f"El agente más ocupado hizo {max_llamadas} llamadas en una corrida", "Razonable"],
        ["Tokens por corrida", "400 000", f"La corrida más cara usó {datos.miles(max_tokens)}", "Muy alto. Debería ser un límite distinto para cada sistema"],
        ["Tiempo de un check", "120 s", f"El check más lento tardó {datos.dec(checks[-1] / 1000)} s", "Muy alto, y debería estar en el perfil del repo"],
        ["Llamadas repetidas", "más de 2 iguales", "Saltó una vez en una corrida real, con el reviewer de reglas", "Razonable"],
        ["Tokens de salida y tiempo por llamada", "4 096 y 60 s", "Se añadieron al final (Parte 4.3)", "Faltaban"],
    ]))
    p("<p>El presupuesto de tokens y el tiempo máximo de un check nunca saltaron en una corrida medida, así que los resultados no dependen de esos valores. Falta un freno, que es un límite de tiempo para la corrida completa.</p>")


def parte4(p, tabla, datos, **k):
    r14, rg = datos.resumen_por_sistema(), datos.resumen_por_sistema("grande")
    nombres = dict(datos.SISTEMAS)

    def fila_razonamiento(sistema, agentes, nivel):
        chico, grande = r14[sistema], rg.get(sistema)
        return [agentes, nivel, f"{datos.media_y_rango(chico['encontrados'])} de 14",
                datos.media_y_rango(chico["falsas_alarmas"]), datos.miles(datos.media(chico["tokens_entrada"])),
                f"{datos.media(chico['segundos']):.0f}"]

    p("<h2>Parte 4 — Extensión: cuánto razona el modelo, y código más difícil</h2>")
    p("<p>La extensión se eligió después de medir el baseline, para saber si antes de añadir agentes alcanzaba con que uno solo razonara más. Después se hicieron dos pruebas más por dudas que dejaron los resultados: qué pasa con cambios más difíciles y por qué algunas corridas tardaban tanto.</p>")

    p("<h3>4.1 — El nivel de razonamiento</h3>")
    p("<p>El modelo de la H200 acepta un parámetro <code>reasoning_effort</code> que le indica cuánto &quot;pensar&quot; antes de responder. Todo el taller corre con <code>low</code>. Aquí se cambia solo ese valor, con el mismo golden set.</p>")
    p(tabla(["agentes", "razonamiento", "encontrados, 14 casos", "hallazgos en casos limpios", "tokens de entrada", "segundos"], [
        fila_razonamiento("baseline", "uno", "bajo"),
        fila_razonamiento("baseline_razonamiento_medio", "uno", "medio"),
        fila_razonamiento("baseline_razonamiento_alto", "uno", "alto"),
        fila_razonamiento("multiagente", "siete", "bajo"),
        fila_razonamiento("multiagente_razonamiento_alto", "siete", "alto"),
    ], numericas=(2, 3, 4, 5)))
    medio, base, multi = r14["baseline_razonamiento_medio"], r14["baseline"], r14["multiagente"]
    p(f"<p>Con razonamiento medio, un solo agente encontró los 14 problemas en sus tres corridas, sin reportar nada en los casos que estaban bien, usando {datos.dec(datos.media(medio['tokens_entrada']) / datos.media(base['tokens_entrada']))} veces los tokens del baseline. Eso sí, es el más lento ({datos.media(medio['segundos']):.0f} segundos contra {datos.media(multi['segundos']):.0f} del multiagente), porque al razonar el modelo escribe mucho más. El nivel alto no fue mejor que el medio. En el multiagente subir el razonamiento no encontró más y sí hizo que reportara más en los casos que estaban bien. Al inicio yo había descartado el nivel medio por una sola llamada de prueba, y al medirlo bien resultó ser el mejor para un agente único.</p>")

    p("<h3>4.2 — Cambios más difíciles</h3>")
    p("<p>Los 14 casos son cambios de pocas líneas. Para ver qué pasa cuando el cambio es más grande o tiene más dependencias entre sus piezas se construyeron tres casos más, sobre la misma mini tienda. Van en un conjunto aparte (<code>golden_set_grande.json</code>) para no alterar el examen de 14.</p>")
    p(tabla(["caso", "qué es", "problemas", "líneas añadidas"], [
        ["G01", "PR grande: cinco de los cambios pequeños (C03, C06, C08, C09, C10) juntos en un solo parche", "6", "74"],
        ["G02", "PR grande: otros cuatro (C04, C05, C07, C11) juntos", "5", "56"],
        ["G03", "Caso complejo: un módulo nuevo de precios con una jerarquía de clases (método plantilla y subclases), un contenedor que inyecta las dependencias y una función con caché", "3", "213"],
    ], numericas=(2, 3)))
    p("<p>En G03 los bugs dependen de cómo se conectan las piezas. Una subclase sobrescribe el método plantilla y se salta el tope que la clase base garantiza. Un valor que debía consultarse cada vez se lee una sola vez al armar el contenedor. Y la clave de la caché no toma en cuenta uno de los dos argumentos. Con el parche aplicado, lint, tipos y tests pasan, y hay un test oculto por cada bug.</p>")
    p(_tabla_sistemas(tabla, datos, "grande"))
    orden = ["baseline", "baseline_con_pistas", "baseline_razonamiento_medio", "baseline_razonamiento_alto", "multiagente", "sin_verificador", "sin_rag", "multiagente_razonamiento_alto"]
    bugs = datos.bugs_del_caso_complejo(orden)
    p("<p>El caso complejo, bug por bug (en cuántas de las tres corridas lo encontró cada sistema):</p>")
    p(tabla(["sistema", "herencia: se salta el método plantilla", "inyección: valor leído una sola vez", "caché: clave incompleta"],
            [[nombres[s], f"{b[0]} de {b[3]}", f"{b[1]} de {b[3]}", f"{b[2]} de {b[3]}"] for s, b in bugs.items() if b[3]], numericas=(1, 2, 3)))
    gb, gm, gmed = rg["baseline"], rg["multiagente"], rg["baseline_razonamiento_medio"]
    p(f"<p>En estos casos la diferencia sí es grande: el baseline encuentra {datos.dec(datos.media(gb['encontrados']))} de 14 y el multiagente {datos.dec(datos.media(gm['encontrados']))}. Casi toda está en el caso complejo, donde ningún agente único con razonamiento bajo o alto encontró el bug de herencia. Juntar muchos cambios simples (G01 y G02) afecta menos que tener que seguir varias piezas para entender el problema (G03).</p>")
    p(f"<p>Pero un solo agente con razonamiento medio también encontró los tres bugs de G03 en sus tres corridas, con {datos.miles(datos.media(gmed['tokens_entrada']))} tokens contra {datos.miles(datos.media(gm['tokens_entrada']))} del multiagente. Su promedio es más bajo ({datos.dec(datos.media(gmed['encontrados']))} de 14) solo por la corrida en la que perdió todos los hallazgos de G01, que es el tercer caso de 2.c. Estos resultados apuntan a que repartir el trabajo ayuda más cuando el código es más complejo, pero no alcanzan para afirmarlo, porque son tres casos que escribí yo y G03 añade archivos completos, que es menos común que modificar funciones.</p>")

    p("<h3>4.3 — El tiempo, y las llamadas que no devuelven nada</h3>")
    t_base, t_multi = datos.segundos_por_caso("baseline", "grande"), datos.segundos_por_caso("multiagente", "grande")
    t14_base, t14_multi = datos.segundos_por_caso("baseline"), datos.segundos_por_caso("multiagente")
    prom = lambda valores: sum(valores) / len(valores)  # noqa: E731
    filas = [["Un caso de los 14 (promedio)", f"{prom([x for v in t14_base.values() for x in v]):.0f}", f"{prom([x for v in t14_multi.values() for x in v]):.0f}", "—"]]
    for caso in ("G01", "G02", "G03"):
        filas.append([caso, f"{prom(t_base[caso]):.0f}", f"{prom(t_multi[caso]):.0f}", f"{max(t_multi[caso]):.0f}"])
    p("<p>El sistema multiagente también tarda bastante más, sobre todo en los casos difíciles.</p>")
    p(tabla(["caso", "baseline, segundos", "multiagente, segundos", "multiagente, peor corrida"], filas, numericas=(1, 2, 3)))
    p("<p>Me llamó la atención porque los cambios no son grandes y un agente solo recibe el diff y abre dos o tres archivos. Al revisar las trazas, la causa principal eran llamadas en las que el modelo gasta todos sus tokens de salida razonando y no devuelve nada, que es lo mismo que ya había pasado en la Parte 0.</p>")
    filas = []
    for etiqueta, prefijo in (("Baseline, 14 casos", "baseline"), ("Multiagente, 14 casos", "multiagente"), ("Baseline, casos difíciles", "baseline_grande"),
                              ("Un agente con razonamiento medio, casos difíciles", "baseline_razonamiento_medio_grande"),
                              ("Multiagente, casos difíciles", "multiagente_grande"), ("Multiagente con razonamiento alto, casos difíciles", "multiagente_razonamiento_alto_grande")):
        v = datos.llamadas_vacias(prefijo)
        filas.append([etiqueta, v["llamadas"], v["vacias"], f"{v['seg_vacias']:.0f}", f"{100 * v['seg_vacias'] / v['seg_modelo']:.0f} %", f"{v['mas_lenta']:.0f}"])
    p(tabla(["corridas (suma de las tres)", "llamadas al modelo", "vacías", "segundos en llamadas vacías", "parte del tiempo de modelo", "llamada más lenta, s"], filas, numericas=(1, 2, 3, 4, 5)))
    p("<p>En los casos pequeños casi no pasa, pero en los difíciles estas llamadas se llevan más del 40 % del tiempo, y al multiagente le afecta más porque hace unas diez veces más llamadas. Había tres decisiones mías que estaban mal: subí el cupo de salida a 8 192 tokens cuando la primera llamada salió vacía, el reintento repetía la misma llamada, y no había un límite de tiempo por llamada.</p>")
    antes, despues = datos.llamadas_vacias("multiagente_grande"), datos.llamadas_vacias("multiagente_grande_cupo4096")
    p(f"<p>Lo corregí con menos tokens de salida por llamada, un máximo de 60 segundos por llamada y un reintento con el nivel de razonamiento más bajo, y volví a medir el multiagente con los tres casos difíciles. La llamada más lenta bajó de {antes['mas_lenta']:.0f} a {despues['mas_lenta']:.0f} segundos, pero las llamadas vacías siguieron apareciendo ({antes['vacias']} antes y {despues['vacias']} después).</p>")
    p("<p>O sea que el arreglo solo limita cuánto puede tardar una llamada, no evita que salga vacía. Los demás sistemas no se volvieron a medir con este cambio.</p>")


def conclusiones(p, **k):
    p("<h2>Conclusiones</h2>")
    p("<ol>"
      "<li>En cambios pequeños, varios agentes encontraron uno o dos problemas más que uno solo, que es lo mismo que cambia entre dos corridas del mismo sistema.</li>"
      "<li>En código más complejo la diferencia fue grande con razonamiento bajo o alto. Con razonamiento medio, un solo agente también encontró los bugs del caso complejo.</li>"
      "<li>Por eso, antes de añadir agentes conviene mejorar el que ya se tiene, con mejores instrucciones y más razonamiento. Cuesta menos tokens, aunque no es más rápido.</li>"
      "<li>El sistema multiagente aporta dos cosas: cita mejor la regla que se incumple y no pierde toda la revisión si una llamada falla. A cambio usa cinco veces más tokens y a veces reporta de más.</li>"
      "<li>De sus piezas, el RAG valió la pena y el verificador no.</li>"
      "<li>Varias conclusiones que tuve en el camino resultaron falsas. Lo que permitió verlo fue tener las trazas, repetir las mediciones y comparar siempre contra un control.</li>"
      "</ol>")


def parte5(p, datos, **k):
    r = datos.resumen_por_sistema()
    base, multi = r["baseline"], r["multiagente"]
    tin_b, tin_m = datos.media(base["tokens_entrada"]), datos.media(multi["tokens_entrada"])
    ll_b, ll_m = datos.media(base["llamadas"]), datos.media(multi["llamadas"])
    c = datos.calibracion()
    peor_pasos = max(c["pasos"]["baseline"])
    p("<h2>Parte 5 — Reflexión</h2>")
    p("<p><b>1. ¿En qué es un agente basado en objetivos y en qué no?</b> Se parece en que busca llegar a un resultado, que es entregar un review, y elige sus acciones según lo que va viendo. Nadie le dice qué archivo leer ni qué buscar. Pero el objetivo no está escrito en ningún lugar que el programa pueda comprobar. Está como texto en el prompt (<code>agentes/prompts.py</code>) y no hay una prueba que diga que ya se cumplió. Dentro del bucle el que decide que terminó es el modelo, cuando deja de pedir herramientas (la función <code>siguiente</code> en <code>agentes/bucle.py</code>), o un freno que lo corta. Tampoco hace un plan, decide un paso a la vez. Lo que sí decide el código es qué se publica, con <code>comprobar_en_codigo</code> y la revisión del informe en <code>agentes/sintetizador.py</code>.</p>")
    p(f"<p><b>2. Con <code>resultados/</code> delante.</b> En los mismos 14 casos, el baseline usó en promedio {datos.miles(tin_b)} tokens de entrada en {ll_b:.0f} llamadas y el sistema multiagente {datos.miles(tin_m)} en {ll_m:.0f}. O sea, {datos.dec(tin_m / tin_b)} veces más tokens con {datos.dec(ll_m / ll_b)} veces más llamadas. Si duplicara el tope de pasos de 12 a 24, en el peor caso los tokens de entrada no se duplicarían sino que crecerían hasta casi cuatro veces, porque en cada paso se reenvía todo el historial. En mis corridas no cambiaría nada, porque el agente más ocupado del baseline hizo como máximo {peor_pasos} llamadas y no llega al tope. Además el presupuesto de tokens es un freno aparte, así que lo que cambiaría es cuál de los dos salta primero si una corrida se descontrola.</p>")
    p("<p><b>3. Un despliegue que hace daño.</b> El siguiente paso de este trabajo es un agente que aplica parches y hace commits en el repositorio de mi trabajo. Ahí el daño sería real: código incorrecto en una rama compartida, o un PR de otra persona con un test malicioso que <code>correr_checks</code> ejecuta. En el servidor pondría lo que aquí sí protegió, que son los comandos en una lista cerrada, el proceso sin variables de entorno y sin red, la escritura limitada a una copia y las comprobaciones en código antes de cualquier modelo. A una persona le dejaría aprobar el plan y cada commit, como una pausa del grafo. La Parte 0 mostró lo que solo parecía proteger: los tests en verde (0.c) y pedirle al modelo en el prompt que no invente (0.a).</p>")


def evolucion(p, tabla, **k):
    p("<h2>Cómo se hizo el trabajo</h2>")
    p("<p>El trabajo no salió al primer intento. Se siguió la regla del curso de hacer un baseline, medirlo, extenderlo y volver a medir, y casi todas las mediciones obligaron a cambiar algo. La tabla resume ese recorrido en orden, y el resto del informe sigue ese mismo orden.</p>")
    p(tabla(["paso", "qué se hizo", "qué mostró la medición", "qué se cambió por eso"], [
        ["1", "Parte 0, antes de construir", "El modelo gastaba todos sus tokens razonando y devolvía una respuesta vacía", "Se limitó el razonamiento y se añadió un reintento"],
        ["2", "Primer diseño, con cuatro dimensiones y un RAG de 12 reglas", "Faltaban clean code y eficiencia, y con tan pocas reglas el RAG casi no hacía falta", "Cinco dimensiones y un índice de 206 fragmentos con documentación descargada"],
        ["3", "Baseline y golden set de 14 casos", "11 de 14. Fallaba en código sin uso, eficiencia e impacto", "Se escribieron los cinco reviewers pensando en esos fallos, lo cual fue un error que se corrige en el paso 6"],
        ["4", "Sistema multiagente", "11 de 14, porque el paso de unir perdía hallazgos", "Se corrigió el paso de unir y dio 14 de 14"],
        ["5", "Ablaciones sin verificador y sin RAG", "Sin RAG salían corridas incompletas", "Era por los prompts, que seguían pidiendo una herramienta que ya no existía. Se corrigieron"],
        ["6", "Revisión de la forma de medir", "Los reviewers tenían mejores instrucciones que el baseline, y cada sistema se había medido con una versión distinta del código", "Un control con un agente único y las mismas instrucciones, y una medición final con el mismo commit"],
        ["7", "Medición final", "El mismo baseline dio 13 en vez de 11", "Tres corridas por sistema"],
        ["8", "Casos más difíciles", "El multiagente sí se separa del baseline, pero tarda demasiado", "Se encontró que el tiempo se iba en llamadas vacías y se pusieron límites"],
        ["9", "Razonamiento medio", "Un solo agente encuentra casi lo mismo que el multiagente", "Cambió la conclusión del taller"],
    ]))
    p("<p>Los casos de prueba también fueron cambiando. Los 14 casos pequeños sirvieron para ver en qué fallaba el baseline, pero después casi todos los sistemas los resolvían y ya no permitían diferenciarlos. Los dos PR grandes bajaron un poco al agente único. El caso que más sirvió fue el último, el complejo, porque fue el único donde los sistemas se separaron con claridad.</p>")


def limitaciones(p, tabla, **k):
    p("<h2>Limitaciones</h2>")
    p("<p>Los errores que cometí al medir están en la sección &quot;Cómo se hizo el trabajo&quot; y se corrigieron antes de la medición final. Aparte de eso, el trabajo tiene estas limitaciones:</p>")
    p("<ul>"
      "<li>El repositorio de prueba es pequeño y los casos difíciles son solo tres. No es lo mismo que un repositorio real.</li>"
      "<li>Solo hay dos casos correctos, así que casi no se mide cuándo el sistema reporta algo que no es un problema. Los hallazgos no esperados de los otros casos no se revisaron uno por uno.</li>"
      "<li>Un acierto se cuenta por archivo, línea y palabras clave, así que un hallazgo poco preciso en la línea correcta puede contar.</li>"
      "<li>No se evaluó la calidad del informe escrito, solo los hallazgos. Por eso no se puede decir si el sintetizador aporta algo.</li>"
      "<li>El golden set, el sistema y los prompts los hice yo, y ajusté los prompts viendo los resultados del mismo golden set.</li>"
      "<li>Son solo tres corridas por sistema, y los tiempos son aproximados porque varios casos corren a la vez en una GPU compartida.</li>"
      "<li>Las llamadas vacías no están resueltas, y el último arreglo solo se midió en el multiagente con los casos difíciles. El resto de las cifras son anteriores a ese cambio.</li>"
      "</ul>")


def futuro(p, **k):
    p("<h2>Trabajo futuro</h2>")
    p("<p>El objetivo sigue siendo llevar <code>dev-cycle</code> completo a LangGraph. Lo que se midió aquí deja una forma de hacerlo: empezar con un agente bien ajustado y añadir otro solo cuando una medición muestre que ayuda, como pasó con el de impacto. Los siguientes pasos serían:</p>")
    p("<ol>"
      "<li>Probar con un repositorio real o más difícil, con casos guardados que no se miren al ajustar los prompts.</li>"
      "<li>Añadir la parte de <code>review-comments</code>. Un comentario de PR se puede tratar como un hallazgo que viene de fuera, y publicar la respuesta pasaría por una aprobación.</li>"
      "<li>Añadir el resto de <code>dev-cycle</code>: planificador, implementador y explicador, con este revisor dentro. Los dos puntos de aprobación de la skill pasarían a ser pausas del grafo.</li>"
      "<li>Usarlo en el proyecto Angular de mi trabajo, que solo necesita su propio <code>perfil.toml</code>.</li>"
      "</ol>")
    p("<p>En el sistema actual quedan mejoras claras: quitar el verificador o hacer que revise todos los hallazgos en una sola llamada, buscar las reglas una sola vez para todos los reviewers, corregir la instrucción del reviewer de clean code y poner un límite de tiempo por corrida.</p>")


def reproducibilidad(p, pre, RAIZ, **k):
    import subprocess

    commit = subprocess.run(["git", "log", "--format=%h", "-1", "--", "revisor"], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    p("<h2>Reproducibilidad</h2>")
    p(f"<p>El código medido es el del commit <code>{commit}</code> (último que toca <code>revisor/</code>). Versiones fijadas en <code>requirements.txt</code> (<code>langgraph==1.2.12</code>) y en <code>repo-prueba/package-lock.json</code>. Todas las tablas de este informe las genera <code>informe/generar_informe.py</code> leyendo <code>resultados/</code>. Ninguna cifra está escrita a mano.</p>")
    p(pre("""uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt
(cd repo-prueba && npm ci)
cp .env.example .env                                  # VPN de la USFQ conectada
.venv/bin/python -m revisor.rag.ingesta               # descarga las fuentes aprobadas del RAG
.venv/bin/python -m pytest -q                         # pruebas del sistema, sin modelo
.venv/bin/python -m evaluacion.parte0.c_tests_en_verde
.venv/bin/python -m evaluacion.evaluar --verificar    # la verdad de cada caso, ejecutada
.venv/bin/python -m evaluacion.evaluar --sistema multiagente --repeticion 1
.venv/bin/python -m evaluacion.forzar_frenos
.venv/bin/python informe/generar_informe.py"""))
    p("<p>Ninguna credencial aparece en el código, las trazas ni el repositorio: se leen de un <code>.env</code> que <code>.gitignore</code> excluye, las herramientas no pueden leerlo y los comandos corren sin las variables del entorno. Se buscaron patrones de clave en <code>resultados/</code> antes de cada commit.</p>")


SECCIONES = [portada, resumen, motivacion, que_se_construyo, evolucion, parte0, parte1, parte2a, parte2b, parte2c, parte3, parte4,
             conclusiones, parte5, limitaciones, futuro, reproducibilidad]
