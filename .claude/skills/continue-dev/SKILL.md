---
name: continue-dev
description: "Avança o desenvolvimento do Anahita pelos backlogs (docs/anahita-backend-backlog.md e docs/anahita-frontend-backlog.md), uma história de usuário por vez, fase por fase — backend primeiro, depois o frontend da mesma fase. Ao fechar uma fase, registra lacunas encontradas, atualiza o changelog, commita e mergeia em release, e pergunta se deve seguir pra próxima fase. Use quando o usuário disser: continue desenvolvendo, continua o backlog, avança a próxima história, próxima etapa, segue o desenvolvimento, continua o Anahita."
---

# Continue Dev

Motor de continuação do desenvolvimento do Anahita entre sessões. Sempre que invocado, retoma exatamente de onde o projeto parou — sem precisar que o usuário reexplique contexto.

## 0. Descubra onde o projeto está

1. Rode `git status` e `git branch` — a árvore deve estar limpa e em `release` (ou `main`) antes de começar. Se houver uma branch `feature/`/`fix/`/`chore/` com trabalho pendente, é sinal de uma história interrompida no meio: retome nela em vez de criar uma nova (pule para a seção 2 direto com essa história).
2. Leia a tabela **Status Geral** de `docs/anahita-backend-backlog.md` e de `docs/anahita-frontend-backlog.md`.
3. Determine a fase-alvo com esta prioridade:
   - **Primeiro**, qualquer fase (backend ou backend) já com status "Em andamento" ou parcialmente marcada (`[x]` misturado com `[ ]`) — termine essa antes de tudo, mesmo que uma fase numericamente anterior já esteja fechada em algum dos dois lados.
   - **Senão**, ache o menor número de fase N tal que o backend da fase N não esteja "Completo" OU o frontend da fase N não esteja "Concluída". Dentro dessa fase N: se o backend ainda não está completo, trabalhe o backend da fase N primeiro; só depois de fechá-lo (changelog + merge, ver seção 4) siga pro frontend da fase N. Se o backend da fase N já está completo mas o frontend não, vá direto pro frontend da fase N.
   - Respeite as dependências explícitas escritas no cabeçalho de cada fase do backlog do frontend (ex. "Depende do backend Fase 3") — nunca comece uma história de frontend cujo endpoint de backend ainda não existe.
4. Anuncie ao usuário, em uma linha, qual fase e domínio (backend/frontend) você vai trabalhar e por quê (retomando uma fase incompleta vs. começando a próxima).

## 1. Antes de começar uma história

- Releia a seção do PRD referenciada pela fase (`docs/anahita-backend-prd.md` ou `docs/anahita-frontend-prd.md`) para os detalhes de modelo/UX daquela história.
- Confirme que a branch local `release` está atualizada: `git checkout release && git pull --ff-only`.
- Crie a branch da história a partir de `release`, seguindo a convenção do `CLAUDE.md`: `feature/<domínio>-<descrição>` (ex. `feature/sessions-notes`, `feature/combat-tracker-ws`).

## 2. Implemente uma história por vez

Trabalhe as histórias da fase **na ordem em que aparecem no backlog** — há dependências entre elas.

- **Backend**: siga o fluxo padrão do domínio (PRD §9.1): `models.py` → migração Alembic → `schemas.py` → `service.py` → `router.py` → testes pytest. Rode `uv run task lint`, `uv run task typecheck` e `uv run task test` (equivalentes a `ruff check`, `mypy`, `pytest`) antes de considerar a história pronta.
- **Frontend**: siga o fluxo `types/*.ts` → `lib/api/*.ts` → `hooks/use-*.ts` → componente(s) em `components/*/` → rota em `app/**/page.tsx` → teste. Rode `npm run lint`, `npm run typecheck` e `npm test` antes de considerar a história pronta.
- **Lacunas mecânicas** (endpoint faltando, campo de schema faltando, mismatch simples entre o que o frontend precisa e o que o backend expõe) descobertas no meio de uma história: resolva inline como parte da própria história (mesmo padrão usado nas lacunas da Fase 1 — implemente o endpoint/campo que falta, sem abrir uma história separada), e documente o que foi preenchido na nota da história.
- **Ambiguidades de verdade** (decisão de produto/design sem resposta óbvia, múltiplos caminhos válidos com trade-offs diferentes, ou algo que muda o escopo combinado com o usuário): **pare e pergunte antes de continuar** — isso não é uma lacuna mecânica, é uma decisão do usuário. Não adivinhe.
- Ao terminar a história (checkboxes todos `[x]`, testes/lint/typecheck limpos): marque `[x]` no backlog com `✅ (data de hoje)` no título da história e um bullet de `Notas:` explicando decisões não óbvias — mesmo estilo já usado no restante do arquivo.
- Commite (convenção do skill `commit`: conventional commits, em inglês, sem menção de coautoria de IA), mergeie em `release` com `--no-ff` e uma mensagem `merge: <resumo> into release`, dê `push`, e apague a branch local (`git branch -d`) — mantendo só `main`/`release` localmente.
- **Continue automaticamente para a próxima história da fase**, sem parar para check-in a cada uma — só pare no meio se cair em uma ambiguidade de verdade (acima) ou se o usuário interromper.

## 3. Fechando a fase — lacunas remanescentes

Quando todas as histórias listadas da fase estiverem `[x]`:

1. Revise as notas que você foi deixando: alguma lacuna foi **deliberadamente adiada** (não resolvida inline porque dependia de outra fase, escopo maior, ou não era estritamente necessária para a história em questão)?
2. Se sim, adicione uma história extra no final da seção da fase no backlog, no mesmo formato das demais, ex. `**Lacunas descobertas na Fase N — pendentes de decisão.**`, com um checkbox por lacuna e uma linha explicando o que falta e por quê não foi resolvido junto.
3. Pergunte ao usuário: **resolver essas lacunas agora (como mais uma história desta fase, antes de fechar) ou deixar em aberto para uma sessão futura e seguir em frente?**
   - Se "resolver agora": trate cada uma como uma história normal (volte à seção 2) antes de prosseguir.
   - Se "deixar em aberto": mantenha os checkboxes `[ ]` no backlog (não invente que foi resolvido) e siga para o changelog mesmo assim.
4. Se não houver nenhuma lacuna deliberadamente adiada, siga direto para o changelog.

## 4. Changelog e merge de fechamento de fase

1. Atualize a linha da fase na tabela **Status Geral** do backlog correspondente (status + data).
2. Adicione as entradas da fase em `docs/CHANGELOG.md`, seção `## [Unreleased]` — use o modo 2 do skill `merge-request` como referência de formato (`feat`→`Added`, `fix`→`Fixed`, etc.), um bullet por história relevante, sem jargão de implementação, no mesmo estilo das entradas já existentes (uma por história, mencionando fase e número).
3. Crie uma branch `chore/changelog-<fase>-<domínio>`, commite (`docs: log <fase> <domínio> in changelog`), mergeie em `release` com `--no-ff`, dê `push`, apague a branch.

## 5. Pergunte antes de avançar

Depois do merge do changelog, pare e pergunte ao usuário se deseja continuar para a próxima fase (nomeie qual seria, seguindo a ordem da seção 0). Nunca encadeie fases automaticamente sem essa confirmação — mesmo que a fase seguinte pareça óbvia.

## Notas gerais

- Nunca marque uma tarefa como `[x]` sem o teste correspondente passando de verdade — as próximas sessões confiam nesses checkboxes.
- Nunca invente que uma lacuna foi resolvida; se ficou pendente, deixe `[ ]` e diga isso explicitamente.
- Se o usuário interromper no meio de uma fase, a próxima invocação deste skill deve detectar a branch/história em andamento (seção 0, passo 1) e retomar dali — não recomeçar a fase do zero.
