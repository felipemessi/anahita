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
| 0    | Catálogo SRD                      | Completo (24 categorias modeladas, migradas, seed en completo + pt-BR parcial) | 2026-08-22    |
| 1    | Fundação (Auth, Campaigns, Characters) | Completo (campanhas, convites, personagens com engine, multiclasse, sessões/notas) | 2026-08-23    |
| 2    | Sessão ao Vivo (Combat, WS)        | Completo (encounter/participantes, WebSocket em tempo real, efeitos mecânicos de condições, log de combate) | 2026-08-23 |
| 3    | World-building                    | Completo (NPCs com stat block do catálogo, locais em hierarquia com prevenção de ciclo, facções, junções NPC↔facção/local/sessão e relações entre facções, busca cross-entidade via tsvector) | 2026-08-23 |
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
  - [x] `models.py`: `Proficiency` (FKs nullable e mutuamente exclusivos por `proficiency_type`), `ProficiencyI18n`, `ProficiencyClass`, `ProficiencyRace` — `equipment_category_id` ganhou a FK real para `catalog_equipment_categories` na história de Equipamento (abaixo); até lá era UUID solto, como `campaign_id` ainda é
  - [x] Migração Alembic — `alembic/versions/1b5ef8883035_*.py` (upgrade/downgrade testados contra Postgres)
  - [x] `schemas.py` + `service.py` (leitura)
  - [x] Teste garantindo que exatamente um FK de referência está preenchido conforme `proficiency_type` — `tests/catalog/test_proficiencies.py`

- **Como jogador, quero o catálogo de Raças completo (com traits, subraças e bônus de habilidade) em vez do MVP mínimo atual.**
  - [x] Estender `models.py` existente (`Race`, `RaceTrait`, `Subrace`, `SubraceTrait`, `RaceAbilityBonus`): adicionar `index` nullable a `Race`/`Subrace`; extrair `name`/`description`/`age`/`alignment_desc`/`size_description`/`language_desc` para `RaceI18n`, `trait_name`/`description` para `RaceTraitI18n` e `SubraceTraitI18n` (seção 7.4.2)
  - [x] Migração Alembic de alteração — recriou o seed do zero (4 registros de placeholder), conforme permitido pela história; `alembic/versions/4a3a38b85c46_*.py` (upgrade/downgrade testados contra Postgres)
  - [x] Atualizar `schemas.py`/`service.py`/`router.py` do catálogo para refletir o novo shape — `list_races_translated`/`get_race_translated` resolvem texto traduzido (fallback `en`) com `locale` como query param no router
  - [x] Atualizar/estender `backend/tests/catalog/test_service.py` e `test_seed.py`

- **Como jogador, quero o catálogo de Classes completo (progressão por nível, features, subclasses, spellcasting) em vez do MVP mínimo atual.**
  - [x] Generalizar `ClassLevelFeature` → `Feature` (suporta subclass, `parent_feature_id`, `FeaturePrerequisite`) — seção 7.4.4
  - [x] Criar `ClassLevel`, `ClassLevelFeature` (junção), `ClassLevelSpellSlot`, `ClassLevelResource`
  - [x] Extrair textos para `ClassDefinitionI18n`, `SubclassDefinitionI18n`, `FeatureI18n`
  - [x] Migração Alembic — `alembic/versions/550deb637bf1_*.py` (upgrade/downgrade testados contra Postgres; limpa os dados antigos de `catalog_class_level_features`/`catalog_class_definitions`, reseedados do zero conforme permitido pela história)
  - [x] `schemas.py`/`service.py`/`router.py` atualizados — `list_classes_translated`/`get_class_translated` resolvem progressão completa (níveis, features, pré-requisitos, spell slots, resources, subclasses) com fallback `en`
  - [x] Testes cobrindo: leitura de progressão completa de uma classe (todos os 20 níveis, Fighter), leitura de recursos por nível (rage_count/rage_damage do Barbarian) — `tests/catalog/test_service.py`, `tests/catalog/test_seed.py`

- **Como jogador, quero o catálogo de Magias completo (319 spells do SRD) com escola, classes que conjuram e dano estruturado.**
  - [x] Adicionar `is_custom`/`campaign_id`/`index`/`magic_school_id` a `Spell` (hoje `school` é string solta — trocar por FK)
  - [x] Criar `SpellI18n`, `SpellClass` (junção)
  - [x] Migração Alembic — `alembic/versions/d95c9bd92d79_*.py` (upgrade/downgrade testados contra Postgres; limpa os dados antigos de `catalog_spells`, reseedados do zero conforme permitido pela história). Seed também garante (get-or-create idempotente) os 8 `MagicSchool` do SRD referenciados por `magic_school_id`, já que o vocabulário fixo ainda não tem seed próprio (história pendente abaixo)
  - [x] `schemas.py`/`service.py`/`router.py` atualizados — `list_spells_translated`/`get_spell_translated` resolvem nome/descrição/higher_levels com fallback `en`, escola (slug do `MagicSchool`) e classes conjuradoras traduzidas
  - [x] Testes: spell com múltiplas classes (Detect Magic: Wizard+Cleric), spell custom presa à campanha
  - **Nota:** o PRD (§7.4.5) não define dano estruturado para `Spell` (diferente de `WeaponDetail`) — dano de magia continua só na `description` em texto livre; título da história ficou mais amplo que o schema detalhado

- **Como jogador, quero o catálogo de Equipamento completo (237 itens + categorias + propriedades de arma) em vez do MVP mínimo atual.**
  - [x] Criar `EquipmentCategory` (+ i18n), estender `Item` com `is_custom`/`campaign_id`/`index`/`equipment_category_id`, criar `ItemI18n`, `ItemProperty` (junção com `WeaponProperty`)
  - [x] Ajustar `WeaponDetail` (`damage_type_id` FK em vez de string) e manter `ArmorDetail`
  - [x] Migração Alembic — `alembic/versions/e6a9cb74db4e_*.py` (upgrade/downgrade testados contra Postgres, duas vezes cada; limpa os dados antigos de `catalog_items` — inclusive o item de tipo `magic_item`, que não existe mais no enum `ItemType`, reseedados do zero conforme permitido pela história). `Proficiency.equipment_category_id` também ganhou a FK real prometida na história de Proficiencies. Seed garante (get-or-create idempotente) `EquipmentCategory`/`WeaponProperty`/`DamageType` referenciados, já que o vocabulário fixo ainda não tem seed próprio (história pendente abaixo)
  - [x] `schemas.py`/`service.py`/`router.py` atualizados — `list_items_translated`/`get_item_translated` resolvem nome/descrição, categoria e propriedades traduzidas, e `damage_type` resolvido no `WeaponDetail`
  - [x] Testes: item arma com propriedades múltiplas (Dagger: Finesse+Light+Thrown), item custom presa à campanha
  - **Nota:** removido o item placeholder `+1 Longsword` (`item_type=magic_item`) do seed — itens mágicos passam a ser modelados na história de Itens Mágicos (`MagicItem`) a seguir, não em `Item`

- **Como jogador, quero o catálogo de Itens Mágicos (362 itens) para poder distribuir loot mágico nas campanhas.**
  - [x] `models.py`: `MagicItem` (+ `variant_of_id` auto-FK), `MagicItemI18n`
  - [x] Migração Alembic — `alembic/versions/b8f90e4b9664_*.py` (upgrade/downgrade testados contra Postgres; puramente aditiva, sem dados antigos para migrar)
  - [x] `schemas.py`/`service.py`/`router.py` — `list_magic_items_translated`/`get_magic_item_translated` resolvem nome/descrição/categoria traduzidos e a lista de variantes (`MagicItemSummary`) de um item base
  - [x] Testes: item mágico com variantes (+1/+2/+3 Longsword, +1/+2 Shield), variante aponta de volta pro item base (`variant_of_id`), item mágico custom preso à campanha

- **Como jogador, quero o catálogo de Backgrounds e Feats para completar a criação de personagem.**
  - [x] `models.py`: `Background`, `BackgroundI18n`, `BackgroundProficiency`, `BackgroundEquipment`, `BackgroundFeature` (+ `BackgroundFeatureI18n`); `Feat`, `FeatI18n`, `FeatPrerequisite`
  - [x] Migração Alembic — `alembic/versions/e931ad0dbbbc_*.py` (upgrade/downgrade testados contra Postgres; puramente aditiva, sem dados antigos para migrar)
  - [x] `schemas.py`/`service.py`/`router.py` — `list_backgrounds_translated`/`get_background_translated` e `list_feats_translated`/`get_feat_translated` resolvem texto traduzido (fallback `en`) e as junções (proficiências/equipamento/feature; pré-requisitos)
  - [x] Testes de cada entidade + seed (2 backgrounds, 3 feats). `BackgroundProficiency`/`FeatPrerequisite` testados via construção direta (não via seed) — dependem de `Proficiency`/`AbilityScoreDefinition`, cujo seed próprio ainda não existe (história de vocabulário fixo pendente abaixo); seed de backgrounds/feats não popula essas duas junções por ora

- **Como DM, quero o catálogo de Monstros (stat blocks completos) para popular encontros e NPCs.**
  - [x] `models.py`: `Monster`, `MonsterI18n`, `MonsterSpeed`, `MonsterSense`, `MonsterArmorClass`, `MonsterProficiency`, `MonsterDamageModifier`, `MonsterConditionImmunity`, `MonsterAction`/`MonsterLegendaryAction`/`MonsterReaction`/`MonsterSpecialAbility` + suas 4 tabelas `*Damage` filhas (seção 7.4.8 do PRD). `CreatureSize` estendido para o range completo (tiny–gargantuan); `DamageModifierType` novo enum
  - [x] Migração Alembic — `alembic/versions/f75f2c608e22_*.py` (16 tabelas, puramente aditiva — sem necessidade de quebrar em 2-3 revisions; upgrade/downgrade testados contra Postgres)
  - [x] `schemas.py`/`service.py`/`router.py` — `list_monsters_translated`/`get_monster_translated` resolvem stat block completo (velocidade, sentidos, CA, resistências/imunidades, ações/legendary actions/reactions/special abilities com dano); ações não têm i18n própria (mesmo shape do PRD, texto direto na linha)
  - [x] Testes: monstro com múltiplas ações + dano (Goblin: Scimitar/Shortbow), monstro com legendary actions (Young Red Dragon), monstro custom preso à campanha. `MonsterProficiency`/`MonsterConditionImmunity` testados via construção direta (mesmo motivo do `BackgroundProficiency`/`FeatPrerequisite` da história anterior — dependem de vocabulário fixo ainda não seedado)

- **Como desenvolvedor, quero Rules/RuleSections modeladas para eventual tela de referência de regras no frontend.**
  - [x] `models.py`: `RuleSection`, `Rule`, `RuleRuleSection` (+ i18n)
  - [x] Migração Alembic — `alembic/versions/6f9cf284365a_*.py` (upgrade/downgrade testados contra Postgres; puramente aditiva)
  - [x] `schemas.py`/`service.py`/`router.py` — `list_rules_translated`/`get_rule_translated` resolvem nome/descrição com fallback `en` e as `RuleSection`s vinculadas
  - [x] Testes básicos: listagem, leitura com seções vinculadas, fallback de locale, 404, idempotência do seed

- **Como desenvolvedor, quero um seed completo em inglês (`en`) para todas as 24 categorias, substituindo os arquivos de placeholder atuais.**
  - [x] Escrever script(s) de conversão de `_data/2014/en/*.json` (formato SRD/APIReference) para o formato normalizado do banco (mapear `index` → FK real, resolver referências em ordem topológica: vocabulário fixo → raças/classes/proficiencies → spells/equipment → backgrounds/feats/monstros) — `backend/app/catalog/seeds/convert_srd.py`, gera os `data/*.json` normalizados a partir do JSON fonte (decisão: pré-geração commitada, não runtime — ver docstring do script)
  - [x] Substituir os JSONs placeholder em `backend/app/catalog/seeds/data/*.json` por datasets completos das 24 categorias (9 fixas + races/classes/spells/items/magic_items/backgrounds/feats/monsters/rules)
  - [x] Estender `backend/app/catalog/seeds/seed.py` para popular as 24 categorias, idempotente por `index`
  - [x] Seed rodado local (SQLite e Postgres real via docker compose) — contagem por tabela confere com a seção 7.4.1-7.4.9 do PRD: 319 spells, 334 monsters, 362 magic items, 237 items, 9 races, 12 classes, 1 background, 1 feat, 33 rules/6 rule sections
  - [x] Testes de idempotência do seed (rodar duas vezes não duplica) — `test_seed_is_idempotent`, cobre todas as 20 categorias

- **Como desenvolvedor, quero um seed parcial em pt-BR para as categorias que já têm tradução disponível.**
  - [x] Mapear quais das 12 categorias com dado em `_data/2014/pt-BR` correspondem a quais tabelas `_i18n` já implementadas — `AbilityScoreDefinitionI18n`, `SkillDefinitionI18n`, `AlignmentI18n`, `ConditionI18n`, `DamageTypeI18n`, `MagicSchoolI18n`, `LanguageI18n`, `WeaponPropertyI18n`, `RaceI18n`, `BackgroundI18n`+`BackgroundFeatureI18n`, `FeatI18n`, `RuleSectionI18n` (as `convert_srd.py`'s pt-BR section docstring); `RaceTrait`/`Subrace` nomes existem no fonte mas sem descrição traduzida, e `Rule` (as 33 entradas finas) não tem fonte pt-BR — ambos ficam de fora, fallback para `en` intacto
  - [x] Estender o seed para popular linhas `_i18n` com `locale='pt-BR'` a partir desses arquivos, sem quebrar quando uma categoria não tem pt-BR (fallback para `en` continua funcionando) — `seed.py`: `_load_pt_br`/`_translations`, mesma passada que já semeia `en`
  - [x] Teste: entidade sem tradução pt-BR retorna `en` via fallback (`test_get_rule_translated_falls_back_to_en`, `test_get_monster_translated_falls_back_to_en`); entidade com tradução pt-BR retorna a tradução (`test_get_race/background/feat_translated_resolves_pt_br`, `test_get_rule_translated_resolves_section_pt_br`)

---

## Fase 1 — Fundação

### Já implementado
- [x] Auth (JWT + refresh token httpOnly, strategy pattern com `local`) — `app/auth/*` *(já implementado)*
- [x] Storage local (`LocalStorageService`) — `app/storage/*` *(já implementado)*
- [x] Catalog MVP (Race/Class/Spell/Item mínimos, a ser **estendido** pela Fase 0, não refeito) — `app/catalog/*` *(já implementado)*
- [x] Engine: ability modifiers, armor class, hit points, conditions, combat, validation, registry de class handlers (genérico) — `engine/*` *(já implementado)*

### Pendente

- **Como usuário, quero me registrar e fazer login para acessar minhas campanhas.** *(verificar se já coberto pelos endpoints de auth existentes — se sim, marcar como feito e pular)*
  - [x] Confirmar que `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh` existem e têm teste de integração cobrindo o fluxo completo — endpoints já existiam; adicionado teste de integração HTTP end-to-end (`TestClient`/`httpx.AsyncClient` contra a app real, com `get_db` sobrescrito para SQLite em memória) em `tests/auth/test_router.py`, cobrindo registro → login → refresh (rotação de cookie) → refresh do token antigo rejeitado, e-mail duplicado, senha errada, refresh sem cookie, logout

- **Como usuário, quero criar uma campanha e ser automaticamente seu DM.**
  - [x] `app/campaigns/models.py`: `Campaign`, `CampaignMember`, `CampaignInvite` (seção 7.2 do PRD)
  - [x] Migração Alembic — `alembic/versions/8045f11d1dfb_add_campaigns_domain.py` (upgrade/downgrade/upgrade testados contra Postgres; downgrade dropa explicitamente os enums `campaignrole`/`campaignstatus`, já que `DROP TABLE` não os remove)
  - [x] `schemas.py`/`domain.py`/`service.py`/`router.py` — `POST /campaigns` (autenticado via `get_current_user`)
  - [x] Regra: criar campanha cria automaticamente `CampaignMember(role=dm)` para o criador — `CampaignService.create_campaign`
  - [x] Testes de service + router (criação, DM automático, unique `(campaign_id, user_id)`, criação exige autenticação) — `tests/campaigns/test_service.py`, `tests/campaigns/test_router.py`

- **Como DM, quero gerar um convite para um jogador entrar na minha campanha.**
  - [x] `service.py`: gerar `invite_code` único (`secrets.token_urlsafe`), expiração configurável (`expires_in_hours`) — `CampaignService.create_invite`/`_require_dm`
  - [x] `router.py`: `POST /campaigns/{campaign_id}/invites` (só DM, 403 caso contrário) e `POST /campaigns/invites/redeem` (resgate, seta `used_by`)
  - [x] Testes: convite expirado não pode ser resgatado (410), convite usado não pode ser reusado (409), código inexistente (404), não-DM não pode criar convite (403), fluxo HTTP completo DM cria → jogador resgata — `tests/campaigns/test_invites.py`, `tests/campaigns/test_router.py`

- **Como usuário, quero ver todas as campanhas em que participo (como DM ou jogador).**
  - [x] Query em `app/queries/` (cross-domain: User → CampaignMember → Campaign) — `app/queries/campaign_queries.py::list_campaigns_for_user`
  - [x] `router.py`: `GET /campaigns` filtrado pelo usuário autenticado
  - [x] Teste: usuário vê só suas campanhas (dono ou jogador via convite resgatado), não as de outros; lista vazia quando não há vínculo — `tests/queries/test_campaign_queries.py`, `tests/campaigns/test_router.py`

- **Como jogador, quero criar uma ficha de personagem vinculada à minha campanha.**
  - [x] `app/characters/models.py`: `Character`, `CharacterAbilityScore`, `CharacterSkill`, `CharacterClass`, `CharacterFeature`, `CharacterRaceChoice`, `CharacterSpell`, `CharacterEquipment` (seção 7.3 do PRD)
  - [x] Migração Alembic — `alembic/versions/8b62d1294f95_add_characters_domain.py` (upgrade/downgrade/upgrade testados contra Postgres)
  - [x] `schemas.py`/`domain.py`/`service.py`/`router.py` — `POST /characters` (autenticado); adicionado também `GET /campaigns/{campaign_id}/members/me` (necessário para o cliente descobrir seu próprio `campaign_member_id` ao criar campanha como DM, já que `POST /campaigns` não o retornava)
  - [x] Regra: `Character.race_id`/`class_definition_id` só podem referenciar catálogo global (SRD) ou custom da própria campanha — `app/characters/domain.py::validate_catalog_reference`, mesmo padrão de `validate_custom_campaign_scope` da Fase 0 (`spell_id`/`item_id` ficam para quando spells/equipamento de personagem forem implementados)
  - [x] Testes: criação de personagem simples (1 classe, 1 raça) com HP/CA/bônus de proficiência calculados via `engine/`, rejeição de referência a catálogo custom de outra campanha, criação para membership de outro usuário rejeitada, ability scores incompletos rejeitados, fluxo HTTP completo — `tests/characters/test_service.py`, `tests/characters/test_router.py`

- **Como jogador, quero ver os atributos calculados da minha ficha (modificadores, bônus de perícia, CA, PV) sem calcular na mão.**
  - [x] Conectar `service.py` de characters à `engine/` (ability modifiers, skill bonus — CA/PV já calculados na criação, seção anterior) — `CharacterService._to_read` recalcula `modifier` (`engine.abilities.calculate_modifier`) e `bonus` de cada uma das 18 skills (`engine.abilities.calculate_skill_bonus`) a cada leitura, nunca confiando em valor persistido; criação agora também inicializa as 18 `CharacterSkill` (não proficientes por padrão)
  - [x] `schemas.py`: response inclui campos calculados (não persistidos) — `CharacterAbilityScoreRead.modifier`, `CharacterSkillRead.ability`/`bonus`
  - [x] `GET /characters/{id}` (novo endpoint), visível ao dono da ficha e ao DM da campanha, 403 para outros jogadores
  - [x] Testes: ficha de exemplo com valores conhecidos → modificadores batem com as regras do 5e; bônus de perícia recalculado após marcar proficiência direto no banco (prova que não é confiado o valor persistido); controle de acesso (dono vê, DM vê, outro jogador não vê) — `tests/characters/test_calculated_fields.py`, `tests/characters/test_router.py`

- **Como jogador multiclasse, quero adicionar uma segunda classe ao meu personagem.**
  - [x] `service.py`: validação de multiclass via `engine/validation.py::validate_multiclass` (prerequisitos de ability score) — `CharacterService.add_class`; tabela de pré-requisitos por classe SRD em `app/characters/domain.py::MULTICLASS_ABILITY_REQUIREMENTS` (nota: `validate_multiclass` só expressa AND-de-habilidades; o pré-requisito real do Fighter é STR13 *ou* DEX13 — simplificado para STR13 só, documentado no código)
  - [x] `router.py`: `POST /characters/{id}/classes` (só o dono da ficha; rejeita classe repetida com 409; recalcula `level`/`proficiency_bonus`)
  - [x] Teste: multiclass válido passa (Fighter→Wizard com INT 13+), inválido (INT insuficiente) é rejeitado (422), classe repetida rejeitada (409), personagem de outro jogador rejeitado (403), fluxo HTTP completo — `tests/characters/test_multiclass.py`, `tests/characters/test_router.py`

- **Como usuário autenticado, quero consultar meu próprio perfil (`GET /auth/me`).** ✅ (2026-08-23)
  - [x] `router.py`: `GET /auth/me` autenticado via `get_current_user`, retorna `UserPublic` (sem `hashed_password`)
  - [x] Teste: retorna o perfil do usuário do token; 401 sem token/token inválido
  - Motivação: o frontend (Fase 0) descobriu essa lacuna — o JWT de acesso só carrega `sub` (user id), então hoje não há forma de o cliente obter `username`/`email` após o login sem esse endpoint (ver `docs/anahita-frontend-backlog.md`, história de login/registro).
  - Notas: nenhum `schemas.py`/`service.py` novo precisou ser criado — reaproveitou `UserPublic` e a dependência `get_current_user` (`app/core/dependencies.py`) já existentes. Próximo passo (Fase 1 do frontend): trocar a decodificação client-side do JWT em `lib/auth/session.ts` por uma chamada real a este endpoint.

- **Como DM, quero criar uma sessão de jogo com número sequencial e notas.**
  - [x] `app/sessions/models.py`: `Session`, `SessionNote` (seção 7.5 do PRD)
  - [x] Migração Alembic — `alembic/versions/5faf7b3b9560_add_sessions_domain.py` (upgrade/downgrade/upgrade testados contra Postgres)
  - [x] `schemas.py`/`domain.py`/`service.py`/`router.py` — `POST`/`GET /campaigns/{campaign_id}/sessions` (criação só DM, `session_number` sequencial automático por campanha), `POST`/`GET /sessions/{session_id}/notes`
  - [x] Regra: `SessionNote.is_private=true` só visível para o DM (texto literal do PRD §7.5) — implementado como: só o DM pode *criar* nota privada (`app/sessions/domain.py::validate_note_author`, 403 se jogador tentar); listagem filtra notas privadas para quem não é DM. `Session.dm_notes` recebe a mesma regra (oculto na resposta para não-DM, construído no schema — nunca sobrescrevendo o valor persistido no ORM)
  - [x] Testes: jogador não cria nota privada (403), jogador não vê notas privadas (nem `dm_notes`), DM vê tudo, não-membro da campanha é rejeitado, numeração sequencial, fluxo HTTP completo — `tests/sessions/test_service.py`, `tests/sessions/test_router.py`

- **Lacunas descobertas pelo frontend (Fase 1) — endpoints que faltavam para telas já construídas.** ✅ (2026-08-23)
  - [x] `GET /campaigns/{campaign_id}` (detalhe) — visível a qualquer membro; 404 se não for membro — `CampaignService.get_campaign`
  - [x] `GET /campaigns/{campaign_id}/members` (lista completa, DM e jogadores) — visível a qualquer membro — `CampaignService.list_members`, `app/queries/campaign_queries.py::list_members_for_campaign`
  - [x] `GET /characters?campaign_id=` (lista de personagens da campanha) — visível a qualquer membro; 403 para não-membro — `CharacterService.list_characters_for_campaign`
  - [x] `PATCH /characters/{character_id}` (atualização de `hit_point_current`/`temporary_hit_points`/`armor_class`/`inspiration`, todos opcionais) — só o dono da ficha; `hit_point_current` acima de `hit_point_max` é rejeitado (422) — `CharacterService.update_character`
  - [x] `POST /catalog/{races,classes,spells,items,monsters}` — criação de homebrew, sempre presa a `campaign_id` (`is_custom=True` forçado no service, nunca aceito do cliente), só o DM da campanha (403 caso contrário) — `app.catalog.service.create_custom_*`, checagem de DM via `app/catalog/router.py::_require_dm` (reaproveita `app/queries/campaign_queries.py::get_membership_for_user`, novo helper cross-domain). Item deriva `equipment_category_id` de `item_type` (mapeamento fixo para uma categoria SRD existente — v1 não modela categoria fina para homebrew); Spell exige `school` batendo com um `MagicSchool.index` já semeado (422 se não bater); Monster aceita só os campos do formulário v1 do frontend, com defaults sãos para o resto do stat block (`hit_dice="1d8"`, atributos 10, `xp=0`) — ficha completa de monstro fica para iteração futura. Magic items/backgrounds/feats/rules **não** ganharam criação nesta leva (fora do v1 do form do frontend).
  - [x] `GET /catalog/{category}` (races/classes/spells/items/magic-items/backgrounds/feats/monsters) ganhou `campaign_id` como query param opcional — sem ele, mantém o comportamento antigo (global); com ele, escopa a listagem a SRD + homebrew *daquela* campanha só (a função de serviço já suportava isso desde a Fase 0 do catálogo — só não estava exposta no router). `rules` não ganhou (sem criação/escopo de homebrew).
  - [x] Testes: detalhe/lista de membros exige membership (404/200), lista de personagens exige membership (403/200), PATCH de HP rejeita dono errado (403) e valor acima do máximo (422), homebrew rejeita não-DM (403), homebrew de uma campanha não aparece na listagem escopada de outra, spell homebrew com escola inexistente é rejeitada (422) — `tests/campaigns/test_router.py`, `tests/characters/test_router.py`, `tests/catalog/test_router_homebrew.py`
  - Motivação: essas lacunas foram descobertas pelo frontend (Fase 1, `docs/anahita-frontend-backlog.md`) ao integrar telas que o PRD já previa mas cujo endpoint correspondente nunca tinha sido implementado — ver notas de cada história da Fase 1 do frontend para o que ficava mockado/pendente antes desta leva.

- **Lacunas remanescentes da leva acima.** ✅ (2026-08-23)
  - [x] `PATCH /campaigns/{campaign_id}` (editar `name`/`description`/`setting`) — só o DM; todos os campos opcionais (só os enviados são alterados) — `CampaignService.update_campaign`
  - [x] `GET /auth/users?ids=` — resolve perfil público (`id`/`email`/`username`) para uma lista de `user_id` (query repetida, `?ids=<uuid>&ids=<uuid>`), autenticado mas sem restrição adicional (username não é sensível) — `AuthService.list_users_by_ids`
  - [x] `POST /catalog/{magic-items,backgrounds,feats,rules}` — criação de homebrew para as 4 categorias restantes, mesmo padrão DM-only + `campaign_id` forçado das outras 5. Magic item homebrew reaproveita a categoria de equipamento `adventuring-gear` (mesma simplificação v1 de `create_custom_item`); background/feat/rule são só campos escalares (sem colunas extras na tabela-base além de `is_custom`/`campaign_id`/`index`, então a criação é só a linha base + `_i18n`). `GET /catalog/rules` ganhou `campaign_id` como os outros 8 (era o único que faltava).
  - [x] `POST /characters/{id}/spells`, `/equipment`, `/features` — todos owner-only, validam referência de catálogo (spell/item) contra a mesma regra de escopo campanha/homebrew usada por raça/classe na criação do personagem; `features` é texto livre (`source_type` `class`/`feat`, `source_name`, `feature_name`, `description`, `level_acquired`) — não resolve automaticamente do catálogo, é registro manual. `CharacterRead` agora inclui `spells`/`equipment`/`features`.
  - [x] Testes: update de campanha (DM ok, não-DM 403), batch de usuários (resolve ids, exige auth), homebrew das 4 categorias novas (criação + DM-only + escopo por campanha em `rules`), spells/equipment/features (adiciona, aparece na leitura, dono errado rejeitado) — `tests/campaigns/test_router.py`, `tests/auth/test_router.py`, `tests/catalog/test_router_homebrew.py`, `tests/characters/test_router.py`

---

## Fase 2 — Sessão ao Vivo

- **Como DM, quero iniciar um encontro de combate e adicionar participantes (PCs e monstros).** ✅ (2026-08-23)
  - [x] `app/combat/models.py`: `Encounter`, `EncounterParticipant`, `EncounterCondition`, `CombatLog` (seção 7.6 do PRD)
  - [x] Migração Alembic — `alembic/versions/84a905f1c458_add_combat_domain.py` (upgrade/downgrade/upgrade testados contra Postgres; downgrade dropa explicitamente os enums `encounterstatus`/`combatactiontype`/`combatconditiontype`)
  - [x] Regra: um `EncounterParticipant` é PC **ou** NPC/monstro, nunca ambos (validação em `domain.py`)
  - [x] `schemas.py`/`service.py`/`router.py` REST (CRUD de encounter/participantes fora do fluxo de turno)
  - [x] Testes de domain (`CombatState`) + service
  - Notas: `EncounterParticipant.npc_id` não tem FK real (NPC é Fase 3, ainda não implementado) — mesmo padrão de `Race.campaign_id` no catálogo. "CombatState" do backlog virou `app/combat/domain.py::advance_turn` (função pura, não classe) + `TurnParticipant`/`TurnAdvanceResult`, testado isoladamente sem DB; será reaproveitado pelo comando `advance_turn` do WebSocket (história 2). Rotas REST: `POST`/`GET /sessions/{session_id}/encounters`, `GET /encounters/{id}`, `POST /encounters/{id}/start` (preparing→active), `POST /encounters/{id}/participants`, `PATCH`/`DELETE /encounters/{id}/participants/{participant_id}` — todas as de escrita são DM-only, leitura é para qualquer membro da campanha. `PATCH` de participante fora do fluxo de turno reaproveita a mesma regra de `CharacterUpdate` (HP acima do máximo rejeitado com 422). Testes: `tests/combat/test_domain.py`, `tests/combat/test_service.py`, `tests/combat/test_router.py` (25 testes).

- **Como DM, quero avançar turnos e aplicar dano/cura/condições em tempo real para todos os jogadores verem.** ✅ (2026-08-23)
  - [x] `app/combat/ws_manager.py`: `WSConnectionManager` (dict `encounter_id → list[WebSocket]`)
  - [x] `app/combat/ws_router.py`: endpoint `/ws/combat/{encounter_id}`, auth via JWT em query param, valida membership
  - [x] Protocolo de mensagens (seção 10.2 do PRD): `state_sync`, `turn_advanced`, `participant_updated`, `encounter_status_changed` (servidor→cliente); `advance_turn`, `update_participant`, `add_participant`, `remove_participant`, `end_encounter` (DM→servidor)
  - [x] Regra: apenas `role=dm` pode enviar comandos; jogadores read-only (validado a cada mensagem)
  - [x] Teste de reconexão: cliente desconecta e reconecta, recebe `state_sync` completo
  - [x] Teste: jogador tentando enviar comando de DM é rejeitado
  - Notas: adicionado evento `error` (servidor→cliente) fora da tabela do PRD §10.2 — necessário para dar feedback de comando inválido/rejeitado ao cliente (`event_type` desconhecido, payload malformado, ou 403/422/404 do service), nunca fecha a conexão. `advance_turn` reaproveita `app/combat/domain.py::advance_turn` (história 1). `update_participant` cobre dano/cura (`hit_point_current`/`temporary_hit_points`/`armor_class`) e condição (`add_condition`/`remove_condition`, cria/remove `EncounterCondition`) num único comando — resolução de efeitos mecânicos das condições fica para a história 3. `add_participant`/`remove_participant` via WS fazem broadcast de `state_sync` completo (o protocolo não define um evento dedicado para essas duas ações). O handler usa `Depends(get_db)` (compatível com `dependency_overrides` dos testes) em vez de abrir sessão direto de `AsyncSessionLocal`, uma sessão por conexão. Testado com `fastapi.testclient.TestClient` (síncrono — é o que de fato dirige WebSocket em teste; a suíte usa `httpx.AsyncClient` pros demais routers, mas isso não dá suporte a WS). Dependência nova: `websockets` (`uv add websockets`), necessária para o transporte WS tanto em runtime (uvicorn) quanto nos testes. 34 testes em `tests/combat/` (25 REST da história 1 + 9 WS novos).

- **Como jogador, quero ver as condições ativas do meu personagem e seus efeitos mecânicos durante o combate.** ✅ (2026-08-23)
  - [x] Conectar `EncounterCondition` a `engine/conditions.py` (`get_condition_effects`)
  - [x] `schemas.py`: response de participante inclui condições + efeitos mecânicos resolvidos
  - [x] Teste: personagem cego (blinded) → efeito de disadvantage retornado
  - Notas: `EncounterParticipantRead.effects: list[MechanicalEffectRead]` — resolvido a cada leitura (nunca persistido), mesmo padrão de `CharacterAbilityScoreRead.modifier`. Isso exigiu refatorar `CombatService` para retornar `EncounterRead`/`EncounterParticipantRead` diretamente (em vez de rows ORM cruas + `.model_validate()` nos routers) — agora no mesmo padrão de `CharacterService`; `router.py`/`ws_router.py` simplificados de acordo (`get_encounter_membership` continua expondo o ORM cru, único caso em que o WS handler precisa do objeto para autenticar antes de montar o read). `app.combat.domain.ConditionType`/`engine.types.ConditionType` convertidos por `.value` (mesmas strings). A engine não modela severidade de exhaustion no banco (`EncounterCondition` não tem coluna de nível — PRD §7.6 não lista uma), então exhaustion é sempre resolvida em `level=1`, documentado em `participant_to_read`. 3 novos testes em `tests/combat/test_condition_effects.py`.

- **Como DM, quero um log do que aconteceu no combate para referência pós-sessão.** ✅ (2026-08-23)
  - [x] `service.py`: toda ação relevante grava `CombatLog`
  - [x] `router.py`: `GET /encounters/{id}/log`
  - [x] Teste: sequência de ações gera log na ordem correta
  - Notas: registrado em `participant joined/left`, dano/cura (`update_participant` REST e `live_update_participant` via WS, delta de `hit_point_current`), condição ganha/perdida, avanço de turno (`Round N: Fulano's turn`) e fim de encontro — todos com `action_type=other` (o enum do PRD — attack/spell/move/dash/dodge/disengage/help/hide/ready/other — é vocabulário de ação declarada em turno, não mapeia 1:1 para essas ações administrativas/de sistema; usar `other` uniformemente evita reinterpretar o enum). Migração nova (`700e6e3f1e67`) tornando `combat_logs.actor_id`/`target_id` `ON DELETE SET NULL` em vez de FK simples — a tabela original (história 1) exigia `actor_id` `NOT NULL`, o que quebraria ao remover um participante referenciado por um log já existente (`remove_participant` é uma ação normal do protocolo); a entrada de log sobrevive à remoção, só perde a referência. `actor_id`/`target_id` nem sempre têm um "ator" real no sentido do PRD (ex. dano não rastreia quem atacou) — usados como "quem entrou/saiu" (join/leave) ou "quem foi afetado" (target, dano/condição), documentado em `CombatLog`/`CombatLogRead`. 5 novos testes (`tests/combat/test_log.py` + 1 em `test_router.py`).

---

## Fase 3 — World-building

- **Como DM, quero cadastrar NPCs com ou sem stat block (usando o catálogo de Monstros da Fase 0).** ✅ (2026-08-23)
  - [x] `app/world/models.py`: `NPC` (com `stat_block_id → Monster`), `Location`, `Faction` (seção 7.7 do PRD)
  - [x] Migração Alembic — `alembic/versions/fbcce0468d89_*.py` (upgrade/downgrade testados contra Postgres, duas vezes)
  - [x] `schemas.py`/`domain.py`/`service.py`/`router.py`
  - [x] Testes: NPC sem stat block, NPC com stat block do SRD, NPC com monstro homebrew da campanha — `tests/world/test_service.py`
  - **Nota:** lacuna mecânica preenchida inline — a história só previa NPC, mas `Location`/`Faction` ganharam CRUD básico (create/list, DM-only para criar) também nesta história, já que nenhuma outra história do backlog cria esses endpoints e as futuras junções (NPCFaction, NPCLocation etc.) precisam de algo pra referenciar. `service.py` valida que `stat_block_id` só aceita monstro SRD (`campaign_id IS NULL`) ou homebrew da própria campanha, nunca homebrew de outra campanha.

- **Como DM, quero organizar locais em hierarquia (região → cidade → taverna).** ✅ (2026-08-23)
  - [x] `service.py`: navegação de `parent_location_id`, prevenção de ciclo — `WorldService.update_location_parent`/`get_location_tree`, `domain.py::validate_no_parent_cycle`
  - [x] `router.py`: árvore de locais por campanha — `GET /campaigns/{campaign_id}/locations/tree`, `PATCH /locations/{location_id}/parent`
  - [x] Teste: ciclo é rejeitado (auto-referência e referência a descendente); árvore de 3 níveis resolve corretamente — `tests/world/test_service.py`
  - **Nota:** lacuna mecânica preenchida inline — `create_location` também passou a validar que `parent_location_id` pertence à mesma campanha (mesma regra já aplicada em `update_location_parent`), já que a história anterior não tinha essa checagem ainda.

- **Como DM, quero relacionar NPCs a facções, locais e sessões para montar o histórico da campanha.** ✅ (2026-08-23)
  - [x] `app/world/models.py`: `NPCFaction`, `NPCLocation`, `NPCSession`, `LocationSession`, `FactionRelationship` (tabelas de junção da seção 7.7)
  - [x] Migração Alembic — `alembic/versions/14ecbccdaf78_*.py` (upgrade/downgrade testados contra Postgres, duas vezes)
  - [x] `service.py`/`router.py` para cada junção — `POST/GET /npcs/{id}/factions`, `/npcs/{id}/locations`, `/npcs/{id}/sessions`, `/locations/{id}/sessions`, `/factions/{id}/relationships`
  - [x] Testes de cada relação — `tests/world/test_service.py`
  - **Nota:** todas as junções são DM-only para criar, exigem que as duas pontas pertençam à mesma campanha (404 se não), e `FactionRelationship` rejeita uma facção relacionada consigo mesma (400). `list_faction_relationships` retorna o vínculo tanto pelo lado `faction_a` quanto `faction_b`.

- **Como DM, quero buscar por nome/descrição em NPCs, locais e facções da minha campanha.** ✅ (2026-08-23)
  - [x] `tsvector` do Postgres em `app/queries/world_queries.py` — `search_world_entities` (UNION ALL rankeado por `ts_rank`, `plainto_tsquery`)
  - [x] `router.py`: endpoint de busca cross-entidade — `GET /campaigns/{campaign_id}/world/search?q=`
  - [x] Teste de busca (Postgres — não roda em SQLite, marcar como teste de integração) — `tests/queries/test_world_queries_postgres.py`, marcado `@pytest.mark.postgres`, pula automaticamente se não houver Postgres alcançável em `TEST_POSTGRES_URL`/padrão local
  - **Nota:** a checagem de membership (403 pra quem não é da campanha) é coberta separadamente em SQLite (`tests/world/test_service.py::test_search_rejects_non_members`, com `search_world_entities` mockado) já que essa parte independe do Postgres.

---

## Fase 4 — Loot, Inventário e Compartilhamento

- **Como DM, quero criar handouts (texto/imagem/mapa) e revelá-los para os jogadores quando quiser.** ✅ (2026-08-23)
  - [x] `app/handouts/models.py`: `Handout` (seção 7.8 do PRD)
  - [x] Migração Alembic
  - [x] `schemas.py`/`service.py`/`router.py` — upload via `StorageService` (reaproveitar `app/storage/`)
  - [x] Regra: `GET /campaigns/{id}/handouts` para jogador só retorna `is_revealed=true`
  - [x] Testes: DM vê tudo, jogador só vê revelados
  - Notas: criação é `multipart/form-data` (`title`/`handout_type`/`content`/`session_id` como campos de formulário + `file` opcional) para caber upload de imagem/mapa no mesmo POST; `HandoutRead.url` resolve `storage_key` via `StorageService.get_url` (nunca expõe o storage_key bruto).

- **Como DM, quero revelar um handout em tempo real durante uma sessão ativa.** ✅ (2026-08-23)
  - [x] Evento `handout_revealed` no WebSocket de combat existente (seção 10.3 do PRD)
  - [x] Teste: broadcast chega para jogadores conectados
  - Notas: `HandoutService.reveal_handout` reaproveita `app.combat.ws_manager.manager` (mesmo registry do `ws_router` de combate) e faz broadcast para todo `Encounter` `active` da sessão do handout; sem sessão ou sem encontro ativo, a revelação só fica visível via REST (comportamento esperado pelo PRD §10.3).

- **Como grupo, quero um inventário compartilhado da campanha.** ✅ (2026-08-23)
  - [x] `app/inventory/models.py`: `PartyInventory` (seção 7.9 do PRD)
  - [x] Migração Alembic
  - [x] `schemas.py`/`service.py`/`router.py`
  - [x] Testes básicos de CRUD
  - Notas: mutação (add/update/remove) restrita ao DM, leitura liberada para qualquer membro da campanha — mesmo padrão de permissão usado em `app.world` para NPCs/locais/facções.

- **Como DM, quero distribuir loot (itens do catálogo ou custom) após um combate, incluindo dinheiro.** ✅ (2026-08-23)
  - [x] `app/inventory/models.py`: `LootDrop` (item do catálogo ou nome livre + moeda em copper)
  - [x] Migração Alembic
  - [x] `service.py`/`router.py`: distribuir para personagem (`claimed_by`)
  - [x] Testes: loot de item custom, loot de moeda pura, claim por personagem
  - Notas: `item_id` referencia só `catalog_items` (não `catalog_magic_items`) — a tabela `LootDrop` do PRD §7.9 declara um único `item_id FK` sem indicar a qual catálogo; suportar também `MagicItem` exigiria um discriminador de tipo ou duas FKs opcionais, então foi deixado de fora deste corte (lacuna registrada abaixo). `claim_loot_drop` é permitido para o próprio jogador do personagem ou para o DM; validação de "não pode ser catálogo e nome custom ao mesmo tempo" e "precisa ter item ou moeda" vive em `app.inventory.domain.validate_loot_drop_kind`, mesmo padrão de `combat.domain.validate_participant_kind`.

**Lacunas descobertas na Fase 4 — pendentes de decisão.**

- [ ] `LootDrop.item_id` não suporta `MagicItem` (só `catalog_items`) — decidir se vale um discriminador de tipo (`item_kind`) ou uma segunda FK opcional `magic_item_id` antes de fechar a fase, ou se fica para quando magic items entrarem de fato no fluxo de loot.

---

## Fase 5 — Registro e Lore

*(Ainda não detalhado — quebrar em histórias quando as Fases 1-4 estiverem concluídas e o formato de diário/wiki estiver definido com mais precisão no PRD.)*

- [ ] Levantar requisitos detalhados de Diário, Recap, Timeline e Wiki antes de quebrar em histórias de usuário
