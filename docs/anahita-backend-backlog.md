# Anahita Backend — Backlog

**Referência:** `docs/anahita-backend-prd.md` (modelo de dados completo, decisões técnicas, estrutura de projeto).

## Como usar este documento

- Marque `[x]` ao concluir uma tarefa. Uma história de usuário só é considerada **pronta** quando todas as suas tarefas estão marcadas **e** `uv run pytest`, `ruff check` e `mypy` passam limpos para o código tocado.
- Trabalhe uma história por vez, na ordem em que aparecem dentro de cada fase (há dependências entre elas — ex. não dá pra fazer `Character` antes do catálogo de `Race`/`ClassDefinition` existir).
- Toda história segue o fluxo padrão do domínio (seção 9.1 do PRD): `models.py` → migração Alembic → `schemas.py` → `service.py` → `router.py` → testes pytest → lint/typecheck limpos. Histórias de catálogo puro (sem endpoint HTTP ainda necessário) podem pular `router.py` — isso é indicado na própria história.
- **Antes de parar uma sessão de trabalho:** atualize a tabela de "Status Geral" abaixo e garanta que todo checkbox reflita o estado real do código (não deixe caixas marcadas por otimismo — a próxima sessão confia nelas).
- Itens já implementados no código (branch `release`, commits até `a5b2cb8`) entram marcados como `[x]` com uma nota `(já implementado)`.

---

## Status Geral

| Fase | Domínio                          | Status                          | Última atualização |
|------|-----------------------------------|----------------------------------|----------------------|
| 0    | Catálogo SRD                      | Parcial (fundação i18n/custom-scope + vocabulário fixo prontos) | 2026-08-22    |
| 1    | Fundação (Auth, Campaigns, Characters) | Parcial (Auth + Storage prontos) | 2026-08-22    |
| 2    | Sessão ao Vivo (Combat, WS)        | Não iniciado                     | —                    |
| 3    | World-building                    | Não iniciado                     | —                    |
| 4    | Loot, Inventário, Handouts         | Não iniciado                     | —                    |
| 5    | Registro e Lore                   | Não iniciado                     | —                    |

---

## Fase 0 — Catálogo SRD (fundação de dados)

> Objetivo: ter as 24 categorias do SRD 2014 modeladas, migradas e semeadas (seed) em `en` (completo) e `pt-BR` (parcial, conforme dados disponíveis em `_data/2014/pt-BR`), antes de qualquer feature de personagem/combate depender delas. Ver seção 7.4 do PRD para o schema detalhado de cada história abaixo.

- **Como desenvolvedor, quero um padrão reutilizável de i18n relacional para que qualquer entidade de catálogo suporte múltiplos idiomas sem JSONB nem tabelas genéricas.**
  - [x] Documentar (docstring/README curto em `app/catalog/`) a convenção `_i18n`: `entity_id` FK, `locale` (String(5), valores `en`/`pt-BR` por ora), unique `(entity_id, locale)`, fallback para `en` quando a tradução do locale ativo não existir — `app/catalog/mixins.py`
  - [x] Criar helper de query genérico em `app/catalog/service.py` (ex. `get_translated(entity, locale)`) que resolve a tradução com fallback, reutilizável por todos os catálogos
  - [x] Escrever teste unitário do helper de fallback (locale ausente → cai pra `en`; locale presente → usa o específico) — `tests/catalog/test_i18n.py`

- **Como DM, quero conteúdo custom (raças, classes, magias, itens, monstros, etc.) preso à minha campanha, para que homebrews não vazem para outras mesas nem para o catálogo global.**
  - [x] Adicionar constraint de domínio (validação em `service.py`, reforçada por CHECK na migração onde o dialeto suportar) `is_custom=False ⟺ campaign_id IS NULL` — implementar uma vez como função utilitária reaproveitada por todos os serviços de catálogo — `app/catalog/domain.py::validate_custom_campaign_scope` + `CatalogEntityMixin` CHECK constraint (aplicada também a `Race`/`ClassDefinition`/`SubclassDefinition`)
  - [x] Escrever teste unitário garantindo que a constraint rejeita `is_custom=True, campaign_id=None` e `is_custom=False, campaign_id=<algo>` — `tests/catalog/test_custom_campaign_scope.py`
  - [x] Escrever teste de query garantindo que uma listagem de catálogo (ex. `list_races(campaign_id=X)`) retorna SRD (`campaign_id IS NULL`) + custom da campanha `X`, mas nunca custom de outra campanha

- **Como desenvolvedor, quero o vocabulário fixo do SRD modelado (Ability Scores, Skills, Alignments, Conditions, Damage Types, Magic Schools, Languages, Weapon Properties) para servir de base a todas as outras categorias.**
  - [x] Criar `models.py`: `AbilityScoreDefinition`, `SkillDefinition`, `Alignment`, `Condition`, `DamageType`, `MagicSchool`, `Language`, `WeaponProperty` + suas 8 tabelas `_i18n` (seção 7.4.1 do PRD)
  - [x] Migração Alembic para as 16 tabelas acima — `alembic/versions/0ab8e6ca5757_*.py` (upgrade/downgrade testados contra Postgres)
  - [x] `schemas.py` (Pydantic, request/response) para as 8 entidades
  - [x] `service.py`: CRUD de leitura (catálogo fixo não tem create via API por ora, só seed)
  - [x] Testes unitários (SQLite) cobrindo criação + leitura traduzida de cada uma das 8 entidades — `tests/catalog/test_fixed_vocabulary.py`

- **Como desenvolvedor, quero Proficiencies modeladas e ligadas a skills/abilities/equipamento para que raças, classes e backgrounds possam referenciá-las.**
  - [x] `models.py`: `Proficiency` (FKs nullable e mutuamente exclusivos por `proficiency_type`), `ProficiencyI18n`, `ProficiencyClass`, `ProficiencyRace` — `equipment_category_id` ainda é UUID solto (sem FK), como `campaign_id`, até a história de Equipamento criar `EquipmentCategory`
  - [x] Migração Alembic — `alembic/versions/1b5ef8883035_*.py` (upgrade/downgrade testados contra Postgres)
  - [x] `schemas.py` + `service.py` (leitura)
  - [x] Teste garantindo que exatamente um FK de referência está preenchido conforme `proficiency_type` — `tests/catalog/test_proficiencies.py`

- **Como jogador, quero o catálogo de Raças completo (com traits, subraças e bônus de habilidade) em vez do MVP mínimo atual.**
  - [x] Estender `models.py` existente (`Race`, `RaceTrait`, `Subrace`, `SubraceTrait`, `RaceAbilityBonus`): adicionar `index` nullable a `Race`/`Subrace`; extrair `name`/`description`/`age`/`alignment_desc`/`size_description`/`language_desc` para `RaceI18n`, `trait_name`/`description` para `RaceTraitI18n` e `SubraceTraitI18n` (seção 7.4.2)
  - [x] Migração Alembic de alteração — recriou o seed do zero (4 registros de placeholder), conforme permitido pela história; `alembic/versions/4a3a38b85c46_*.py` (upgrade/downgrade testados contra Postgres)
  - [x] Atualizar `schemas.py`/`service.py`/`router.py` do catálogo para refletir o novo shape — `list_races_translated`/`get_race_translated` resolvem texto traduzido (fallback `en`) com `locale` como query param no router
  - [x] Atualizar/estender `backend/tests/catalog/test_service.py` e `test_seed.py`

- **Como jogador, quero o catálogo de Classes completo (progressão por nível, features, subclasses, spellcasting) em vez do MVP mínimo atual.**
  - [ ] Generalizar `ClassLevelFeature` → `Feature` (suporta subclass, `parent_feature_id`, `FeaturePrerequisite`) — seção 7.4.4
  - [ ] Criar `ClassLevel`, `ClassLevelFeature` (junção), `ClassLevelSpellSlot`, `ClassLevelResource`
  - [ ] Extrair textos para `ClassDefinitionI18n`, `SubclassDefinitionI18n`, `FeatureI18n`
  - [ ] Migração Alembic
  - [ ] `schemas.py`/`service.py`/`router.py` atualizados
  - [ ] Testes cobrindo: leitura de progressão completa de uma classe (todos os 20 níveis), leitura de recursos por nível (ex. rage_count do Barbarian)

- **Como jogador, quero o catálogo de Magias completo (319 spells do SRD) com escola, classes que conjuram e dano estruturado.**
  - [ ] Adicionar `is_custom`/`campaign_id`/`index`/`magic_school_id` a `Spell` (hoje `school` é string solta — trocar por FK)
  - [ ] Criar `SpellI18n`, `SpellClass` (junção)
  - [ ] Migração Alembic
  - [ ] `schemas.py`/`service.py`/`router.py` atualizados
  - [ ] Testes: spell com múltiplas classes, spell custom presa à campanha

- **Como jogador, quero o catálogo de Equipamento completo (237 itens + categorias + propriedades de arma) em vez do MVP mínimo atual.**
  - [ ] Criar `EquipmentCategory` (+ i18n), estender `Item` com `is_custom`/`campaign_id`/`index`/`equipment_category_id`, criar `ItemI18n`, `ItemProperty` (junção com `WeaponProperty`)
  - [ ] Ajustar `WeaponDetail` (`damage_type_id` FK em vez de string) e manter `ArmorDetail`
  - [ ] Migração Alembic
  - [ ] `schemas.py`/`service.py`/`router.py` atualizados
  - [ ] Testes: item arma com propriedades múltiplas, item custom

- **Como jogador, quero o catálogo de Itens Mágicos (362 itens) para poder distribuir loot mágico nas campanhas.**
  - [ ] `models.py`: `MagicItem` (+ `variant_of_id` auto-FK), `MagicItemI18n`
  - [ ] Migração Alembic
  - [ ] `schemas.py`/`service.py`/`router.py`
  - [ ] Testes: item mágico com variantes (ex. +1/+2/+3)

- **Como jogador, quero o catálogo de Backgrounds e Feats para completar a criação de personagem.**
  - [ ] `models.py`: `Background`, `BackgroundI18n`, `BackgroundProficiency`, `BackgroundEquipment`, `BackgroundFeature`; `Feat`, `FeatI18n`, `FeatPrerequisite`
  - [ ] Migração Alembic
  - [ ] `schemas.py`/`service.py`/`router.py`
  - [ ] Testes de cada entidade + seed

- **Como DM, quero o catálogo de Monstros (stat blocks completos) para popular encontros e NPCs.**
  - [ ] `models.py`: `Monster`, `MonsterI18n`, `MonsterSpeed`, `MonsterSense`, `MonsterArmorClass`, `MonsterProficiency`, `MonsterDamageModifier`, `MonsterConditionImmunity`, `MonsterAction`/`MonsterLegendaryAction`/`MonsterReaction`/`MonsterSpecialAbility` + suas 4 tabelas `*Damage` filhas (seção 7.4.8 do PRD)
  - [ ] Migração Alembic (maior migração do catálogo — considerar quebrar em 2-3 revisions se ficar difícil de revisar)
  - [ ] `schemas.py`/`service.py`/`router.py`
  - [ ] Testes: monstro com múltiplas ações + dano, monstro com legendary actions, monstro custom preso à campanha

- **Como desenvolvedor, quero Rules/RuleSections modeladas para eventual tela de referência de regras no frontend.**
  - [ ] `models.py`: `RuleSection`, `Rule`, `RuleRuleSection` (+ i18n)
  - [ ] Migração Alembic
  - [ ] `schemas.py`/`service.py`/`router.py`
  - [ ] Testes básicos

- **Como desenvolvedor, quero um seed completo em inglês (`en`) para todas as 24 categorias, substituindo os arquivos de placeholder atuais.**
  - [ ] Escrever script(s) de conversão de `_data/2014/en/*.json` (formato SRD/APIReference) para o formato normalizado do banco (mapear `index` → FK real, resolver referências em ordem topológica: vocabulário fixo → raças/classes/proficiencies → spells/equipment → backgrounds/feats/monstros)
  - [ ] Substituir `backend/app/catalog/seeds/data/{races,classes,spells,items}.json` por datasets completos (ou gerar em runtime a partir do JSON fonte — decidir e documentar a escolha)
  - [ ] Estender `backend/app/catalog/seeds/seed.py` para popular as 20 categorias novas, idempotente por `index`
  - [ ] Rodar seed local e conferir contagem de registros por tabela bate com a seção 7.4.1-7.4.9 do PRD (ex. 319 spells, 334 monsters, 362 magic items)
  - [ ] Testes de idempotência do seed (rodar duas vezes não duplica)

- **Como desenvolvedor, quero um seed parcial em pt-BR para as categorias que já têm tradução disponível.**
  - [ ] Mapear quais das 12 categorias com dado em `_data/2014/pt-BR` correspondem a quais tabelas `_i18n` já implementadas
  - [ ] Estender o seed para popular linhas `_i18n` com `locale='pt-BR'` a partir desses arquivos, sem quebrar quando uma categoria não tem pt-BR (fallback para `en` continua funcionando)
  - [ ] Teste: entidade sem tradução pt-BR retorna `en` via fallback; entidade com tradução pt-BR retorna a tradução

---

## Fase 1 — Fundação

### Já implementado
- [x] Auth (JWT + refresh token httpOnly, strategy pattern com `local`) — `app/auth/*` *(já implementado)*
- [x] Storage local (`LocalStorageService`) — `app/storage/*` *(já implementado)*
- [x] Catalog MVP (Race/Class/Spell/Item mínimos, a ser **estendido** pela Fase 0, não refeito) — `app/catalog/*` *(já implementado)*
- [x] Engine: ability modifiers, armor class, hit points, conditions, combat, validation, registry de class handlers (genérico) — `engine/*` *(já implementado)*

### Pendente

- **Como usuário, quero me registrar e fazer login para acessar minhas campanhas.** *(verificar se já coberto pelos endpoints de auth existentes — se sim, marcar como feito e pular)*
  - [ ] Confirmar que `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh` existem e têm teste de integração cobrindo o fluxo completo

- **Como usuário, quero criar uma campanha e ser automaticamente seu DM.**
  - [ ] `app/campaigns/models.py`: `Campaign`, `CampaignMember`, `CampaignInvite` (seção 7.2 do PRD)
  - [ ] Migração Alembic
  - [ ] `schemas.py`/`domain.py`/`service.py`/`router.py`
  - [ ] Regra: criar campanha cria automaticamente `CampaignMember(role=dm)` para o criador
  - [ ] Testes de service + router (criação, unique `(campaign_id, user_id)`)

- **Como DM, quero gerar um convite para um jogador entrar na minha campanha.**
  - [ ] `service.py`: gerar `invite_code` único, expiração
  - [ ] `router.py`: endpoint de criação de convite (só DM) e de resgate (`used_by`)
  - [ ] Testes: convite expirado não pode ser resgatado, convite usado não pode ser reusado

- **Como usuário, quero ver todas as campanhas em que participo (como DM ou jogador).**
  - [ ] Query em `app/queries/` (cross-domain: User → CampaignMember → Campaign)
  - [ ] `router.py`: `GET /campaigns` filtrado pelo usuário autenticado
  - [ ] Teste: usuário vê só suas campanhas, não as de outros

- **Como jogador, quero criar uma ficha de personagem vinculada à minha campanha.**
  - [ ] `app/characters/models.py`: `Character`, `CharacterAbilityScore`, `CharacterSkill`, `CharacterClass`, `CharacterFeature`, `CharacterRaceChoice`, `CharacterSpell`, `CharacterEquipment` (seção 7.3 do PRD)
  - [ ] Migração Alembic
  - [ ] `schemas.py`/`domain.py`/`service.py`/`router.py`
  - [ ] Regra: `Character.race_id`/`class_definition_id`/`spell_id`/`item_id` só podem referenciar catálogo global (SRD) ou custom da própria campanha (reaproveitar a validação de "custom preso à campanha" da Fase 0)
  - [ ] Testes: criação de personagem simples (1 classe, 1 raça), rejeição de referência a catálogo custom de outra campanha

- **Como jogador, quero ver os atributos calculados da minha ficha (modificadores, bônus de perícia, CA, PV) sem calcular na mão.**
  - [ ] Conectar `service.py` de characters à `engine/` (ability modifiers, skill bonus, armor class, hit points)
  - [ ] `schemas.py`: response inclui campos calculados (não persistidos)
  - [ ] Testes: ficha de exemplo com valores conhecidos → conferir modificadores calculados batem com as regras do 5e

- **Como jogador multiclasse, quero adicionar uma segunda classe ao meu personagem.**
  - [ ] `service.py`: validação de multiclass via `engine/validation.py` (prerequisitos de ability score)
  - [ ] `router.py`: endpoint de adicionar classe
  - [ ] Teste: multiclass válido passa, inválido (ability score insuficiente) é rejeitado

- **Como DM, quero criar uma sessão de jogo com número sequencial e notas.**
  - [ ] `app/sessions/models.py`: `Session`, `SessionNote` (seção 7.5 do PRD)
  - [ ] Migração Alembic
  - [ ] `schemas.py`/`domain.py`/`service.py`/`router.py`
  - [ ] Regra: `SessionNote.is_private=true` só visível para o DM
  - [ ] Testes: jogador não vê notas privadas de outro autor; DM vê tudo

---

## Fase 2 — Sessão ao Vivo

- **Como DM, quero iniciar um encontro de combate e adicionar participantes (PCs e monstros).**
  - [ ] `app/combat/models.py`: `Encounter`, `EncounterParticipant`, `EncounterCondition`, `CombatLog` (seção 7.6 do PRD)
  - [ ] Migração Alembic
  - [ ] Regra: um `EncounterParticipant` é PC **ou** NPC/monstro, nunca ambos (validação em `domain.py`)
  - [ ] `schemas.py`/`service.py`/`router.py` REST (CRUD de encounter/participantes fora do fluxo de turno)
  - [ ] Testes de domain (`CombatState`) + service

- **Como DM, quero avançar turnos e aplicar dano/cura/condições em tempo real para todos os jogadores verem.**
  - [ ] `app/combat/ws_manager.py`: `WSConnectionManager` (dict `encounter_id → list[WebSocket]`)
  - [ ] `app/combat/ws_router.py`: endpoint `/ws/combat/{encounter_id}`, auth via JWT em query param, valida membership
  - [ ] Protocolo de mensagens (seção 10.2 do PRD): `state_sync`, `turn_advanced`, `participant_updated`, `encounter_status_changed` (servidor→cliente); `advance_turn`, `update_participant`, `add_participant`, `remove_participant`, `end_encounter` (DM→servidor)
  - [ ] Regra: apenas `role=dm` pode enviar comandos; jogadores read-only (validado a cada mensagem)
  - [ ] Teste de reconexão: cliente desconecta e reconecta, recebe `state_sync` completo
  - [ ] Teste: jogador tentando enviar comando de DM é rejeitado

- **Como jogador, quero ver as condições ativas do meu personagem e seus efeitos mecânicos durante o combate.**
  - [ ] Conectar `EncounterCondition` a `engine/conditions.py` (`get_condition_effects`)
  - [ ] `schemas.py`: response de participante inclui condições + efeitos mecânicos resolvidos
  - [ ] Teste: personagem cego (blinded) → efeito de disadvantage retornado

- **Como DM, quero um log do que aconteceu no combate para referência pós-sessão.**
  - [ ] `service.py`: toda ação relevante grava `CombatLog`
  - [ ] `router.py`: `GET /encounters/{id}/log`
  - [ ] Teste: sequência de ações gera log na ordem correta

---

## Fase 3 — World-building

- **Como DM, quero cadastrar NPCs com ou sem stat block (usando o catálogo de Monstros da Fase 0).**
  - [ ] `app/world/models.py`: `NPC` (com `stat_block_id → Monster`), `Location`, `Faction` (seção 7.7 do PRD)
  - [ ] Migração Alembic
  - [ ] `schemas.py`/`domain.py`/`service.py`/`router.py`
  - [ ] Testes: NPC sem stat block, NPC com stat block do SRD, NPC com monstro homebrew da campanha

- **Como DM, quero organizar locais em hierarquia (região → cidade → taverna).**
  - [ ] `service.py`: navegação de `parent_location_id`, prevenção de ciclo
  - [ ] `router.py`: árvore de locais por campanha
  - [ ] Teste: ciclo é rejeitado; árvore de 3 níveis resolve corretamente

- **Como DM, quero relacionar NPCs a facções, locais e sessões para montar o histórico da campanha.**
  - [ ] `app/world/models.py`: `NPCFaction`, `NPCLocation`, `NPCSession`, `LocationSession`, `FactionRelationship` (tabelas de junção da seção 7.7)
  - [ ] Migração Alembic
  - [ ] `service.py`/`router.py` para cada junção
  - [ ] Testes de cada relação

- **Como DM, quero buscar por nome/descrição em NPCs, locais e facções da minha campanha.**
  - [ ] `tsvector` do Postgres em `app/queries/world_queries.py`
  - [ ] `router.py`: endpoint de busca cross-entidade
  - [ ] Teste de busca (Postgres — não roda em SQLite, marcar como teste de integração)

---

## Fase 4 — Loot, Inventário e Compartilhamento

- **Como DM, quero criar handouts (texto/imagem/mapa) e revelá-los para os jogadores quando quiser.**
  - [ ] `app/handouts/models.py`: `Handout` (seção 7.8 do PRD)
  - [ ] Migração Alembic
  - [ ] `schemas.py`/`service.py`/`router.py` — upload via `StorageService` (reaproveitar `app/storage/`)
  - [ ] Regra: `GET /handouts` para jogador só retorna `is_revealed=true`
  - [ ] Testes: DM vê tudo, jogador só vê revelados

- **Como DM, quero revelar um handout em tempo real durante uma sessão ativa.**
  - [ ] Evento `handout_revealed` no WebSocket de combat existente (seção 10.3 do PRD)
  - [ ] Teste: broadcast chega para jogadores conectados

- **Como grupo, quero um inventário compartilhado da campanha.**
  - [ ] `app/inventory/models.py`: `PartyInventory` (seção 7.9 do PRD)
  - [ ] Migração Alembic
  - [ ] `schemas.py`/`service.py`/`router.py`
  - [ ] Testes básicos de CRUD

- **Como DM, quero distribuir loot (itens do catálogo ou custom) após um combate, incluindo dinheiro.**
  - [ ] `app/inventory/models.py`: `LootDrop` (item do catálogo, incluindo `MagicItem` da Fase 0, ou nome livre + moeda em copper)
  - [ ] Migração Alembic
  - [ ] `service.py`/`router.py`: distribuir para personagem (`claimed_by`)
  - [ ] Testes: loot de item custom, loot de moeda pura, claim por personagem

---

## Fase 5 — Registro e Lore

*(Ainda não detalhado — quebrar em histórias quando as Fases 1-4 estiverem concluídas e o formato de diário/wiki estiver definido com mais precisão no PRD.)*

- [ ] Levantar requisitos detalhados de Diário, Recap, Timeline e Wiki antes de quebrar em histórias de usuário
