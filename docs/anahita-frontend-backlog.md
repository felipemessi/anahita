# Anahita Frontend — Backlog

**Referência:** `docs/anahita-frontend-prd.md` (arquitetura, rotas, componentes, decisões de UX) e `docs/anahita-backend-backlog.md` (o frontend de uma fase só pode avançar depois que os endpoints correspondentes existirem no backend).

## Como usar este documento

- Marque `[x]` ao concluir uma tarefa. Uma história de usuário só é considerada **pronta** quando todas as tarefas estão marcadas **e** `npm run lint`, `npm run typecheck` e `npm test` (vitest + testing-library) passam para o código tocado.
- Trabalhe uma história por vez, na ordem em que aparecem. Cada história de UI pressupõe o endpoint de backend correspondente já pronto (ver backlog do backend) — se não estiver, comece por lá ou trabalhe com mocks e marque a tarefa de "integração real" como pendente.
- Toda história de tela segue o fluxo: `types/*.ts` → `lib/api/*.ts` → `hooks/use-*.ts` → componente(s) em `components/*/` → rota em `app/**/page.tsx` → teste (vitest + testing-library).
- **Antes de parar uma sessão de trabalho:** atualize a tabela de "Status Geral" abaixo.
- Hoje (branch `release`, commit `06c9f54`) o projeto frontend é só o **esqueleto vazio**: todas as rotas/componentes/libs listados no PRD existem como arquivos de 0 bytes. Nada está marcado como já implementado neste backlog — é ponto de partida real.

---

## Status Geral

| Fase | Domínio                              | Status         | Última atualização |
|------|----------------------------------------|-----------------|----------------------|
| 0    | Fundação de app (providers, auth, API client, locale) | Não iniciado | 2026-08-22 |
| 1    | Campanhas, Personagens, Catálogo       | Não iniciado    | 2026-08-22           |
| 2    | Sessão ao Vivo (Combat Tracker)        | Não iniciado    | —                    |
| 3    | World-building                          | Não iniciado    | —                    |
| 4    | Loot, Inventário e Handouts             | Não iniciado    | —                    |
| 5    | Registro e Lore                         | Não iniciado    | —                    |

---

## Fase 0 — Fundação de App

> Objetivo: ter o esqueleto do Next.js funcional — providers, autenticação, cliente de API, tema e locale — antes de construir qualquer tela de domínio. Depende do backend Fase 1 (auth) já pronto.

- **Como usuário, quero abrir o app e ver a landing/dashboard renderizados com o tema visual correto.**
  - [ ] `app/layout.tsx`: providers (`QueryProvider`, `ThemeProvider`), fontes (DM Sans + Space Mono), `styles/globals.css` com CSS variables do tema (deep navy + gold, dark padrão)
  - [ ] `providers/query-provider.tsx`, `providers/theme-provider.tsx`
  - [ ] `app/page.tsx`: landing simples (CTA login/registro)
  - [ ] Configurar `next.config.ts` com `output: 'standalone'`
  - [ ] Teste: layout renderiza sem erros (smoke test)

- **Como usuário, quero fazer login/registro e ter minha sessão mantida entre navegações.**
  - [ ] `lib/api/client.ts`: fetch client-side, access token em memória, refresh automático em 401
  - [ ] `lib/api/server.ts`: fetch server-side propagando cookie de refresh token
  - [ ] `lib/auth/session.ts`, `lib/auth/middleware.ts`: leitura de sessão + proteção de rotas (`middleware.ts` redireciona para `/auth/login`)
  - [ ] `app/auth/login/page.tsx`, `app/auth/register/page.tsx`
  - [ ] Teste: middleware bloqueia rota protegida sem sessão; libera com sessão válida
  - [ ] Teste: formulário de login chama a API e trata erro de credenciais inválidas

- **Como usuário, quero escolher o idioma em que vejo o catálogo (SRD) da campanha.**
  - [ ] `lib/i18n/locale.ts`: leitura/escrita do cookie `anahita_locale`, default `en`
  - [ ] `components/catalog/locale-switcher.tsx` no header
  - [ ] `lib/api/client.ts`/`server.ts`: anexar `?locale=` em chamadas a `lib/api/catalog.ts`
  - [ ] Teste: trocar locale invalida o cache de catálogo do TanStack Query

- **Como desenvolvedor, quero os tipos base espelhando os schemas do backend antes de construir telas.**
  - [ ] `types/campaign.ts`, `types/character.ts`, `types/catalog.ts` (24 categorias + `translations`), `types/session.ts`, `types/combat.ts`, `types/world.ts`, `types/handout.ts`, `types/inventory.ts`
  - [ ] Conferir que cada tipo bate com o `schemas.py` Pydantic correspondente no backend (checagem manual, não há geração automática por ora)

---

## Fase 1 — Campanhas, Personagens, Catálogo

> Depende do backend Fase 0 (catálogo) e Fase 1 (campaigns/characters).

- **Como usuário, quero ver e criar campanhas.**
  - [ ] `lib/api/campaigns.ts`, `hooks/use-campaign.ts`
  - [ ] `app/campaigns/page.tsx`: lista com role (DM/Player), status, última sessão; botão criar campanha + inserir código de convite
  - [ ] `app/campaigns/[campaignId]/page.tsx`: dashboard (próxima sessão, personagens ativos, atividade recente; para DM: notas rápidas, NPCs/locais recentes, handouts pendentes)
  - [ ] `app/campaigns/[campaignId]/layout.tsx` + `components/layout/campaign-sidebar.tsx`, `header.tsx`, `mobile-nav.tsx`
  - [ ] `app/join/[inviteCode]/page.tsx`: aceitar convite
  - [ ] Testes: lista renderiza campanhas do usuário; criar campanha chama a API e redireciona

- **Como DM, quero gerenciar membros e configurações da campanha.**
  - [ ] `app/campaigns/[campaignId]/settings/page.tsx`: membros, gerar convite, configurações gerais
  - [ ] Teste: apenas DM vê ações de gestão de membros (Player vê read-only)

- **Como jogador/DM, quero navegar pelo catálogo do SRD e da campanha (races, classes, spells, equipment, magic-items, monsters, backgrounds, feats, rules).**
  - [ ] `lib/api/catalog.ts`, `hooks/use-catalog.ts` (lista, detalhe, busca — aware de locale)
  - [ ] `app/campaigns/[campaignId]/catalog/page.tsx`: hub com abas por categoria
  - [ ] `app/campaigns/[campaignId]/catalog/[category]/page.tsx` + `components/catalog/catalog-list.tsx`, `catalog-filter-bar.tsx`
  - [ ] `app/campaigns/[campaignId]/catalog/[category]/[entryId]/page.tsx` + `components/catalog/catalog-entry-detail.tsx`
  - [ ] `components/catalog/monster-stat-block.tsx` (renderiza um `Monster` completo — reaproveitado em World e Combat)
  - [ ] Testes: lista filtra por busca; badge SRD vs. homebrew aparece corretamente

- **Como DM, quero criar conteúdo homebrew (raça, classe, magia, item, monstro, etc.) preso à minha campanha.**
  - [ ] `app/campaigns/[campaignId]/catalog/[category]/new/page.tsx` + `components/catalog/custom-entry-form.tsx` (formulário adaptado por categoria — pelo menos races/classes/spells/items/monsters na v1)
  - [ ] Regra de UI: form nunca expõe campo `campaign_id` — é sempre implícito pela rota atual
  - [ ] Regra de UI: botão "criar homebrew" só aparece para `role=dm`
  - [ ] Teste: form envia `is_custom=true` + `campaign_id` da campanha atual automaticamente; Player não vê o botão

- **Como jogador, quero criar minha ficha de personagem guiado por um wizard.**
  - [ ] `lib/api/characters.ts`, `hooks/use-character.ts`
  - [ ] `app/campaigns/[campaignId]/characters/new/page.tsx` + `components/characters/creation-wizard/{step-race,step-class,step-background,step-ability-scores,step-equipment,step-review}.tsx`
  - [ ] Cada etapa consome o catálogo da campanha (SRD + homebrew) via `use-catalog.ts`; opções seguintes dependem de escolhas anteriores (perícias dependem da classe, etc.)
  - [ ] `lib/utils/dnd-rules.ts`: espelho client-side dos cálculos da rules engine (modifier, proficiency bonus, skill bonus) para feedback instantâneo no wizard
  - [ ] Teste: fluxo completo do wizard gera o payload correto para `POST /characters`
  - [ ] Teste: `dnd-rules.ts` bate com casos de teste conhecidos (mesmos usados no backend `engine/`)

- **Como jogador, quero ver e editar minha ficha de personagem.**
  - [ ] `app/campaigns/[campaignId]/characters/page.tsx`: lista de personagens da campanha
  - [ ] `app/campaigns/[campaignId]/characters/[characterId]/page.tsx` + `components/characters/character-sheet.tsx`, `ability-scores.tsx`, `skill-list.tsx`, `spell-slots.tsx`
  - [ ] Seções: cabeçalho, ability scores (grid 2x3), skills, combat (AC/HP editável inline/speed/iniciativa), spells, equipment, features
  - [ ] HP editável inline: mutação otimista via TanStack Query
  - [ ] Teste: edição de HP atualiza a UI antes da resposta do servidor (otimista) e reverte em caso de erro

---

## Fase 2 — Sessão ao Vivo (Combat Tracker)

> Depende do backend Fase 2 (encounters + WebSocket).

- **Como DM, quero gerenciar sessões e suas notas.**
  - [ ] `lib/api/sessions.ts`, `hooks/use-session.ts`
  - [ ] `app/campaigns/[campaignId]/sessions/page.tsx` + `components/sessions/session-card.tsx`
  - [ ] `app/campaigns/[campaignId]/sessions/[sessionId]/page.tsx` + `components/sessions/note-editor.tsx`, `quick-note.tsx`
  - [ ] Regra de UI: notas privadas (`is_private`) só aparecem para o DM
  - [ ] Teste: Player não vê notas privadas de outro autor

- **Como DM, quero um combat tracker mobile-first para rodar combates na mesa.**
  - [ ] `lib/ws/combat-socket.ts`, `lib/ws/types.ts`, `providers/combat-provider.tsx`, `hooks/use-combat.ts`
  - [ ] `app/campaigns/[campaignId]/combat/[encounterId]/layout.tsx` (fullscreen mobile, esconde sidebar/header) + `page.tsx`
  - [ ] `components/combat/initiative-tracker.tsx`, `participant-card.tsx` (nome, barra de HP, badge de AC, badges de condição, destaque do turno atual)
  - [ ] Reconexão: ao reconectar, processa `state_sync` e resincroniza a UI
  - [ ] Teste: `combat-provider` processa `turn_advanced`/`participant_updated`/`encounter_status_changed` corretamente

- **Como DM, quero ações rápidas de dano/cura/condição em poucos taps.**
  - [ ] `components/combat/damage-dialog.tsx`: input numérico +/- com confirmação (menos de 3 taps)
  - [ ] `components/combat/condition-badges.tsx`: toggle de condições (tap adiciona/remove)
  - [ ] `components/combat/turn-indicator.tsx`: botão fixo no rodapé "avançar turno"
  - [ ] `components/combat/monster-picker.tsx`: busca no catálogo de `Monster` ao adicionar participante, autocompleta HP/AC/nome; alternativa de form manual para NPCs sem stat block
  - [ ] Teste: dialog de dano envia o evento WS correto (`update_participant`)
  - [ ] Teste: `monster-picker` autocompleta os campos ao selecionar um monstro do catálogo

- **Como jogador, quero acompanhar o combate em tempo real sem poder alterar nada.**
  - [ ] Visão read-only do tracker (mesmos componentes, sem os controles de ação do DM)
  - [ ] Teste: jogador não vê botões de ação; UI atualiza via WS mesmo assim

---

## Fase 3 — World-building

> Depende do backend Fase 3.

- **Como DM, quero cadastrar e organizar NPCs, locais e facções.**
  - [ ] `lib/api/world.ts`, `hooks/use-world.ts`
  - [ ] `app/campaigns/[campaignId]/world/page.tsx`: hub com três seções
  - [ ] `app/campaigns/[campaignId]/world/npcs/page.tsx` + `components/world/npc-card.tsx` (nome, raça, ocupação, facções; botão "ver stat block" quando `stat_block_id` existe, reaproveitando `monster-stat-block.tsx`)
  - [ ] `app/campaigns/[campaignId]/world/locations/page.tsx` + `components/world/location-tree.tsx` (árvore expansível região→cidade→taverna)
  - [ ] `app/campaigns/[campaignId]/world/factions/page.tsx` + `components/world/faction-graph.tsx` (lista de relações ou grafo simples)
  - [ ] `components/world/entity-link-badge.tsx`: badges de vínculo (sessões, facções, locais)
  - [ ] Testes: árvore de locations renderiza hierarquia correta; NPC card mostra stat block quando aplicável

- **Como DM, quero buscar por nome/descrição em NPCs, locais e facções.**
  - [ ] Campo de busca no hub de world, chamando o endpoint de full-text search do backend
  - [ ] Teste: busca retorna resultados combinando as três entidades

---

## Fase 4 — Loot, Inventário e Handouts

> Depende do backend Fase 4. **Nota:** as pastas `app/.../handouts/` e `components/handouts/` ainda nem existem no esqueleto atual — precisam ser criadas nesta fase (não foram scaffoldadas junto com o resto).

- **Como grupo, quero ver e gerenciar o inventário compartilhado da campanha.**
  - [ ] `lib/api/inventory.ts`, `hooks/use-inventory.ts`
  - [ ] `app/campaigns/[campaignId]/inventory/page.tsx` + `components/inventory/loot-table.tsx`, `item-card.tsx`
  - [ ] Teste: lista de inventário renderiza itens do catálogo (incluindo magic items) e itens custom

- **Como DM, quero criar e revelar handouts para os jogadores.**
  - [ ] Criar `app/campaigns/[campaignId]/handouts/page.tsx`, `lib/api/handouts.ts`, `hooks/use-handouts.ts`
  - [ ] `components/handouts/handout-card.tsx`, `handout-reveal-button.tsx`, `handout-viewer.tsx`
  - [ ] Visão DM: lista completa, toggle reveal/hide, upload de imagem/mapa, editor de texto, filtro por sessão
  - [ ] Visão jogador: só handouts revelados, galeria de imagens em tamanho grande
  - [ ] Reveal em tempo real: escutar evento `handout_revealed` no WebSocket de combat ativo (reaproveita `combat-provider`/`lib/ws`)
  - [ ] Teste: jogador só vê handouts com `is_revealed=true`; reveal via WS atualiza a UI do jogador sem reload

---

## Fase 5 — Registro e Lore

*(Ainda não detalhado — depende do backend Fase 5, também pendente de levantamento de requisitos.)*

- [ ] Quebrar em histórias de usuário quando o backend definir o modelo de Diário/Recap/Timeline/Wiki
