"""
app_streamlit.py — Interface web para deploy público (Streamlit Cloud).

Converte a lógica de negócio do CLI em uma aplicação web interativa, mantendo todas as funcionalidades originais e adicionando visualizações gráficas para gestores e órgãos de controle.

Deploy: https://filasaudemental.streamlit.app
"""

import json
import os
from datetime import datetime

import streamlit as st

# Importa a integração com ViaCEP
from src.servicos import consultar_cep, formatar_endereco, ErroConsultaCEP

# ── Configuração da página ─────────────────────────────────────────────────

st.set_page_config(
    page_title="Fila Saúde Mental — SUS/DF",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos ────────────────────────────────────────────────────────────────

CORES_RISCO = {
    "VERMELHO": "#c0392b",
    "LARANJA": "#e67e22",
    "AMARELO": "#f1c40f",
    "VERDE": "#27ae60",
    "AZUL": "#2980b9",
}

ARQUIVO_DADOS = "fila_dados.json"

# ── Persistência simples ───────────────────────────────────────────────────

def carregar_fila():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_fila(fila):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(fila, f, ensure_ascii=False, indent=2, default=str)


def inicializar_estado():
    if "fila" not in st.session_state:
        st.session_state.fila = carregar_fila()


# ── Interface principal ────────────────────────────────────────────────────

def main():
    inicializar_estado()
    fila = st.session_state.fila

    st.title("🧠 Fila Saúde Mental")
    st.caption("Gerenciador de Fila para Serviços de Saúde Mental no SUS · v1.1.0")

    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
    aguardando = [p for p in fila if not p.get("atendido_em")]
    atendidos = [p for p in fila if p.get("atendido_em")]
    criticos = [p for p in aguardando if p["classificacao"] in ("VERMELHO", "LARANJA")]

    col_info1.metric("Na fila", len(aguardando))
    col_info2.metric("Atendidos hoje", len(atendidos))
    col_info3.metric("Casos críticos", len(criticos), delta=None)
    col_info4.metric("Total registros", len(fila))

    st.divider()

    aba1, aba2, aba3 = st.tabs(["📋 Fila de Espera", "➕ Cadastrar Paciente", "📊 Estatísticas"])

    # ── Aba 1: Fila de Espera ──────────────────────────────────────────────
    with aba1:
        st.subheader("Pacientes aguardando atendimento")

        ordem = {"VERMELHO": 5, "LARANJA": 4, "AMARELO": 3, "VERDE": 2, "AZUL": 1}
        fila_ordenada = sorted(
            aguardando,
            key=lambda p: (-ordem.get(p["classificacao"], 0), p["entrada"])
        )

        if not fila_ordenada:
            st.info("Nenhum paciente aguardando no momento.")
        else:
            for i, p in enumerate(fila_ordenada, 1):
                cor = CORES_RISCO.get(p["classificacao"], "#999")
                with st.container():
                    c1, c2, c3, c4 = st.columns([1, 3, 2, 2])
                    c1.markdown(
                        f"<span style='background:{cor};color:white;padding:4px 8px;"
                        f"border-radius:4px;font-weight:bold'>{p['classificacao']}</span>",
                        unsafe_allow_html=True,
                    )
                    c2.markdown(f"**{p['nome']}** · {p['idade']} anos")
                    c3.markdown(f"📍 {p.get('regiao_saude', '—') or '—'}")
                    entrada_dt = p.get("entrada", "")
                    c4.markdown(f"🕐 {entrada_dt[:16] if entrada_dt else '—'}")

                    with st.expander("Ver detalhes / Registrar atendimento"):
                        st.write(f"**CPF:** {p['cpf']}")
                        st.write(f"**Demanda:** {p.get('demanda', '—')}")
                        if p.get("cep"):
                            st.write(f"**CEP:** {p['cep']}")

                        if st.button(f"✅ Registrar atendimento", key=f"atend_{p['cpf']}"):
                            for reg in st.session_state.fila:
                                if reg["cpf"] == p["cpf"] and not reg.get("atendido_em"):
                                    reg["atendido_em"] = datetime.now().isoformat()
                            salvar_fila(st.session_state.fila)
                            st.success(f"Atendimento de {p['nome']} registrado.")
                            st.rerun()

    # ── Aba 2: Cadastrar Paciente ──────────────────────────────────────────
    with aba2:
        st.subheader("Cadastrar novo paciente na fila")

        with st.container():
            col_a, col_b = st.columns(2)
            nome = col_a.text_input("Nome completo *")
            cpf = col_b.text_input("CPF (somente números) *", max_chars=11)
            idade = col_a.number_input("Idade *", min_value=0, max_value=120, value=None)
            classificacao = col_b.selectbox(
                "Classificação de risco *",
                options=["VERMELHO", "LARANJA", "AMARELO", "VERDE", "AZUL"],
                format_func=lambda x: {
                    "VERMELHO": "🔴 VERMELHO — Emergência (risco imediato)",
                    "LARANJA": "🟠 LARANJA — Muito urgente (risco alto)",
                    "AMARELO": "🟡 AMARELO — Urgente (risco moderado)",
                    "VERDE": "🟢 VERDE — Pouco urgente (risco baixo)",
                    "AZUL": "🔵 AZUL — Não urgente (acompanhamento)",
                }[x],
            )
            demanda = st.text_area("Demanda / Motivo do encaminhamento *")

            st.markdown("---")
            st.markdown("**🔍 Busca de endereço por CEP (opcional — integração ViaCEP)**")
            cep_input = st.text_input("CEP", placeholder="Ex.: 72115-670", max_chars=9)

            dados_cep = {}
            regiao_saude = ""

            if cep_input:
                with st.spinner("Consultando ViaCEP..."):
                    try:
                        dados_cep = consultar_cep(cep_input)
                        regiao_saude = dados_cep.get("regiao_saude", "")
                        st.success(
                            f"📍 {formatar_endereco(dados_cep)}  \n"
                            f"🏥 **{regiao_saude}**"
                        )
                    except ErroConsultaCEP as e:
                        st.warning(f"⚠️ {e}")

            if st.button("Adicionar à fila", type="primary"):
                erros = []
                if not nome:
                    erros.append("Nome é obrigatório.")
                if not cpf or len(cpf) != 11:
                    erros.append("CPF deve ter 11 dígitos.")
                if idade is None:
                    erros.append("Idade é obrigatória.")
                if not demanda:
                    erros.append("Demanda é obrigatória.")
                if any(p["cpf"] == cpf for p in st.session_state.fila if not p.get("atendido_em")):
                    erros.append("Paciente com este CPF já está na fila.")

                if erros:
                    for e in erros:
                        st.error(e)
                else:
                    novo = {
                        "nome": nome,
                        "cpf": cpf,
                        "idade": int(idade),
                        "classificacao": classificacao,
                        "demanda": demanda,
                        "cep": dados_cep.get("cep", ""),
                        "regiao_saude": regiao_saude,
                        "entrada": datetime.now().isoformat(),
                        "atendido_em": None,
                    }
                    st.session_state.fila.append(novo)
                    salvar_fila(st.session_state.fila)
                    st.success(f"✅ {nome} adicionado à fila com classificação **{classificacao}**.")
                    st.balloons()

    # ── Aba 3: Estatísticas ────────────────────────────────────────────────
    with aba3:
        st.subheader("Painel de estatísticas da fila")

        if not aguardando:
            st.info("Nenhum paciente na fila para calcular estatísticas.")
        else:
            # Distribuição por risco
            contagem_risco = {r: 0 for r in CORES_RISCO}
            for p in aguardando:
                contagem_risco[p["classificacao"]] = contagem_risco.get(p["classificacao"], 0) + 1

            st.markdown("**Distribuição por classificação de risco**")
            for risco, qtd in contagem_risco.items():
                if qtd > 0:
                    st.markdown(
                        f"<span style='background:{CORES_RISCO[risco]};color:white;"
                        f"padding:2px 8px;border-radius:4px'>{risco}</span> "
                        f"{'█' * qtd} {qtd} paciente(s)",
                        unsafe_allow_html=True,
                    )

            st.markdown("---")
            st.markdown("**Distribuição por Região de Saúde (SES-DF)**")
            regioes = {}
            for p in aguardando:
                r = p.get("regiao_saude") or "Não informado"
                regioes[r] = regioes.get(r, 0) + 1
            for regiao, qtd in sorted(regioes.items(), key=lambda x: -x[1]):
                st.markdown(f"- **{regiao}**: {qtd} paciente(s)")

            # Faixas etárias
            st.markdown("---")
            st.markdown("**Distribuição por faixa etária**")
            faixas = {"Crianças (0-12)": 0, "Adolescentes (13-17)": 0,
                      "Adultos (18-59)": 0, "Idosos (60+)": 0}
            for p in aguardando:
                idade_p = p.get("idade", 0)
                if idade_p <= 12:
                    faixas["Crianças (0-12)"] += 1
                elif idade_p <= 17:
                    faixas["Adolescentes (13-17)"] += 1
                elif idade_p <= 59:
                    faixas["Adultos (18-59)"] += 1
                else:
                    faixas["Idosos (60+)"] += 1

            for faixa, qtd in faixas.items():
                st.markdown(f"- **{faixa}**: {qtd}")


if __name__ == "__main__":
    main()
