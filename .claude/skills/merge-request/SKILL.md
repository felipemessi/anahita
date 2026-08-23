---
name: merge-request
description: "Sugere o texto (título + descrição) de um merge/pull request comparando a branch atual com a branch base, sem abrir o PR automaticamente. Depois que o texto for aprovado, registra a entrada correspondente no changelog em docs/. Use quando o usuário disser: crie um PR, texto pra merge request, sugestão de MR, abrir PR, PR aprovado, atualiza o changelog, PR foi mergeado."
---

# Merge Request

Este skill tem dois modos. Identifique qual o usuário quer pelo pedido; se não estiver claro, pergunte.

## Modo 1 — Rascunho de PR (padrão)

Objetivo: **apenas devolver o texto sugerido no chat.** Não rode `gh pr create` nem qualquer comando que efetivamente abra o PR, a menos que o usuário peça explicitamente para abrir.

1. Descubra a branch base. Regra do projeto (`CLAUDE.md`): features usam `release` como base; um PR de `release` para `main` é um lançamento oficial.
   - Se a branch atual começa com `feature/`, `fix/` ou `chore/`, a base é `release`.
   - Se a branch atual é `release`, a base é `main` (lançamento oficial — verifique se é isso que o usuário quer antes de sugerir tag semver).
2. Rode `git log <base>..HEAD --oneline` e `git diff <base>...HEAD --stat` para levantar os commits e arquivos alterados.
3. Monte a sugestão:
   - **Título**: mesmo estilo de commit semântico (`<tipo>: <resumo>`), resumindo a mudança principal do PR.
   - **Descrição**, sempre concisa e objetiva:
     - `## Resumo` — 1-3 linhas do que foi feito e por quê.
     - `## Mudanças` — bullet list derivada dos commits/diff (agrupe por tema se houver muitos commits).
     - `## Testes` — quais testes rodaram/passaram (ex.: `uv run pytest`, `npm test`). Se não houver evidência de testes, avise o usuário em vez de inventar.
     - `## Notas` (opcional) — breaking changes, follow-ups, migrations pendentes (`alembic upgrade` etc.), apenas se relevante.
   - **NUNCA** inclua menção de coautoria/geração por IA (`Co-Authored-By: Claude`, `🤖 Generated with Claude Code` etc.) no corpo sugerido — mesma regra do skill `commit`.
4. Apresente o texto pronto para o usuário copiar.

## Modo 2 — Changelog pós-aprovação

Disparado quando o usuário disser algo como "ok", "aprovado", "atualiza o changelog".

1. Garanta que existe `docs/CHANGELOG.md`; crie seguindo o formato [Keep a Changelog](https://keepachangelog.com/) se ainda não existir, com uma seção `## [Unreleased]` no topo.
2. Descubra o que foi mergeado (`git log` dos commits do PR aprovado, ou peça ao usuário um resumo se não for possível inferir).
3. Dois casos:
   - **Merge de feature/fix/chore → `release`**: adicione as entradas na seção `## [Unreleased]`, agrupadas por tipo de commit (Added/Changed/Fixed/etc., mapeando `feat→Added`, `fix→Fixed`, `refactor`/`chore`/`docs`/`test`→`Changed` ou seção correspondente). Uma linha por mudança relevante, sem jargão de implementação.
   - **Merge `release` → `main` (lançamento oficial)**: transforme `## [Unreleased]` na seção da versão lançada, ex. `## [2026.0.0.1] - 2026-08-22` (peça a tag semver ao usuário se ele não informou — CLAUDE.md exige versionamento semântico nesses lançamentos), e deixe uma nova seção `## [Unreleased]` vazia acima para os próximos merges.
4. Salve o arquivo e mostre o diff da entrada adicionada ao usuário. Não commite automaticamente — use o skill `commit` para isso se o usuário pedir.
