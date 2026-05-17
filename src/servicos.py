"""
servicos.py — Integração com APIs externas.

Módulo responsável pela comunicação com serviços externos utilizados
pelo Fila Saúde Mental. Atualmente integra a API ViaCEP para validação
e enriquecimento de dados de endereço dos pacientes.

API: ViaCEP (https://viacep.com.br)
Tipo: REST / HTTP GET — pública, gratuita, sem autenticação.
"""

from __future__ import annotations

import requests

VIACEP_URL = "https://viacep.com.br/ws/{cep}/json/"
TIMEOUT_SEGUNDOS = 5


class ErroConsultaCEP(Exception):
    """Exceção lançada quando a consulta ao ViaCEP falha."""


def consultar_cep(cep: str) -> dict:
    """
    Consulta o ViaCEP e retorna os dados de endereço do CEP informado.

    Parâmetros
    ----------
    cep : str
        CEP no formato '70000000' (apenas dígitos, 8 caracteres).

    Retorno
    -------
    dict com as chaves: logradouro, bairro, localidade, uf.

    Exceções
    --------
    ErroConsultaCEP : em caso de CEP inválido, não encontrado ou
                      falha de comunicação com o serviço externo.
    """
    cep_limpo = "".join(filter(str.isdigit, cep))

    if len(cep_limpo) != 8:
        raise ErroConsultaCEP(
            f"CEP inválido: '{cep}'. Informe exatamente 8 dígitos."
        )

    url = VIACEP_URL.format(cep=cep_limpo)

    try:
        resposta = requests.get(url, timeout=TIMEOUT_SEGUNDOS)
        resposta.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ErroConsultaCEP(
            "Não foi possível conectar ao ViaCEP. Verifique a conexão com a internet."
        )
    except requests.exceptions.Timeout:
        raise ErroConsultaCEP(
            f"Tempo de resposta excedido ({TIMEOUT_SEGUNDOS}s) ao consultar o ViaCEP."
        )
    except requests.exceptions.HTTPError as exc:
        raise ErroConsultaCEP(f"Erro HTTP ao consultar o ViaCEP: {exc}")

    dados = resposta.json()

    if dados.get("erro"):
        raise ErroConsultaCEP(
            f"CEP '{cep_limpo}' não encontrado na base do ViaCEP."
        )

    return {
        "cep": cep_limpo,
        "logradouro": dados.get("logradouro", ""),
        "bairro": dados.get("bairro", ""),
        "localidade": dados.get("localidade", ""),
        "uf": dados.get("uf", ""),
        "regiao_saude": _mapear_regiao_saude_df(dados.get("bairro", ""), dados.get("uf", "")),
    }


def _mapear_regiao_saude_df(bairro: str, uf: str) -> str:
    """
    Mapeamento simplificado de bairros do DF às Regiões de Saúde da SES-DF.
    Útil para direcionar o paciente à unidade CAPS mais próxima.
    """
    if uf != "DF":
        return "Fora do DF — verificar referência interestadual"

    bairro_upper = bairro.upper()

    mapeamento = {
        "CENTRAL": ["ASA NORTE", "ASA SUL", "CRUZEIRO", "OCTOGONAL", "SUDOESTE"],
        "NORTE/LESTE": ["PLANALTINA", "SOBRADINHO", "PARANOÁ", "SÃO SEBASTIÃO"],
        "SUL": ["GAMA", "SANTA MARIA", "RECANTO DAS EMAS"],
        "OESTE/SUDOESTE": ["CEILÂNDIA", "TAGUATINGA", "SAMAMBAIA", "BRAZLÂNDIA"],
        "CENTRO-NORTE": ["GUARÁ", "PARK WAY", "NÚCLEO BANDEIRANTE", "CANDANGOLÂNDIA"],
        "LESTE": ["JARDIM BOTÂNICO", "LAGO SUL", "LAGO NORTE"],
        "NORTE": ["SOBRADINHO II", "FERCAL", "PLANALTINA"],
    }

    for regiao, bairros in mapeamento.items():
        if any(b in bairro_upper for b in bairros):
            return f"Região de Saúde {regiao}"

    return "Região de Saúde não identificada — consultar SISREG"


def formatar_endereco(dados_cep: dict) -> str:
    """Formata os dados do CEP em string legível para exibição no CLI."""
    partes = []
    if dados_cep.get("logradouro"):
        partes.append(dados_cep["logradouro"])
    if dados_cep.get("bairro"):
        partes.append(dados_cep["bairro"])
    cidade_uf = f"{dados_cep.get('localidade', '')} / {dados_cep.get('uf', '')}"
    partes.append(cidade_uf)
    return " — ".join(filter(None, partes))
