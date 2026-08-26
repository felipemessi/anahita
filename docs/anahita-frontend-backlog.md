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
| 2    | Sessão ao Vivo (Combat Tracker)        | Concluída       | 2026-08-23           |
| 3    | World-building                          | Concluída       | 2026-08-23           |
| 4    | Loot, Inventário e Handouts             | Concluída       | 2026-08-24           |
| 5    | Registro e Lore                         | Concluída (diário DM-only fora do menu pra jogador, recap cronológico, timeline híbrida com marcos manuais, wiki em markdown linkável ao World e incluída na busca) | 2026-08-24 |
| 6    | Interatividade de Ficha e Combate       | Concluída (magias por círculo com busca/preparo/slots, inventário e moeda editáveis, sessão aberta + iniciativa obrigatória, ações de combate declaradas com resultado ao vivo, resumo de personagem pra outros jogadores com auto-abertura do próprio, rolagem manual em todo ponto de rolagem de combate) | 2026-08-25 |
| 7    | Sobrevivência, Descanso e Recursos      | Concluída (dados de vida em descanso curto, testes de morte automáticos com estado estável inferido no cliente, indicador de concentração com DC no combat tracker, perícias passivas, level-up com PV/ASI/talento, ações lendárias e reações de monstro, recursos de classe com atalho na declaração de ação) | 2026-08-25 |
| 8    | Dashboard e Refinamentos de Ficha       | Pendente | 2026-08-25 |

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

- **Como DM, quero ações rápidas de dano/cura/condição em poucos taps.** ✅ (2026-08-23)
  - [x] `components/combat/damage-dialog.tsx`: input numérico +/- com confirmação (menos de 3 taps)
  - [x] `components/combat/condition-badges.tsx`: toggle de condições (tap adiciona/remove)
  - [x] `components/combat/turn-indicator.tsx`: botão fixo no rodapé "avançar turno"
  - [x] `components/combat/monster-picker.tsx`: busca no catálogo de `Monster` ao adicionar participante, autocompleta HP/AC/nome; alternativa de form manual para NPCs sem stat block
  - [x] Teste: dialog de dano envia o evento WS correto (`update_participant`)
  - [x] Teste: `monster-picker` autocompleta os campos ao selecionar um monstro do catálogo
  - Notas: nenhuma lacuna de backend — `update_participant`/`add_participant`/`remove_participant` via WS já cobriam tudo. `damage-dialog.tsx` tem presets de 1 tap (-1/-5/-10/+1/+5/+10) e um campo "outro" de 2 taps (digitar + confirmar "Dano"/"Cura"); dano nunca deixa `hit_point_current` negativo (`Math.max(0, …)` client-side, o backend já rejeita negativo via `ge=0`). `condition-badges.tsx` e a exibição em `participant-card.tsx` (Fase 2 história 2) agora compartilham o mapa de labels via `lib/utils/conditions.ts` (extraído nesta história para não duplicar as 15 traduções). `monster-picker.tsx` acabou sendo o formulário inteiro de "adicionar participante" (não só a busca) — inclui iniciativa/ordem de turno, que o catálogo não tem opinião sobre; ao selecionar um monstro, autocompleta nome/PV/CA (primeira entrada de `armor_classes`) via `useCatalogEntry`, mas os campos continuam editáveis para NPCs sem stat block. `turn-indicator.tsx` substituiu o botão inline que a história anterior tinha colocado direto em `page.tsx`. Sem endpoint de remoção de condição em lote — cada toggle é um `update_participant` (`add_condition`/`remove_condition`) separado, como o protocolo já previa.

- **Como jogador, quero acompanhar o combate em tempo real sem poder alterar nada.** ✅ (2026-08-23)
  - [x] Visão read-only do tracker (mesmos componentes, sem os controles de ação do DM)
  - [x] Teste: jogador não vê botões de ação; UI atualiza via WS mesmo assim
  - Notas: nenhuma lacuna — a árvore de componentes já era compartilhada entre DM e jogador desde a história 2 (`app/campaigns/[campaignId]/combat/[encounterId]/page.tsx` só passa `renderActions` para `InitiativeTracker` quando `isDm`, e só renderiza `TurnIndicator`/"Adicionar participante" para o DM); esta história ficou principalmente em cobrir isso com teste (`page.test.tsx`, 3 casos: jogador sem controles, DM com controles, e HP do jogador atualizando de uma rerenderização do estado do `useCombat()` sem nenhuma ação do jogador — simula o que `CombatProvider` faz ao processar um `participant_updated` de verdade). Adicionado um rótulo "Modo espectador" no cabeçalho para o jogador, só cosmético. Servidor já rejeita comandos de não-DM (`ws_router._handle_message`) mesmo que a UI de alguma forma exibisse um controle — defesa em profundidade que já existia, não nova nesta história.

---

## Fase 3 — World-building

> Depende do backend Fase 3.

- **Como DM, quero cadastrar e organizar NPCs, locais e facções.** ✅ (2026-08-23)
  - [x] `lib/api/world.ts`, `hooks/use-world.ts`
  - [x] `app/campaigns/[campaignId]/world/page.tsx`: hub com três seções
  - [x] `app/campaigns/[campaignId]/world/npcs/page.tsx` + `components/world/npc-card.tsx` (nome, raça, ocupação, facções; botão "ver stat block" quando `stat_block_id` existe, reaproveitando `monster-stat-block.tsx`)
  - [x] `app/campaigns/[campaignId]/world/locations/page.tsx` + `components/world/location-tree.tsx` (árvore expansível região→cidade→taverna)
  - [x] `app/campaigns/[campaignId]/world/factions/page.tsx` + `components/world/faction-graph.tsx` (lista de relações ou grafo simples)
  - [x] `components/world/entity-link-badge.tsx`: badges de vínculo (sessões, facções, locais)
  - [x] Testes: árvore de locations renderiza hierarquia correta; NPC card mostra stat block quando aplicável
  - **Nota:** `types/world.ts` era provisório (Fase 0) e ficou desatualizado em relação ao backend real da Fase 3 — corrigido inline: adicionado `id` às interfaces de junção (`NpcFaction`, `NpcLocation`, `NpcSession`, `LocationSession`, `FactionRelationship`, que o backend sempre retorna), acrescentado `LocationTreeNode` e os tipos `*Create`. `components/layout/campaign-sidebar.tsx` teve o item "World" marcado `implemented: true` (lacuna mecânica — senão a navegação continuaria desabilitada mesmo com as telas prontas). `FactionGraph` é uma lista de relações por facção (não um grafo visual) e `entity-link-badge` são badges de contagem simples — dentro do que o backlog permite ("lista de relações ou grafo simples"). Criação de NPC com stat block (busca no catálogo de monstros) e vínculos NPC↔sessão/local↔sessão via UI ficaram fora do escopo desta história (endpoints já existem no backend, prontos para uma UI dedicada numa iteração futura); o card já sabe renderizar o stat block quando o campo existir via API.

- **Como DM, quero buscar por nome/descrição em NPCs, locais e facções.** ✅ (2026-08-23)
  - [x] Campo de busca no hub de world, chamando o endpoint de full-text search do backend
  - [x] Teste: busca retorna resultados combinando as três entidades — `app/campaigns/[campaignId]/world/page.test.tsx`
  - **Nota:** `searchWorld`/`useWorldSearch` já tinham sido criados na história anterior (API/hook prontos, só sem UI); esta história só adicionou o campo de busca e a renderização dos resultados no hub. Cada resultado linka para a página de lista da entidade (`/world/npcs`, `/world/locations`, `/world/factions`) — não há rota de detalhe por entidade ainda, então não dá pra linkar direto no item.

- **Lacunas descobertas na Fase 3 (frontend) — pendentes de decisão.**
  - [x] Criar NPC com stat block ✅ (2026-08-23): busca no catálogo de monstros (`useCatalogList("monsters", { search, campaign_id })`, mesmo padrão do `MonsterPicker` do combat tracker) embutida no formulário de `npcs/page.tsx`; seleciona um monstro da lista, mostra o nome escolhido com opção de remover, e envia `stat_block_id` em `POST .../npcs`. Testado em `npcs/page.test.tsx` (com e sem stat block).
  - [x] Vincular NPC a sessão / local a sessão ✅ (2026-08-23): `NpcCard` ganhou um controle "Vincular a uma sessão" (DM-only, oculto pra jogador) que abre um select das sessões da campanha e chama `POST /npcs/{id}/sessions`; `locations/page.tsx` ganhou um formulário equivalente (seleciona local + sessão) para `POST /locations/{id}/sessions`. Badge de "sessões" no `NpcCard` já refletia a contagem real (via `useNpcSessions`) desde a história anterior — só faltava como criar o vínculo pela UI, que é o que esta história resolveu.
  - [x] Rotas de detalhe por entidade ✅ (2026-08-23): `/world/npcs/[npcId]`, `/world/locations/[locationId]`, `/world/factions/[factionId]` — cada uma resolve a entidade filtrando a listagem já cacheada da campanha (`useNpcs`/`useLocations`/`useFactions`, sem endpoint `GET` por id no backend, que não existe) e renderiza seus vínculos de verdade (facções com papel, locais com tipo de presença, sessões com nota, sublocais, relações entre facções). `NpcCard`, `LocationTree` e `FactionGraph` agora linkam pro nome da entidade em vez de só texto estático; resultados de busca no hub linkam direto pra entidade específica em vez da lista da categoria.
  - **Nota:** não existe `GET /npcs/{id}` (nem locations/factions) no backend — resolvido client-side reaproveitando a query da listagem (já teria que ser buscada de qualquer forma para popular a lista); evita depender de um endpoint novo só pra isso. Se o volume de NPCs/locais/facções por campanha crescer muito, vale revisitar com um endpoint de detalhe dedicado.

---

## Fase 4 — Loot, Inventário e Handouts

> Depende do backend Fase 4. **Nota:** as pastas `app/.../handouts/` e `components/handouts/` ainda nem existem no esqueleto atual — precisam ser criadas nesta fase (não foram scaffoldadas junto com o resto).

- **Como grupo, quero ver e gerenciar o inventário compartilhado da campanha.** ✅ (2026-08-24)
  - [x] `lib/api/inventory.ts`, `hooks/use-inventory.ts`
  - [x] `app/campaigns/[campaignId]/inventory/page.tsx` + `components/inventory/loot-table.tsx`, `item-card.tsx`
  - [x] Teste: lista de inventário renderiza itens do catálogo (incluindo magic items) e itens custom
  - Notas: não existe endpoint de backend que agregue loot no nível da campanha (`GET /encounters/{id}/loot` é por encontro) — `lib/api/inventory.ts#listCampaignLootDrops` compõe sessões → encontros → loot numa única função para alimentar a página; a criação de loot pelo DM exige escolher um desses encontros num select. Reivindicar loot usa o personagem do próprio jogador na campanha (`campaign_member_id` == a própria membership).

- **Como DM, quero criar e revelar handouts para os jogadores.** ✅ (2026-08-24)
  - [x] Criar `app/campaigns/[campaignId]/handouts/page.tsx`, `lib/api/handouts.ts`, `hooks/use-handouts.ts`
  - [x] `components/handouts/handout-card.tsx`, `handout-reveal-button.tsx`, `handout-viewer.tsx`
  - [x] Visão DM: lista completa, toggle reveal/hide, upload de imagem/mapa, editor de texto, filtro por sessão
  - [x] Visão jogador: só handouts revelados, galeria de imagens em tamanho grande
  - [x] Reveal em tempo real: escutar evento `handout_revealed` no WebSocket de combat ativo (reaproveita `lib/ws`)
  - [x] Teste: jogador só vê handouts com `is_revealed=true`; reveal via WS atualiza a UI do jogador sem reload
  - Notas: criação de handout envia `multipart/form-data` (`lib/api/client.ts#apiFetch` foi ajustado para não forçar `Content-Type: application/json` quando o body é `FormData`, deixando o browser definir o boundary). O reveal em tempo real reaproveita `lib/ws/combat-socket.ts` diretamente (não o `CombatProvider`, que carrega estado de combate desnecessário aqui) — `useHandoutRevealListener` só abre o socket quando a sessão filtrada tem um encontro `active`, então o "filtro por sessão" é pré-requisito prático para o reveal ao vivo.

---

## Fase 5 — Registro e Lore

> Depende do backend Fase 5. Requisitos levantados e detalhados em `docs/anahita-frontend-prd.md` §6/§9.6 e `docs/anahita-backend-prd.md` §7.10 (2026-08-24). **Nota:** as pastas `app/.../journal/`, `app/.../recap/`, `app/.../timeline/`, `app/.../wiki/` e os componentes correspondentes ainda não existem no esqueleto atual — precisam ser criadas nesta fase.

- **Como DM, quero manter um diário privado da campanha.** ✅ (2026-08-24)
  - [x] `lib/api/journal.ts`, `hooks/use-journal.ts`
  - [x] `app/campaigns/[campaignId]/journal/page.tsx` + `components/journal/journal-entry-card.tsx`, `journal-editor.tsx`
  - [x] Rota não aparece no menu (`campaign-sidebar.tsx`/`mobile-nav.tsx`) para quem não é DM — nem como link desabilitado, some de vez
  - [x] Teste: jogador não vê o item de menu "Diário"; tentativa de acesso direto à rota trata o 403 do backend sem vazar conteúdo
  - Notas: `NAV_ITEMS` ganhou um campo `dmOnly?: boolean`; `CampaignSidebar`/`MobileNav` agora recebem `role` (vindo de `useMyMembership` no layout) e filtram itens `dmOnly` fora da lista renderizada, não só desabilitados. A página de Diário roda a query independente do papel local — se o backend responder 403 (acesso direto por URL), mostra uma mensagem genérica sem nunca montar o editor/lista.

- **Como grupo, quero ver a história da campanha até agora.** ✅ (2026-08-24)
  - [x] `app/campaigns/[campaignId]/recap/page.tsx` — reaproveita `useSessions` (`hooks/use-session.ts`), sem novo arquivo em `lib/api/`
  - [x] Lista os `summary` de sessões em ordem, pulando sessões sem resumo ainda
  - [x] Teste: renderiza os resumos na ordem certa e omite sessões sem `summary`
  - Notas: item "Recap" adicionado ao `NAV_ITEMS` sem `dmOnly` (visível a todo o grupo). Ordenação e filtro (`summary` ausente) feitos no próprio componente sobre o resultado de `useSessions`, sem tocar o hook existente.

- **Como grupo, quero ver uma timeline combinando o que aconteceu em cada sessão com marcos que o mestre adicionar manualmente.** ✅ (2026-08-24)
  - [x] `lib/api/timeline.ts`, `hooks/use-timeline.ts`
  - [x] `app/campaigns/[campaignId]/timeline/page.tsx` + `components/timeline/timeline-event-card.tsx` (visual distinto pra automático vs. manual)
  - [x] Form do DM para criar evento manual (título, descrição, data in-game livre, sessão âncora opcional)
  - [x] Teste: renderiza entradas automáticas e manuais juntas, na ordem devolvida pelo backend; só DM vê o form de criação
  - Notas: form de criação embutido em `page.tsx` (sem arquivo próprio) já que o backlog só lista `timeline-event-card.tsx` como componente. `TimelineEventCard` só mostra "Apagar" pro DM e só em entradas manuais — entradas automáticas nunca são editáveis/apagáveis (refletem `Session.summary`).

- **Como DM, quero criar páginas de wiki com lore livre, linkáveis a NPCs, locais e facções.** ✅ (2026-08-24)
  - [x] `lib/api/wiki.ts`, `hooks/use-wiki.ts`
  - [x] `app/campaigns/[campaignId]/wiki/page.tsx` (lista) + `app/campaigns/[campaignId]/wiki/[pageId]/page.tsx` (detalhe)
  - [x] `components/wiki/wiki-page-card.tsx`, `wiki-page-editor.tsx` (markdown), `wiki-page-links.tsx`
  - [x] Renderização do markdown do `content` na página de detalhe
  - [x] Badges de link pra NPC/Local/Facção na página de detalhe, cada um navegando pra tela do World correspondente
  - [x] Estender a busca do hub de World (`useWorldSearch`) para incluir páginas de wiki nos resultados
  - [x] Teste: DM cria/edita página; jogador só lê (sem editor); busca do World encontra página de wiki por título
  - Notas: dependência nova `react-markdown` (renderiza para elementos React, sem `dangerouslySetInnerHTML` — sem necessidade de sanitização extra). `WorldSearchResult.entity_type` ganhou `"wiki_page"`; o hub de World (`app/campaigns/[campaignId]/world/page.tsx`) roteia esse tipo pra `/campaigns/{id}/wiki/{id}` em vez de um subcaminho de `/world`. Sem plugin de tipografia do Tailwind instalado — o markdown é estilizado com utilitários `[&_tag]:` direto no container em vez de classes `prose`.

---

## Fase 6 — Interatividade de Ficha e Combate

> Depende do backend Fase 6 (`docs/anahita-backend-backlog.md`), ainda pendente — cada história abaixo só pode integrar de verdade depois que o endpoint correspondente existir; até lá, trabalhar com mocks e marcar a tarefa de "integração real" como pendente. Levantado em 2026-08-24 a partir de pedido do grupo — ver Fase 7 para os complementos de sobrevivência/descanso/recursos levantados na mesma sessão.

- **Como jogador, quero adicionar, remover, preparar/despreparar e ver detalhes das minhas magias, organizadas por círculo, com busca por classe/círculo/nome.** ✅ (2026-08-25)
  - [x] `lib/api/characters.ts`: `updateCharacterSpell` (toggle `prepared`), `removeCharacterSpell`, estender `hooks/use-character.ts`
  - [x] `components/characters/spell-list-by-circle.tsx` (substitui/estende `spell-slots.tsx`): agrupa magias conhecidas por círculo (0 = truques), toggle preparar/despreparar, botão remover, modal/expansível de detalhe (descrição, componentes, duração — reaproveita dados já resolvidos do catálogo)
  - [x] `components/characters/spell-search.tsx`: busca no catálogo de spells da campanha filtrando por classe do personagem, círculo e nome (reaproveita `useCatalogList("spells", { campaign_id, filters })`, mesmo padrão de `catalog-filter-bar.tsx`)
  - [x] Regra de UI: ao tentar preparar/adicionar acima do limite da classe, mostrar a mensagem de erro do backend (limite atual, quantas já preparadas/conhecidas) em vez de um erro genérico
  - [x] Teste: preparar acima do limite mostra o erro; remover magia libera espaço na lista; busca filtra por classe+círculo+nome
  - Notas: lacuna mecânica descoberta e resolvida inline — `GET /catalog/spells` não tinha filtro por classe (`SpellSummary` não carrega `classes`, e buscar o detalhe completo de cada spell só pra filtrar seria caro); adicionado `class_index` como query param no backend (`list_spells`/`list_spells_translated`/router), com teste próprio, antes de implementar a busca do frontend. `spell-slots.tsx` antigo (lista simples + form de adicionar) foi removido — sua função de listar/adicionar virou `spell-list-by-circle.tsx`; o nome `spell-slots.tsx` fica livre pra história 2 (indicador numérico de slots).

- **Como jogador, quero ver meus slots de magia disponíveis/usados por círculo e gastá-los ao conjurar, incluindo ritual (sem custo) e conjuração em nível maior.** ✅ (2026-08-25)
  - [x] `components/characters/spell-slots.tsx`: indicador visual por círculo (ex. pontos preenchidos/vazios) refletindo `used`/`max`
  - [x] Botão "conjurar" em cada magia da lista por círculo: se a magia permite ritual, oferece a opção "conjurar como ritual" (não consome slot); se permite conjuração em nível maior, oferece um seletor de nível (só habilitado até o maior círculo com slot disponível)
  - [x] Botões de descanso curto/longo na ficha; longo restaura os slots (mutação otimista, reverte em erro)
  - [x] Teste: conjurar consome o slot certo; ritual não consome; upcast exige e consome o slot do nível escolhido; sem slot disponível o botão de conjurar fica desabilitado com tooltip explicando
  - Notas: o seletor de nível só aparece quando há mais de uma opção de slot disponível para upcast; quando só existe uma opção diferente do círculo próprio da magia (ex. slot do próprio nível esgotado, só sobra o de cima), o botão "conjurar" já usa esse nível por padrão sem precisar do seletor.

- **Como jogador, quero adicionar, editar, ver detalhes e remover itens do meu inventário, e registrar ganho/gasto de moedas.** ✅ (2026-08-25)
  - [x] `lib/api/characters.ts`: `updateCharacterEquipment`, `removeCharacterEquipment`, `updateCharacterCurrency`; estender `hooks/use-character.ts`
  - [x] `components/characters/equipment-list.tsx` (substitui a seção inline de equipamento em `character-sheet.tsx`): toggle equipado/attunement, editor de quantidade, botão remover, expansível de detalhe (descrição do item do catálogo)
  - [x] `components/characters/currency-tracker.tsx`: saldo atual por tipo de moeda + form rápido de ganho/gasto (mutação otimista, reverte em erro de saldo negativo)
  - [x] Teste: editar/remover item atualiza a lista; gasto acima do saldo mostra erro e reverte o otimismo

- **Como DM, quero abrir uma sessão para ser jogada; como grupo, quero que o combate já comece com todos os personagens da campanha, exigindo iniciativa antes do primeiro turno.** ✅ (2026-08-25)
  - [x] `lib/api/sessions.ts`: `openSession`; botão "Abrir sessão" em `sessions/[sessionId]/page.tsx` (DM only)
  - [x] Ao iniciar um encontro (`useStartEncounter`), a UI reflete que todos os PCs da campanha já entraram como participantes (sem precisar adicionar manualmente); monstros continuam adicionados via `monster-picker.tsx`
  - [x] `components/combat/initiative-prompt.tsx`: tela/modal que aparece antes do primeiro turno pedindo a cada jogador (e ao DM, pelos NPCs/dele) rolar iniciativa; `advance_turn`/rodada só ficam disponíveis quando todos rolaram
  - [x] Teste: `initiative-prompt` bloqueia o avanço de turno até completar; jogador só rola a própria iniciativa, DM rola pelas dos NPCs
  - Notas: "jogador só rola a própria" é reforçado pelo servidor (`roll_initiative` no backend, 403 se não for dono), não pelo cliente — o `InitiativePrompt` mostra o botão de rolar pra todo participante faltando iniciativa (mais simples, sem duplicar lógica de posse no frontend) e qualquer erro 403 aparece via `lastError`, mesmo padrão já usado pros outros comandos WS. `TurnIndicator` fica escondido enquanto falta iniciativa; `InitiativePrompt` assume esse lugar até todos rolarem.

- **Como jogador/DM, quero declarar ações de combate (ataque com arma, manualmente, com magia, e ações como agarrar/empurrar) com resolução automática de acerto e dano.** ✅ (2026-08-25)
  - [x] `components/combat/action-picker.tsx`: por participante no turno atual, opções de ação (Atacar com arma equipada, Atacar manualmente — digitar bônus/dano, Conjurar magia, Agarrar, Empurrar, Disparada, Esquivar, Desengajar, Ajudar, Esconder-se, Preparar, Procurar)
  - [x] Resultado da ação (acerto/erro, dano aplicado, condição imposta) aparece no log de combate em tempo real (reaproveita o WS de combate já existente)
  - [x] Teste: `action-picker` envia o comando WS correto por tipo de ação; resultado renderizado a partir do evento de resposta do servidor
  - Notas: lacuna mecânica descoberta e resolvida inline no backend — `declare_action` só resolvia `attack_weapon`/`attack_spell`/`grapple`/`shove` (Fase 6 do backend), rejeitando as ações "de sabor" (Disparada, Esquivar, Desengajar, Ajudar, Esconder-se, Preparar, Procurar) com 422; adicionado um resolvedor genérico que só registra a ação no `CombatLog` sem rolar nada, já que essas ações não têm nenhuma rolagem associada. `components/combat/action-log.tsx` (novo) e `actionLog` no `CombatProvider`/`useCombat` também não existiam — precisavam existir pra "resultado aparece no log em tempo real" fazer sentido; consomem os eventos `action_resolved` já emitidos pelo WS, mantendo os últimos 10. Ações sem alvo natural (as 7 "de sabor") declaram tendo o próprio participante como alvo, já que o payload exige `target_id`.

- **Como jogador, quero ver os outros personagens da campanha só com detalhes básicos, e ter o meu próprio personagem selecionado automaticamente.** ✅ (2026-08-25)
  - [x] `app/campaigns/[campaignId]/characters/page.tsx`: para um jogador, mostra os demais personagens com card resumido (nome/raça/classe/nível, sem link pra ficha completa); o próprio personagem continua linkando pra ficha completa
  - [x] Ao entrar em `characters/page.tsx` como jogador com exatamente um personagem na campanha, redirecionar automaticamente para a ficha desse personagem em vez de mostrar a lista
  - [x] Teste: jogador não consegue navegar pra ficha completa de outro personagem (rota direta trata o resumo/403 do backend sem vazar dados); auto-redirect só acontece pro jogador, nunca pro DM
  - Notas: "exatamente um personagem na campanha" interpretado como "exatamente um personagem **próprio**" (não o total de personagens da campanha) — é o dono que precisa ser levado direto pra ficha dele, independente de quantos outros jogadores tenham personagem na mesma campanha; documentado no componente. A rota direta pra ficha de outro jogador já é seguramente tratada pelo backend (`CharacterSummary` em vez de 403) — o teste de "não vaza dados" cobre isso a nível de componente (`CharactersPage` nunca renderiza link pra ficha alheia), a garantia de fato vem do backend (Fase 6 backend, história 7).

- **Como jogador/DM, quero que toda rolagem (ataque, dano, resistência, perícia, iniciativa) seja feita automaticamente pelo sistema por padrão, mas eu possa digitar o resultado manualmente quando preferir.** ✅ (2026-08-25)
  - [x] `lib/utils/dice.ts`, `components/characters/roll-log.tsx`/`roll-button.tsx`: rolagem client-side (1d20 + bônus) ao clicar em modificador de habilidade/resistência/perícia/iniciativa na ficha, com um log das últimas rolagens — feito nesta sessão, mas **puramente cosmético**: nada é enviado ao backend nem aparece pra outros jogadores/DM
  - [x] Estender `RollButton`/`roll-log` (ou componente equivalente) para as rolagens do combate (ataque/dano/resistência declaradas via `action-picker`, iniciativa), agora sim chamando o backend (Fase 6 do backend) — resultado visível a todos os participantes via WS, não só localmente
  - [x] Em cada ponto de rolagem do combate, oferecer um campo "digitar manualmente" como alternativa ao clique (que aciona a rolagem automática do servidor) — nunca o contrário: rolagem automática é sempre a ação padrão/primária
  - [x] Teste: rolagem automática chama o endpoint sem `manual_result`; digitar manualmente envia `manual_result` e o valor aparece igual pros outros participantes via WS
  - Notas: a interatividade puramente client-side da ficha (modificadores/resistências/perícias/iniciativa) já está em produção — ver commit `feat: add click-to-roll interactivity to character sheet`. Ela cobre o "clique rola dado" pedido para a ficha, mas não é o sistema de rolagem desta história (que precisa ser servidor-autoritativo para combate, onde o resultado importa pra todos os participantes, não só pra quem clicou). O "componente equivalente" ao `RollButton`/`roll-log` acabou sendo `action-picker.tsx`/`initiative-prompt.tsx` (declaração server-autoritativa) + `action-log.tsx` (resultado em tempo real via WS, história 5) — já existiam antes desta história fechar o botão/campo de rolagem manual em si (`manual_attack_roll`/`manual_damage_roll`/`manual_target_roll`/`initiative` manual), que é o que faltava e foi adicionado agora: um link "digitar manualmente" abre os campos numéricos correspondentes, escondidos por padrão — nunca a ação primária.

---

## Fase 7 — Sobrevivência, Descanso e Recursos

> Depende do backend Fase 7 (`docs/anahita-backend-backlog.md`, completo em 2026-08-25). Itens complementares levantados junto com a Fase 6, separados em fase própria por terem escopo e prioridade próprios. Levantado em 2026-08-24.

- **Como jogador, quero gastar dados de vida num descanso curto e ver quantos ainda tenho disponíveis. ✅ (2026-08-25)**
  - [x] `components/characters/hit-dice-tracker.tsx`: indicador de dados de vida disponíveis/gastos (mesmo padrão visual do `spell-slots.tsx` da Fase 6) + botão "gastar dado de vida" que informa quantos gastar
  - [x] Botão "descanso curto" na ficha aciona o gasto de dados de vida escolhido e atualiza PV (mutação otimista, reverte em erro)
  - [x] Teste: gastar dado de vida atualiza PV e o contador de dados restantes; botão desabilita quando não há dados disponíveis
  - Notas: o gasto de dados de vida acontece pelo próprio botão "Gastar dado de vida" do `hit-dice-tracker.tsx` (que já dispara o descanso curto com a quantidade escolhida), em vez de acoplar a escolha ao botão genérico "Descanso curto" da ficha — mantém os dois fluxos independentes (um descanso curto sem gasto de dados continua possível pelo botão da ficha). Sem mutação otimista: a cura rolada é decidida no servidor, então o valor final só é conhecido após a resposta.

- **Como jogador, quero fazer testes de morte quando meu personagem chega a 0 PV, vendo sucessos/falhas acumulados. ✅ (2026-08-25)**
  - [x] `components/characters/death-save-tracker.tsx`: aparece automaticamente quando `hit_point_current === 0`, mostra 3 marcadores de sucesso/falha e um botão "rolar" (chama o endpoint de death save)
  - [x] Estados visuais claros para estável (3 sucessos) e morto (3 falhas)
  - [x] Teste: rolar preenche o marcador certo conforme o resultado; 3 falhas mostra estado "morto"; qualquer cura reseta os marcadores
  - Notas: o backend não persiste um estado "estável" separado — 3 sucessos apenas zera os dois contadores, mesmo formato de "ainda não rolou". O componente infere "estável" no cliente comparando com a renderização anterior (teve progresso e depois zerou sem morrer) — só vale enquanto o componente está montado; um reload da página perde essa distinção e volta pro estado neutro (mecanicamente correto, já que não há mais teste de morte pendente de qualquer forma).

- **Como jogador, quero indicar que estou concentrando numa magia e ser avisado da DC do teste de concentração quando meu personagem tomar dano em combate. ✅ (2026-08-25)**
  - [x] Indicador de "concentrando em [magia]" na ficha e no `participant-card.tsx` do combat tracker
  - [x] Botão "iniciar concentração" ao conjurar uma magia de concentração (a partir da lista de magias da Fase 6); conjurar outra encerra a anterior automaticamente
  - [x] Quando um participante concentrando toma dano no combate, a UI mostra a DC do teste (vinda do evento WS) com um atalho pra rolar a resistência de CON correspondente
  - [x] Teste: dano em participante concentrando exibe a DC; indicador de concentração muda ao trocar de magia
  - Notas: não existe um botão "iniciar concentração" separado — conjurar uma magia de concentração (botão "conjurar" já existente do `spell-list-by-circle.tsx`) já dispara isso automaticamente no backend (`cast_spell`), inclusive encerrando a concentração anterior; o indicador na ficha (`concentration-indicator.tsx`) só reflete esse estado e permite encerrar manualmente. No `participant-card.tsx`, a DC aparece com um `RollButton` de atalho pra rolar a resistência de CON — a tela de combate foi envolvida num `RollLogProvider` (não estava, no fechamento inicial desta história; resolvido como lacuna antes de fechar a Fase 7) pra isso funcionar. O modificador de CON usado vem do `save_bonus` já calculado do `Character` (personagem) ou, pra um monstro do catálogo, do modificador bruto de `constitution` (a proficiência de resistência do monstro não é resolvida — `MonsterProficiency` só aponta pra uma `Proficiency` genérica, não distingue "resistência de CON" sem outra consulta ao catálogo — simplificação documentada); um participante puramente manual/NPC sem stat block rola em +0.

- **Como jogador, quero ver minhas perícias passivas na ficha. ✅ (2026-08-25)**
  - [x] `ability-scores.tsx`/nova seção `passive-scores.tsx`: exibe Percepção/Investigação/Intuição passivas (vindas de `CharacterRead`, sem cálculo client-side)
  - [x] Teste: renderiza os três valores vindos da API

- **Como jogador, quero subir de nível meu personagem pela ficha, escolhendo melhoria de habilidade ou talento quando aplicável. ✅ (2026-08-25)**
  - [x] `components/characters/level-up-dialog.tsx`: fluxo guiado (escolher classe a subir, confirmar PV ganho, em nível de ASI escolher entre distribuir pontos ou talento do catálogo)
  - [x] Teste: fluxo completo gera o payload correto pro endpoint de level-up; nível sem ASI pula a etapa de escolha
  - Notas: escopo restrito a subir de nível numa classe que o personagem já tem — multiclasse (adicionar uma classe nova) ainda não tem fluxo de UI nenhum no frontend (endpoint `POST /classes` já existe no backend desde a Fase 1, mas sem tela; gap pré-existente, não introduzido por esta história). O nível de ASI é detectado consultando `ClassLevel.ability_score_bonuses` do catálogo (`useCatalogEntry("classes", ...)`) pro próximo nível da classe escolhida. "Confirmar PV ganho" é feedback pós-ação (o servidor rola o dado de vida), não uma etapa de pré-confirmação — mensagem de sucesso mostra o novo PV máximo.

- **Como DM, quero disparar ações lendárias e reações de monstros pelo combat tracker. ✅ (2026-08-25)**
  - [x] `components/combat/legendary-action-picker.tsx`: para participantes NPC/monstro com stat block, lista as ações lendárias/reações disponíveis (via `monster-stat-block.tsx`, já usado no catálogo) com contador de uso por rodada
  - [x] Teste: ação lendária fica desabilitada quando o limite da rodada é atingido; resultado aparece no log de combate
  - Notas: pra um participante `npc_id` (sem `monster_id` direto), o stat block é resolvido buscando o NPC via `useNpcs(campaignId)` e seu `stat_block_id` — não existe um hook de NPC único por id ainda, então isso busca a lista inteira da campanha e filtra no cliente (aceitável, mesma lista já usada em outras telas do World). O evento `action_resolved` cai no `ActionLog` do mesmo jeito que qualquer outra ação (já coberto pelo reducer genérico testado em `combat-provider.test.ts`), sem teste redundante aqui. `use_legendary_action`/`trigger_reaction` no hook `useCombat` viraram `sendLegendaryAction`/`triggerReaction` (não `useLegendaryAction`) pra não serem confundidos com hooks React pelo eslint (`react-hooks/rules-of-hooks`) ao serem chamados dentro de um `onClick`.

- **Como jogador, quero usar e acompanhar recursos de classe (fúria, ki, etc.) na ficha e no combate. ✅ (2026-08-25)**
  - [x] `components/characters/class-resources.tsx`: lista de recursos da classe (nome, usado/máximo) com botão "usar"; aparece também como atalho no `participant-card.tsx` durante o combate
  - [x] Descanso curto/longo (já construído na história de dados de vida desta fase) restaura os recursos conforme o tipo de recarga de cada um
  - [x] Teste: usar recurso decrementa e desabilita no limite; descanso do tipo certo restaura, do tipo errado não
  - Notas: o atalho de combate ficou no `action-picker.tsx` (onde o `Character` completo do participante do turno atual já é buscado, via `useCharacter`), em vez de no `participant-card.tsx` — esse último não carrega os dados completos do personagem pra cada participante da lista, só `EncounterParticipant` (sem `resources`); buscar o `Character` por participante ali exigiria N chamadas extras, então o atalho aparece durante a própria declaração de ação de quem está no turno, que é quando faz sentido gastar o recurso mesmo. A restauração por tipo de recarga é inteiramente server-side (já coberta pelos testes do backend) — sem lógica client-side pra testar aqui, só a invalidação de cache já genérica do `useRestCharacter`.

---

## Fase 8 — Dashboard e Refinamentos de Ficha

> Depende do backend Fase 8 (`docs/anahita-backend-backlog.md`), ainda pendente para os itens marcados abaixo como "depende de backend" — os demais já podem ser feitos hoje, sem endpoint novo, contra o que já existe nas Fases 6/7. Levantado pelo grupo em 2026-08-25 (revisão de Dashboard/Ficha em uso).

- **Como jogador/DM, quero ver no dashboard da campanha a próxima sessão, NPCs/locais recentes e handouts pendentes de verdade, não placeholders. ✅ (2026-08-26)**
  - [x] `lib/api/campaigns.ts`: `getCampaignDashboard`, `hooks/use-campaign.ts`: `useCampaignDashboard`
  - [x] `app/campaigns/[campaignId]/page.tsx`: substituir os três placeholders "em breve" (próxima sessão, NPCs/locais recentes, handouts pendentes) por dados reais do endpoint
  - [x] Teste: dashboard renderiza próxima sessão/NPCs recentes/handouts pendentes a partir do mock da API
  - Notas: reaproveitado `SessionCard` já existente pra "próxima sessão" (mesmo componente da lista de sessões). `types/world.ts::Location` ganhou `created_at` (faltava no tipo — o backend já expõe desde a Fase 8, `LocationRead`). Handouts pendentes usam um tipo dedicado leve (`DashboardHandout`: id/title/handout_type/created_at), sem puxar o `Handout` completo (com `url` resolvida) já que a lista do dashboard é só um resumo, não abre o visualizador.

- **Como jogador, quero subir de nível adicionando uma classe nova (multiclasse) pela ficha, não só subindo uma classe que já tenho. ✅ (2026-08-26)**
  - [x] `level-up-dialog.tsx`: opção "adicionar uma nova classe" — lista as classes do catálogo da campanha que o personagem ainda não possui, reaproveitando o mesmo fluxo de confirmação de PV/ASI já existente
  - [x] Teste: escolher uma classe nova envia o payload correto pro mesmo endpoint de level-up; classes já possuídas continuam no fluxo de "subir nível" normal
  - Notas: o `<select>` de classe ganhou um segundo `<optgroup>` ("Multiclasse — adicionar uma nova classe") com as classes do catálogo que o personagem ainda não tem (`class_definition_id` fora do conjunto já possuído); o valor da opção carrega `new:<id>` vs. `existing:<CharacterClass.id>` pra diferenciar sem mudar o payload enviado ao backend, que já aceita `class_definition_id` de uma classe nova (Fase 7). Nível seguinte calculado como 1 pra classe nova (não há `CharacterClass.level` ainda) — mesmo fluxo de ASI/PV, já que o backend resolve isso do mesmo jeito.

- **Como jogador, quero que o subir de nível me pergunte as escolhas mecânicas que ganho (estilo de luta, pacto, domínio etc.), de forma pesquisável. ✅ (2026-08-26)**
  - [x] `level-up-dialog.tsx`: quando a resposta do backend indicar `requires_choice`, exibir as opções (`FeatureOption`) com campo de busca (reaproveita `catalog-filter-bar.tsx`) antes de confirmar
  - [x] Enviar `feature_choices` no corpo da confirmação de level-up
  - [x] `character-sheet.tsx`/seção de Características: exibir as escolhas feitas (ex. "Estilo de Luta: Duelismo")
  - [x] Teste: nível com escolha obrigatória bloqueia a confirmação até uma opção ser selecionada; nível sem escolha pula essa etapa
  - Notas: `ApiError` ganhou um campo `detail: unknown` (antes só guardava a string de mensagem) — o 422 de `requires_choice` vem com um objeto estruturado, não uma string, e precisava chegar íntegro até o componente. Fluxo: primeira tentativa de confirmar sem `feature_choices` retorna 422 com `{requires_choice, choices: [{feature_id, required_count, options}]}`; o diálogo detecta isso (`isRequiresChoiceDetail`), renderiza um `<select>` por escolha exigida (`required_count` vezes, cobrindo Eldritch Invocations/Metamagic com mais de uma), com busca por nome quando a lista de opções passa de 5, e só reabilita "Confirmar" quando todas estiverem preenchidas; a segunda tentativa já inclui `feature_choices` e conclui. Lacuna mecânica encontrada e resolvida inline: o backend não tinha `GET /catalog/features/{id}` (só o `GET /catalog/features` de lista) — necessário pra ficha resolver o nome de uma opção já escolhida (`feature_option_id`) fora do fluxo de level-up; adicionado reaproveitando `catalog_service.get_feature_translated`, já existente.

- **Como jogador, quero ver minhas rolagens recentes no rodapé da ficha, não competindo com o resto do conteúdo. ✅ (2026-08-26)**
  - [x] `character-sheet.tsx`: reposicionar `roll-log`/histórico de rolagens para o final da ficha (abaixo de todas as seções)
  - [x] Teste: rolagem recente aparece na seção do rodapé após um clique de rolagem
  - Notas: `roll-log.tsx` renderizava o painel automaticamente dentro do próprio `RollLogProvider`, antes de `children` — por isso aparecia sempre no topo, mesmo o provider envolvendo a ficha inteira. Refatorado: `RollLogProvider` agora só fornece o contexto (`roll` + `entries`); o painel virou um componente separado exportado, `RollLogPanel`, que cada consumidor posiciona onde quiser. Em `character-sheet.tsx` ele foi movido pro fim do `<article>`, após `FeaturesSection`. A página de combate (`combat/[encounterId]/page.tsx`) também usava `RollLogProvider` esperando o log automático — lacuna mecânica encontrada e corrigida inline: adicionado `<RollLogPanel />` lá também (fim da tela), pra não perder a exibição de rolagens no combate. Testes existentes que dependiam da renderização automática (`ability-scores.test.tsx`, `skill-list.test.tsx`, `participant-card.test.tsx`) foram ajustados para renderizar `<RollLogPanel />` explicitamente; teste novo em `roll-log.test.tsx` cobre o mecanismo de posicionamento em si. Não foi escrito teste de integração da `CharacterSheet` inteira (árvore de hooks muito grande pra mockar) — a posição real no `character-sheet.tsx` foi conferida por leitura de código, não por teste end-to-end desse arquivo.

- **Como jogador, quero ver uma animação de dado rolando (~1.5s) antes do resultado aparecer, em todo ponto de rolagem da ficha e do combate. ✅ (2026-08-26, parcial — ver notas)**
  - [x] `components/characters/dice-roll-modal.tsx`: modal que anima ~1.5s trocando valores aleatórios e fixa no resultado final; texto final no formato "resultado do dado + modificador = total"
  - [x] Integrar o modal em todo `RollButton`/ponto de rolagem existente (ability scores, resistências, perícias, iniciativa, testes de morte, dados de vida) — a rolagem em si (client-side ou vinda do servidor) não muda, só a apresentação
  - [x] Teste: modal exibe a animação por ~1.5s e depois o resultado final correspondente ao valor real rolado
  - [ ] Ataque/dano em combate (`action-picker.tsx` → `ActionLog`) — deliberadamente adiado, ver notas
  - Notas: `dice-roll-modal.tsx` é genérico (`{label, rollResult, modifier, total}`), sem saber se a rolagem veio do cliente ou do servidor. `roll-log.tsx` foi expandido para orquestrar a animação: `RollLogProvider` guarda um `pending` roll e só o move pro log (`entries`) quando o modal termina (~1.5s de giro + ~0.9s exibindo o resultado fixo, depois fecha sozinho); `useRoll()` (client-side, usado por `RollButton` → atributos/resistências/perícias/iniciativa) continua com a mesma assinatura, agora passando pelo modal antes de aparecer no log — nenhum consumidor existente de `useRoll`/`RollButton` precisou mudar. Testes de morte e dados de vida não expunham o valor do dado nenhum lugar da UI — lacuna mecânica encontrada e resolvida inline: backend ganhou `CharacterDeathSaveResponse` (`character` + `roll_result`) e `CharacterRestResponse` (`character` + `hit_dice_rolls: CharacterHitDiceRollResult[]`, um item por classe gasta na Fase 8 do backend) substituindo o `CharacterRead` cru desses dois endpoints (`POST .../rest` e `POST .../death-save`), mesmo padrão já usado por `CharacterSpellCastResponse`; `death-save-tracker.tsx` e `hit-dice-tracker.tsx` chamam `useShowServerRoll()` (novo hook do `roll-log.tsx`) com o resultado antes de deixar a mutation invalidar a ficha. **Deliberadamente fora desta história:** ataque/dano em combate é resolvido via `declareAction` (WebSocket, `useCombat`) e aparece no `ActionLog` compartilhado entre DM e jogadores em tempo real — atrasar essa revelação por ~1.5s introduziria risco real de dessincronização entre os clientes conectados (cada um veria o resultado em um momento diferente, competindo com outras atualizações da mesma combat state via WS), então não foi encaixado nesta história; requer desenho próprio (fila de animação por cliente, não bloqueando o estado compartilhado).

- **Como jogador, quero escolher a estratégia de geração de atributos (standard array, point buy, custom ou rolagem) no wizard de criação de personagem. ✅ (2026-08-26)**
  - [x] `step-ability-scores.tsx`: seletor de método — `standard array` (distribuir os valores fixos 15/14/13/12/10/8 entre os atributos), `point buy` (orçamento de 27 pontos com custo por valor, feedback do saldo restante), `roll` (4d6 descarta o menor, usando o modal de rolagem da história anterior), `custom` (digitação livre)
  - [x] Enviar `generation_method` no payload de `POST /characters` — o backend já suportava desde a Fase 8 do backend
  - [x] Teste: point buy bloqueia distribuição acima do orçamento; standard array só permite usar cada valor uma vez; roll gera 6 conjuntos de 4d6-menor via o utilitário de dados já existente (`lib/utils/dice.ts`)
  - Notas: `lib/utils/dice.ts` ganhou `rollD6`/`roll4d6DropLowest`. `wizard-state.ts` ganhou `abilityGenerationMethod` (default `standard_array`) e as constantes de point buy (`POINT_BUY_COSTS`/`BUDGET`/`MIN`/`MAX`), espelhando exatamente a tabela do backend (`domain.py::POINT_BUY_COSTS`). `standard_array` e `roll` compartilham a mesma UX de "distribuir um pool fixo de 6 valores" — trocar de método reseta os atributos já atribuídos para evitar valores inválidos sobrando de outro método. O pool de `roll` pode ter valores repetidos (duas rolagens de 4d6 dando o mesmo total), diferente do array padrão — a lista de opções disponíveis por atributo agora conta ocorrências (`availableForAbility`) em vez de um simples "já usado?" booleano, senão um valor repetido sumiria do seletor assim que qualquer atributo o usasse uma vez. `roll` reaproveita o `DiceRollModal` da história anterior diretamente (fora do `RollLogProvider`, já que o wizard não tem um log de rolagens de personagem) para animar antes de revelar o pool gerado.

- **Como jogador, quero ver minhas perícias com proficiência em destaque e rolar com o bônus certo (incluindo proficiência).**
  - [ ] `skill-list.tsx`: destaque visual (ícone/cor) para perícias proficientes e com expertise
  - [ ] Confirmar que o clique-para-rolar de cada perícia usa `CharacterSkillRead.bonus` (já inclui bônus de proficiência calculado no backend), não recalcula só o modificador de habilidade no cliente
  - [ ] Teste: perícia proficiente renderiza o destaque; rolagem de perícia usa o bônus completo (modificador + proficiência quando aplicável)

- **Como jogador, quero confirmar antes de disparar um descanso curto ou longo, já que isso reseta PV/slots/recursos.**
  - [ ] Modal de confirmação (`AlertDialog` já usado em outros pontos destrutivos da ficha) antes de `POST /characters/{id}/rest` nos dois modos
  - [ ] Teste: cancelar o modal não dispara a chamada; confirmar dispara normalmente
  - Notas: a mecânica de reset já está correta no backend (Fases 6/7) — só falta a confirmação na UI.

- **Como jogador de Paladin/Cleric, quero escolher qual opção de Canalizar Divindade estou usando quando tenho mais de uma.**
  - [ ] `class-resources.tsx`: para o recurso `channel_divinity_charges`, exibir um seletor das opções disponíveis (`FeatureOption`) antes de confirmar o uso, quando houver mais de uma
  - [ ] Enviar `option_id` no `POST /characters/{id}/resources/{resource_key}/use`
  - [ ] Teste: recurso com múltiplas opções exige seleção antes de habilitar o botão "usar"; recurso com uma única opção usa direto, sem seletor
  - Depende de backend: `option_id` no endpoint de uso de recurso + vínculo `FeatureOption` (Fase 8 do backend)

- **Como jogador, quero escolher o alvo ao conjurar uma magia (aliado/inimigo/eu mesmo) e ver a DC quando ela exigir resistência.**
  - [ ] `spell-list-by-circle.tsx`/tela de combate: ao conjurar, pedir `target_participant_id` conforme `target_type` da magia (self não pede alvo; enemy/ally listam os participantes do encontro atual)
  - [ ] Magias `saving_throw`: exibir a DC calculada retornada pelo servidor e um atalho pra rolar a resistência do alvo (reaproveita `RollButton`/`roll-log` já usados na concentração, Fase 7)
  - [ ] Magias `attack_roll`: reaproveitar o fluxo já existente de `attack_spell` (Fase 6)
  - [ ] Magias `cast_only`: registrar o efeito sem pedir rolagem nenhuma
  - [ ] Teste: cada `action_type` de magia mostra o fluxo de UI correspondente (seleção de alvo, DC exibida, ou nenhuma rolagem)
  - Depende de backend: `action_type`/`target_type`/`save_ability_score_id` em `Spell` + DC no resultado de `cast` (Fase 8 do backend)

- **Bugfix — preparar uma magia está preparando a lista inteira em vez de só a magia clicada.**
  - [ ] Investigar `spell-list-by-circle.tsx`/hook de toggle `prepared`: identificar se é colisão de chave de cache do TanStack Query, callback compartilhado entre itens da lista, ou estado local não isolado por `CharacterSpell.id`
  - [ ] Corrigir para que o toggle afete só a entrada clicada
  - [ ] Teste de regressão: preparar uma magia específica não altera o estado `prepared` das demais da lista

- **Como jogador, quero minhas magias organizadas em seções por círculo, e só poder adicionar uma magia que meu personagem realmente pode ter naquele círculo/classe (com opção de forçar mediante confirmação).**
  - [ ] `spell-list-by-circle.tsx`: reestruturar em acordeões por círculo (0 = truques) com subtítulo, em vez da lista única atual
  - [ ] `spell-search.tsx`: verificar, antes de permitir adicionar, se o círculo da magia está disponível para a classe/nível atual do personagem (classes conjuradoras e progressão já resolvidas via `useCatalogEntry("classes", ...)`, mesmo dado usado pelo level-up)
  - [ ] Se o círculo não estiver disponível, exibir modal de confirmação ("tem certeza que quer adicionar mesmo assim?") antes de enviar o POST
  - [ ] Teste: magia de círculo disponível adiciona direto; magia de círculo indisponível pede confirmação antes de enviar; usuário pode cancelar
  - Notas: o backend já rejeita com 422 acima do limite de preparadas/conhecidas (Fase 6) — esta história é uma checagem preventiva de elegibilidade por círculo/classe, complementar a essa validação, não uma substituição dela.

- **Como jogador, quero que minha CA na ficha reflita a armadura/escudo equipados, automaticamente.**
  - [ ] `equipment-list.tsx`: nenhuma mudança de UI necessária além de garantir que o toggle `equipped` invalida a query da ficha (`useCharacter`) pra reexibir a CA recalculada
  - [ ] Teste: equipar/desequipar armadura atualiza o valor de CA exibido na ficha após a resposta do servidor
  - Depende de backend: recalcular `armor_class` no toggle de equipamento (Fase 8 do backend)

- **Como jogador, quero registrar ganho e gasto de moedas por denominação (cobre, prata, ouro, platina), não só um valor abstrato.**
  - [ ] `currency-tracker.tsx`: inputs separados para as 4 denominações (cp/sp/gp/pp — sem `ep`, decisão do grupo), convertendo o total pro delta em copper esperado por `POST /characters/{id}/currency`
  - [ ] Exibição do saldo decompõe o valor em copper armazenado pra denominações (maior pra menor: pp→gp→sp→cp), em vez de mostrar só o número bruto de copper
  - [ ] Teste: ganho/gasto misto (ex. +2 gp -5 sp) calcula o delta certo em copper; exibição decompõe corretamente um saldo conhecido
  - Notas: sem mudança de backend — `Character.currency_cp` continua como coluna única normalizada (decisão da Fase 6); a conversão por denominação acontece só na UI.

- **Como DM, quero que qualquer lista de catálogo usada para adicionar algo à ficha seja pesquisável, e que adicionar de fato integre o efeito mecânico correspondente.**
  - [ ] Campo de busca por nome (reaproveitando `catalog-filter-bar.tsx`) em toda lista de seleção usada pra adicionar algo à ficha que hoje não tem busca (features/talentos avulsos, opções de feature da história de level-up acima)
  - [ ] Ao adicionar um item que concede um recurso/efeito mecânico modelado (ex. talento que dá um recurso de classe, feature que altera CA/ataque), refletir isso nos componentes correspondentes (`class-resources.tsx`, cálculo de CA) em vez de só criar um registro de texto solto em Características
  - [ ] Teste: busca filtra a lista corretamente; adicionar um item com efeito mecânico modelado aparece refletido no componente correspondente
  - Depende de backend (parcial): a modelagem de `FeatureOption`/escolhas (Fase 8 do backend) cobre o caso de escolhas de nível; itens sem modelagem mecânica dedicada continuam registrados como texto livre, como hoje.
