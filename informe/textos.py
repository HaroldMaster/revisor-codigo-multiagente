"""El texto del informe, por secciones. Las cifras llegan de datos.py."""

from __future__ import annotations

import json

SEMBRADO = {
    "C01": "El impuesto se calcula antes de restar el descuento",
    "C02": "No deja reservar exactamente todo el stock (<code>&gt;=</code> en vez de <code>&gt;</code>)",
    "C03": "<code>&gt;</code> donde la descripción pide «10 incluidas», y un test que no afirma ningún valor",
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


def motivacion(p, tabla, **k):
    p("<h2>Motivación</h2>")
    p("<p>En el trabajo uso un conjunto de <i>skills</i> propias para Claude Code: <code>dev-cycle</code> (implementar un ticket), <code>review-custom</code> (revisar mis cambios antes de un commit) y <code>review-comments</code> (resolver el feedback de un PR). Cada una es una receta escrita en prosa que un solo agente sigue paso a paso. Funcionan, pero tienen tres límites que una receta no puede resolver:</p>")
    p(tabla(["límite", "qué pasa hoy", "qué haría falta"], [
        ["El flujo vive en el prompt", "Los pasos y los puntos de «STOP: pedir aprobación» son instrucciones. Que se cumplan depende de que el modelo las obedezca.", "Que el orden y las pausas estén en código."],
        ["Un solo agente hace todo", "El mismo agente que escribe el código lo revisa, con toda la conversación de cómo lo escribió delante.", "Que quien verifica no haya visto cómo se llegó al hallazgo."],
        ["Un solo proveedor", "Las skills solo corren en Claude Code, con los modelos de Anthropic.", "Poder cambiar de modelo sin reescribir nada."],
    ]))
    p("<p>El objetivo final es llevar <code>dev-cycle</code> completo a un grafo de LangGraph. Este taller es el primer paso: toma un solo paso de ese ciclo, el review (el 2.3 de <code>dev-cycle</code>, que hoy invoca a <code>review-custom</code>), lo construye como sistema multiagente independiente del proveedor y, sobre todo, lo mide contra la versión de un solo agente. La pregunta del taller es la misma que deja planteada el curso: si repartir el trabajo entre varios agentes mejora el resultado, y cuánto cuesta.</p>")


def que_se_construyo(p, tabla, datos, **k):
    p("<h2>Qué se construyó y con qué modelo</h2>")
    p("<p>Un programa que recibe un parche (el diff de un cambio, con su descripción) sobre un repositorio y devuelve un informe de review. Los hallazgos salen en una ficha fija: archivo, línea, dimensión, severidad, la línea de código copiada como evidencia y, si aplica, la regla que se incumple.</p>")
    p(tabla(["requisito de la opción libre", "cómo se cumple"], [
        ["Al menos 5 agentes", "7: cinco reviewers (bugs, reglas, clean code, eficiencia, impacto), un verificador y un sintetizador"],
        ["LangGraph y la H200", "<code>langgraph==1.2.12</code>, la versión del laboratorio; la H200 es el proveedor por defecto"],
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
    p("<p class='nota'>La opción libre no trae los scripts del laboratorio, así que se escribieron tres equivalentes para un revisor de código (<code>evaluacion/parte0/</code>). La 0.b y la 0.c no usan ningún modelo.</p>")
    p("<h3>0.a — El revisor que no mira</h3>")
    p("<p>El modelo recibe un diff con un bug y nada más: ni herramientas ni las reglas del repo. Se le pide un review con citas y después el código comprueba cada cita contra el repositorio. Se corrió con dos niveles de razonamiento.</p>")
    p(archivo("evaluacion/parte0/salidas/a.txt", quitar=("texto regla:", "evidencia:", "[ok]")))
    p("<p>Con razonamiento bajo el modelo devuelve cero hallazgos, aunque el cambio tiene un bug. Eso es peor que un error, porque una respuesta vacía con el formato correcto se lee como «todo está bien». Con razonamiento alto sí ve el bug, pero las reglas que cita no existen y el texto que pone como «literal» es inventado, igual que algunos de los archivos afectados. Para no tener que adivinar, el modelo necesita poder leer los archivos y preguntar por las reglas, y además alguien tiene que comprobar que lo que cita existe. Por eso el sistema tiene herramientas, RAG y comprobaciones en código.</p>")
    p("<p class='nota'>Salvedad: el prompt le pide al modelo el identificador y el texto de una regla que no puede conocer. Lo correcto habría sido que respondiera que no los tiene, pero la forma de la pregunta lo induce a inventar, y eso limita lo que esta prueba demuestra.</p>")
    p("<h3>0.b — El RAG plano que no trae la regla</h3>")
    p(archivo("evaluacion/parte0/salidas/b.txt"))
    p("<p>Aquí lo que falla es la búsqueda, no el modelo. La línea del diff y la regla que la prohíbe no comparten ninguna palabra, así que un índice por palabras da similitud cero y devuelve tres reglas cualesquiera. Con ese contexto el modelo citaría una regla que no aplica, o ninguna. En cambio, cuando se pregunta por la intención del cambio aparecen las dos reglas correctas. Por eso la descripción de <code>buscar_reglas</code> le pide al agente que pregunte por la intención y que no pegue código. Esta prueba usa TF-IDF. El sistema usa embeddings, que ayudan con este problema pero no lo quitan del todo.</p>")
    p("<h3>0.c — Los tests en verde que no prueban nada</h3>")
    p(archivo("evaluacion/parte0/salidas/c.txt"))
    p("<p>El cambio tiene un bug en un caso borde y llega con un test que solo revisa que la función exista. Si uno mira solo el código de salida, lo aprueba. Las dos comprobaciones en código lo rechazan sin usar ningún modelo: la primera ve que ninguna afirmación del test compara un valor, y la segunda rompe la función a propósito y los tests siguen pasando. La primera comprobación no detectaría un test que sí compara un valor pero el equivocado. Por eso la decisión final puede quedar en un modelo, pero después de estas comprobaciones.</p>")


def parte1(p, tabla, pre, pasos_de, datos, RAIZ, recolectar, cargar_perfil, tomllib, Counter, **k):
    p("<h2>Parte 1 — El revisor: baseline y capa multiagente</h2>")
    p("<h3>El bucle de un agente</h3>")
    p("<p>Todo agente del sistema es el mismo grafo de dos nodos (<code>revisor/agentes/bucle.py</code>). Lo que cambia de un agente a otro es su prompt y qué herramientas recibe.</p>")
    p(pre("""inicio → modelo ──pidió herramientas y quedan pasos──→ herramientas ─┐
            ↑─────────────────────────────────────────────────────────┘
            └── respondió, o saltó un freno ──→ fin → extraer los hallazgos en la ficha fija

Condición de parada: el modelo responde sin pedir herramientas, o salta un freno
(tope de pasos, presupuesto de tokens, repetición)."""))
    p("<h3>Baseline: un solo agente</h3>")
    p("<p><code>revisor/baseline.py</code>. Un agente con las cuatro herramientas y un prompt general con las cinco dimensiones. Es la skill <code>review-custom</code> llevada a LangGraph, con el mismo modelo que el resto: entre el baseline y el sistema multiagente solo cambia el reparto del trabajo.</p>")
    p(pre("inicio → preparar → reviewer único → informe → fin"))
    p("<h3>Capa multiagente</h3>")
    p(pre("""            ┌→ reviewer de bugs ───────┐
            ├→ reviewer de reglas ─────┤
preparar ───┼→ reviewer de clean code ─┼→ unir → comprobar ─┬→ verificar ─┬→ sintetizar → fin
            ├→ reviewer de eficiencia ─┤  (código) (código)  │  (modelo)   │
            └→ reviewer de impacto ────┘                     └─────────────┘
                                                   sin hallazgos pendientes"""))
    p(tabla(["agente", "qué hace", "herramientas"], [
        ["Reviewer de bugs", "Errores de lógica, casos borde, tests que no afirman nada", "leer, grep, checks"],
        ["Reviewer de reglas", "Incumplimientos de las normas; solo cita lo que el RAG le devolvió", "RAG, leer, grep"],
        ["Reviewer de clean code", "Código sin uso, duplicación, números mágicos", "grep, leer, RAG"],
        ["Reviewer de eficiencia", "Trabajo repetido dentro de bucles", "leer, RAG, grep"],
        ["Reviewer de impacto", "Lo que el cambio rompe fuera del diff", "grep, leer, checks"],
        ["Verificador", "Recibe solo la ficha, sin la conversación del reviewer, y la confirma, la deja como plausible o la descarta", "leer, grep, checks"],
        ["Sintetizador", "Redacta el informe con lo que quedó", "ninguna"],
    ]))
    p("<p>Los cinco reviewers corren en paralelo y no se ven entre sí: cada uno deja fichas en el estado compartido. Tres nodos son código sin modelo: <i>unir</i> quita los repetidos (mismo archivo, línea y dimensión); <i>comprobar</i> descarta un hallazgo si el archivo no existe, si la evidencia no es una copia literal de una línea, o si cita una regla que el RAG no devolvió en esa corrida; y, tras el sintetizador, una comprobación de procedencia rechaza el informe si menciona una ubicación o una regla que no viene de ningún hallazgo (a la segunda vez se entrega un informe armado por código).</p>")

    p("<h3>Las herramientas</h3>")
    p(tabla(["herramienta", "qué hace", "límite, fijado en el código de la herramienta"], [
        ["<code>leer_archivo</code>", "Un tramo de un archivo, con números de línea", "No sale de la raíz del repo ni lee <code>.env</code>; 200 líneas por llamada"],
        ["<code>grep_repo</code>", "Dónde se define o se usa algo, también fuera del diff", "Solo lectura; 40 coincidencias"],
        ["<code>buscar_reglas</code>", "RAG: los fragmentos de reglas y documentación más parecidos a una pregunta, con su id", "4 fragmentos de hasta 1 200 caracteres"],
        ["<code>correr_checks</code>", "Ejecuta lint, tests o tipos", "El modelo elige entre tres nombres; el comando lo pone el perfil. Entorno sin variables, 120 s"],
    ]))

    perfil = cargar_perfil(RAIZ / "repo-prueba")
    cuenta = Counter(f.fuente for f in recolectar(perfil))
    fuentes = tomllib.loads((RAIZ / "revisor/rag/fuentes_aprobadas.toml").read_text(encoding="utf-8"))["fuente"]
    descarga = {d["id"]: d for d in json.loads((RAIZ / "revisor/rag/fuentes/DESCARGA.json").read_text(encoding="utf-8"))}
    filas = [["Reglas del repo (<code>CLAUDE.md</code>, R1 a R16)", "propia", cuenta["CLAUDE.md"], "—"]]
    for f in fuentes:
        tipo = "repositorio comunitario" if f["id"] == "clean-code-typescript" else "documentación oficial"
        filas.append([f["motivo"].split(". Repositorio")[0], tipo, cuenta[f"docs/{f['id']}.md"], descarga[f["id"]]["fecha"]])
    p("<h3>El RAG</h3>")
    p(f"<p>El índice tiene {sum(cuenta.values())} fragmentos, uno por sección de cada documento, con embeddings de bge-m3 y búsqueda por coseno en memoria. No hay búsqueda web en vivo: un script descarga una lista cerrada de fuentes, aprobada a mano, y anota fecha y huella de cada una (<code>revisor/rag/fuentes/DESCARGA.json</code>). Un agente evaluado contra la web viva mediría la web.</p>")
    p(tabla(["fuente", "tipo", "fragmentos", "descargada"], filas, numericas=(2,)))
    p("<p class='nota'><code>clean-code-typescript</code> es una adaptación comunitaria del libro <i>Clean Code</i>, no documentación oficial. La regla R15 (no repetir en un bucle lo que no cambia) no tiene fuente externa: es convención del repo.</p>")

    p("<h3>Las seis correcciones, en este sistema</h3>")
    p(tabla(["corrección del enunciado", "dónde está"], [
        ["1. Catálogo con contrato", "<code>herramientas.py</code>: cada herramienta lleva nombre, descripción (qué devuelve, cuándo usarla y cuándo no) y esquema; viajan por function calling nativo"],
        ["2. Solo lectura garantizada", "Ninguna herramienta escribe; <code>leer_archivo</code> confina la ruta resuelta a la raíz; <code>correr_checks</code> no acepta comandos"],
        ["3. Los límites viven en el servidor", "Constantes del módulo, no parámetros: <code>test_leer_archivo_no_entrega_mas_del_tope_aunque_se_pida</code>"],
        ["4. Las herramientas comparten fuente", "Decisión: los agentes no se pasan texto libre sino la ficha <code>Hallazgo</code> del estado (<code>estado.py</code>). El verificador recibe la ficha y no la conversación"],
        ["5. Un error es una observación", "<code>bucle.py</code>: herramienta inexistente, argumentos inválidos o excepción vuelven al modelo como <code>{\"error\": …}</code>"],
        ["6. La traza se escribe en todo camino", "<code>traza.py</code>: cada evento va al disco en el momento; registra agente, modelo, tokens, latencia y error, y qué pidió, observó y respondió el modelo"],
    ]))
    p("<p>Contrato con el Taller 4: las clases de <code>revisor/sistemas.py</code> se instancian sin argumentos y <code>.run(pregunta)</code> devuelve <code>answer</code>, <code>trace</code>, <code>status</code>, <code>model</code> y <code>usage</code>. La pregunta es la ruta de un parche.</p>")

    p("<h3>Dos corridas</h3>")
    p("<p class='nota'>Caso C01 con el baseline, y caso C11 con el sistema multiagente (se muestran los primeros pasos; las trazas completas están en <code>resultados/trazas/</code>).</p>")
    p(pasos_de("resultados/trazas/baseline/C01.jsonl", maximo=12))
    p(pasos_de("resultados/trazas/multiagente/C11.jsonl", maximo=22))


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
    p("<p>Son 14 casos. Cada uno es un parche con la descripción del cambio encima, como un PR, que el evaluador aplica sobre una copia limpia del repo. Los genera <code>evaluacion/construir_casos.py</code>; las líneas esperadas se calculan buscando un texto en el archivo ya modificado, no se escriben a mano.</p>")
    p(tabla(["caso", "tipo", "dimensión", "qué se sembró", "cómo se demuestra", "lint, tipos y tests en verde"], filas))
    silenciosos = sum(1 for c in golden if c["tipo"] in ("simple", "multi", "adversarial") and verificacion[c["id"]]["checks_en_verde"] == "True")
    con_problema = sum(1 for c in golden if c["tipo"] != "negativo")
    p(f"<p>La verdad no es una etiqueta: <code>evaluar.py --verificar</code> la ejecuta. Para un bug, un test oculto que falla con el parche (y pasa sin él cuando el código ya existía); para una regla, un patrón en el archivo o un check que falla; para el código sin uso, que el símbolo aparezca una sola vez. Los 14 casos pasan esa comprobación. En {silenciosos} de los {con_problema} casos con problema, lint, tipos y tests quedan en verde con el problema dentro.</p>")
    p("<p>Un hallazgo cuenta como acierto si cae en el archivo y el rango de líneas esperados y, cuando el caso lo pide, menciona lo que debe (por ejemplo «descuento»). Aparte se cuenta si citó la regla correcta. Los hallazgos fuera de todo rango esperado se cuentan como «no esperados»: no se juzga si son falsos, así que solo los dos casos limpios miden falsas alarmas de verdad.</p>")


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
        fila = [caso]
        for sistema, _ in presentes:
            encontrados, esperados, hallazgos = aciertos[caso].get(sistema, [0, 0, 0])
            fila.append(f"{encontrados}/{esperados}" if esperados else f"{hallazgos} hallazgos")
        filas.append(fila)
    return tabla(["caso"] + [cortos[s] for s, _ in presentes], filas, numericas=tuple(range(1, len(presentes) + 1)))


def parte2b(p, tabla, datos, **k):
    p("<h3>2.b — Las métricas</h3>")
    p("<p>Todos los sistemas se midieron con el mismo golden set, el mismo modelo y el mismo commit, tres veces cada uno, porque el modelo no es determinista. Cada celda es el promedio de las tres corridas y, entre paréntesis, el mínimo y el máximo; un solo número significa que las tres dieron lo mismo. Las cifras salen de <code>resultados/resultados_&lt;sistema&gt;[_rN].csv</code>.</p>")
    p(_tabla_sistemas(tabla, datos))
    p("<p class='nota'>Baseline: un agente con un prompt general. «Con las instrucciones de los reviewers»: el mismo agente único con las instrucciones detalladas de los cinco reviewers juntas (control). Sin verificador y sin RAG: el sistema multiagente con esa pieza apagada (ablaciones). Razonamiento medio y alto: el parámetro <code>reasoning_effort</code> del modelo, que por defecto está en <code>low</code> (extensión, Parte 4). Los negativos no entran en «problemas encontrados»: no hay nada que acertar.</p>")
    p("<p>Aciertos por caso, sumando las tres corridas (3/3 es «lo encontró las tres veces»):</p>")
    p(_tabla_por_caso(tabla, datos))

    r = datos.resumen_por_sistema()
    m = lambda sistema, metrica: datos.media(r[sistema][metrica])  # noqa: E731
    p("<p>Lo que se ve en estas tablas:</p>")
    p("<ul>"
      f"<li>El sistema multiagente encontró los 14 problemas en todas sus corridas, y sus dos ablaciones también. El baseline quedó en {datos.dec(m('baseline', 'encontrados'))} de promedio, entre 11 y 13. Los casos que falla son tres (C09, C10 y C11), y el que más se repite es el C11, donde se cambia una utilidad y eso altera el impuesto en otro módulo.</li>"
      f"<li>Una parte de esa ventaja venía de las instrucciones y no de tener más agentes. El agente único con las instrucciones de los reviewers sube a {datos.dec(m('baseline_con_pistas', 'encontrados'))}. Y con razonamiento medio (Parte 4) un solo agente también encontró los 14 en sus tres corridas.</li>"
      f"<li>Donde más se nota la diferencia es en el costo. El multiagente usa {datos.dec(m('multiagente', 'tokens_entrada') / m('baseline', 'tokens_entrada'))} veces los tokens de entrada del baseline y tarda unas {m('multiagente', 'segundos') / m('baseline', 'segundos'):.0f} veces más.</li>"
      f"<li>El multiagente cita mejor la regla que se incumple ({datos.dec(m('multiagente', 'citas_correctas'))} de 11, contra {datos.dec(m('baseline', 'citas_correctas'))} del baseline). Tiene sentido, porque uno de sus reviewers solo se dedica a preguntar por las reglas.</li>"
      f"<li>En cambio, el multiagente a veces reporta algo en los dos casos que estaban bien ({datos.dec(m('multiagente', 'falsas_alarmas'))} hallazgos de promedio), y los agentes únicos nunca lo hicieron. Esto se revisa en 2.c.</li>"
      f"<li>El verificador no valió lo que cuesta. Sin él se encontró lo mismo usando un {100 * (1 - m('sin_verificador', 'tokens_entrada') / m('multiagente', 'tokens_entrada')):.0f} % menos de tokens. Lo único a su favor es que hay un poco menos de hallazgos no esperados ({datos.dec(m('multiagente', 'no_esperados'))} contra {datos.dec(m('sin_verificador', 'no_esperados'))}), pero esa diferencia es muy pequeña para darla por cierta.</li>"
      f"<li>El RAG no ayudó a encontrar más problemas, pero sí a citarlos. Sin RAG se encuentran los mismos 14, pero no se cita ninguna regla, y los hallazgos no esperados suben de {datos.dec(m('multiagente', 'no_esperados'))} a {datos.dec(m('sin_rag', 'no_esperados'))}. Lo que pasa es que, sin las reglas escritas, los agentes las deducen leyendo el código y a veces deducen reglas que no existen.</li>"
      "<li>Hay que tener cuidado con las diferencias pequeñas. Con tres corridas, que un sistema encuentre un caso más que otro no dice mucho, porque el mismo baseline varió entre 11 y 13. Además, estos 14 casos son cambios pequeños sobre un repositorio pequeño. En la Parte 4 se prueba con cambios más difíciles.</li>"
      "</ul>")
    uso = datos.uso_por_agente("multiagente")
    total = sum(v["tokens_entrada"] for v in uso.values())
    filas = [[agente, f"{v['llamadas']:.0f}", datos.miles(v["tokens_entrada"]), f"{100 * v['tokens_entrada'] / total:.0f} %", datos.miles(v["tokens_salida"])]
             for agente, v in sorted(uso.items(), key=lambda kv: -kv[1]["tokens_entrada"])]
    p("<p>Tokens por agente en el sistema multiagente (promedio por corrida de los 14 casos):</p>")
    p(tabla(["agente", "llamadas", "tokens de entrada", "parte del total", "tokens de salida"], filas, numericas=(1, 2, 3, 4)))


def parte2c(p, pasos_de, **k):
    p("<h3>2.c — Análisis de fallos</h3>")
    p("<p>Se eligieron los tres peores resultados del sistema entregado y de su baseline, y para cada uno se señala la pieza a la que apunta la traza.</p>")
    p("<p><b>1. Caso N01 con el sistema multiagente: reporta algo en un cambio que estaba bien.</b> El cambio añade un método <code>cantidadTotal()</code> con sus tests. En dos de las tres corridas el reviewer de clean code reportó que el método «no tiene ningún consumidor en producción», y el verificador lo confirmó.</p>")
    p(pasos_de("resultados/trazas/multiagente/N01.jsonl", maximo=40, solo=("reviewer_clean_code", "verificador")))
    p("<p>Lo que dice el hallazgo es verdad, porque todavía nadie llama a ese método. El problema está en la instrucción que le di al reviewer de clean code. Le pedí reportar todo lo exportado que «solo aparece donde se define», y esa instrucción la escribí pensando en el caso C09. Aquí se aplica a un método nuevo que viene con sus tests, que es como empieza cualquier funcionalidad. De este caso aprendí dos cosas. La primera es que el verificador revisa si lo que se afirma es verdad, pero no si eso es realmente un problema. La segunda es que el caso que yo consideraba «limpio» no lo era del todo según la regla R10 como la escribí, así que también hay que corregir el golden set. La parte que falla es el prompt de ese reviewer, y también el propio caso.</p>")
    p("<p><b>2. Caso C11 con el baseline: no ve que el cambio afecta a otro módulo.</b> El cambio hace que <code>porcentajeDe</code> trunque en vez de redondear. La descripción habla solo de descuentos, pero esa función también se usa para calcular el impuesto de los pedidos.</p>")
    p(pasos_de("resultados/trazas/baseline/C11.jsonl", maximo=12))
    p("<p>El agente sí tuvo la información que necesitaba, porque su búsqueda le devolvió el uso en <code>pedidos.ts</code> donde se calcula el impuesto. Pero después corrió los tests, vio que pasaban y concluyó que el cambio «es correcto y está bien hecho». Es lo mismo que mostró la Parte 0.c, pero ahora dentro del agente: como los tests pasaron, dio el cambio por bueno. La parte que falla aquí es el modelo, y también que nadie tenía como tarea revisar el impacto. En el sistema multiagente, el reviewer de impacto solo se dedica a ver qué pasa con cada lugar donde se usa lo que cambió, y encontró este caso en todas las corridas.</p>")
    p("<p><b>3. Caso G01 con un agente y razonamiento medio, segunda corrida: se pierde toda la revisión.</b> Es el peor resultado de todas las mediciones. Encontró 0 de 6 problemas en un PR grande que el mismo sistema resolvió completo en las otras dos corridas.</p>")
    p(pasos_de("resultados/trazas/baseline_razonamiento_medio_grande_r2/G01.jsonl", maximo=16, errores=True))
    p("<p>El agente sí hizo la revisión: leyó los archivos y resumió lo que había encontrado. El fallo fue al final, cuando se le piden los hallazgos en el formato fijo. El modelo gastó dos veces los 8 192 tokens que tenía de salida solo razonando y no devolvió nada. El sistema anotó el error en la traza, pero entregó «sin hallazgos» con estado <code>completed</code>, o sea, una revisión vacía que parece una revisión de un cambio sin problemas. Es el mismo tipo de falla silenciosa de la Parte 0.a, y solo me di cuenta porque revisé la traza. La parte que falla es el modelo y también el sistema, que no avisaba. Se corrigieron dos cosas (Parte 4): ahora en esa situación el informe sale con un aviso y con estado <code>incompleto</code>, y el reintento ya no repite la misma llamada. Este caso también muestra una ventaja del sistema multiagente: si a uno de sus siete agentes le pasa esto, se pierde una parte de la revisión, pero no toda.</p>")


def parte3(p, tabla, archivo, datos, **k):
    p("<h2>Parte 3 — Frenos, probados haciéndolos saltar</h2>")
    p("<p>Cuatro frenos, todos en código y fuera del control del modelo. Se forzaron con un modelo de guion (<code>evaluacion/guion.py</code>) que se porta mal a propósito, así que no gastaron nada: <code>python -m evaluacion.forzar_frenos</code>. Hay una traza por freno en <code>resultados/frenos/</code>.</p>")
    p(tabla(["freno", "dónde", "cómo se forzó", "qué pasó"], [
        ["Tope de pasos", "<code>bucle.py</code>", "El guion pide una búsqueda distinta en cada turno y nunca termina; límite 4", "Corta al cuarto paso; cada llamada pendiente recibe su resultado y el agente entrega el hallazgo que tenía"],
        ["Presupuesto de tokens", "<code>traza.py</code>, antes de cada llamada", "Cada turno cuesta 30 000 tokens; límite 120 000 con 35 000 de reserva", "Corta a los 91 500; la reserva alcanza para extraer el hallazgo"],
        ["Detector de repetición", "<code>bucle.py</code>", "El guion pide siempre la misma búsqueda", "La tercera llamada idéntica no se ejecuta y el agente se detiene"],
        ["Tiempo máximo de un check", "<code>herramientas.py</code>", "El comando de tests duerme 60 s; límite 2 s", "Se mata el grupo de procesos; el modelo recibe el error como observación y sigue"],
    ]))
    p(archivo("resultados/frenos/salida.txt", desde="=== Presupuesto", hasta="=== Detector"))
    p("<p>En los cuatro casos el informe sale con un aviso arriba y la corrida queda con estado <code>incompleto</code>; nunca devuelve una respuesta vacía. La reserva del presupuesto existe para eso: el trabajo normal puede gastar hasta el límite menos la reserva, y solo los pasos de cierre (extraer los hallazgos y redactar) pueden usar el resto. Sin ella, una corrida que agota el presupuesto pierde todo lo que gastó.</p>")
    p("<p>Estos frenos tienen límites. El presupuesto se revisa antes de cada llamada, cuando todavía no se sabe cuánto va a costar, así que puede pasarse por una llamada. El detector de repetición solo detecta la llamada idéntica. No detecta a un agente que alterna entre dos llamadas, ni al que cambia un poco los argumentos cada vez. Para esos casos queda el tope de pasos. No hay un freno de confirmación humana porque ninguna herramienta escribe, pero sería obligatorio cuando el sistema aplique parches (ver Trabajo futuro).</p>")

    c = datos.calibracion()
    filas = []
    for sistema, nombre in datos.SISTEMAS:
        if sistema in c["pasos"]:
            pasos, tokens = sorted(c["pasos"][sistema]), sorted(c["tokens"][sistema])
            filas.append([nombre, len(pasos), pasos[len(pasos) // 2], pasos[-1],
                          datos.miles(tokens[len(tokens) // 2]), datos.miles(tokens[-1])])
    checks = c["checks"]
    p("<h3>De dónde salen los límites</h3>")
    p("<p>Los valores de los límites los puse antes de medir nada y sin apoyarme en ninguna referencia. Eso es una debilidad del trabajo, porque un límite debería salir de una fuente o de una medición. Después de medir los comparé con lo que usaron las corridas de verdad:</p>")
    p(tabla(["sistema", "corridas", "llamadas del reviewer más ocupado: mediana", "máximo", "tokens por corrida: mediana", "máximo"], filas, numericas=(1, 2, 3, 4, 5)))
    p(tabla(["límite", "valor", "con qué se contrasta", "veredicto"], [
        ["Pasos por agente", "12 (10 en los reviewers, 6 en el verificador)", "LangGraph 1.2.12 no pone un tope útil por defecto (<code>DEFAULT_RECURSION_LIMIT</code> = 10 007 en el paquete instalado): el tope es responsabilidad de quien escribe el agente. El máximo observado está en la tabla de arriba", "Razonable: deja margen sobre el peor caso sin permitir bucles largos"],
        ["Tokens por corrida", "400 000, con 30 000 de reserva", "No se encontró una recomendación externa con un número: depende del modelo y del costo. Solo queda la medición propia", "Demasiado holgado y mal planteado: es un solo límite para todos los sistemas. Debería ser por sistema, por ejemplo el doble de su peor caso"],
        ["Tiempo de un check", "120 s", f"Vitest 4.1.11 corta cada test a los 5 s por defecto. En {len(checks)} ejecuciones medidas el check tardó {datos.dec(checks[len(checks) // 2] / 1000)} s de mediana y {datos.dec(checks[-1] / 1000)} s de máximo", "El peor de los tres: sobra por dos órdenes de magnitud. Depende del repo revisado, así que debería estar en <code>perfil.toml</code>"],
        ["Repetición", "más de 2 llamadas idénticas", "Ninguna referencia: es criterio", "Saltó en corridas reales (abajo)"],
        ["Cupo de salida y tiempo por llamada", "4 096 tokens y 60 s (antes 8 192 y 180 s)", "Se midieron tres cupos sobre los casos difíciles (Parte 4.3)", "Faltaban como frenos: se añadieron al final, al ver llamadas de más de dos minutos que no devolvían nada"],
    ]))
    reales = [(s, f, a, n) for (s, f, a), n in c["frenos"].items()]
    if reales:
        p("<p>Además de los forzados, estos frenos saltaron solos en las corridas medidas:</p>")
        p(tabla(["sistema", "freno", "agente", "veces"], [[dict(datos.SISTEMAS).get(s, s), f, a, n] for s, f, a, n in sorted(reales)], numericas=(3,)))
    p("<p>Ni el presupuesto de tokens ni el tiempo máximo de un check se dispararon en una corrida medida, así que los resultados de la Parte 2 no dependen de sus valores. Sigue faltando un freno: un límite de tiempo para la corrida completa.</p>")


def parte4(p, tabla, datos, **k):
    r14, rg = datos.resumen_por_sistema(), datos.resumen_por_sistema("grande")
    nombres = dict(datos.SISTEMAS)

    def fila_razonamiento(sistema, agentes, nivel):
        chico, grande = r14[sistema], rg.get(sistema)
        return [agentes, nivel, f"{datos.media_y_rango(chico['encontrados'])} de 14",
                datos.media_y_rango(chico["falsas_alarmas"]), datos.miles(datos.media(chico["tokens_entrada"])),
                f"{datos.media(chico['segundos']):.0f}",
                f"{datos.media_y_rango(grande['encontrados'])} de 14" if grande else "—"]

    p("<h2>Parte 4 — Extensión: cuánto razona el modelo, y código más difícil</h2>")
    p("<p>La extensión se eligió después de medir el baseline. La pregunta era si, antes de añadir más agentes, alcanzaba con que un solo agente razonara más. Después se hicieron dos pruebas más, que salieron de dudas que dejaron los primeros resultados: qué pasa con cambios más difíciles, y por qué algunas corridas tardaban tanto.</p>")

    p("<h3>4.1 — El nivel de razonamiento</h3>")
    p("<p>El modelo de la H200 acepta un parámetro <code>reasoning_effort</code> que le indica cuánto «pensar» antes de responder. Todo el taller corre con <code>low</code>. Aquí se cambia solo ese valor, con el mismo golden set.</p>")
    p(tabla(["agentes", "razonamiento", "encontrados, 14 casos", "hallazgos en casos limpios", "tokens de entrada", "segundos", "encontrados, casos difíciles (4.2)"], [
        fila_razonamiento("baseline", "uno", "bajo"),
        fila_razonamiento("baseline_razonamiento_medio", "uno", "medio"),
        fila_razonamiento("baseline_razonamiento_alto", "uno", "alto"),
        fila_razonamiento("multiagente", "siete", "bajo"),
        fila_razonamiento("multiagente_razonamiento_alto", "siete", "alto"),
    ], numericas=(2, 3, 4, 5, 6)))
    medio, base, multi = r14["baseline_razonamiento_medio"], r14["baseline"], r14["multiagente"]
    p(f"<p>Con razonamiento medio, un solo agente encontró los 14 problemas en sus tres corridas y no reportó nada en los casos que estaban bien. Usó {datos.dec(datos.media(medio['tokens_entrada']) / datos.media(base['tokens_entrada']))} veces los tokens del baseline, mientras que el sistema multiagente usa {datos.dec(datos.media(multi['tokens_entrada']) / datos.media(base['tokens_entrada']))} veces. Lo malo es que es el más lento: sus 14 casos suman {datos.media(medio['segundos']):.0f} segundos, contra {datos.media(multi['segundos']):.0f} del multiagente. Esto pasa porque el tiempo depende de cuánto texto genera el modelo, y cuando razona escribe mucho más. El nivel alto no fue mejor que el medio y tuvo más hallazgos no esperados. En el multiagente, subir el razonamiento no ayudó a encontrar más y sí hizo que reportara más cosas en los casos que estaban bien. Creo que es porque cada reviewer tiene una tarea pequeña y no necesita razonar tanto. Al inicio yo había descartado el nivel medio por una sola llamada de prueba. Al medirlo bien, el resultado fue otro.</p>")

    p("<h3>4.2 — Cambios más difíciles</h3>")
    p("<p>Los 14 casos son cambios de pocas líneas. Para ver qué pasa cuando el cambio es más grande o tiene más dependencias entre sus piezas se construyeron tres casos más, sobre la misma mini tienda. Van en un conjunto aparte (<code>golden_set_grande.json</code>) para no alterar el examen de 14.</p>")
    p(tabla(["caso", "qué es", "problemas", "líneas añadidas"], [
        ["G01", "PR grande: cinco de los cambios pequeños (C03, C06, C08, C09, C10) juntos en un solo parche", "6", "74"],
        ["G02", "PR grande: otros cuatro (C04, C05, C07, C11) juntos", "5", "56"],
        ["G03", "Caso complejo: un módulo nuevo de precios con una jerarquía de clases (método plantilla y subclases), un contenedor que inyecta las dependencias y una función con caché", "3", "213"],
    ], numericas=(2, 3)))
    p("<p>En G03 los tres bugs no se ven leyendo una sola línea, porque dependen de cómo se conectan las piezas. En el primero, una subclase sobrescribe el método plantilla y con eso se salta el tope que la clase base garantiza. En el segundo, un valor que debía consultarse cada vez se lee una sola vez, cuando se arma el contenedor. En el tercero, la clave de la caché no toma en cuenta uno de los dos argumentos. Con el parche aplicado, lint, tipos y tests pasan. Hay tres tests ocultos, uno por cada bug, que demuestran que existen.</p>")
    p(_tabla_sistemas(tabla, datos, "grande"))
    orden = ["baseline", "baseline_con_pistas", "baseline_razonamiento_medio", "baseline_razonamiento_alto", "multiagente", "sin_verificador", "sin_rag", "multiagente_razonamiento_alto"]
    bugs = datos.bugs_del_caso_complejo(orden)
    p("<p>El caso complejo, bug por bug (en cuántas de las tres corridas lo encontró cada sistema):</p>")
    p(tabla(["sistema", "herencia: se salta el método plantilla", "inyección: valor leído una sola vez", "caché: clave incompleta"],
            [[nombres[s], f"{b[0]} de {b[3]}", f"{b[1]} de {b[3]}", f"{b[2]} de {b[3]}"] for s, b in bugs.items() if b[3]], numericas=(1, 2, 3)))
    gb, gm, gmed = rg["baseline"], rg["multiagente"], rg["baseline_razonamiento_medio"]
    p(f"<p>En estos casos la diferencia sí es grande. El baseline encuentra {datos.dec(datos.media(gb['encontrados']))} de 14 y el sistema multiagente {datos.dec(datos.media(gm['encontrados']))}. La mayor parte de la diferencia está en el caso complejo. Ningún agente único con razonamiento bajo o alto encontró el bug de herencia en ninguna corrida, y todas las versiones multiagente encontraron los tres bugs las tres veces. Juntar muchos cambios simples (G01 y G02) le afecta menos a un agente único que tener código donde hay que seguir varias piezas para entender el problema (G03).</p>")
    p(f"<p>Sin embargo, con razonamiento medio la diferencia se vuelve a reducir. Un solo agente con razonamiento medio también encontró los tres bugs de G03 en sus tres corridas, usando {datos.miles(datos.media(gmed['tokens_entrada']))} tokens contra {datos.miles(datos.media(gm['tokens_entrada']))} del multiagente. Su promedio ({datos.dec(datos.media(gmed['encontrados']))} de 14) es más bajo que el del multiagente por una sola corrida, en la que perdió todos los hallazgos de G01. Es el tercer caso que se explica en 2.c.</p>")
    p("<p>Con esto se puede decir que el sistema multiagente ayuda más cuando el problema no está en la línea que cambia, sino en cómo esa línea se relaciona con otras piezas. También aguanta mejor cuando una llamada al modelo falla. Pero un agente único con razonamiento medio llega casi al mismo resultado con una quinta parte de los tokens. Los datos van en la dirección de que repartir el trabajo ayuda más mientras más complejo es el código, pero no alcanzan para afirmarlo. Son solo tres casos, los escribí yo para el taller, y G03 añade archivos completos, que es menos común en un PR que modificar funciones.</p>")

    p("<h3>4.3 — El tiempo, y las llamadas que no devuelven nada</h3>")
    t_base, t_multi = datos.segundos_por_caso("baseline", "grande"), datos.segundos_por_caso("multiagente", "grande")
    t14_base, t14_multi = datos.segundos_por_caso("baseline"), datos.segundos_por_caso("multiagente")
    prom = lambda valores: sum(valores) / len(valores)  # noqa: E731
    filas = [["Un caso de los 14 (promedio)", f"{prom([x for v in t14_base.values() for x in v]):.0f}", f"{prom([x for v in t14_multi.values() for x in v]):.0f}", "—"]]
    for caso in ("G01", "G02", "G03"):
        filas.append([caso, f"{prom(t_base[caso]):.0f}", f"{prom(t_multi[caso]):.0f}", f"{max(t_multi[caso]):.0f}"])
    p("<p>El sistema multiagente no solo usa más tokens, también tarda bastante más. En los casos difíciles la diferencia es todavía mayor.</p>")
    p(tabla(["caso", "baseline, segundos", "multiagente, segundos", "multiagente, peor corrida"], filas, numericas=(1, 2, 3)))
    p("<p>Me llamó la atención que tardara tanto, porque los cambios no son grandes (el mayor tiene 213 líneas) y un agente no lee todo el repositorio, solo recibe el diff y abre dos o tres archivos. Revisé las trazas llamada por llamada y la causa principal era otra. Hay llamadas en las que el modelo gasta todos los tokens de salida razonando y no devuelve nada. Es el mismo comportamiento que ya había aparecido en la Parte 0, y vuelve a aparecer cuando la entrada es más larga.</p>")
    filas = []
    for etiqueta, prefijo in (("Baseline, 14 casos", "baseline"), ("Multiagente, 14 casos", "multiagente"), ("Baseline, casos difíciles", "baseline_grande"),
                              ("Un agente con razonamiento medio, casos difíciles", "baseline_razonamiento_medio_grande"),
                              ("Multiagente, casos difíciles", "multiagente_grande"), ("Multiagente con razonamiento alto, casos difíciles", "multiagente_razonamiento_alto_grande")):
        v = datos.llamadas_vacias(prefijo)
        filas.append([etiqueta, v["llamadas"], v["vacias"], f"{v['seg_vacias']:.0f}", f"{100 * v['seg_vacias'] / v['seg_modelo']:.0f} %", f"{v['mas_lenta']:.0f}"])
    p(tabla(["corridas (suma de las tres)", "llamadas al modelo", "vacías", "segundos en llamadas vacías", "parte del tiempo de modelo", "llamada más lenta, s"], filas, numericas=(1, 2, 3, 4, 5)))
    p("<p>En los casos pequeños casi no pasa. En los difíciles estas llamadas se llevan más del 40 % del tiempo, y al sistema multiagente le afecta más porque hace unas diez veces más llamadas. Detrás había tres decisiones mías que estuvieron mal. Cuando la primera llamada salió vacía subí el cupo de salida a 8 192 tokens, y con eso el fallo solo tardaba más en aparecer. El reintento repetía la misma llamada sin cambiar nada. Y no había un límite de tiempo que cortara una llamada de dos minutos y medio.</p>")
    filas = []
    for etiqueta, sufijo, cupo in (("Como se midió todo lo anterior", "", "8 192"), ("Con el arreglo", "arreglo", "2 048"), ("Con el arreglo y cupo intermedio (valor que se deja)", "cupo4096", "4 096")):
        prefijo = "multiagente_grande" + (f"_{sufijo}" if sufijo else "")
        v = datos.llamadas_vacias(prefijo)
        tiempos = datos.segundos_por_caso("multiagente", "grande", sufijo)
        por_corrida = [sum(tiempos[c][i] for c in tiempos) for i in range(len(next(iter(tiempos.values()))))]
        filas.append([etiqueta, cupo, ", ".join(str(n) for n in datos.encontrados_con_etiqueta("multiagente", "grande", sufijo)),
                      f"{min(por_corrida):.0f} a {max(por_corrida):.0f}", f"{v['mas_lenta']:.0f}", v["vacias"]])
    p("<p>Lo corregí en un commit aparte y volví a medir el sistema multiagente con los tres casos difíciles. Los cambios fueron un cupo de salida más bajo, que se puede configurar por rol, un máximo de 60 segundos por llamada, y un reintento que usa siempre el nivel de razonamiento más bajo.</p>")
    p(tabla(["versión", "cupo de salida", "encontrados de 14, por corrida", "segundos por corrida", "llamada más lenta, s", "llamadas vacías"], filas, numericas=(1, 3, 4, 5)))
    p("<p>El arreglo solo resuelve una parte del problema. Ahora ninguna llamada pasa de 60 segundos y el tiempo por corrida es más parejo, pero las llamadas vacías siguen apareciendo igual de seguido. Además, si el cupo es muy bajo algún reviewer se queda sin espacio para responder. Al probarlo también vi que la opción que debía apagar el razonamiento en este servidor no lo apaga. Lo único que lo reduce de verdad es el nivel bajo, que ya estaba puesto. Los demás sistemas no se volvieron a medir con este cambio.</p>")


def conclusiones(p, **k):
    p("<h2>Conclusiones</h2>")
    p("<ol>"
      "<li>En cambios pequeños, usar varios agentes no encontró mucho más que usar uno. La diferencia fue de uno o dos casos de 14, que es lo mismo que cambia entre dos corridas del mismo sistema. Y desaparece si el agente único razona un poco más.</li>"
      "<li>En código donde hay que seguir varias piezas para ver el problema, sí hubo diferencia. Con razonamiento bajo o alto, ningún agente único encontró el bug de herencia del caso complejo, y el sistema multiagente lo encontró siempre. Con razonamiento medio, un solo agente también lo encontró.</li>"
      "<li>Antes de añadir agentes conviene mejorar el que ya se tiene. Con mejores instrucciones y razonamiento medio, un solo agente llegó casi al mismo resultado con menos de la mitad de los tokens. Eso sí, no fue más rápido, porque razonar más también toma más tiempo.</li>"
      "<li>Lo que sí aporta el sistema multiagente es que cita mejor la regla que se incumple y que no pierde toda la revisión cuando una llamada falla. A cambio usa cinco veces más tokens, tarda más y a veces reporta algo en cambios que estaban bien.</li>"
      "<li>De las piezas del sistema, el RAG sí valió la pena y el verificador no. El RAG permite citar la regla y reduce los hallazgos de más. El verificador revisa si lo que se afirma es verdad, pero no si es un problema, y usa un tercio de los tokens.</li>"
      "<li>Lo que más ayudó a no llegar a conclusiones equivocadas fue lo que no depende del modelo: las comprobaciones en código, las trazas y volver a medir con un control. Varias conclusiones que tuve en el camino resultaron falsas cuando las revisé así.</li>"
      "</ol>")


def parte5(p, datos, **k):
    r = datos.resumen_por_sistema()
    base, multi = r["baseline"], r["multiagente"]
    tin_b, tin_m = datos.media(base["tokens_entrada"]), datos.media(multi["tokens_entrada"])
    ll_b, ll_m = datos.media(base["llamadas"]), datos.media(multi["llamadas"])
    c = datos.calibracion()
    peor_pasos = max(c["pasos"]["baseline"])
    p("<h2>Parte 5 — Reflexión</h2>")
    p("<p><b>1. ¿En qué es un agente basado en objetivos y en qué no?</b> Se parece a un agente basado en objetivos en que busca llegar a un resultado (entregar un review) y elige sus acciones según lo que va viendo. Nadie le dice qué archivo leer ni qué buscar. Pero no lo es del todo, porque el objetivo no está escrito en ningún lugar que el programa pueda comprobar. El objetivo está como texto en el prompt (<code>agentes/prompts.py</code>) y no hay una prueba que diga «ya se cumplió». Dentro del bucle, el que decide que terminó es el modelo, cuando deja de pedir herramientas (la función <code>siguiente</code> en <code>agentes/bucle.py</code>), o un freno que lo corta. Tampoco hace un plan, decide un paso a la vez. Lo que sí decide el código es qué se publica: <code>comprobar_en_codigo</code> y el veredicto del verificador (<code>agentes/verificador.py</code>), y la revisión de procedencia del informe (<code>agentes/sintetizador.py</code>). En resumen, el objetivo lo pone una persona, el modelo decide cuándo terminó y el código decide qué se publica.</p>")
    p(f"<p><b>2. Con <code>resultados/</code> delante.</b> En los mismos 14 casos, el baseline usó en promedio {datos.miles(tin_b)} tokens de entrada en {ll_b:.0f} llamadas ({datos.miles(tin_b / ll_b)} por llamada). El sistema multiagente usó {datos.miles(tin_m)} en {ll_m:.0f} llamadas ({datos.miles(tin_m / ll_m)} por llamada). O sea, {datos.dec(tin_m / tin_b)} veces más tokens con {datos.dec(ll_m / ll_b)} veces más llamadas. Si duplicara el tope de pasos de 12 a 24, en el peor caso los tokens de entrada no se duplicarían sino que crecerían hasta casi cuatro veces, porque en cada paso se reenvía todo el historial y lo que se va sumando es 1 + 2 + … + n observaciones. En la práctica no cambiaría nada, por dos razones que salen de mis cifras. La primera es que el agente más ocupado del baseline hizo como máximo {peor_pasos} llamadas contando la de cierre, así que no llega al tope. La segunda es que el presupuesto de tokens es un freno aparte y no cambia al mover el de pasos. Lo que cambiaría es cuál de los dos frenos salta primero si una corrida se descontrola.</p>")
    p("<p><b>3. Un despliegue que hace daño.</b> El siguiente paso de este trabajo es un agente que aplica parches y hace commits en el repositorio de mi trabajo. Ahí el daño sería real: código incorrecto que llega a una rama compartida, o un PR de otra persona con un test malicioso que <code>correr_checks</code> ejecuta. En el servidor pondría lo que aquí sí protegió: los comandos en una lista cerrada, el proceso sin variables de entorno y sin red, la escritura limitada a una copia, y las comprobaciones en código antes de cualquier modelo. A una persona le dejaría aprobar el plan y cada commit, pero como una pausa del grafo y no como una instrucción en el prompt. La Parte 0 mostró lo que solo parecía proteger: los tests en verde (0.c) y la instrucción de «no inventes» en el prompt (0.a). En el caso adversarial el modelo ignoró el comentario que pedía no reportar nada, pero eso lo decidió el modelo y no es una garantía.</p>")


def evolucion(p, tabla, **k):
    p("<h2>Cómo evolucionó el trabajo</h2>")
    p("<p>El resultado final no salió al primer intento. Se siguió la regla del curso (baseline → medir → extender → medir) y casi todas las mediciones obligaron a cambiar algo, ya sea el código, las pruebas o la forma de medir. La tabla muestra ese recorrido en orden. Cada fila corresponde a uno o más commits del repositorio.</p>")
    p(tabla(["paso", "qué se hizo", "qué mostró la medición", "qué se cambió por eso"], [
        ["1", "Parte 0, antes de construir nada",
         "El modelo de la H200 gastó los 4 096 tokens en razonar y devolvió una respuesta vacía, sin error",
         "El nivel de razonamiento pasó a ser un ajuste del <code>.env</code> y toda llamada detecta la respuesta vacía y reintenta (<code>revisor/llamada.py</code>)"],
        ["2", "Primer diseño: cuatro dimensiones (bugs, reglas, código muerto, impacto) y un RAG solo con las 12 reglas del repo",
         "Antes de medir, al revisar el diseño: un review real también mira clean code y eficiencia, y con 15 fragmentos el RAG casi sobraba (las reglas caben en el prompt)",
         "Cinco dimensiones; reglas R13 a R16 con su fuente; el índice pasó de 15 a 206 fragmentos con documentación descargada"],
        ["3", "Baseline de un agente y golden set de 14 casos",
         "11 de 14 (commit <code>dbe8dc9</code>). Las trazas mostraron los tres fallos: vio con grep que una función no se usaba y no lo reportó (C09); no miró qué hacía la llamada dentro del bucle (C10); los tests pasaron y dio el cambio por bueno (C11)",
         "Se escribieron los cinco reviewers especializados, con instrucciones que atacan esos tres fallos. Fue un error de método, que se corrige en el paso 6"],
        ["4", "Capa multiagente: cinco reviewers, verificador y sintetizador",
         "11 de 14 en la primera corrida (no se commiteó). Las trazas mostraron que el paso de unir fusionaba líneas vecinas y dimensiones distintas, y perdía hallazgos reales",
         "Unir pasó a exigir mismo archivo, línea y dimensión. Segunda corrida: 14 de 14 (commit <code>7c85395</code>)"],
        ["5", "Ablaciones: sin verificador y sin RAG",
         "Sin verificador, mismo resultado con menos tokens. Sin RAG: 13 de 14 y 6 corridas incompletas",
         "Al preguntarse si estaba bien no haber adaptado los prompts: no lo estaba. Se había quitado la herramienta pero los prompts seguían pidiéndola. Corregido, sin RAG da 14 de 14 y ninguna incompleta: la conclusión anterior era un efecto del prompt"],
        ["6", "Revisión del método, buscando más errores como el anterior",
         "Cuatro: instrucciones de los reviewers sacadas del examen, extensión que comparaba dos cambios a la vez, trazas sin contenido, y sistemas medidos con versiones distintas del código",
         "Control con un agente único que recibe esas mismas instrucciones; multiagente con razonamiento alto; trazas con lo que el modelo pidió, observó y respondió; una medición final de todo con un mismo commit"],
        ["7", "Medición final de los siete sistemas",
         "El mismo baseline que había dado 11 dio 13 de 14: la diferencia entre dos corridas era tan grande como las diferencias entre sistemas que se estaban interpretando",
         "Tres repeticiones por sistema; las tablas muestran promedio y rango"],
        ["8", "Pregunta que quedaba: ¿y con código más difícil?",
         "El repo de prueba es pequeño y un solo agente lo lee casi entero",
         "Dos «PR grandes» que juntan varios casos y un caso complejo con herencia, inyección de dependencias y caché (Parte 4.2)"],
        ["9", "Medición de los casos difíciles",
         "El sistema multiagente sí se separa del baseline (13,7 frente a 8,7 de 14). Pero tarda mucho más de lo que justifica el tamaño de los cambios",
         "Se revisaron las trazas llamada por llamada: cerca de la mitad del tiempo se iba en llamadas que no devolvían nada. Se bajó el cupo de salida, se añadió un límite de tiempo por llamada y se cambió el reintento (Parte 4.3)"],
        ["10", "Razonamiento medio, que se había descartado con una sola llamada de prueba",
         "Un solo agente con razonamiento medio encontró los 14 problemas en sus tres corridas, y los tres bugs del caso complejo",
         "La conclusión del taller pasó de «el multiagente gana en código difícil» a «primero conviene ajustar el agente único»"],
    ]))
    p("<p><b>Cómo fueron cambiando las pruebas.</b> Los casos de prueba tampoco fueron los mismos desde el inicio. Primero hice 14 casos pequeños, uno o dos por cada tipo de problema. Sirvieron para ver en qué fallaba el baseline (C09, C10 y C11), pero después casi todos los sistemas los resolvían completos y ya no permitían diferenciarlos. Los dos casos que estaban bien (N01 y N02) sirvieron para ver que el multiagente a veces reporta de más, y también mostraron que uno de ellos no estaba tan bien armado. Después junté varios casos en dos PR grandes (G01 y G02), pensando que con más cambios a la vez un agente único se perdería. Sí bajó, pero poco. El caso que más sirvió fue el último (G03), con herencia, inyección de dependencias y caché: ahí los agentes únicos con razonamiento bajo o alto encontraron la mitad de los bugs o menos, y el multiagente los encontró todos. Y con ese mismo caso se vio que el razonamiento medio también los encuentra.</p>")
    p("<p>De todo este recorrido me quedo con dos cosas. La primera es que varias conclusiones que en algún momento parecían claras (que el baseline era mucho peor, que sin RAG se perdía un caso, que solo el multiagente resolvía el caso complejo) resultaron ser ruido entre corridas, un prompt mal adaptado o una medición que faltaba. La segunda es que todas se detectaron de la misma forma: teniendo las trazas y volviendo a medir con un control.</p>")


def limitaciones(p, tabla, **k):
    p("<h2>Errores cometidos y limitaciones</h2>")
    p("<p>Durante el taller cometí varios errores en la forma de medir. Se detectaron y corrigieron antes de la medición final, y están en el historial de commits. Los pongo aquí porque afectan cuánto se puede confiar en cada resultado.</p>")
    p(tabla(["error", "qué consecuencia tenía", "qué se hizo"], [
        ["Las instrucciones de los cinco reviewers se escribieron después de ver en qué fallaba el baseline, con pistas a la medida de esos fallos", "El sistema multiagente tenía mejores instrucciones además de más agentes: no se podía saber cuál de las dos cosas mejoraba el resultado", "Se añadió un control: un solo agente con esas mismas instrucciones. Las pistas siguen saliendo del examen, para los dos sistemas"],
        ["El paso de unir hallazgos fusionaba líneas vecinas y dimensiones distintas", "Se perdían problemas reales: la primera medición del multiagente dio 11 de 14", "Se corrigió mirando las trazas del propio golden set, y se volvió a medir"],
        ["En la ablación sin RAG se quitó la herramienta pero los prompts seguían pidiendo usarla", "6 de 14 corridas quedaron incompletas y se «perdía» un caso: las dos cosas eran efecto del prompt contradictorio, no de la falta de RAG", "Los prompts de esa ablación ya no nombran la herramienta, y hay una prueba que lo exige"],
        ["La extensión comparó un agente con razonamiento alto contra el multiagente con razonamiento bajo", "Dos cambios a la vez", "Se midió también el multiagente con razonamiento alto"],
        ["Las trazas no guardaban qué devolvía cada herramienta ni qué respondía el modelo", "El análisis de fallos no tenía evidencia", "Ahora guardan un extracto de cada cosa"],
        ["Cada sistema se midió al terminarlo, con el código en estados distintos, y una sola vez", "Se interpretaron como diferencias entre sistemas cosas que eran ruido: el mismo baseline dio 11 y después 13 de 14", "Una medición final de todos con el mismo commit, y tres repeticiones de cada uno"],
    ]))
    p("<p>Limitaciones que todavía tiene el trabajo:</p>")
    p("<ul>"
      "<li><b>El repositorio de prueba es pequeño</b>: unos diez archivos, que un solo agente lee casi enteros en cuatro pasos. Los tres casos difíciles de la Parte 4 son una aproximación, no un repositorio real: los escribió la misma persona que el sistema, y el caso complejo añade archivos completos en vez de modificar funciones.</li>"
      "<li><b>Las falsas alarmas casi no se miden</b>: solo hay dos casos limpios. Los hallazgos «no esperados» de los demás casos no los juzga nadie y algunos pueden ser legítimos.</li>"
      "<li><b>El acierto es por ubicación y palabras clave</b>, con rangos de líneas amplios en algunos casos: un hallazgo poco preciso que caiga en la línea correcta puede contarse como acierto.</li>"
      "<li><b>El golden set, el sistema y los prompts los hice yo</b>, y ajusté los prompts viendo los resultados del propio golden set. No hay casos guardados que no se hayan mirado.</li>"
      "<li><b>Son solo tres repeticiones.</b> Sirven para ver cuánto cambia un resultado entre corridas, pero no alcanzan para medirlo bien.</li>"
      "<li><b>Los tiempos son aproximados</b>: cuatro casos corren en paralelo sobre una GPU compartida, y dependen mucho de las llamadas vacías, que no ocurren igual en cada corrida.</li>"
      "<li><b>El último arreglo se midió solo en un sistema.</b> El cambio de cupo, tiempo y reintento de la Parte 4.3 se probó con el multiagente sobre los casos difíciles. El resto de las cifras del informe son anteriores a ese cambio.</li>"
      "<li><b>Las llamadas vacías no están resueltas.</b> Solo se limitó cuánto pueden tardar, y falta un límite de tiempo para la corrida completa.</li>"
      "</ul>")


def futuro(p, **k):
    p("<h2>Trabajo futuro</h2>")
    p("<p>El objetivo que motivó el taller sigue siendo llevar <code>dev-cycle</code> completo a LangGraph. Lo que se midió aquí cambia la razón para hacerlo. La ventaja no es que más agentes siempre encuentren más. La ventaja es que el flujo, las aprobaciones y los límites pasan de estar en una receta a estar en código, que el sistema no depende de un solo proveedor y que cada paso se puede medir. También queda una forma de decidir cuántos agentes usar: empezar con uno bien ajustado y añadir otro solo cuando una medición muestre que ayuda, como pasó con el de impacto. El orden previsto:</p>")
    p("<ol>"
      "<li><b>Un repositorio de prueba difícil.</b> Código real, o escrito a propósito con muchas dependencias entre piezas, diffs grandes y dependencias a varios saltos, con su golden set y casos reservados que no se miren al ajustar prompts. Es la condición para saber si repartir el trabajo ayuda donde un agente solo se queda corto.</li>"
      "<li><b>Resolver feedback (<code>review-comments</code>).</b> Un comentario de PR es un hallazgo que viene de fuera: reutiliza la ficha y el verificador, y añade un clasificador y un redactor de respuestas. Publicar pasa por una pausa de aprobación.</li>"
      "<li><b>El ciclo completo (<code>dev-cycle</code>).</b> Planificador, implementador y explicador, con este revisor como subgrafo. Los dos «STOP» de la skill (aprobar el plan y aprobar el commit) pasarían a ser nodos <code>interrupt</code> con checkpointer, de modo que no se pueda escribir en el repo sin pasar por ellos.</li>"
      "<li><b>El repositorio real.</b> Un <code>perfil.toml</code> para un proyecto Angular, que es donde se quiere usar. El implementador es el rol donde más sentido tiene probar un modelo distinto, y el sistema ya lo permite.</li>"
      "</ol>")
    p("<p>Mejoras ya identificadas en el sistema actual: verificar los hallazgos en una sola llamada en vez de un bucle por hallazgo, o quitar el verificador; hacer una búsqueda inicial de reglas compartida por todos los reviewers, porque hoy varios preguntan lo mismo; acotar la instrucción del reviewer de clean code que produce hallazgos en cambios correctos; un presupuesto de tokens por sistema y un límite de tiempo por corrida; y el tiempo máximo de un check en el perfil del repo.</p>")


def reproducibilidad(p, pre, RAIZ, **k):
    import subprocess

    commit = subprocess.run(["git", "log", "--format=%h", "-1", "--", "revisor"], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    p("<h2>Reproducibilidad</h2>")
    p(f"<p>El código medido es el del commit <code>{commit}</code> (último que toca <code>revisor/</code>). Versiones fijadas en <code>requirements.txt</code> (<code>langgraph==1.2.12</code>) y en <code>repo-prueba/package-lock.json</code>. Todas las tablas de este informe las genera <code>informe/generar_informe.py</code> leyendo <code>resultados/</code>; ninguna cifra está escrita a mano.</p>")
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


SECCIONES = [portada, motivacion, que_se_construyo, parte0, parte1, parte2a, parte2b, parte2c, parte3, parte4,
             conclusiones, parte5, evolucion, limitaciones, futuro, reproducibilidad]
