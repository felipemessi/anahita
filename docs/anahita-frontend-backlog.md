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
| 0    | Fundação de app (providers, auth, API client, locale) | Concluída       | 2026-08-23           |
| 1    | Campanhas, Personagens, Catálogo       | Concluída (todas as lacunas de backend identificadas foram implementadas e integradas — ver notas de cada história) | 2026-08-23 |
| 2    | Sessão ao Vivo (Combat Tracker)        | Em andamento (história 1/4 concluída)    | 2026-08-23           |
| 3    | World-building                          | Não iniciado    | —                    |
| 4    | Loot, Inventário e Handouts             | Não iniciado    | —                    |
| 5    | Registro e Lore                         | Não iniciado    | —                    |

---

## Fase 0 — Fundação de App

> Objetivo: ter o esqueleto do Next.js funcional — providers, autenticação, cliente de API, tema e locale — antes de construir qualquer tela de domínio. Depende do backend Fase 1 (auth) já pronto.

- **Como usuário, quero abrir o app e ver a landing/dashboard renderizados com o tema visual correto.** ✅ (2026-08-23)
  - [x] `app/layout.tsx`: providers (`QueryProvider`, `ThemeProvider`), fontes (DM Sans + Space Mono), `styles/globals.css` com CSS variables do tema (deep navy + gold, dark padrão)
  - [x] `providers/query-provider.tsx`, `providers/theme-provider.tsx`
  - [x] `app/page.tsx`: landing simples (CTA login/registro)
  - [x] Configurar `next.config.ts` com `output: 'standalone'`
  - [x] Teste: layout renderiza sem erros (smoke test)
  - Notas: projeto Next.js bootstrapado do zero (package.json/tsconfig/tailwind/eslint/vitest estavam vazios — Fase 0 real começa aqui). Stack: Next 15 + React 19 + Tailwind v3 (CSS vars) + next-themes + TanStack Query v5 + Vitest/RTL. `lint`, `typecheck` e `test` passam. `next build` completo ainda falha, como esperado — as demais páginas do esqueleto (`auth/`, `campaigns/`, etc.) continuam como stubs de 0 bytes até suas próprias histórias.

- **Como usuário, quero fazer login/registro e ter minha sessão mantida entre navegações.** ✅ (2026-08-23)
  - [x] `lib/api/client.ts`: fetch client-side, access token em memória, refresh automático em 401
  - [x] `lib/api/server.ts`: fetch server-side propagando cookie de refresh token
  - [x] `lib/auth/session.ts`, `lib/auth/middleware.ts`: leitura de sessão + proteção de rotas (`middleware.ts` redireciona para `/auth/login`)
  - [x] `app/auth/login/page.tsx`, `app/auth/register/page.tsx`
  - [x] Teste: middleware bloqueia rota protegida sem sessão; libera com sessão válida
  - [x] Teste: formulário de login chama a API e trata erro de credenciais inválidas
  - Notas: backend não tem endpoint `/auth/me`/users — o JWT de acesso só carrega `sub` (user id), então `lib/auth/session.ts` decodifica isso client-side (sem verificar assinatura, só para UI) e não expõe username/email ainda; isso deverá ser resolvido quando o backend expuser perfil do usuário (possivelmente já na Fase 1, dashboard de campanhas). Criado também `src/middleware.ts` (não listado no backlog, mas exigido pela convenção do Next.js para o middleware ser de fato carregado) que delega para `lib/auth/middleware.ts::authMiddleware`. `lib/api/server.ts` resolve o access token chamando `/auth/refresh` diretamente com o cookie de refresh propagado (em vez de um Route Handler interno dedicado — mais simples e equivalente). Novas env vars: `NEXT_PUBLIC_API_URL` (client) e `ANAHITA_API_URL` (server), documentadas em `.env.example`.

- **Como usuário, quero escolher o idioma em que vejo o catálogo (SRD) da campanha.** ✅ (2026-08-23)
  - [x] `lib/i18n/locale.ts`: leitura/escrita do cookie `anahita_locale`, default `en`
  - [x] `components/catalog/locale-switcher.tsx` no header
  - [x] `lib/api/client.ts`/`server.ts`: anexar `?locale=` em chamadas a `lib/api/catalog.ts`
  - [x] Teste: trocar locale invalida o cache de catálogo do TanStack Query
  - Notas: `lib/api/catalog.ts` ainda não existe (é da Fase 1) — `apiFetch`/`serverApiFetch` ganharam um parâmetro opcional `locale` genérico que já anexa `?locale=`, pronto para o `catalog.ts` da Fase 1 usar. `locale-switcher.tsx` ainda não está montado em nenhum header real (`components/layout/header.tsx` também é Fase 1); ele exporta `CATALOG_QUERY_KEY_PREFIX = ["catalog"]`, que `hooks/use-catalog.ts` (Fase 1) deve usar como prefixo de toda query key de catálogo para a invalidação funcionar.

- **Como desenvolvedor, quero os tipos base espelhando os schemas do backend antes de construir telas.** ✅ (2026-08-23)
  - [x] `types/campaign.ts`, `types/character.ts`, `types/catalog.ts` (24 categorias + `translations`), `types/session.ts`, `types/combat.ts`, `types/world.ts`, `types/handout.ts`, `types/inventory.ts`
  - [x] Conferir que cada tipo bate com o `schemas.py` Pydantic correspondente no backend (checagem manual, não há geração automática por ora)
  - Notas: `campaign.ts`, `character.ts`, `catalog.ts` e `session.ts` foram conferidos linha a linha contra `backend/app/{campaigns,characters,catalog,sessions}/schemas.py` + `domain.py` — batem. `catalog.ts` não tem campo `translations` bruto porque o backend já resolve o texto traduzido no servidor via `?locale=` antes de responder (schemas trazem `name`/`description` já resolvidos, não um blob de traduções) — a menção a "translations" no backlog está desatualizada em relação à implementação real. `combat.ts`, `world.ts`, `handout.ts`, `inventory.ts` são **provisórios**: os domínios de backend correspondentes (Fases 2–4) ainda não existem, então foram espelhados a partir do modelo de dados descrito em `docs/anahita-backend-prd.md` §7.6–7.9 — precisam ser reconferidos contra o `schemas.py` real assim que cada domínio for implementado no backend.

---

## Fase 1 — Campanhas, Personagens, Catálogo

> Depende do backend Fase 0 (catálogo) e Fase 1 (campaigns/characters).

- **Como usuário, quero ver e criar campanhas.** ✅ (2026-08-23)
  - [x] `lib/api/campaigns.ts`, `hooks/use-campaign.ts`
  - [x] `app/campaigns/page.tsx`: lista com role (DM/Player), status, última sessão; botão criar campanha + inserir código de convite
  - [x] `app/campaigns/[campaignId]/page.tsx`: dashboard (próxima sessão, personagens ativos, atividade recente; para DM: notas rápidas, NPCs/locais recentes, handouts pendentes)
  - [x] `app/campaigns/[campaignId]/layout.tsx` + `components/layout/campaign-sidebar.tsx`, `header.tsx`, `mobile-nav.tsx`
  - [x] `app/join/[inviteCode]/page.tsx`: aceitar convite
  - [x] Testes: lista renderiza campanhas do usuário; criar campanha chama a API e redireciona
  - Notas: `GET /campaigns/{id}` (detalhe) e "personagens ativos" (via `GET /characters?campaign_id=`) agora são integração real — backend ganhou esses endpoints numa leva de lacunas descobertas pelo frontend (ver `docs/anahita-backend-backlog.md`, "Lacunas descobertas pelo frontend"). `useCampaign(id)` chama `getCampaign()` diretamente (não deriva mais de `useCampaigns()`). "role" na lista de `/campaigns` (`app/campaigns/page.tsx`) continua aproximada por `owner_id === user.id` — o backend não retorna role em lote na listagem, só por campanha via `/members/me` ou `/members`; não fizemos N chamadas extra por linha da lista para não sobrecarregar a tela inicial. "Última sessão", "NPCs/locais recentes" e "handouts pendentes" continuam placeholders "em breve" — dependem das Fases 2-4 do backend, ainda não implementadas. Aproveitado `GET /auth/me` (task separada desta sessão): `lib/auth/session.ts` agora busca o perfil real via `getCurrentUser()` em vez de decodificar o JWT client-side; `header.tsx` exibe o `username` real.

- **Como DM, quero gerenciar membros e configurações da campanha.** ✅ (2026-08-23)
  - [x] `app/campaigns/[campaignId]/settings/page.tsx`: membros, gerar convite, configurações gerais
  - [x] Teste: apenas DM vê ações de gestão de membros (Player vê read-only)
  - Notas: geração de convite (`POST /campaigns/{id}/invites`) e lista de membros (`GET /campaigns/{id}/members`, agora implementado no backend) são integração real. Membros exibem `user_id` bruto — não há endpoint em lote para resolver username/email por id (`GET /auth/me` só retorna o usuário logado); resolver isso fica para uma iteração futura se a UI precisar de nomes. Edição de configurações gerais (nome/descrição/setting) continua placeholder — backend não tem `PATCH /campaigns/{id}`. Refatorado `app/campaigns/[campaignId]/{layout,page,settings/page}.tsx` e `app/join/[inviteCode]/page.tsx` para ler o param de rota via `useParams()` (next/navigation) em vez de `use(params)` — mais simples de testar em Client Components e evita suspense sem boundary.

- **Como jogador/DM, quero navegar pelo catálogo do SRD e da campanha (races, classes, spells, equipment, magic-items, monsters, backgrounds, feats, rules).** ✅ (2026-08-23)
  - [x] `lib/api/catalog.ts`, `hooks/use-catalog.ts` (lista, detalhe, busca — aware de locale)
  - [x] `app/campaigns/[campaignId]/catalog/page.tsx`: hub com abas por categoria
  - [x] `app/campaigns/[campaignId]/catalog/[category]/page.tsx` + `components/catalog/catalog-list.tsx`, `catalog-filter-bar.tsx`
  - [x] `app/campaigns/[campaignId]/catalog/[category]/[entryId]/page.tsx` + `components/catalog/catalog-entry-detail.tsx`
  - [x] `components/catalog/monster-stat-block.tsx` (renderiza um `Monster` completo — reaproveitado em World e Combat)
  - [x] Testes: lista filtra por busca; badge SRD vs. homebrew aparece corretamente
  - Notas: `lib/api/catalog.ts` mapeia as 9 categorias para os paths reais do backend (`equipment` → `/catalog/items`, o único que não bate 1:1). `hooks/use-catalog.ts` reaproveita `CATALOG_QUERY_KEY_PREFIX` de `locale-switcher.tsx` (Fase 0) para que a troca de locale invalide todas as queries de catálogo. Todo `useCatalogList` chamado a partir de uma rota de campanha (hub de catálogo e os 3 passos do wizard que consomem catálogo) passa `campaign_id` — o backend só passou a aceitar esse filtro nesta sessão (antes a listagem sempre trazia homebrew de *todas* as campanhas quando `include_custom=true`, um vazamento de dados corrigido junto com a criação de homebrew). `catalog-entry-detail.tsx` só tem renderização dedicada para `monsters` (via `monster-stat-block.tsx`); as outras 8 categorias caem num fallback genérico (nome/descrição + dump JSON dos campos restantes num `<details>`) — renderização específica por categoria (traits de raça, progressão de classe, componentes de magia etc.) fica para uma iteração futura. `catalog-filter-bar.tsx` cobre busca por nome (usado pelo teste); filtros específicos por categoria (nível/escola em spells, tipo em equipment, CR em monsters) ainda não foram implementados — a API já aceita `filters` genéricos para isso.

- **Como DM, quero criar conteúdo homebrew (raça, classe, magia, item, monstro, etc.) preso à minha campanha.** ✅ (2026-08-23)
  - [x] `app/campaigns/[campaignId]/catalog/[category]/new/page.tsx` + `components/catalog/custom-entry-form.tsx` (formulário adaptado por categoria — pelo menos races/classes/spells/items/monsters na v1)
  - [x] Regra de UI: form nunca expõe campo `campaign_id` — é sempre implícito pela rota atual
  - [x] Regra de UI: botão "criar homebrew" só aparece para `role=dm`
  - [x] Teste: form envia `is_custom=true` + `campaign_id` da campanha atual automaticamente; Player não vê o botão
  - Notas: integração real — o backend ganhou `POST /catalog/{races,classes,spells,items,monsters}` (escopado a `campaign_id`, só DM, `is_custom=True` sempre forçado no service, nunca aceito do cliente além do próprio `campaign_id`; ver `docs/anahita-backend-backlog.md`, "Lacunas descobertas pelo frontend"). Campos específicos por categoria implementados para classes/spells/equipment/monsters (races usa só nome+descrição); magic-items/backgrounds/feats/rules **não** ganharam criação nesta leva — fora do v1 do form do frontend e do backend. Item homebrew deriva a categoria de equipamento a partir de `item_type` (mapeamento fixo para uma categoria SRD já semeada); Spell exige que `school` bata com um `MagicSchool.index` semeado (ex. `evocation`) — escola inexistente retorna 422, que o form mostra como "backend ainda não aceita criação de homebrew nesta categoria" (mensagem genérica, não distingue esse caso específico de outros erros de validação — melhoria futura). Monster homebrew usa defaults sãos para os campos fora do form v1 (`hit_dice="1d8"`, atributos 10, `xp=0`).

- **Como jogador, quero criar minha ficha de personagem guiado por um wizard.** ✅ (2026-08-23)
  - [x] `lib/api/characters.ts`, `hooks/use-character.ts`
  - [x] `app/campaigns/[campaignId]/characters/new/page.tsx` + `components/characters/creation-wizard/{step-race,step-class,step-background,step-ability-scores,step-equipment,step-review}.tsx`
  - [x] Cada etapa consome o catálogo da campanha (SRD + homebrew) via `use-catalog.ts`; opções seguintes dependem de escolhas anteriores (perícias dependem da classe, etc.)
  - [x] `lib/utils/dnd-rules.ts`: espelho client-side dos cálculos da rules engine (modifier, proficiency bonus, skill bonus) para feedback instantâneo no wizard
  - [x] Teste: fluxo completo do wizard gera o payload correto para `POST /characters`
  - [x] Teste: `dnd-rules.ts` bate com casos de teste conhecidos (mesmos usados no backend `engine/`)
  - Notas: wizard implementado como componente único com estado local por passo (não rotas por etapa — não exigido pelo backlog). `CharacterCreate` do backend não tem campo de equipamento inicial — `step-equipment.tsx` é só informativo (mostra o equipamento do antecedente escolhido via catálogo, sem enviar nada). `background` no payload é sempre o **nome** do antecedente escolhido no catálogo (`CharacterCreate.background` é texto livre no backend, não uma referência de id). Perícias disponíveis por classe (dependência mencionada no backlog) não foram modeladas — `CharacterCreate` não tem campo de seleção de perícias; skills vêm calculadas pelo backend na leitura da ficha. `dnd-rules.ts` espelha `backend/engine/abilities.py` fórmula a fórmula, com os mesmos casos de `backend/tests/engine/test_abilities.py` portados para vitest.

- **Como jogador, quero ver e editar minha ficha de personagem.** ✅ (2026-08-23)
  - [x] `app/campaigns/[campaignId]/characters/page.tsx`: lista de personagens da campanha
  - [x] `app/campaigns/[campaignId]/characters/[characterId]/page.tsx` + `components/characters/character-sheet.tsx`, `ability-scores.tsx`, `skill-list.tsx`, `spell-slots.tsx`
  - [x] Seções: cabeçalho, ability scores (grid 2x3), skills, combat (AC/HP editável inline/speed/iniciativa), spells, equipment, features
  - [x] HP editável inline: mutação otimista via TanStack Query
  - [x] Teste: edição de HP atualiza a UI antes da resposta do servidor (otimista) e reverte em caso de erro
  - Notas: integração real — backend ganhou `GET /characters?campaign_id=` (lista, `app/campaigns/[campaignId]/characters/page.tsx` já usa) e `PATCH /characters/{id}` (HP/CA/PV temporário/inspiration, todos opcionais; `hit_point_current` acima do máximo é rejeitado com 422 pelo backend, e o form já trata isso como erro) — ver `docs/anahita-backend-backlog.md`, "Lacunas descobertas pelo frontend". "Iniciativa" continua derivada client-side do modificador de Destreza via `dnd-rules.ts` (não é um campo do backend). Spells/equipment/features do personagem ficam "em breve" — não modelados em `Character` ainda (fora do escopo desta leva de lacunas).

- **Lacunas remanescentes — pendentes de backend antes de poderem ser resolvidas no frontend.** ✅ (2026-08-23)
  - [x] `app/campaigns/[campaignId]/settings/page.tsx`: formulário de edição de nome/descrição/setting da campanha (hoje só leitura) — depende de `PATCH /campaigns/{campaign_id}` (`docs/anahita-backend-backlog.md`, "Lacunas remanescentes")
  - [x] `app/campaigns/[campaignId]/settings/page.tsx`: lista de membros mostrar `username` em vez do `user_id` cru — depende de um endpoint em lote de perfil público (`docs/anahita-backend-backlog.md`, "Lacunas remanescentes")
  - [x] `components/catalog/custom-entry-form.tsx`: campos de formulário para as categorias magic-items/backgrounds/feats/rules (hoje só nome+descrição, sem POST algum já que o backend não aceita) — depende de `POST /catalog/{magic-items,backgrounds,feats,rules}`; `rules` também precisa de `campaign_id` em `GET /catalog/rules` para escopar homebrew corretamente
  - [x] `components/characters/character-sheet.tsx`: seções "Spells" (lista por nível com slots/prepared toggle), "Equipment" (inventário pessoal com equipped toggle) e "Features" (lista por fonte) — hoje "em breve"; depende de endpoints de `CharacterSpell`/`CharacterEquipment`/features resolvidas na ficha (`docs/anahita-backend-backlog.md`, "Lacunas remanescentes")
  - Notas: `settings/page.tsx` agora tem formulário de edição (nome/descrição/cenário) para o DM via `PATCH /campaigns/{id}` e mostra `username` real dos membros via `GET /auth/users?ids=` (novo hook `useUserProfiles`/`lib/api/users.ts`). `custom-entry-form.tsx` ganhou campos por categoria para magic-items (raridade), backgrounds (traços/ideais/vínculos/defeitos — sem campo "descrição", que `BackgroundCreate` não tem) e rules (campo "desc", não "description" — chave real do schema do backend); feats já usava só nome+descrição, que já batia. `spell-slots.tsx` virou um componente ativo (lista de magias conhecidas + form de adicionar via catálogo da campanha, com toggle "preparada"); `character-sheet.tsx` ganhou seções reais de Equipamento (inventário + form de adicionar item do catálogo) e Características (lista + form de registrar feature de classe/talento, texto livre — não resolvido automaticamente do catálogo). "Slots" de magia por nível (do texto original do backlog) não foram implementados — `CharacterSpell` não modela slots, só a lista de magias conhecidas/preparadas.

---

## Fase 2 — Sessão ao Vivo (Combat Tracker)

> Depende do backend Fase 2 (encounters + WebSocket).

- **Como DM, quero gerenciar sessões e suas notas.** ✅ (2026-08-23)
  - [x] `lib/api/sessions.ts`, `hooks/use-session.ts`
  - [x] `app/campaigns/[campaignId]/sessions/page.tsx` + `components/sessions/session-card.tsx`
  - [x] `app/campaigns/[campaignId]/sessions/[sessionId]/page.tsx` + `components/sessions/note-editor.tsx`, `quick-note.tsx`
  - [x] Regra de UI: notas privadas (`is_private`) só aparecem para o DM
  - [x] Teste: Player não vê notas privadas de outro autor
  - Notas: backend já tinha tudo que essa história precisava (`POST/GET /campaigns/{id}/sessions`, `POST/GET /sessions/{id}/notes`) — nenhuma lacuna encontrada. A filtragem de notas privadas é feita inteiramente no backend (`SessionService.list_notes`); o frontend não reimplementa essa regra, só renderiza o que a API retorna (o teste de `note-editor.test.tsx` documenta isso — não há lógica de filtro do lado do cliente para testar, só a ausência de vazamento). Não existe `GET /sessions/{id}` (só a listagem por campanha), então a página de detalhe deriva a sessão a partir do cache de `useSessions(campaignId)` por id — sem chamada extra. `quick-note.tsx` é o formulário compacto de adicionar nota (reaproveitado dentro de `note-editor.tsx`); o checkbox "nota privada" só é renderizado quando `isDm=true`. Nomes de autor resolvidos via `useUserProfiles` (já existente da Fase 1, `GET /auth/users?ids=`). `campaign-sidebar.tsx`: item "Sessões" passou de `implemented: false` para `true`. Sem edição de `dm_notes`/status da sessão nesta história (backend não expõe `PATCH /sessions/{id}` — fora do escopo do backlog atual).

- **Como DM, quero um combat tracker mobile-first para rodar combates na mesa.** ✅ (2026-08-23)
  - [x] `lib/ws/combat-socket.ts`, `lib/ws/types.ts`, `providers/combat-provider.tsx`, `hooks/use-combat.ts`
  - [x] `app/campaigns/[campaignId]/combat/[encounterId]/layout.tsx` (fullscreen mobile, esconde sidebar/header) + `page.tsx`
  - [x] `components/combat/initiative-tracker.tsx`, `participant-card.tsx` (nome, barra de HP, badge de AC, badges de condição, destaque do turno atual)
  - [x] Reconexão: ao reconectar, processa `state_sync` e resincroniza a UI
  - [x] Teste: `combat-provider` processa `turn_advanced`/`participant_updated`/`encounter_status_changed` corretamente
  - Notas: backend já tinha tudo que essa história precisava (`/ws/combat/{id}` com o protocolo do PRD §10.2 implementado à risca) — nenhuma lacuna encontrada. `types/combat.ts` deixou de ser provisório: reconferido linha a linha contra `backend/app/combat/schemas.py`/`domain.py` (ganhou o campo `effects` que não existia na versão provisória). `lib/ws/combat-socket.ts` encapsula o WebSocket nativo com reconexão automática (backoff exponencial, teto de 15s) — como o servidor sempre manda um `state_sync` completo logo após aceitar a conexão (PRD §10.5), a resincronização é só "mais um `state_sync`" para o reducer, sem lógica especial de "é a primeira conexão ou uma reconexão". `providers/combat-provider.tsx` expõe `combatReducer` (função pura) só para teste — processa os 5 tipos de evento do servidor; testado sem montar socket/provider algum. Como Next.js não permite um layout "pular" o layout pai facilmente, `app/campaigns/[campaignId]/layout.tsx` passou a esconder header/sidebar/mobile-nav quando a rota bate com `/combat/[id]` (checado via `usePathname`), e o layout aninhado de combat só entra com `CombatProvider` + wrapper fullscreen. **Adicionado além do escopo listado no backlog** (necessário como ponto de entrada, já que sem isso a rota `/combat/[encounterId]` seria inalcançável pela UI): `lib/api/combat.ts` + `useEncounters`/`useCreateEncounter`/`useStartEncounter` em `hooks/use-combat.ts`, e uma seção "Encontros" em `sessions/[sessionId]/page.tsx` (criar encontro, iniciar, abrir tracker) — usa os endpoints REST de `encounters` que já existiam (`POST/GET /sessions/{id}/encounters`, `POST /encounters/{id}/start`). `advance_turn` renderizado como um botão simples na página por ora — vira `turn-indicator.tsx` dedicado na próxima história (ações rápidas).

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
