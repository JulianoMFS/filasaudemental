"""
test_integracao.py — Testes de integração com o serviço externo ViaCEP.

Diferentemente dos testes unitários (test_modelos.py), estes testes
validam a comunicação real da aplicação com a API externa, garantindo
que o fluxo de dados não quebra sob condições variadas.

Estratégia de teste:
  - Teste de integração real: usa um CEP conhecido do DF (Esplanada dos
    Ministérios — CEP público e estável) para validar o contrato da API.
  - Teste com mock (unittest.mock): isola a lógica de tratamento de erros
    sem depender de conectividade de rede, garantindo CI/CD verde mesmo
    em ambientes sem internet.

Referência: pytest-mock / unittest.mock (stdlib)
"""

from __future__ import annotations

import pytest
import requests
from unittest.mock import MagicMock, patch

from src.servicos import (
    ErroConsultaCEP,
    consultar_cep,
    formatar_endereco,
    _mapear_regiao_saude_df,
)

# ---------------------------------------------------------------------------
# Testes de integração REAIS (dependem de conexão com a internet)
# Marcados com @pytest.mark.integration para permitir exclusão no CI offline
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_consultar_cep_real_valido():
    """
    Integração real: valida que o ViaCEP retorna dados corretos para o
    CEP 70050-900 (Esplanada dos Ministérios, Brasília/DF).
    CEP escolhido por ser estável, público e facilmente verificável.
    """
    resultado = consultar_cep("70050900")

    assert resultado["cep"] == "70050900"
    assert resultado["uf"] == "DF"
    assert "Brasília" in resultado["localidade"] or resultado["localidade"] != ""
    assert "regiao_saude" in resultado
    assert isinstance(resultado["regiao_saude"], str)


@pytest.mark.integration
def test_consultar_cep_real_invalido():
    """
    Integração real: CEP inexistente deve levantar ErroConsultaCEP
    com mensagem informativa.
    """
    with pytest.raises(ErroConsultaCEP) as excinfo:
        consultar_cep("00000000")
    assert "não encontrado" in str(excinfo.value).lower()


@pytest.mark.integration
def test_consultar_cep_formato_com_hifen():
    """
    Integração real: a função deve aceitar CEP formatado com hífen
    e retornar resultado correto.
    """
    resultado = consultar_cep("70050-900")
    assert resultado["cep"] == "70050900"


# ---------------------------------------------------------------------------
# Testes com MOCK — isolados de rede, adequados para CI/CD
# ---------------------------------------------------------------------------

@patch("src.servicos.requests.get")
def test_consultar_cep_mock_sucesso(mock_get):
    """
    Mock: simula resposta bem-sucedida do ViaCEP e valida que a função
    extrai e retorna os campos corretamente.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "cep": "70050-900",
        "logradouro": "Esplanada dos Ministérios",
        "bairro": "Zona Cívico-Administrativa",
        "localidade": "Brasília",
        "uf": "DF",
        "erro": None,
    }
    mock_get.return_value = mock_response

    resultado = consultar_cep("70050900")

    assert resultado["cep"] == "70050900"
    assert resultado["uf"] == "DF"
    assert resultado["localidade"] == "Brasília"
    assert "regiao_saude" in resultado
    mock_get.assert_called_once()


@patch("src.servicos.requests.get")
def test_consultar_cep_mock_cep_nao_encontrado(mock_get):
    """
    Mock: ViaCEP retorna {'erro': true} para CEPs inexistentes.
    Valida que ErroConsultaCEP é lançado corretamente.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"erro": True}
    mock_get.return_value = mock_response

    with pytest.raises(ErroConsultaCEP) as excinfo:
        consultar_cep("99999999")
    assert "não encontrado" in str(excinfo.value).lower()


@patch("src.servicos.requests.get")
def test_consultar_cep_mock_timeout(mock_get):
    """
    Mock: simula timeout de rede. Valida tratamento de exceção.
    """
    mock_get.side_effect = requests.exceptions.Timeout()

    with pytest.raises(ErroConsultaCEP) as excinfo:
        consultar_cep("70050900")
    assert "tempo" in str(excinfo.value).lower()


@patch("src.servicos.requests.get")
def test_consultar_cep_mock_sem_conexao(mock_get):
    """
    Mock: simula ausência de conectividade de rede.
    """
    mock_get.side_effect = requests.exceptions.ConnectionError()

    with pytest.raises(ErroConsultaCEP) as excinfo:
        consultar_cep("70050900")
    assert "conectar" in str(excinfo.value).lower()


def test_consultar_cep_formato_invalido_menos_de_8_digitos():
    """
    Unitário: CEP com menos de 8 dígitos deve ser rejeitado antes
    de qualquer chamada de rede.
    """
    with pytest.raises(ErroConsultaCEP) as excinfo:
        consultar_cep("7005")
    assert "inválido" in str(excinfo.value).lower()


def test_consultar_cep_formato_invalido_letras():
    """
    Unitário: CEP contendo letras deve ser rejeitado.
    """
    with pytest.raises(ErroConsultaCEP):
        consultar_cep("ABCDEFGH")


# ---------------------------------------------------------------------------
# Testes do mapeamento de Regiões de Saúde do DF
# ---------------------------------------------------------------------------

def test_mapear_regiao_saude_ceilandia():
    regiao = _mapear_regiao_saude_df("Ceilândia Norte", "DF")
    assert "OESTE" in regiao.upper() or "SUDOESTE" in regiao.upper()


def test_mapear_regiao_saude_fora_do_df():
    regiao = _mapear_regiao_saude_df("Centro", "SP")
    assert "Fora do DF" in regiao


def test_mapear_regiao_saude_nao_identificado():
    regiao = _mapear_regiao_saude_df("Bairro Desconhecido", "DF")
    assert "não identificada" in regiao.lower()


# ---------------------------------------------------------------------------
# Testes de formatação
# ---------------------------------------------------------------------------

def test_formatar_endereco_completo():
    dados = {
        "logradouro": "Esplanada dos Ministérios",
        "bairro": "Zona Cívico-Administrativa",
        "localidade": "Brasília",
        "uf": "DF",
    }
    resultado = formatar_endereco(dados)
    assert "Esplanada dos Ministérios" in resultado
    assert "Brasília" in resultado
    assert "DF" in resultado


def test_formatar_endereco_sem_logradouro():
    """CEPs de regiões rurais frequentemente não possuem logradouro."""
    dados = {
        "logradouro": "",
        "bairro": "Zona Rural",
        "localidade": "Planaltina",
        "uf": "DF",
    }
    resultado = formatar_endereco(dados)
    assert "Planaltina" in resultado
    assert "DF" in resultado
