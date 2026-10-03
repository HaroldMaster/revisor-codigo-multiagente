def test_carga_los_comandos_del_repo(perfil):
    assert perfil.checks == {
        "lint": "npx eslint .",
        "tests": "npx vitest run",
        "tipos": "npx tsc --noEmit",
    }


def test_lista_el_codigo_sin_lo_ignorado(perfil):
    rutas = [r.relative_to(perfil.raiz).as_posix() for r in perfil.archivos_de_codigo()]
    assert "src/pedidos/pedidos.ts" in rutas
    assert all(r.startswith("src/") for r in rutas)
    assert not any("node_modules" in r for r in rutas)


def test_encuentra_el_archivo_de_reglas(perfil):
    assert [r.name for r in perfil.archivos_de_reglas()] == ["CLAUDE.md"]
