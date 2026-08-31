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
| 8    | Dashboard e Refinamentos de Ficha       | Concluída (dashboard de campanha com dados reais, multiclasse e escolhas de nível no level-up, rolagens recentes no rodapé, animação de dado em toda a ficha e no combate, geração de atributos com 4 métodos, opções de Canalizar Divindade, alvo/DC de magias saving_throw, bugfix de preparo de magia, acordeão de magias por círculo com checagem de elegibilidade, CA reativa a equipamento, moeda por denominação, busca no catálogo de talentos) | 2026-08-26 |
| 9    | Correções e Regressões                  | Concluída (dashboard já funcionava com o fix de backend, formulário de homebrew troca inputs livres por `<select>` nos campos de enum com erro de API exposto, link de Configurações da campanha visível como item DM-only, seleção de alvo em combate confirmada funcionando — gap real é a Fase 13, documentado como dependência) | 2026-08-28 |
| 10   | Ficha do Personagem: Edição, Identidade e Navegação | Concluída (edição de identidade/atributos com aviso de cascata, avatar circular com upload/remoção, escolha de proficiências restrita ao conjunto de raça/classe, dropdown de sessões da ficha + menu hambúrguer, reordenação pessoal de sessões com botões subir/descer) | 2026-08-30 |
| 11   | Catálogo Homebrew: Profundidade e Estrutura | Concluída (raça homebrew com sub-formulário dedicado, selects estruturados e labels de unidade no formulário genérico, componentes de detalhe por categoria substituindo o dump de JSON cru, exclusão de entrada homebrew com confirmação e mensagem de erro da API) | 2026-08-31 |
| 12   | Recursos de Classe e Interatividade Mágica | Concluída (recurso de classe com efeito mapeado abre seleção de alvos e declara `use_class_resource` via combate em vez de só decrementar; magia `cast_only` com alvo — cura/dano direto — passa a declarar `attack_spell` via combate para o efeito ser de fato aplicado, em vez do endpoint da ficha bookkeeping-only; contador de duração de magia já estava concluído) | 2026-08-31 |
| 13   | Fluxo de Sessões: Fundamentos Faltantes | Concluída (botão de concluir sessão e edição de título DM-only, character-picker pra adicionar PCs ao combate — fecha o gap de seleção de alvo da Fase 9 —, toggle de revelação de NPC com badge oculto/revelado) | 2026-08-29 |
| 14   | Loot e Inventário Integrado             | Pendente | 2026-08-28 |
| 15   | Redesign de Sessões: Mapas Dinâmicos e Tokens | Pendente | 2026-08-28 |

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

- **Como jogador, quero ver uma animação de dado rolando (~1.5s) antes do resultado aparecer, em todo ponto de rolagem da ficha e do combate. ✅ (2026-08-26)**
  - [x] `components/characters/dice-roll-modal.tsx`: modal que anima ~1.5s trocando valores aleatórios e fixa no resultado final; texto final no formato "resultado do dado + modificador = total"
  - [x] Integrar o modal em todo `RollButton`/ponto de rolagem existente (ability scores, resistências, perícias, iniciativa, testes de morte, dados de vida) — a rolagem em si (client-side ou vinda do servidor) não muda, só a apresentação
  - [x] Teste: modal exibe a animação por ~1.5s e depois o resultado final correspondente ao valor real rolado
  - [x] Ataque/dano em combate (`action-picker.tsx` → `ActionLog`)
  - Notas: `dice-roll-modal.tsx` é genérico (`{label, rollResult, modifier, total}`), sem saber se a rolagem veio do cliente ou do servidor. `roll-log.tsx` foi expandido para orquestrar a animação: `RollLogProvider` guarda um `pending` roll e só o move pro log (`entries`) quando o modal termina (~1.5s de giro + ~0.9s exibindo o resultado fixo, depois fecha sozinho); `useRoll()` (client-side, usado por `RollButton` → atributos/resistências/perícias/iniciativa) continua com a mesma assinatura, agora passando pelo modal antes de aparecer no log — nenhum consumidor existente de `useRoll`/`RollButton` precisou mudar. Testes de morte e dados de vida não expunham o valor do dado nenhum lugar da UI — lacuna mecânica encontrada e resolvida inline: backend ganhou `CharacterDeathSaveResponse` (`character` + `roll_result`) e `CharacterRestResponse` (`character` + `hit_dice_rolls: CharacterHitDiceRollResult[]`, um item por classe gasta na Fase 8 do backend) substituindo o `CharacterRead` cru desses dois endpoints (`POST .../rest` e `POST .../death-save`), mesmo padrão já usado por `CharacterSpellCastResponse`; `death-save-tracker.tsx` e `hit-dice-tracker.tsx` chamam `useShowServerRoll()` (novo hook do `roll-log.tsx`) com o resultado antes de deixar a mutation invalidar a ficha. **Ataque/dano em combate** foi deliberadamente adiado nesta história (risco presumido de dessincronizar DM/jogadores atrasando a revelação de um resultado vindo por WebSocket) e resolvido depois, como lacuna de fechamento de fase — ver a nota daquela história mais abaixo pra como acabou sendo feito com segurança.

- **Como jogador, quero escolher a estratégia de geração de atributos (standard array, point buy, custom ou rolagem) no wizard de criação de personagem. ✅ (2026-08-26)**
  - [x] `step-ability-scores.tsx`: seletor de método — `standard array` (distribuir os valores fixos 15/14/13/12/10/8 entre os atributos), `point buy` (orçamento de 27 pontos com custo por valor, feedback do saldo restante), `roll` (4d6 descarta o menor, usando o modal de rolagem da história anterior), `custom` (digitação livre)
  - [x] Enviar `generation_method` no payload de `POST /characters` — o backend já suportava desde a Fase 8 do backend
  - [x] Teste: point buy bloqueia distribuição acima do orçamento; standard array só permite usar cada valor uma vez; roll gera 6 conjuntos de 4d6-menor via o utilitário de dados já existente (`lib/utils/dice.ts`)
  - Notas: `lib/utils/dice.ts` ganhou `rollD6`/`roll4d6DropLowest`. `wizard-state.ts` ganhou `abilityGenerationMethod` (default `standard_array`) e as constantes de point buy (`POINT_BUY_COSTS`/`BUDGET`/`MIN`/`MAX`), espelhando exatamente a tabela do backend (`domain.py::POINT_BUY_COSTS`). `standard_array` e `roll` compartilham a mesma UX de "distribuir um pool fixo de 6 valores" — trocar de método reseta os atributos já atribuídos para evitar valores inválidos sobrando de outro método. O pool de `roll` pode ter valores repetidos (duas rolagens de 4d6 dando o mesmo total), diferente do array padrão — a lista de opções disponíveis por atributo agora conta ocorrências (`availableForAbility`) em vez de um simples "já usado?" booleano, senão um valor repetido sumiria do seletor assim que qualquer atributo o usasse uma vez. `roll` reaproveita o `DiceRollModal` da história anterior diretamente (fora do `RollLogProvider`, já que o wizard não tem um log de rolagens de personagem) para animar antes de revelar o pool gerado.

- **Como jogador, quero ver minhas perícias com proficiência em destaque e rolar com o bônus certo (incluindo proficiência). ✅ (2026-08-26)**
  - [x] `skill-list.tsx`: destaque visual (ícone/cor) para perícias proficientes e com expertise
  - [x] Confirmar que o clique-para-rolar de cada perícia usa `CharacterSkillRead.bonus` (já inclui bônus de proficiência calculado no backend), não recalcula só o modificador de habilidade no cliente
  - [x] Teste: perícia proficiente renderiza o destaque; rolagem de perícia usa o bônus completo (modificador + proficiência quando aplicável)
  - Notas: o clique-para-rolar já usava `skill.bonus` (o texto "(proficiente)"/"(especialização)" também já existia) — faltava só o destaque visual. Adicionado um indicador de bolinha (mesmo padrão `●` já usado em `ability-scores.tsx` pra resistências proficientes): vazia sem proficiência, preenchida parcial (borda + fundo translúcido) com proficiência, sólida com especialização; a linha inteira também ganha `font-medium` quando proficiente.

- **Como jogador, quero confirmar antes de disparar um descanso curto ou longo, já que isso reseta PV/slots/recursos. ✅ (2026-08-26)**
  - [x] Modal de confirmação (`AlertDialog` já usado em outros pontos destrutivos da ficha) antes de `POST /characters/{id}/rest` nos dois modos
  - [x] Teste: cancelar o modal não dispara a chamada; confirmar dispara normalmente
  - Notas: a mecânica de reset já está correta no backend (Fases 6/7) — só faltava a confirmação na UI. Nenhum `AlertDialog` existia de fato no código (a nota do backlog estava desatualizada) — criado `components/ui/confirm-dialog.tsx` como primeiro primitivo genérico de `components/ui/` (convenção shadcn citada no `CLAUDE.md`, ainda não iniciada), reaproveitando o mesmo estilo de overlay fixo/centralizado do `DiceRollModal`. `character-sheet.tsx`: os botões "Descanso curto"/"Descanso longo" agora só abrem o `ConfirmDialog` (`pendingRest`); a chamada de fato (`handleRest`) só dispara em `onConfirm`. Testado no nível do `ConfirmDialog` (genérico: fechado não renderiza, cancelar chama `onCancel` sem `onConfirm`, confirmar chama `onConfirm`) — não foi escrito um teste de integração da `CharacterSheet` inteira pelo mesmo motivo já registrado na história do rodapé de rolagens (árvore de hooks grande demais pra mockar); a fiação em `character-sheet.tsx` foi conferida por leitura de código. Escopo: só os dois botões de "descanso" — o botão "gastar dado de vida" do `HitDiceTracker` não abre confirmação, já que ele é uma ação aditiva sobre um descanso curto já em andamento, não a declaração do descanso em si.

- **Como jogador de Paladin/Cleric, quero escolher qual opção de Canalizar Divindade estou usando quando tenho mais de uma. ✅ (2026-08-26)**
  - [x] `class-resources.tsx`: para o recurso `channel_divinity_charges`, exibir um seletor das opções disponíveis (`FeatureOption`) antes de confirmar o uso, quando houver mais de uma
  - [x] Enviar `option_id` no `POST /characters/{id}/resources/{resource_key}/use`
  - [x] Teste: recurso com múltiplas opções exige seleção antes de habilitar o botão "usar"; recurso com uma única opção usa direto, sem seletor
  - Notas: o backend já aceitava `option_id` em `use_resource` (Fase 8 do backend), mas não expunha a *lista* de opções disponíveis pro cliente descobrir se um recurso precisa de seleção — só `last_feature_option_id` (a última usada). Lacuna mecânica encontrada e resolvida inline: novo `GET /characters/{id}/resources/{resource_key}/options` (`CharacterService.get_resource_options`, reaproveitando `_resource_options` já existente) retorna as `FeatureRead` do catálogo (traduzidas) — vazio quando o recurso não tem conceito de opção ou nenhuma bate com as classes do personagem. `class-resources.tsx` virou `ResourceRow` por item (hook próprio `useResourceOptions`), com `<select>` exigido só quando há mais de uma opção; `useSpendCharacterResource` passou a receber `{resourceKey, optionId}` em vez de só `resourceKey` (único consumidor era este componente).

- **Como jogador, quero escolher o alvo ao conjurar uma magia (aliado/inimigo/eu mesmo) e ver a DC quando ela exigir resistência. ✅ (2026-08-26)**
  - [x] `spell-list-by-circle.tsx`/tela de combate: ao conjurar, pedir `target_participant_id` conforme `target_type` da magia (self não pede alvo; enemy/ally listam os participantes do encontro atual)
  - [x] Magias `saving_throw`: exibir a DC calculada retornada pelo servidor e um atalho pra rolar a resistência do alvo (reaproveita `RollButton`/`roll-log` já usados na concentração, Fase 7)
  - [x] Magias `attack_roll`: reaproveitar o fluxo já existente de `attack_spell` (Fase 6)
  - [x] Magias `cast_only`: registrar o efeito sem pedir rolagem nenhuma
  - [x] Teste: cada `action_type` de magia mostra o fluxo de UI correspondente (seleção de alvo, DC exibida, ou nenhuma rolagem)
  - Notas: **decisão de escopo confirmada com o usuário antes de implementar** — seleção de alvo só faz sentido dentro de um encontro ativo, e a ficha standalone (`spell-list-by-circle.tsx`) não tem esse contexto (só `campaignId`/`characterId`, sem `sessionId`/`encounterId`); o `ActionPicker` do combate já tinha os participantes do encontro à mão. Escolhido estender o `ActionPicker` em vez de levar contexto de sessão pra ficha. Novo kind `cast_spell_effect` ("Conjurar magia (efeito)") ao lado do já existente `attack_spell` (renomeado pra "Conjurar magia (ataque)" pra diferenciar) — ele não passa pelo `declareAction`/log de combate (WS), chama direto `POST /spells/{id}/cast` (o mesmo endpoint que a ficha usa), já que o efeito é do personagem, não uma ação resolvida pelo motor de combate. Ao escolher uma magia com `target_type !== "self"` exige alvo antes de habilitar "Declarar"; `action_type: "attack_roll"` mostra aviso pra usar "Conjurar magia (ataque)" em vez disso; `cast_only` conjura direto sem UI extra; `saving_throw` mostra a CD retornada + um `RollButton` pra a resistência do alvo, resolvendo `save_ability_score_id` → código de habilidade via `useAbilityScores()` (novo). Lacunas mecânicas resolvidas inline: `Spell` (frontend) não tinha `action_type`/`target_type`/`save_ability_score_id` mesmo já existindo no backend; `CharacterSpellCastRequest`/resposta de `castCharacterSpell` estavam com o mesmo bug já visto na história de animação de dado — tipadas como `Character` puro quando o backend sempre devolveu `CharacterSpellCastResponse` (`character` + `save_dc` + `target_participant_id`), corrigido do mesmo jeito (response não lido nem usado antes, então não quebrava nada, só desperdiçava os campos). Não havia endpoint de catálogo pra ability scores (`app/catalog/schemas.py` já tinha `AbilityScoreDefinitionRead` e `service.py` já tinha `list_ability_scores`, só faltava o router) — adicionado `GET /catalog/ability-scores` (sem tradução, `index` é código fixo).

- **Bugfix — preparar uma magia está preparando a lista inteira em vez de só a magia clicada. ✅ (2026-08-26)**
  - [x] Investigar `spell-list-by-circle.tsx`/hook de toggle `prepared`: identificar se é colisão de chave de cache do TanStack Query, callback compartilhado entre itens da lista, ou estado local não isolado por `CharacterSpell.id`
  - [x] Corrigir para que o toggle afete só a entrada clicada
  - [x] Teste de regressão: preparar uma magia específica não altera o estado `prepared` das demais da lista
  - Notas: investigação não encontrou uma mutação/estado de fato compartilhado entre magias — `handleTogglePrepared` já usava `spell.id` corretamente tanto no payload (`spellEntryId`) quanto na key da lista (`key={spell.id}`), e o backend (`CharacterService.update_spell`) já resolve só a entrada pedida. O único ponto real de acoplamento entre linhas: o botão "preparar"/"preparada" de **cada** magia ficava desabilitado enquanto **qualquer** toggle da lista estivesse em voo, porque todas usavam o mesmo `updateSpell.isPending` (um único hook de mutation compartilhado pelo componente inteiro) — no fim, cada linha sempre reflete só a sua própria mudança quando a resposta chega, mas visualmente parecia que "a lista inteira reagia" enquanto uma rolava. Trocado por um estado local `togglingId`, então só o botão da magia realmente clicada desabilita durante a chamada.

- **Como jogador, quero minhas magias organizadas em seções por círculo, e só poder adicionar uma magia que meu personagem realmente pode ter naquele círculo/classe (com opção de forçar mediante confirmação). ✅ (2026-08-26)**
  - [x] `spell-list-by-circle.tsx`: reestruturar em acordeões por círculo (0 = truques) com subtítulo, em vez da lista única atual
  - [x] `spell-search.tsx`: verificar, antes de permitir adicionar, se o círculo da magia está disponível para a classe/nível atual do personagem (classes conjuradoras e progressão já resolvidas via `useCatalogEntry("classes", ...)`, mesmo dado usado pelo level-up)
  - [x] Se o círculo não estiver disponível, exibir modal de confirmação ("tem certeza que quer adicionar mesmo assim?") antes de enviar o POST
  - [x] Teste: magia de círculo disponível adiciona direto; magia de círculo indisponível pede confirmação antes de enviar; usuário pode cancelar
  - Notas: o backend já rejeita com 422 acima do limite de preparadas/conhecidas (Fase 6) — esta história é uma checagem preventiva de elegibilidade por círculo/classe, complementar a essa validação, não uma substituição dela. Acordeão implementado com `<details>`/`<summary>` nativos (todos abertos por padrão) em vez de um componente controlado — `<summary><h3>…</h3></summary>` preserva o role `heading` (spec do HTML permite um heading como filho de `summary`), então nada mudou pros testes que já buscavam por `getByRole("heading", …)`. Checagem de elegibilidade ficou em `spell-list-by-circle.tsx` (não em `spell-search.tsx`, que só lista/filtra o catálogo): busca a definição completa da classe ativa (`useCatalogEntry("classes", activeClassOption.id)`), acha o `ClassLevel` do nível atual do personagem naquela classe, e calcula o maior círculo com `slot_count > 0`; truques (círculo 0) nunca pedem confirmação. Reaproveitado o `ConfirmDialog` da história de descanso.

- **Como jogador, quero que minha CA na ficha reflita a armadura/escudo equipados, automaticamente. ✅ (2026-08-26 — já funcionava)**
  - [x] `equipment-list.tsx`: nenhuma mudança de UI necessária além de garantir que o toggle `equipped` invalida a query da ficha (`useCharacter`) pra reexibir a CA recalculada
  - [x] Teste: equipar/desequipar armadura atualiza o valor de CA exibido na ficha após a resposta do servidor
  - Notas: nenhuma mudança de código foi necessária — `useUpdateCharacterEquipment` já invalidava exatamente a query key que `useCharacter` (usada por `app/campaigns/[campaignId]/characters/[characterId]/page.tsx`) assina, então o toggle de `equipped` já disparava um refetch e a CA recalculada pelo backend (`_recalculate_armor_class`, Fase 8 do backend) já chegava na ficha. Adicionado só o teste de regressão que faltava (`use-character.test.ts`), com `useCharacter` e `useUpdateCharacterEquipment` reais sob o mesmo `QueryClient`, provando o fluxo ponta a ponta em vez de assumir pela leitura de código.

- **Como jogador, quero registrar ganho e gasto de moedas por denominação (cobre, prata, ouro, platina), não só um valor abstrato. ✅ (2026-08-26)**
  - [x] `currency-tracker.tsx`: inputs separados para as 4 denominações (cp/sp/gp/pp — sem `ep`, decisão do grupo), convertendo o total pro delta em copper esperado por `POST /characters/{id}/currency`
  - [x] Exibição do saldo decompõe o valor em copper armazenado pra denominações (maior pra menor: pp→gp→sp→cp), em vez de mostrar só o número bruto de copper
  - [x] Teste: ganho/gasto misto (ex. +2 gp -5 sp) calcula o delta certo em copper; exibição decompõe corretamente um saldo conhecido
  - Notas: sem mudança de backend — `Character.currency_cp` continua como coluna única normalizada (decisão da Fase 6); a conversão por denominação acontece só na UI. A exibição do saldo já decompunha corretamente (só precisava tirar `ep` da lista de denominações usada tanto na exibição quanto nos inputs, por decisão do grupo). Trocado o par de botões "Ganhar"/"Gastar" com um valor único por 4 inputs (um por denominação), cada um aceitando negativo — um único "Registrar" soma `valor × taxa` de cada denominação num delta de copper e envia uma chamada só, cobrindo ganho/gasto misto na mesma ação (ex. "+2 gp -5 sp").

- **Como DM, quero que qualquer lista de catálogo usada para adicionar algo à ficha seja pesquisável, e que adicionar de fato integre o efeito mecânico correspondente. ✅ (2026-08-26 — parcial, ver notas)**
  - [x] Campo de busca por nome (reaproveitando `catalog-filter-bar.tsx`) em toda lista de seleção usada pra adicionar algo à ficha que hoje não tem busca (features/talentos avulsos, opções de feature da história de level-up acima)
  - [x] Ao adicionar um item que concede um recurso/efeito mecânico modelado (ex. talento que dá um recurso de classe, feature que altera CA/ataque), refletir isso nos componentes correspondentes (`class-resources.tsx`, cálculo de CA) em vez de só criar um registro de texto solto em Características
  - [x] Teste: busca filtra a lista corretamente; adicionar um item com efeito mecânico modelado aparece refletido no componente correspondente
  - Notas: escopo real dessa história, verificado antes de implementar: "opções de feature da história de level-up" já tinha busca desde a história de escolhas de nível (Fase 8, `level-up-dialog.tsx`, busca inline quando a lista passa de 5 opções) — nada a fazer ali. O único ponto sem busca era o formulário 100% texto-livre de "Adicionar característica" (`FeaturesSection`, em `character-sheet.tsx`): pra `source_type="feat"`, virou uma busca de verdade no catálogo de talentos da campanha (`useCatalogList("feats", {campaign_id})` + `CatalogFilterBar`), escolhendo um talento da lista em vez de digitar o nome; `source_type="class"` continua com os campos de texto livre, já que "características de classe fora do level-up" não têm um catálogo fechado equivalente pra buscar (a modelagem de nível/level-up já cobre isso via `FeatureOption`). Quanto a "refletir o efeito mecânico": não existe hoje nenhum vínculo de catálogo entre `Feat` e um recurso de classe/CA (`Feat` não referencia `ClassLevelResource` nem nada equivalente) — só as escolhas de nível (`FeatureOption`, já resolvidas automaticamente pelo backend desde a Fase 8) têm modelagem mecânica dedicada, e essas já refletem nos componentes certos sem passar por este formulário. Então, como a própria história previa ("itens sem modelagem mecânica dedicada continuam registrados como texto livre"), um talento adicionado por aqui continua sendo só um registro de `CharacterFeature` — a busca resolve a descoberta/seleção, não inventa um sistema de efeitos mecânicos que o catálogo ainda não modela.

**Lacunas descobertas na Fase 8 — resolvidas ao fechar a fase.**

- [x] Animação de dado (~1.5s) no ataque/dano resolvido em combate (`action-picker.tsx` → `ActionLog`, via `declareAction`/WebSocket). ✅ (2026-08-26) — Notas: reavaliando o receio original (registrado na história de animação de dado) contra o código de verdade: `combat-provider.tsx`'s `action_resolved` só alimenta `actionLog` (a lista de texto do log) — não toca PV/turno/condições de participante (essas vêm de eventos próprios, `participant_updated`/`turn_advanced`), então atrasar só a revelação da entrada do log **num cliente específico** nunca competia com nem atrasava o estado de combate compartilhado; o risco de dessincronização presumido antes não se confirmou lendo o fluxo real. `DeclareActionResultRead`/`DeclareActionResultPayload` já carregavam `attack_roll`/`attack_bonus`/`attacker_check`/`target_check`/`damage_rolled` estruturados no broadcast (não precisou de mudança de backend) — só não estavam sendo usados no frontend. `action-log.tsx`: ao chegar uma entrada nova em `actionLog` com algum desses campos, enfileira e anima cada rolagem envolvida em sequência via `DiceRollModal` (ex. ataque → dano), sem bloquear a lista em si (que já reflete o texto da entrada imediatamente, como antes — só o "flourish" de animação é backgroundizado por cliente). Ações sem rolagem (flavor actions) não acionam o modal.

---

## Fase 9 — Correções e Regressões

> Depende do backend Fase 9. Levantamento do grupo em 2026-08-28: vários itens reportados como "não funciona" já têm rota de backend + tela de frontend prontas no código — tratar como investigação de bug, não redesenho.

- **Como jogador, quero ver a próxima sessão agendada no dashboard da campanha.** ✅ (2026-08-28)
  - [x] Reproduzir com o backend corrigido (Fase 9 do backend): confirmar que o card "próxima sessão" (`app/campaigns/[campaignId]/page.tsx`) volta a aparecer
  - [x] Se o fix de backend exigir `scheduled_date` obrigatório na criação, ajustar o formulário rápido de sessão (`app/campaigns/[campaignId]/sessions/page.tsx`) para pedir a data
  - [x] Teste: card mostra a sessão agendada após o fix
  - Notas: sem mudança de código necessária no dashboard/tipos — o fix de backend (Fase 9) já não exige `scheduled_date`, e o frontend já tratava `scheduled_date: string | null` corretamente em todo o caminho (`types/session.ts`, `types/campaign.ts`, `SessionCard`, `campaigns/[campaignId]/page.tsx`). O formulário rápido de sessão (`sessions/page.tsx`) continua enviando só `{ title }`, o que já bate com `SessionCreate` no backend (`scheduled_date` opcional, default `None`). Único ajuste: adicionado teste em `page.test.tsx` cobrindo explicitamente uma `next_session` sem `scheduled_date`, confirmando que o card aparece (sem linha de data) em vez de cair no placeholder "Nenhuma sessão futura agendada".

- **Como mestre, quero criar conteúdo homebrew em todas as categorias do catálogo. ✅ (2026-08-28)**
  - [x] Reproduzir o bug relatado com o usuário, em cada categoria (`custom-entry-form.tsx`) — capturar mensagem de erro exata mostrada na tela
  - [x] Corrigir a causa raiz encontrada no frontend (validação de formulário, envio de payload incorreto) coordenando com o fix de backend da Fase 9
  - [x] Se a mensagem genérica de erro ("backend ainda não aceita criação de homebrew nesta categoria") estiver mascarando o erro real, trocar por uma mensagem que reflita o `detail` retornado pela API
  - [x] Teste: criação em cada uma das 9 categorias funciona ponta a ponta
  - Notas: a causa raiz real (backend) já tinha sido corrigida — `MonsterCreate.size` era `str` livre e agora é o enum `CreatureSize`, rejeitando valor inválido com 422 em vez de 500. No frontend, `custom-entry-form.tsx` deixava o mestre digitar qualquer texto nos campos `size` (monsters), `item_type` (equipment) e `school` (spells) via `<input type="text">`, o que produzia justamente valores inválidos para esses enums — trocados por `<select>` com as opções corretas (`CreatureSize`, `ItemType`, `SpellSchool` de `types/catalog.ts`). `lib/api/catalog.ts` tinha um comentário desatualizado dizendo que `POST /catalog/{category}` não existia (já existe e funciona para as 9 categorias) — removido, sem impacto funcional (não havia lógica condicional baseada nele). A mensagem de erro genérica ("backend ainda não aceita...") foi trocada por uma que usa o `detail` real da resposta da API, incluindo a extração das mensagens por campo de um 422 do FastAPI (`detail` como lista de `{msg}`), com fallback pra mensagem genérica em erros não-`ApiError`.

- **Como mestre, quero selecionar o alvo de um ataque/magia em combate.** ✅ (2026-08-28)
  - [x] Reproduzir com o usuário: `action-picker.tsx` num encontro com participantes mistos (personagens + monstros) vs. só monstros
  - [x] Corrigir a causa raiz encontrada (pode depender do fix de "adicionar personagem ao combate" da Fase 13)
  - [x] Teste: dropdown de alvo lista participantes corretamente em ambos os cenários
  - Notas: confirmado por leitura de código que NÃO é bug isolado de frontend — `ActionPicker` (`components/combat/action-picker.tsx`) renderiza o `<select>` de alvo a partir da prop `otherParticipants`, que a página de combate (`app/campaigns/[campaignId]/combat/[encounterId]/page.tsx`) já popula corretamente com `encounter.participants.filter((p) => p.id !== currentTurnParticipant.id)` — todos os participantes, independente de serem personagem ou monstro. O componente em si funciona igual em encontros mistos e em encontros só-de-monstros. O "dropdown vazio" relatado só ocorre porque a única via de adicionar participantes ao encontro hoje é `MonsterPicker` (seção "Adicionar participante" da página) — não existe ainda um `character-picker.tsx`/fluxo equivalente para adicionar personagens/jogadores, então um encontro típico (só monstros adicionados) não tem ninguém além do próprio atacante pra listar como alvo. Essa lacuna já está corretamente registrada na Fase 13, história 3 ("Como mestre, quero adicionar personagens (jogadores) ao combate, não só monstros/NPCs") — não duplicado aqui. Adicionado teste de regressão em `action-picker.test.tsx` provando que o dropdown de alvo lista corretamente todos os `otherParticipants` passados (misturando personagem e monstro) — comprova que o componente funciona; falta apenas a via de entrada (Fase 13) para popular o encontro com personagens.

- **Como mestre, quero editar o nome da minha campanha.** ✅ (2026-08-28)
  - [x] Confirmar com o usuário se o link para `app/campaigns/[campaignId]/settings/page.tsx` está descobrível na navegação atual — a tela e o `PATCH /campaigns/{id}` já existem e funcionam
  - [x] Se for um problema de descoberta (não de funcionalidade), adicionar uma entrada visível de "Configurações" no menu/nav da campanha
  - [x] Teste: link de Configurações está visível e leva ao formulário de edição de nome
  - Notas: confirmado por leitura de código que `settings/page.tsx` e `PATCH /campaigns/{id}` já funcionavam (cobertos por `settings/page.test.tsx` e pelo router do backend) — não era um bug de funcionalidade. O item "Configurações" já existia em `campaign-sidebar.tsx`/`mobile-nav.tsx` desde a Fase 1, mas visível igualmente para DM e jogador, misturado a mais 10 itens de conteúdo sem nenhum destaque — fácil de passar despercebido, especialmente na barra inferior mobile. Corrigido tratando-o como ação DM-only (mesmo padrão do item "Diário"): marcado `dmOnly: true` em `NAV_ITEMS` (oculto para jogadores em ambos os componentes de navegação) e adicionado um separador visual (`separatorBefore`) acima do item na sidebar desktop para destacá-lo como ação administrativa. Testes novos em `campaign-sidebar.test.tsx` cobrindo visibilidade pro DM e ocultação pro jogador.

---

## Fase 10 — Ficha do Personagem: Edição, Identidade e Navegação

> Depende do backend Fase 10.

- **Como jogador, quero editar as informações do meu personagem depois de criado (nome, alinhamento, antecedente, atributos-base).** ✅ (2026-08-29)
  - [x] `lib/api/characters.ts`: `updateCharacterInfo` (novo, distinto de `updateCharacterHp`), estender `hooks/use-character.ts`
  - [x] Formulário de edição na ficha (`character-sheet.tsx`), reaproveitando o padrão visual do editor inline de HP; campos de ability score exigem confirmação (aviso de efeitos em cascata em CA/PV/perícias)
  - [x] Teste: edição de nome/alinhamento/antecedente atualiza a ficha; edição de ability score mostra o aviso de confirmação antes de enviar
  - Notas: novo componente `components/characters/character-info-editor.tsx` (colapsado atrás de um botão "Editar informações" no cabeçalho da ficha), com o mesmo padrão de draft state + `onBlur`/submit do editor de HP. Nome/alinhamento/antecedente enviam o PATCH direto ao submeter o form. Alterar qualquer atributo-base abre um `ConfirmDialog` (mesmo componente do fluxo de descanso) avisando que CA/PV máximo/perícias podem mudar; só ao confirmar o PATCH é disparado. O payload só inclui os campos realmente alterados (`ability_scores` é parcial — só as habilidades editadas). Raça/classe permanecem sem UI de edição (fora de escopo, backend não aceita).

- **Como jogador, quero colocar uma imagem no meu personagem, exibida "redonda" na ficha e (depois) no mapa.** ✅ (2026-08-30)
  - [x] `lib/api/characters.ts`: `uploadCharacterPortrait` (multipart, mesmo padrão de upload de Handouts)
  - [x] Componente de avatar circular (`border-radius: 50%`) no cabeçalho da ficha, reaproveitado depois nos tokens do mapa (Fase 15)
  - [x] Teste: upload atualiza o avatar exibido; personagem sem imagem mostra um placeholder (iniciais ou ícone)
  - Notas: `lib/api/characters.ts` ganhou `uploadCharacterPortrait`/`removeCharacterPortrait` (mesmo padrão multipart de `createHandout`), com hooks `useUploadCharacterPortrait`/`useRemoveCharacterPortrait` em `hooks/use-character.ts`. Split em dois componentes: `components/characters/character-avatar.tsx` (puramente visual — circular, placeholder de iniciais quando sem `portrait_url`, deliberadamente sem lógica de upload para ser reaproveitado nos tokens do mapa na Fase 15) e `components/characters/character-portrait.tsx` (wrapper com upload/troca/remoção, usado no cabeçalho da `character-sheet.tsx`). `Character.portrait_url` (tipo) espelha `CharacterRead.portrait_url` do backend; `CharacterSummary` não ganhou o campo (backend também não expõe para quem não é dono/DM). Upload/remoção são owner-only no backend — o frontend não faz checagem própria de dono, só exibe o erro retornado (mesmo padrão do `CharacterInfoEditor`).

- **Como jogador, quero marcar minhas proficiências com base nas capacidades da minha raça e classe(s), não livremente.** ✅ (2026-08-30)
  - [x] `lib/api/characters.ts`/`hooks/use-character.ts`: consumir o novo endpoint de escolha restrita de proficiência
  - [x] UI na ficha: lista o conjunto de escolha válido (ex. "escolha 2 de: ...") derivado da raça/classe do personagem, em vez de um campo livre
  - [x] Teste: só as opções do conjunto válido aparecem selecionáveis; proficiências fixas de raça/classe aparecem já marcadas, não editáveis
  - Notas: o backend Fase 10 só tinha `POST /characters/{id}/proficiencies` (grava a escolha) — não existia forma de descobrir o conjunto válido antes de submeter, então foi adicionado `GET /characters/{id}/proficiencies` (`CharacterService.get_proficiency_choices`, owner-only) retornando cada `ProficiencyChoiceGroup` com `choose_count`/`options`/`selected`, reaproveitando `_skill_choice_groups`; testado em `backend/tests/characters/test_proficiency_choices.py`. Novo componente `components/characters/proficiency-choices.tsx` (hooks `useProficiencyChoices`/`useSetProficiencyChoices`), montado na ficha logo após `SkillList`. Como o backend não expõe forma de desfazer uma escolha já feita, uma perícia em `selected` renderiza marcada e desabilitada (mesmo tratamento das proficiências fixas) — só as opções ainda não escolhidas do grupo ficam selecionáveis, até o `choose_count` restante; um grupo já totalmente preenchido não renderiza mais. `SKILL_LABELS` foi exportado de `skill-list.tsx` para reuso.

- **Como jogador, quero que a navegação da ficha mostre as sessões do personagem agrupadas num dropdown (com overflow) e que a navegação geral do app fique num menu hambúrguer no topo.** ✅ (2026-08-30)
  - [x] `lib/api/characters.ts`: `getCharacterSessions` (novo endpoint do backend Fase 10)
  - [x] Reorganizar o header da página de ficha (`app/campaigns/[campaignId]/characters/[characterId]/page.tsx`): dropdown de sessões do personagem (com overflow pros que não couberem) + ícone de menu hambúrguer agrupando a navegação geral do app (hoje em `campaign-sidebar.tsx`/`header.tsx`)
  - [x] Teste: dropdown lista as sessões do personagem; hambúrguer abre/fecha a navegação geral sem cobrir o conteúdo da ficha
  - Notas: novo `hooks/use-character.ts` → `useCharacterSessions` sobre `getCharacterSessions`. Novo componente isolado `components/characters/character-sessions-dropdown.tsx` (botão "Sessões" + contagem, lista com `max-h-72 overflow-y-auto`, fecha em Escape/clique fora) — deixado deliberadamente separado para a próxima história (reordenar sessões) acoplar dentro dele. Novo `components/layout/app-nav-menu.tsx`: botão hambúrguer que reaproveita `NAV_ITEMS` (exportado de `campaign-sidebar.tsx`) num painel overlay `position: absolute` com backdrop — fica fechado por padrão e nunca desloca o conteúdo da ficha, só sobrepõe enquanto aberto. Escopo limitado à página da ficha (`page.tsx`); `header.tsx`/`campaign-sidebar.tsx`/`mobile-nav.tsx` do layout de campanha não foram alterados — continuam servindo as demais páginas normalmente. Papel do usuário (`role`) obtido via `useMyMembership` (já usado no layout de campanha) para decidir itens DM-only no hambúrguer.

- **Como jogador, quero reordenar as sessões na minha ficha para organização pessoal.** ✅ (2026-08-30)
  - [x] `lib/api/characters.ts`: `reorderCharacterSessions` (drag-and-drop ou botões subir/descer)
  - [x] UI de reordenação dentro do dropdown de sessões da história anterior
  - [x] Teste: reordenar atualiza a ordem exibida sem afetar a lista de sessões vista por outro personagem/jogador
  - Notas: `lib/api/characters.ts` ganhou `reorderCharacterSessions` sobre `PATCH /characters/{id}/sessions/order` (backend Fase 10, já mergeado); novo hook `useReorderCharacterSessions` em `hooks/use-character.ts` faz o swap otimista no cache de `useCharacterSessions` (chave `[...CHARACTERS_QUERY_KEY, characterId, "sessions"]`) e reverte em erro. Botões subir/descer (não drag-and-drop — mais simples e acessível) dentro de `components/characters/character-sessions-dropdown.tsx`, como planejado na história anterior: cada linha virou um `flex` com o `Link` da sessão + coluna de dois botões (▲/▼), primeiro/último item com o botão correspondente desabilitado. Owner-only é reforçado só no backend (mesmo padrão do `CharacterPortrait`/`CharacterInfoEditor`) — os botões aparecem para qualquer visualizador da ficha e um erro de um não-dono (403) aparece inline no dropdown (`role="alert"`), já que a página da ficha não carrega hoje uma flag "sou o dono" para decidir visibilidade client-side. A reordenação é por-personagem (a `CharacterSessionOrder` do backend já garante isso) — não afeta a ordem que outro jogador/personagem vê da mesma sessão.

---

## Fase 11 — Catálogo Homebrew: Profundidade e Estrutura

> Depende do backend Fase 11.

- **Como mestre, quero customizar todos os atributos possíveis de uma raça homebrew.** ✅ (2026-08-30)
  - [x] `custom-entry-form.tsx`: expor os campos hoje ausentes na categoria `races` (`speed`, `size`, `darkvision_range`) e os novos endpoints de anexo (bônus de atributo, traços, sub-raças, idiomas, proficiências)
  - [x] Teste: formulário de raça homebrew salva todos os atributos customizados; leitura de volta reflete o que foi salvo
  - Notas: `custom-entry-form.tsx` agora despacha `category === "races"` para um sub-formulário dedicado (`race-homebrew-form.tsx`) em vez de crescer o modelo genérico "um campo texto/número/select por chave" — raças carregam anexos estruturados (`language_ids`/`proficiency_ids` multi-select na criação, mais bônus de atributo/traços/sub-raças via `POST /catalog/races/{id}/...` só depois que a raça existe) que não cabem nesse modelo. O dispatch acontece antes de qualquer hook ser chamado no componente (sem violar Rules of Hooks), delegando a lógica dos demais campos pro corpo original renomeado `GenericCatalogEntryForm`. Após a criação, `race-attach-panel.tsx` mostra os anexos já salvos (lidos de volta via `useCatalogEntry`) e formulários para adicionar bônus de atributo, traços e sub-raças (sub-raça aceita um bônus + um traço inline por submissão, já que o backend aceita listas — limite conhecido: bônus/traços extras da mesma sub-raça exigiriam repetir o POST de anexo, não coberto por esta UI). Gap de backend descoberto durante a implementação: não existia endpoint para listar `Language`/`Proficiency` (só apareciam embutidos em `RaceRead`), impossibilitando montar os checkboxes de `language_ids`/`proficiency_ids` — adicionados `GET /catalog/languages` e `GET /catalog/proficiencies` (reaproveitando `service.list_languages`/`list_proficiencies`, já existentes) com testes de integração em `test_router_homebrew.py`.

- **Como mestre, quero poder excluir uma raça/classe/magia/... homebrew que eu criei.** ✅ (2026-08-31)
  - [x] `lib/api/catalog.ts`: `deleteCustomEntry` (as 9 categorias)
  - [x] Botão "excluir" na tela de detalhe do catálogo (`catalog-entry-detail.tsx`), visível só pro DM e só em entradas homebrew (`is_custom=true`) da própria campanha — nunca em conteúdo SRD
  - [x] Modal de confirmação antes de excluir (ação destrutiva)
  - [x] Teste: botão só aparece pra DM em homebrew; exclusão remove a entrada da lista; entrada SRD nunca mostra o botão
  - Notas: `deleteCustomEntry` reaproveita `CATALOG_CATEGORY_PATH` (já existente) para as 9 categorias e o novo hook `useDeleteCustomEntry` (`hooks/use-catalog.ts`) invalida as queries da categoria no sucesso. O botão vive num `EntryHeader` novo dentro de `catalog-entry-detail.tsx`, condicionado a `entry.is_custom && useMyMembership(campaignId).role === "dm"` — mesmo padrão de checagem de DM já usado em `catalog/[category]/new/page.tsx`. Usa o `ConfirmDialog` genérico existente; ao confirmar, chama `deleteEntry.mutateAsync` e navega de volta pra lista da categoria em caso de sucesso, ou mostra `ApiError.message` (cobrindo o 409 de referência existente) sem fechar a tela em caso de erro. A página `[entryId]/page.tsx` passou a repassar `campaignId` pro componente (antes só passava `category`/`entry`).

- **Como mestre, quero que os campos do formulário de homebrew tenham unidades declaradas e usem seleção estruturada quando o conjunto de opções é limitado, em vez de texto livre.** ✅ (2026-08-30)
  - [x] `custom-entry-form.tsx`: trocar campos como `spell.school` (hoje `type: "text"` apesar do backend exigir um `MagicSchool.index` válido) e `equipment.item_type` por `<select>` com as opções reais do vocabulário fixo do catálogo
  - [x] Adicionar labels de unidade nos campos que precisam (ex. "alcance (metros)", "duração (rodadas/minutos)", "peso (kg)")
  - [x] Teste: seleção de escola de magia via `<select>` envia o `index` correto; tentativa de submissão sem selecionar um campo obrigatório mostra erro antes do POST
  - Notas: `spell.school`, `equipment.item_type` e `monster.size` já haviam virado `<select>` num fix anterior da Fase 9 (`747ee5c`); o gap restante desta história era `magic-item.rarity`, que ainda era `type: "text"` apesar de existir um vocabulário fixo (`ItemRarity` em `catalog/domain.py`, já espelhado em `types/catalog.ts`) — agora também é `<select>`. Labels de unidade adicionados em `spells` (alcance/duração/tempo de conjuração/componentes) e `equipment` (peso/custo); campos que já eram enum (`school`/`item_type`/`size`/`rarity`) não precisam de unidade, o rótulo já é autoexplicativo. Validação de campo obrigatório usa a constraint nativa do HTML (`required`) — testado verificando que `mutateAsync` não é chamado e `checkValidity()` retorna `false` quando um `<select required>` fica sem seleção.

- **Como jogador/mestre, quero ver os detalhes técnicos de qualquer item do catálogo exibidos adequadamente, não como JSON cru.** ✅ (2026-08-31)
  - [x] Criar componentes de detalhe dedicados por categoria (`race-detail.tsx`, `class-detail.tsx`, `spell-detail.tsx`, `item-detail.tsx`, `magic-item-detail.tsx`, `background-detail.tsx`, `feat-detail.tsx`, `rule-detail.tsx`), seguindo o padrão já estabelecido por `monster-stat-block.tsx` (grids `dl`, unidades nos labels, seções agrupadas)
  - [x] `catalog-entry-detail.tsx`: rotear para o componente certo por categoria, mantendo o fallback genérico só para casos não cobertos
  - [x] Teste: cada categoria renderiza sua visão estruturada; nenhuma categoria cai mais no dump de JSON cru por padrão
  - Notas: as 9 categorias agora têm visão estruturada — as 8 novas mais `monsters`, que já usava `monster-stat-block.tsx`. `catalog-entry-detail.tsx` virou um roteador puro (`CategoryBody`, um `switch` por categoria) que separa a responsabilidade nova (roteamento + cabeçalho com nome/badge/excluir) do corpo específico de cada categoria; o dump de JSON genérico (`GenericBody`) só roda pra categorias fora das 9 dedicadas, hoje nenhuma. IDs estrangeiros (ex. `save_ability_score_id`, `ability_score_id` de pré-requisito de talento) não são resolvidos pro nome da habilidade — ficam fora da UI por ora, já que não há um lookup pronto de `AbilityScoreDefinition.id → index` nas telas de catálogo; texto livre já resolvido no idioma (descrição, traços) é exibido normalmente. Teste único em `catalog-entry-detail.test.tsx` cobre as 9 categorias mais a visibilidade do botão excluir, em vez de um arquivo de teste por componente de detalhe.

---

## Fase 12 — Recursos de Classe e Interatividade Mágica

> Depende do backend Fase 12.

- **Como jogador, quero que recursos de classe que geram ações (ex. Turn Undead) disparem a ação correspondente, não só decrementem um contador.** ✅ (2026-08-31)
  - [x] `class-resources.tsx`: ao usar um recurso que aciona efeito mecânico, abrir o fluxo de seleção de alvo/resolução (reaproveitando `action-picker.tsx`) em vez de só decrementar o contador
  - [x] Teste: uso do recurso com efeito de ação abre a seleção de alvo; uso de um recurso sem efeito de ação continua funcionando como hoje (só decrementa)
  - Notas: `ClassResources` ganhou uma prop opcional `combat` (`{ participantId, otherParticipants, declareAction }`), passada só por `action-picker.tsx` (a ficha standalone continua sem ela, comportamento inalterado). Quando a opção selecionada tem `Feature.index` num conjunto local espelhando `CombatService._CLASS_RESOURCE_EFFECTS` do backend (hoje só `channel-divinity-turn-undead`) **e** há contexto de combate, "usar" vira um seletor de alvos (checkboxes dos outros participantes) em vez de disparar `useSpendCharacterResource` direto; ao confirmar, declara `use_class_resource` via `declareAction` (WS) com `target_id`/`additional_target_ids`/`resource_key`/`resource_option_id` — o backend resolve o teste de resistência e o efeito numa chamada só. Qualquer outra combinação (sem `combat`, ou opção sem efeito mapeado) segue exatamente o fluxo antigo. `types/combat.ts` ganhou `"use_class_resource"` em `CombatActionType`; `lib/ws/types.ts` ganhou `ClassResourceTargetOutcome`, os campos novos de `DeclareActionResult` (`healing_applied`/`resource_key`/`resource_targets`) e de `WSDeclareActionPayload` (`resource_key`/`resource_option_id`/`additional_target_ids`/`manual_save_rolls`) — mirror de `DeclareActionResultRead`/`WSDeclareActionPayload` do backend. Sem override de rolagem manual de resistência na UI (`manual_save_rolls` fica só no tipo, não exposto — simplificação deliberada de escopo; o servidor rola automaticamente contra o stat block de cada alvo). O resultado (sucesso/falha por alvo, DC) já chega pronto em `result.description` (montado pelo backend) — `action-log.tsx` renderiza sem mudança adicional.

- **Como jogador, quero que magias com alvo apliquem o efeito automaticamente ao alvo em combate (cura, dano com resistência).** ✅ (2026-08-31)
  - [x] Confirmar que `action-picker.tsx` (kind `cast_spell_effect`) já cobre cura/buff corretamente após o fix de backend da Fase 12; ajustar UI se o backend passar a exigir/retornar algo novo pra esses casos
  - [x] Teste: conjurar uma magia de cura em combate aplica o HP ao alvo selecionado e reflete no `participant-card.tsx` correspondente
  - Notas: **não cobria** — a auditoria encontrou que o fix de backend (Fase 12) aplica o efeito de uma magia `cast_only` com alvo (cura/dano direto) via `_resolve_spell_effect`, disparado pelo action_type `attack_spell`/`declare_action` — não pelo endpoint `POST /spells/{id}/cast` que `cast_spell_effect` chamava (esse continua bookkeeping-only mesmo dentro de um encontro, por design). Corrigido: `handleCastEffect` agora detecta `action_type === "cast_only" && effectNeedsTarget` (heal/dano direto, ex. Cure Wounds) e declara `attack_spell` via `declareAction` (mesmo caminho que "Conjurar magia (ataque)") em vez de chamar `castSpell`; `saving_throw` e magias `cast_only` sem alvo (ex. Mage Armor, self-only) continuam no fluxo antigo (endpoint da ficha, DC exibida + rolagem manual), sem mudança. Como o catálogo não modela dado de cura (só dano ofensivo tem `SpellDamage`, Fase 8), a UI ganhou um campo opcional "Cura rolada"/"Dano rolado" (`manual_damage_roll`) só quando esse caminho novo está ativo — em branco, o servidor tenta rolar do catálogo (funciona pra magias ofensivas com `SpellDamage`, ex. Magic Missile) e, sem isso também, só registra o cast sem aplicar nada (mesmo fallback do backend). `action-log.tsx`/`lib/ws/types.ts` ganharam `healing_applied` na animação de rolagem (ao lado de `damage_rolled` já existente), então a cura anima como as demais rolagens; `participant-card.tsx` já reflete a HP atualizada via `participant_updated` (evento padrão de qualquer mudança de HP em combate), sem mudança própria necessária ali.

- **Como jogador, quero ver um contador de duração de magia, respeitando rodadas em combate e tempo real fora de combate, destacando quando está prestes a expirar.** ✅ (2026-08-31)
  - [x] Componente de contador de duração (reaproveitando o indicador de concentração já existente, Fase 7) — modo rodadas (decrementa a cada `turn_advanced` recebido via WS) e modo tempo real (contagem regressiva client-side a partir de `expires_at`)
  - [x] Destaque visual (cor/animação) nos últimos segundos/rodadas antes de expirar
  - [x] Teste: contador em modo rodadas decrementa corretamente a cada turno; contador em modo tempo real expira no momento certo
  - Notas: novo `DurationCounter` (`frontend/src/components/characters/duration-counter.tsx`), integrado no `ConcentrationIndicator` existente via prop opcional `concentrationRemaining` (não quebra os usos/testes sem a prop). Modo rodadas lê `useOptionalCombatContext().encounter.current_round` (novo hook não-throwing em `combat-provider.tsx`, `null` fora de um `CombatProvider`, ex.: ficha standalone) e decrementa 1 rodada por incremento de `current_round`, não por `turn_advanced` bruto (várias trocas de turno podem ocorrer sem fechar a rodada). Modo tempo real usa `setInterval` client-side a partir de `remaining_seconds`. Destaque "urgente" (pulse + `role="alert"`): última rodada ou últimos 6s restantes.

---

## Fase 13 — Fluxo de Sessões: Fundamentos Faltantes

> Depende do backend Fase 13.

- **Como mestre, quero concluir uma sessão.** ✅ (2026-08-29)
  - [x] `lib/api/sessions.ts`: `completeSession`
  - [x] Botão "Concluir sessão" em `app/campaigns/[campaignId]/sessions/[sessionId]/page.tsx`, visível pro DM quando `status === "in_progress"`
  - [x] Teste: botão conclui a sessão e atualiza o status exibido
  - Notas: adicionado `completeSession` em `lib/api/sessions.ts` (`POST /sessions/{id}/complete`) e o hook `useCompleteSession(campaignId)` em `hooks/use-session.ts`, invalidando a mesma query key de `useSessions` usada tanto na página de detalhe quanto na lista de sessões. Botão "Concluir sessão" aparece ao lado do rótulo de status quando `isDm && session.status === "in_progress"`. Testes novos em `page.test.tsx` cobrindo o clique do DM (chama a mutation com o id da sessão) e a ausência do botão para jogadores.

- **Como mestre, quero editar o nome de uma sessão.** ✅ (2026-08-29)
  - [x] `lib/api/sessions.ts`: `updateSession`
  - [x] Trocar o título estático da página de detalhe por um campo editável (visível só pro DM)
  - [x] Teste: edição de nome persiste e reflete na lista de sessões
  - Notas: adicionado `updateSession` em `lib/api/sessions.ts` (`PATCH /sessions/{id}`, tipo `SessionUpdate` novo em `types/session.ts`) e o hook `useUpdateSession(campaignId)` em `hooks/use-session.ts`. Título estático da página de detalhe trocado por um modo de edição (botão "Editar" visível só pro DM, abre um `<input>` com botões "Salvar"/"Cancelar"); ao salvar, dispara `PATCH` e invalida a query `useSessions(campaignId)`, que também é a fonte de dados de `sessions/page.tsx` — a lista reflete o novo título automaticamente sem mudança adicional lá. Testes novos em `page.test.tsx` cobrindo a edição/salvamento do título pelo DM e a ausência do botão "Editar" para jogadores.

- **Como mestre, quero adicionar personagens (jogadores) ao combate, não só monstros/NPCs.** ✅ (2026-08-29)
  - [x] `components/combat/character-picker.tsx` (novo, ao lado de `monster-picker.tsx`): busca personagens da campanha (`useCharacters(campaignId)`), autocompleta HP/AC a partir da ficha
  - [x] `app/campaigns/[campaignId]/combat/[encounterId]/page.tsx`: alternância entre "adicionar monstro" e "adicionar personagem" ao criar participante
  - [x] Teste: adicionar personagem via `character-picker` cria o participante com `character_id` preenchido corretamente
  - Notas: `CharacterPicker` segue o mesmo padrão visual/de estado do `MonsterPicker`, mas mais simples — sem entrada manual, já que um participante-personagem sempre carrega `character_id` e a ficha é a fonte da verdade. `useCharacters(campaignId)` popula um `<select>` (em vez da busca por texto do monstro, já que a lista de personagens de uma campanha é tipicamente pequena); ao escolher um, um `useEffect` autopreenche nome/PV máximo/CA a partir do registro — usando o type guard `isFullCharacter` já existente em `types/character.ts`, já que `listCharacters` retorna `Character | CharacterSummary` e só o DM (que é quem vê este picker) recebe a ficha completa com esses campos. Iniciativa e ordem de turno continuam manuais, como no `MonsterPicker`. Submissão fica desabilitada até um personagem ser selecionado. Na página de combate, um par de botões-abas ("Monstro/NPC" / "Personagem") substitui a renderização fixa do `MonsterPicker` dentro do painel "Adicionar participante" já existente — sem mudar o fluxo de abrir/fechar o painel. Resolve a lacuna de seleção de alvo em combate identificada na Fase 9 (história "bug: alvo vazio no ActionPicker"): agora um encontro pode ter participantes-personagem, populando o dropdown de alvo do `ActionPicker`.

- **Como mestre, quero que NPCs fiquem ocultos para jogadores até que eu decida revelá-los.** ✅ (2026-08-29)
  - [x] `npc-card.tsx`: toggle de revelação (DM-only), badge visual de "oculto"/"revelado"
  - [x] Visão do jogador em `world/npcs/page.tsx`: lista só NPCs revelados
  - [x] Teste: jogador não vê NPC oculto na lista; DM vê e revela normalmente
  - Notas: backend já filtrava `GET /campaigns/{id}/npcs` para não-DM e expunha `POST /npcs/{id}/reveal` (mergeado antes desta história) — bastou consumir. Adicionado `Npc.is_revealed` em `types/world.ts`, `revealNpc` em `lib/api/world.ts`, `useRevealNpc` em `hooks/use-world.ts`, seguindo o mesmo padrão já usado por `Handout.is_revealed`/`useRevealHandout`. `npc-card.tsx` ganhou badge "Oculto"/"Revelado" (visível só pro DM) e botão "Revelar" (DM-only, some quando já revelado). `world/npcs/page.tsx` não precisou de mudança — a filtragem de NPCs ocultos pro jogador já é feita pelo backend na própria listagem consumida por `useNpcs`. Testes novos em `npc-card.test.tsx` (badge/botão) e `world/npcs/page.test.tsx` (DM vê+revela; jogador só vê NPCs já revelados).

---

## Fase 14 — Loot e Inventário Integrado

> Depende do backend Fase 14.

- **Como jogador, quero que ao reivindicar um item de loot ele entre no meu inventário de personagem de verdade.** ✅ (2026-08-31)
  - [x] `loot-table.tsx`: após claim bem-sucedido, invalidar/atualizar a query de equipamento do personagem (`useCharacter`) pra refletir o novo item na ficha
  - [x] Teste: claim de loot atualiza a seção de Equipamento da ficha do personagem que reivindicou
  - Notas: `useClaimLootDrop` (hooks/use-inventory.ts) agora invalida `[...CHARACTERS_QUERY_KEY, character_id]` além do feed de loot da campanha, no `onSuccess`, usando o `character_id` da própria variável da mutation — sem precisar de payload extra do backend, já que `claim_loot_drop` já mescla o item em `CharacterEquipment`.

- **Como mestre, quero atribuir um item de loot a qualquer jogador diretamente.** ✅ (2026-08-31)
  - [x] `loot-table.tsx`: menu "atribuir a..." por item de loot, visível só pro DM, listando os personagens da campanha
  - [x] Teste: DM atribui loot a um personagem que não é o seu; ação não aparece pra jogador comum
  - Notas: `LootTable` ganhou props opcionais `isDm`/`characters` (tipadas como `Character | CharacterSummary`, mesmo union que `useCharacters` já retorna); a página de inventário passa `isDm` (via `useMyMembership`) e a lista de personagens da campanha. O menu reusa o mesmo `useClaimLootDrop`/endpoint de claim já usado pelo botão "Reivindicar".

---

## Fase 15 — Redesign de Sessões: Mapas Dinâmicos e Tokens

> Depende do backend Fase 15. Maior fase do backlog — construir em cima da base estabilizada pelas Fases 9-14. Modelo validado com o grupo: mapa = imagem enviada pelo mestre + grid de 1,5m sobreposto (snap); movimento limitado por deslocamento em combate (por turno), livre fora de combate, mestre sempre pode mover qualquer token; sincronização em tempo real via WebSocket.

- **Como mestre, quero subir uma imagem de mapa para uma sessão/encontro, com grid de 1,5m sobreposto.**
  - [ ] `lib/api/maps.ts`, `hooks/use-map.ts`
  - [ ] `components/maps/map-upload.tsx` (DM-only) — upload de imagem, ajuste manual do tamanho de célula do grid sobre a imagem enviada
  - [ ] Teste: upload cria o mapa e exibe o grid sobreposto corretamente

- **Como jogador/mestre, quero ver e posicionar tokens de personagem/NPC/monstro no mapa.**
  - [ ] `components/maps/map-canvas.tsx`: canvas com pan/zoom, renderiza a imagem de fundo + grid + tokens (reaproveitando o avatar circular da Fase 10 para tokens de personagem)
  - [ ] Drag-and-drop de token com snap à célula de grid mais próxima
  - [ ] Teste: arrastar um token pra uma nova célula chama a API de atualização de posição com as coordenadas corretas (snapadas)

- **Como jogador, quero que meu token respeite o deslocamento do meu personagem em combate, e se mova livremente fora de combate; o mestre pode mover qualquer token.**
  - [ ] `map-canvas.tsx`: destacar visualmente o alcance de movimento restante do personagem no turno atual (células alcançáveis dentro do `speed`) quando em combate
  - [ ] Bloquear/mostrar erro ao tentar mover além do alcance no próprio turno; sem bloqueio fora de combate
  - [ ] Teste: tentar mover além do alcance em combate mostra erro e não persiste a posição; movimento dentro do alcance funciona; DM sempre pode mover qualquer token

- **Como grupo, quero ver a posição dos tokens atualizando em tempo real para todos os presentes na sessão.**
  - [ ] `lib/ws/map-socket.ts` (ou estender `combat-socket.ts`): processa `token_moved`/`token_added`/`token_removed`, reconectando e resincronizando via `state_sync` estendido
  - [ ] Teste: `map-provider`/reducer processa os eventos de token corretamente, mesmo padrão de teste já usado pro `combat-provider`

- **Como mestre/jogador, quero selecionar 1 ou mais alvos diretamente no mapa ao declarar um ataque ou conjurar uma magia.**
  - [ ] Estender `action-picker.tsx` para permitir clique direto em um ou mais tokens do mapa como forma de selecionar alvo(s), em vez de só dropdown — clique simples pra alvo único, clique múltiplo (ou desenho de área) pra ações em área
  - [ ] Teste: seleção por clique no mapa produz a mesma lista de `target_participant_id`s que o dropdown produziria; ação de área seleciona todos os tokens dentro do raio

Notas gerais da fase: cada história deve integrar de verdade contra o endpoint correspondente do backend Fase 15 assim que ele existir — não deixar mocks acumulando entre histórias, mesmo padrão disciplinado já usado nas Fases 0-8.
