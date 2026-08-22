# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), e este
projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/) para os
lançamentos oficiais (`release` → `main`), conforme definido em `CLAUDE.md`.

## [Unreleased]

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
