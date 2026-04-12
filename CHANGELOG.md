# Changelog

Todas as mudanças relevantes do projeto serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e o versionamento adota [Semantic Versioning](https://semver.org/lang/pt-BR/).

### [1.0.0] - 2026-04-12

### Adicionado
- Interface CLI completa com menu interativo
- Cadastro de pacientes com validação de CPF, idade e dados obrigatórios
- Classificação de risco por protocolo Manchester adaptado (5 níveis)
- Listagem da fila ordenada por prioridade (risco + tempo de espera)
- Registro de atendimento com data/hora
- Remoção de paciente (desistência/transferência)
- Busca de paciente por CPF
- Estatísticas: totais, por classificação, por faixa etária, tempo médio
- Persistência em arquivo JSON
- 25+ testes automatizados com pytest
- Linting com Ruff
- Pipeline CI com GitHub Actions
- Documentação completa no README.md
