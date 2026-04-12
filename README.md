# Fila Saúde Mental

**Gerenciador de Fila para Serviços de Saúde Mental no SUS**

> Versão atual: **1.0.0**

---

## Descrição do Problema Real:

No Sistema Único de Saúde (SUS), os serviços de saúde mental, especialmente aqueles destinados ao público infantojuvenil, enfrentam filas de espera que podem ultrapassar meses ou até anos (+510 dias). Centros como os CAPS (Centros de Atenção Psicossocial, Adolescentro e Centro de Orientação Médico-Psicopedagógica - COMPP, no Distrito Federal) e unidades especializadas recebem demandas crescentes, mas a gestão dessas filas frequentemente podem ocasionar erros de classificação e direcionamento incorretos originados da Atenção Primária à Saúde (APS) e de hospitais.

Isso resulta em:
- Pacientes de alto risco aguardando o mesmo tempo que casos não urgentes;
- Falta de visibilidade sobre o tamanho e perfil da demanda represada;
- Dificuldade em gerar dados para gestores e órgãos de controle (MPDFT, DPDF e TCDF);
- Perda de pacientes que desistem sem registro, com busca de atendimento na rede privada de saúde.

## Proposta da Solução:

O **Fila Saúde Mental** é uma aplicação CLI (linha de comando) que permite as equipes de saúde mental gerenciar a fila de espera de forma organizada, com **classificação de risco** baseada no protocolo Manchester adaptado (5 níveis de urgência - vermelho, laranja, amarelo, verde e azul). A fila é automaticamente ordenada por prioridade: pacientes com maior risco (vermelho) são atendidos primeiro; em caso de empate, quem está esperando há mais tempo tem preferência.

A aplicação oferece cadastro com validação, registro de atendimento, remoção por desistência, busca por CPF e um painel de estatísticas com contagem por classificação de risco e faixa etária.

## Público-Alvo:

- Profissionais de saúde mental em unidades do SUS (CAPS, Centros especializados - COMPP e Adolescentro, e ambulatórios)
- Equipes de regulação e gestão de filas em secretarias de saúde
- Estudantes e pesquisadores de saúde pública

## Funcionalidades Principais:

- **Cadastro de pacientes** com validação de CPF, idade e dados obrigatórios
- **Classificação de risco** em 5 níveis (Vermelho, Laranja, Amarelo, Verde, Azul)
- **Fila priorizada** automaticamente por risco e tempo de espera
- **Registro de atendimento** com data/hora
- **Remoção** de pacientes (desistência/transferência)
- **Busca** por CPF
- **Estatísticas**: total na fila, atendidos, tempo médio de espera, distribuição por risco e faixa etária
- **Persistência** dos dados em arquivo JSON local

## Tecnologias Utilizadas:

- **Linguagem**: Python 3.10+
- **Testes**: pytest
- **Linting**: Ruff
- **CI/CD**: GitHub Actions
- **Armazenamento**: JSON (arquivo local)

## Instalação:

### Pré-requisitos
- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)

### Passos:

```bash
# 1. Clone o repositório
git clone https://github.com/julianoMFS/fila-saude-mental.git
cd fila-saude-mental

# 2. (Opcional) Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. Instale as dependências de desenvolvimento
pip install -e ".[dev]"
```

## Execução:

```bash
python -m src.cli
```

Ao iniciar, o sistema exibirá um menu interativo:

```
╔══════════════════════════════════════════════════════════════╗
║                 FILA SAÚDE MENTAL  v1.0.0                    ║
║           Gerenciador de Fila em Saúde Mental SUS            ║
╚══════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────┐
│  1. Adicionar paciente à fila       │
│  2. Listar fila de espera           │
│  3. Registrar atendimento           │
│  4. Remover paciente (desistência)  │
│  5. Buscar paciente por CPF         │
│  6. Estatísticas da fila            │
│  7. Sair                            │
└─────────────────────────────────────┘
```

### Exemplo de uso - Adicionar paciente

```
  Escolha uma opção: 1

-- Adicionar Paciente --
  Nome completo: Maria Silva
  CPF (somente números): 12345678901
  Idade: 34

  Classificações de risco:
    5. VERMELHO — Emergência - Risco imediato
    4. LARANJA — Muito urgente - Risco alto
    3. AMARELO — Urgente - Risco moderado
    2. VERDE — Pouco urgente - Risco baixo
    1. AZUL — Não urgente - Acompanhamento

  Informe o número da classificação (1-5): 3
  Demanda / Motivo do encaminhamento: Ansiedade grave com ideação suicida

  ✓ Paciente 'João da Silva' adicionado com sucesso!
    Classificação: AMARELO
```

### Exemplo de uso - Estatísticas:

```
-- Estatísticas da Fila --

  Pacientes aguardando: 12
  Pacientes atendidos:  5
  Tempo médio de espera: 23.4 dias

  Por classificação de risco:
    VERMELHO   │   1 █
    LARANJA    │   2 ██
    AMARELO    │   4 ████
    VERDE      │   3 ███
    AZUL       │   2 ██

  Por faixa etária:
    Crianças (0-12):      3
    Adolescentes (13-17): 4
    Adultos (18-59):      4
    Idosos (60+):         1
```

## Executar os Testes:

```bash
pytest tests/ -v
```

Os testes cobrem:
- Validação de CPF (formato, tamanho, dígitos repetidos)
- Validação de idade (limites, valores inválidos)
- Adição de pacientes (rejeição de dados inválidos)
- Persistência de dados em arquivo
- Ordenação da fila por prioridade
- Registro de atendimento e remoção
- Busca por CPF
- Estatísticas com fila vazia e preenchida

## Executar o Lint:

```bash
ruff check src/ tests/
```

Para correção automática:

```bash
ruff check --fix src/ tests/
```

## Estrutura do Projeto

```
fila-saude-mental/
├── src/
│   ├── __init__.py          # Versão do pacote
│   ├── modelos.py           # Modelos, validações e lógica de negócio
│   └── cli.py               # Interface de linha de comando
├── tests/
│   ├── __init__.py
│   └── test_modelos.py      # 25+ testes automatizados
├── .github/
│   └── workflows/
│       └── ci.yml           # Pipeline CI (lint + testes)
├── pyproject.toml            # Manifesto, versão, dependências
├── README.md                 # Esta documentação
├── CHANGELOG.md              # Registro de mudanças
├── LICENSE                   # Licença MIT
└── .gitignore
```

## Versão Atual:

**1.0.0** — Primeira versão estável com todas as funcionalidades planejadas.

Veja o [CHANGELOG.md](CHANGELOG.md) para o histórico de mudanças.

## Autor:

**Juliano Morais** Disciplina: Bootcamp II, Turma A - 0226, UniCEUB, 2026/1

## Repositório Público

[https://github.com/JulianoMFS/fila-saude-mental](https://github.com/JulianoMFS/fila-saude-mental)

---

## Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).
