from revisor.rag.indice import construir_indice, partir_markdown, recolectar


def test_cada_regla_es_un_fragmento_con_su_id(perfil):
    ids = [f.id for f in recolectar(perfil, con_docs=False)]
    for numero in range(1, 17):
        assert f"R{numero}" in ids
    assert len(ids) == len(set(ids))


def test_el_fragmento_de_una_regla_incluye_su_porque(perfil):
    r1 = next(f for f in recolectar(perfil, con_docs=False) if f.id == "R1")
    assert "centavos" in r1.texto
    assert "Por qué" in r1.texto


def test_un_encabezado_dentro_de_un_bloque_de_codigo_no_parte(perfil):
    texto = "# Uno\n\n```\n# no es titulo\n```\n\n# Dos\n\ncuerpo"
    titulos = [f.titulo for f in partir_markdown(texto, "x.md", "docs", "x")]
    assert titulos == ["Uno", "Dos"]


def test_buscar_devuelve_la_regla_mas_parecida(perfil, embeddings):
    indice = construir_indice(perfil, embeddings, con_docs=False, cache=False)
    fragmento, _ = indice.buscar("impuesto después del descuento IMPUESTO_PORCENTAJE", k=1)[0]
    assert fragmento.id == "R12"
    assert indice.tiene("R12")
    assert not indice.tiene("R99")
