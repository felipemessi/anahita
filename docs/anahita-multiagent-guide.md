# Anahita — Guia de Desenvolvimento Multi-Agente

## Setup Inicial, Workflow Paralelo com Claude Code e Continuidade entre Sessões

**Data:** 2026-04-08

---

## 1. Setup Inicial do Projeto

### 1.1 Estrutura Git

```bash
cd ~/projects/anahita
git init
git checkout -b main

# Branch de referência para releases estáveis
git checkout -b release
git checkout main
```

Copie os PRDs para o repositório:

```bash
git add .
git commit -m "docs: add backend and frontend PRDs"
git push -u origin main
git checkout release
git merge main
git push -u origin release
git checkout main
```

### 1.2 CLAUDE.md — Instruções Globais para Todos os Agentes

Crie o arquivo `CLAUDE.md` na raiz do projeto. O Claude Code lê este arquivo automaticamente em cada sessão:

```bash
cat > CLAUDE.md << 'EOF'
# Anahita — Instruções para Claude Code

## Projeto
Anahita é uma plataforma multi-mesa para gerenciamento de campanhas de D&D 5e.
PRDs completos em `docs/anahita-backend-prd.md` e `docs/anahita-frontend-prd.md`.

## Stack
- Backend: Python 3.14+, FastAPI, SQLAlchemy async, Alembic, Postgres
- Ferramentas Python: Gerenciamento com `uv`, tarefas com `taskipy` (uv tool), lint e formatação com `ruff` e checagem estática de tipos com `mypy`
- Frontend: Next.js (App Router), TypeScript strict, shadcn/ui, TanStack Query
- Infra: Docker Compose (Nginx + Frontend + Backend + Postgres 18)

## Regras de Desenvolvimento

### Git
- Branch naming: `feature/<domain>-<description>`, `fix/<description>`, `chore/<description>`
- Base para novas features: branch `release` (sempre atualizada)
- Commits: conventional commits (feat:, fix:, test:, chore:, docs:, refactor:)
- Cada feature deve ter PR pronto para revisão

### Código
- Backend: Python type hints em tudo. Pydantic para validação. Async by default. Uso do `ruff` e `mypy` obrigatório.
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
- `uv run pytest`, `npm test`, `npm run lint`, `npm run typecheck`, `task <nome>`
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
EOF
```

Commit:

```bash
git add CLAUDE.md
git commit -m "chore: add CLAUDE.md with agent instructions"
```

### 1.3 Instalar Claude Code (se ainda não tiver)

```bash
npm install -g @anthropic-ai/claude-code
```

Verifique:

```bash
claude --version
```

---

## 2. Workflow Multi-Agente com Worktrees

### 2.1 Conceito

Cada agente Claude Code trabalha em uma **worktree** separada — um diretório independente com seu próprio branch, ligado ao mesmo repositório Git. Isso permite que múltiplos agentes editem arquivos simultaneamente sem conflito.

```
~/projects/anahita/                          ← main worktree (você)
~/projects/anahita/.claude/worktrees/
    ├── feature-auth/                        ← agente 1
    ├── feature-campaigns/                   ← agente 2
    └── feature-rules-engine/                ← agente 3
```

### 2.2 Iniciando Agentes em Paralelo

Abra múltiplos terminais no WSL. Em cada um:

```bash
cd ~/projects/anahita

# Terminal 1 — Agente trabalhando em auth
claude --worktree feature-auth

# Terminal 2 — Agente trabalhando em campaigns
claude --worktree feature-campaigns

# Terminal 3 — Agente trabalhando na rules engine
claude --worktree feature-rules-engine
```

O `--worktree` cria automaticamente:
- Um diretório em `.claude/worktrees/<nome>/`
- Um branch `worktree-<nome>` baseado na branch padrão do remote

### 2.3 Dando o Prompt Inicial para Cada Agente

Cada agente recebe um prompt focado na sua feature. Exemplo:

**Terminal 1 (auth):**
```
Leia o PRD em docs/anahita-backend-prd.md, seções 4 (Autenticação) e 7.1 (Auth & Users).

Implemente o domínio auth:
- models.py (User, AuthProvider)
- domain.py
- schemas.py (register, login, token refresh)
- strategies/base.py (AuthStrategy ABC)
- strategies/local.py (email + senha com JWT)
- service.py
- router.py
- core/security.py (hashing, JWT)

Crie testes para toda a lógica.
Base na branch release. Crie branch feature/auth.
Faça commits atômicos com conventional commits.
Ao finalizar, me avise para eu revisar e abrir o PR.
```

**Terminal 2 (campaigns):**
```
Leia o PRD em docs/anahita-backend-prd.md, seções 3 e 7.2.

Implemente o domínio campaigns:
- models.py (Campaign, CampaignMember, CampaignInvite)
- domain.py
- schemas.py
- service.py
- router.py

Crie testes. Base na branch release. Branch feature/campaigns.
Commits atômicos. Me avise ao finalizar.
```

### 2.4 Usando Worktrees Manuais (mais controle)

Se preferir controle total sobre o branch base e o local:

```bash
# Crie worktrees manualmente baseadas na release
git worktree add ../anahita-auth -b feature/auth release
git worktree add ../anahita-campaigns -b feature/campaigns release
git worktree add ../anahita-engine -b feature/rules-engine release

# Inicie Claude Code em cada uma
cd ../anahita-auth && claude --name "auth"
cd ../anahita-campaigns && claude --name "campaigns"
cd ../anahita-engine && claude --name "rules-engine"
```

O `--name` dá um nome descritivo à sessão para facilitar o `/resume`.

---

## 3. Continuidade — Parar e Retomar Depois

### 3.1 Parando uma Sessão

Quando atingir o limite diário ou precisar parar:

1. No Claude Code, digite `/exit` ou Ctrl+C
2. O Claude mostra: `Resume this session with: claude --resume <session-id>`
3. **Anote o session-id** ou use nomes descritivos (`--name`)

Se a worktree tem commits ou mudanças, o Claude pergunta se quer manter. **Diga que sim** — isso preserva o diretório e o branch.

#### Checklist de controle para retomar

- [ ] Anotar o `session-id` exibido pelo Claude
- [ ] Usar `--name` descritivo sempre que possível
- [ ] Confirmar o branch atual da worktree (`git branch`)
- [ ] Confirmar que as mudanças estão commitadas ou salvas localmente
- [ ] Confirmar que a worktree ainda existe em `.claude/worktrees/` ou em um diretório manual
- [ ] Se estiver usando worktrees manuais, anotar o caminho do diretório e o nome do branch
- [ ] Anotar qualquer instrução de prompt ou contexto relevante da feature em andamento

### 3.2 Retomando uma Sessão

```bash
cd ~/projects/anahita

# Opção 1: picker interativo (mostra sessões de todas as worktrees do repo)
claude --resume

# Opção 2: retomar por session-id
claude --resume <session-id>

# Opção 3: continuar a sessão mais recente
claude --continue
```

O picker do `/resume` mostra sessões de todas as worktrees do repositório. Você pode retomar uma sessão de outra worktree sem trocar de diretório.

### 3.3 Se Usou Worktrees Manuais

```bash
# Volte ao diretório da worktree
cd ../anahita-auth

# Retome
claude --resume
# ou
claude --continue
```

### 3.4 Boas Práticas para Continuidade

- **Nomeie as sessões** com `--name` ao criar. Facilita encontrar depois.
- **Commit frequente.** Se o agente commita a cada etapa, você não perde progresso ao parar.
- **Mantenha as worktrees** ao sair. Só limpe após o merge.
- **O contexto persiste** na sessão. Ao retomar, o Claude lembra o que estava fazendo.

---

## 4. Fluxo de PR e Merge

### 4.1 Após o Agente Finalizar

```bash
# Veja o estado da worktree
cd ~/projects/anahita/.claude/worktrees/feature-auth/
# ou cd ../anahita-auth (se worktree manual)

# Verifique os commits
git log --oneline release..HEAD

# Rode os testes
uv run pytest

# Push para o remote
git push -u origin feature/auth
```

### 4.2 Abrir PR

Se estiver usando GitHub:

```bash
gh pr create --base release --title "feat: auth domain" --body "Implementa autenticação com strategy pattern"
```

Ou abra manualmente no GitHub/GitLab.

### 4.3 Lançamentos Oficiais (`release` > `main`)

Todas as branches de release agrupam features testadas. Quando for estabilizar uma versão nova para produção:
1. Abra um PR da branch `release` para a `main`.
2. Após o merge ser aprovado e aplicado, deve-se extrair e aplicar uma **tag semântica** que descreve o avanço no formato temporal/semântico, como `2026.0.0.1`.

```bash
git checkout main
git pull
git tag 2026.0.0.1
git push origin 2026.0.0.1
```

### 4.3 Após o Merge

```bash
# Atualize a release local
git checkout release
git pull

# Limpe a worktree
git worktree remove .claude/worktrees/feature-auth
# ou
git worktree remove ../anahita-auth

# Delete o branch local
git branch -d feature/auth
```

### 4.4 Novo Agente Pega a Release Atualizada

O próximo agente que você iniciar com `--worktree` vai automaticamente se basear na release atualizada (que agora inclui o auth mergido). Assim, cada feature parte do estado mais recente.

---

## 5. Postgres MCP Server para Debug

Útil para o Claude Code inspecionar o banco durante desenvolvimento (schema, dados de seed, debug de queries).

### 5.1 Instalação

O server MCP oficial de Postgres usa Node.js:

```bash
npm install -g @modelcontextprotocol/server-postgres
```

### 5.2 Configuração no Projeto

Crie o arquivo `.mcp.json` na raiz do projeto:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://anahita:anahita@localhost:5432/anahita"
      }
    }
  }
}
```

### 5.3 Garantir que o Postgres Está Acessível

O Postgres roda no Docker Compose. Para que o Claude Code (rodando no WSL host) acesse, o container precisa expor a porta:

```yaml
# compose.yaml (parcial)
services:
  postgres:
    image: postgres:18-alpine
    ports:
      - "5432:5432"    # expõe para o host/WSL
    environment:
      - POSTGRES_USER=anahita
      - POSTGRES_PASSWORD=anahita
      - POSTGRES_DB=anahita
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### 5.4 Testando

Inicie o Postgres:

```bash
docker compose up -d postgres
```

No Claude Code, verifique se o MCP está conectado:

```
/mcp
```

Deve mostrar o server `postgres` como conectado. Agora o Claude Code pode:
- Inspecionar schema: "Mostre as tabelas do banco"
- Debug queries: "Execute SELECT * FROM users LIMIT 5"
- Validar migrations: "Verifique se a tabela campaign_members existe"

### 5.5 Segurança

O `.mcp.json` fica no repositório (conveniência para o time). Se a senha for sensível, use variável de ambiente:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "$DATABASE_URL"
      }
    }
  }
}
```

E exporte antes de iniciar o Claude Code:

```bash
export DATABASE_URL="postgresql://anahita:anahita@localhost:5432/anahita"
claude
```

---

## 6. Ordem Sugerida de Implementação

Features organizadas para minimizar dependências entre agentes paralelos:

### Onda 1 (paralelo, sem dependência entre si)

| Agente | Feature | Branch |
|--------|---------|--------|
| A | Scaffolding (pyproject.toml, Dockerfile, docker-compose, alembic init) | `chore/scaffolding` |
| B | Rules Engine (engine/ inteira — Python puro, zero deps externas) | `feature/rules-engine` |

### Onda 2 (após merge da Onda 1)

| Agente | Feature | Branch |
|--------|---------|--------|
| A | Auth (User, AuthProvider, strategies, JWT) | `feature/auth` |
| B | Catalog + Seeds (Race, Class, Spell, Item + dados SRD) | `feature/catalog` |
| C | Core Storage (StorageService ABC + LocalStorageService) | `feature/storage` |

### Onda 3 (após merge da Onda 2)

| Agente | Feature | Branch |
|--------|---------|--------|
| A | Campaigns (Campaign, Member, Invite) | `feature/campaigns` |
| B | Characters (Character + todas as sub-tabelas) | `feature/characters` |

### Onda 4 (após merge da Onda 3)

| Agente | Feature | Branch |
|--------|---------|--------|
| A | Sessions (Session, SessionNote) | `feature/sessions` |
| B | World-building (NPC, Location, Faction + junções) | `feature/world` |

### Onda 5 (após merge da Onda 4)

| Agente | Feature | Branch |
|--------|---------|--------|
| A | Combat (Encounter, Participant, Conditions, WebSocket) | `feature/combat` |
| B | Inventory + Handouts | `feature/inventory-handouts` |

### Onda 6 — Frontend (após backend estável)

| Agente | Feature | Branch |
|--------|---------|--------|
| A | Frontend scaffolding (Next.js, shadcn, tema, layout) | `chore/frontend-scaffolding` |
| B | API client + types (lib/api/, types/) | `feature/frontend-api-client` |

---

## 7. Checklist por Feature

Antes de considerar uma feature pronta para PR:

- [ ] Todos os arquivos do domínio criados (models, domain, schemas, service, router)
- [ ] Alembic migration gerada e testada
- [ ] Testes unitários passando
- [ ] Testes de integração (se aplicável)
- [ ] Type hints completos
- [ ] Commits com conventional commits
- [ ] Sem código comentado ou TODO não planejado
- [ ] Router registrado no main.py
- [ ] Branch atualizada com a release antes do PR
