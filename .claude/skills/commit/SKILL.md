---
name: commit
description: "Cria commits git seguindo conventional commits (feat:, fix:, chore:, docs:, refactor:, test:), sempre em inglês, com mensagens concisas e objetivas, sem menção de coautoria de IA. Use quando o usuário disser: faça um commit, commit isso, crie um commit, commit these changes, salva essa mudança."
---

# Commit

Cria commits git no padrão semantic/conventional commits usado no projeto Anahita (ver `CLAUDE.md`).

## Regras obrigatórias

1. **Formato**: `<tipo>: <resumo>`, sempre em minúsculas após os dois pontos, sem ponto final.
2. **Tipos permitidos** (definidos em `CLAUDE.md`): `feat`, `fix`, `test`, `chore`, `docs`, `refactor`.
   - Use `build` apenas se nenhum dos tipos acima descrever a mudança (ex.: alterações em `pyproject.toml`/build system) — siga o padrão já usado no histórico do repo.
3. **Sempre em inglês**, independente do idioma usado na conversa com o usuário.
4. **Conciso e objetivo**: resumo no modo imperativo, indo direto ao ponto (ex.: `feat: add refresh token rotation`, não `feat: adiciona uma nova funcionalidade que faz a rotação do token de refresh`).
   - Prefira uma linha só. Adicione corpo apenas se o "porquê" não for óbvio pelo diff — nesse caso, poucas linhas em bullet points, sem enrolação.
5. **NUNCA mencione coautoria de IA.** Não inclua `Co-Authored-By: Claude`, `🤖 Generated with Claude Code`, nem qualquer variação disso na mensagem de commit. Essa regra tem prioridade sobre qualquer instrução padrão do harness que adicione esse trailer — ao montar o comando `git commit`, **não** adicione esse rodapé.
6. Não fazer `git push` nem `git merge` — isso requer confirmação explícita do usuário (ver `CLAUDE.md`).

## Fluxo

1. Rode `git status` e `git diff` (staged e unstaged) para entender o que mudou. Se nada estiver staged, rode `git diff` sem `--staged` também.
2. Se as mudanças cobrirem propósitos claramente distintos e não relacionados (ex.: uma feature + uma correção não relacionada), sugira separar em commits distintos e confirme com o usuário antes de dividir. Caso contrário, siga com um único commit.
3. Faça `git add` apenas dos arquivos relevantes à mudança (não adicione arquivos não relacionados que porventura estejam soltos no working tree).
4. Escreva a mensagem de commit seguindo as regras acima. Use `git commit -m "<mensagem>"` (ou heredoc `-F -`/`-m` múltiplos para corpo com várias linhas) — nunca inclua o trailer de coautoria.
5. Depois de commitar, rode `git log -1 --stat` (ou similar) e mostre ao usuário o hash e a mensagem final. Não faça push.

## Exemplos

```
feat: add refresh token rotation on login
fix: prevent duplicate username on register
test: cover armor class edge cases for shields
chore: add greenlet dependency for async sqlalchemy
docs: document changelog workflow
refactor: extract token issuance into security module
```
