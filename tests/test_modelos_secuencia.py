"""Los modelos de secuencia dan EXACTAMENTE lo mismo que antes de consolidar secuencia_v1 y secuencia_v2_dow.

Producción (ensamble_v2) usa secuencia_v3 -> secuencia_final: no se tocó. v1 y v2_dow ahora heredan de él
y solo declaran su configuración. El oro (oro_secuencia.json) se capturó ANTES del cambio.
"""
import json, os, sys

import numpy as np
import pytest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import oro_modelos as OM

with open(os.path.join(AQUI, "oro_secuencia.json"), encoding="utf-8") as f:
    ORO = json.load(f)

HAY_DATOS = os.path.exists(os.path.join(OM.RAIZ, "historial.txt"))
pytestmark = pytest.mark.skipif(not HAY_DATOS, reason="falta historial.txt")


@pytest.fixture(scope="module")
def huellas():
    return OM.huellas()


@pytest.mark.parametrize("nombre", OM.NOMBRES)
def test_prediccion_identica_a_la_de_antes(huellas, nombre):
    nuevo, viejo = huellas[nombre], ORO[nombre]
    assert nuevo["nombre"] == viejo["nombre"]
    assert nuevo["forma"] == viejo["forma"]
    np.testing.assert_allclose(nuevo["fila0"], viejo["fila0"], rtol=0, atol=1e-12)
    np.testing.assert_allclose(nuevo["fila_ultima"], viejo["fila_ultima"], rtol=0, atol=1e-12)
    assert nuevo["suma_cuadrados"] == pytest.approx(viejo["suma_cuadrados"], abs=1e-9)
    assert nuevo["max"] == pytest.approx(viejo["max"], abs=1e-12)


def test_las_cuatro_versiones_siguen_siendo_distintas(huellas):
    """Si dos coincidieran, la consolidación habría perdido una configuración."""
    assert len({h["suma_cuadrados"] for h in huellas.values()}) == len(OM.NOMBRES)
