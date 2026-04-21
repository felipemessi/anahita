# Anahita — Instruções para Claude Code

## Projeto
Anahita é uma plataforma multi-mesa para gerenciamento de campanhas de D&D 5e.
PRDs completos em `docs/anahita-backend-prd.md` e `docs/anahita-frontend-prd.md`.

## Stack
- Backend: Python 3.14+, FastAPI, SQLAlchemy async, Alembic, Postgres
- Ferramentas Python: Gerenciamento com `uv`, tarefas com `taskipy` (uv tool), lint e formatação com `ruff`, análise estática com `mypy`
- Frontend: Next.js (App Router), TypeScript strict, shadcn/ui, TanStack Query
- Infra: Docker Compose (Nginx + Frontend + Backend + Postgres 18)

## Regras de Desenvolvimento

### Git
- Branch naming: `feature/<domain>-<description>`, `fix/<description>`, `chore/<description>`
- Base para novas features: branch `release` (sempre atualizada)
- Commits: conventional commits (feat:, fix:, test:, chore:, docs:, refactor:)
- Cada feature deve ter PR pronto para revisão para a branch `release`
- Lançamentos oficiais (PR de `release` > `main`): A versão deve ser demarcada com tags seguindo versionamento semântico (ex: `2026.0.0.1`).

### Código
- Backend: Python type hints em tudo. Pydantic para validação. Async by default. Uso de `ruff` e `mypy` obrigatório.
- Frontend: TypeScript strict. Sem `any`. Sem `as` desnecessário.
- Testes obrigatórios para toda feature antes do commit.
- Backend testes: pytest + pytest-asyncio. SQLite para testes unitários.
- Frontend testes: vitest + testing-library.

### Estrutura Backend
Cada domínio segue: models.py, domain.py, schemas.py, service.py, router.py.
Queries complexas/cross-domain vão em app/queries/.
Rules engine em engine/ — Python puro, sem dependência de framework.

### Estrutura Frontend
App Router. Server Components para dados estáveis. Client + React Query para mutações.
WebSocket para combat tracker. shadcn/ui para componentes base.

### Comandos Pré-Autorizados (não destrutivos)
Os seguintes comandos podem ser executados sem pedir confirmação:
- `git status`, `git log`, `git diff`, `git branch`, `git worktree list`
- `ls`, `cat`, `find`, `grep`, `tree`, `wc`
- `uv run pytest`, `npm test`, `npm run lint`, `npm run typecheck`, `task <name>`
- `alembic history`, `alembic heads`, `alembic current`
- `docker compose ps`, `docker compose logs`
- `uv add`, `uv sync`, `npm install` (para dependências do projeto)
- Leitura de qualquer arquivo do projeto
- Criação e edição de arquivos dentro do projeto

### Comandos que Precisam de Confirmação
- `git push`, `git merge` em branches protegidas
- `alembic upgrade`, `alembic downgrade`
- `docker compose up`, `docker compose down`
- Qualquer comando destrutivo (`rm`, `drop`, etc.)
