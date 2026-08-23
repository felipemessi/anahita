# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), e este
projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/) para os
lançamentos oficiais (`release` → `main`), conforme definido em `CLAUDE.md`.

## [Unreleased]

### Added
- Modelagem completa do catálogo SRD 2014 no PRD do backend (seção 7.4):
  expandido de 4 para as 24 categorias (vocabulário fixo, raças, classes e
  progressão, magias, equipamento e itens mágicos, backgrounds e feats,
  monstros/stat blocks, regras), com padrão relacional de i18n (`_i18n`)
  e regra de conteúdo homebrew sempre preso à campanha.
- `docs/anahita-backend-backlog.md` e `docs/anahita-frontend-backlog.md`:
  backlogs com histórias de usuário em checklist, organizados por fase,
  pensados para retomada entre sessões de desenvolvimento.

### Changed
- PRD do frontend atualizado para acompanhar o catálogo expandido: seletor
  de locale para o conteúdo do catálogo, telas de navegação e criação de
  conteúdo homebrew, wizard de criação de personagem e seleção de monstro
  no combat tracker.

### Fixed
- Testes de autenticação (`tests/auth/test_service.py`) falhavam com
  `greenlet library is required` por falta da extra `asyncio` na dependência
  do SQLAlchemy.
- Chave secreta JWT padrão abaixo do mínimo recomendado, disparando
  `InsecureKeyLengthWarning` do PyJWT.

### Changed
- Padrão `__pycache__` no `.gitignore` ampliado para também casar arquivos,
  não só diretórios.

### Added
- Skills do Claude Code (`commit`, `merge-request`) para padronizar commits
  semânticos e o fluxo de merge request do projeto.
