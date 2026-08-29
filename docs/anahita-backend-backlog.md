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
| 4    | Loot, Inventário, Handouts         | Completo (handouts com upload/reveal em tempo real via WebSocket de combate, inventário compartilhado, loot com item de catálogo/magic item/custom e moeda, claim por personagem) | 2026-08-24 |
| 5    | Registro e Lore                   | Completo (diário DM-only, recap via `summary` de sessão, timeline híbrida sessões+eventos manuais, wiki linkável a NPCs/locais/facções na busca cross-entidade) | 2026-08-24 |
| 6    | Interatividade de Ficha e Combate | Completo (magias por círculo com limites/slots, inventário editável, moeda, sessão aberta populando combate com iniciativa obrigatória, ações declaradas resolvidas automaticamente via `engine/dice.py` com override manual, visibilidade de ficha restrita a dono/DM) | 2026-08-24 |
| 7    | Sobrevivência, Descanso e Recursos | Completo (dados de vida em descanso curto/longo por classe, testes de morte automáticos, concentração com DC exposta, perícias passivas, subida de nível com PV/ASI/talento, ações lendárias e reações de monstro, recursos de classe com controle de uso e recarga) | 2026-08-25 |
| 8    | Dashboard e Refinamentos de Ficha  | Completo (dashboard de campanha cross-domain, geração de atributos com point buy/standard array validados, escolhas mecânicas de nível reaproveitando `parent_feature_id` do catálogo incluindo seleção múltipla e features de subclasse, opção de Canalizar Divindade rastreada, magias classificadas por tipo de ação/alvo com DC de resistência, CA recalculada a partir do equipamento, proficiência de arma real no ataque de combate) | 2026-08-25 |
| 9    | Correções e Regressões             | Completo (dashboard mostra sessão sem data agendada e corrige off-by-one de fuso na comparação de "hoje"; criação de monstro homebrew com `size` inválido agora rejeita com 422 em vez de derrubar o servidor; seleção de alvo em combate confirmada funcionando — bug relatado era sintoma da Fase 13, sem gap de backend) | 2026-08-28 |
| 10   | Ficha do Personagem: Edição, Identidade e Navegação | Pendente | 2026-08-28 |
| 11   | Catálogo Homebrew: Profundidade e Estrutura | Pendente | 2026-08-28 |
| 12   | Recursos de Classe e Interatividade Mágica | Pendente | 2026-08-28 |
| 13   | Fluxo de Sessões: Fundamentos Faltantes | Pendente | 2026-08-28 |
| 14   | Loot e Inventário Integrado        | Pendente | 2026-08-28 |
| 15   | Redesign de Sessões: Mapas Dinâmicos e Tokens | Pendente | 2026-08-28 |

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

## Fase 9 — Correções e Regressões

> Objetivo: um levantamento do grupo em 2026-08-28 apontou vários itens como "não funciona" que o código já implementa (rota + service prontos). Antes de desenhar qualquer feature nova, reproduzir e corrigir a causa raiz de cada um. Levantado junto com as Fases 10-15 abaixo, a partir de feedback de uso real (ver `docs/anahita-frontend-backlog.md` para a contraparte de UI de cada item).

- **Como jogador, quero ver a próxima sessão agendada no dashboard da campanha.** ✅ (2026-08-28)
  - [x] Reproduzir: criar uma sessão pelo formulário rápido de sessões e confirmar se ela aparece no card "próxima sessão" do dashboard
  - [x] Causa raiz suspeita: `get_campaign_dashboard()` (`app/queries/dashboard_queries.py`) filtra por `Session.scheduled_date.is_not(None)`, mas nada hoje força uma sessão a ter `scheduled_date` — sessões criadas sem data ficam invisíveis pra sempre no dashboard
  - [x] Decidir e implementar: exigir `scheduled_date` na criação (`SessionCreate`), ou fazer o dashboard cair pra `created_at`/status quando `scheduled_date` for nulo
  - [x] Revisar a comparação de data (`datetime.now(UTC).date()`) — checar se pode gerar off-by-one perto da meia-noite pra usuários fora de UTC; ajustar se confirmado
  - [x] Testes: sessão sem `scheduled_date` aparece (ou é corretamente tratada) no dashboard; sessão agendada para "hoje" aparece independente do fuso do servidor
  - Notas: story deve começar reproduzindo o problema (não presumir a causa como certa) antes de commitar a um fix.
  - Notas: causa raiz confirmada reproduzindo o formulário rápido (`frontend/src/app/campaigns/[campaignId]/sessions/page.tsx`) — ele só envia `title`, então toda sessão quick-created fica sem `scheduled_date` e a query do dashboard (`Session.scheduled_date.is_not(None)`) a exclui pra sempre. Decisão: **não** tornar `scheduled_date` obrigatório em `SessionCreate` (quebraria o fluxo rápido existente, mais disruptivo); em vez disso `get_campaign_dashboard()` agora trata sessões sem `scheduled_date` como candidatas válidas a "próxima sessão" (via `OR scheduled_date IS NULL`), ordenando-as depois das sessões com data futura (`ORDER BY scheduled_date IS NULL, scheduled_date, session_number`). Também confirmado o off-by-one: comparar `scheduled_date` (data pura, sem fuso) contra `datetime.now(UTC).date()` esconde sessões marcadas para "hoje" por usuários em fuso negativo (ex. Américas) quando o UTC já virou o dia seguinte; corrigido recuando o cutoff em 1 dia (`today - timedelta(days=1)`) — mitigação pragmática já que não há fuso por usuário/campanha persistido hoje (registrar como possível melhoria futura).

- **Como mestre, quero criar conteúdo homebrew em todas as categorias do catálogo (magia, equipamento, item mágico, monstro, antecedente, talento, regra). ✅ (2026-08-28)**
  - [x] Reproduzir com o usuário como DM: tentar `POST /catalog/{spells,items,magic-items,monsters,backgrounds,feats,rules}` pela UI de cada categoria e capturar o erro/comportamento exato
  - [x] As 9 rotas já existem e funcionam em `app/catalog/router.py` (`_require_dm` guardando cada uma) — investigar se a falha é de permissão (role da campanha em questão), validação (422 silencioso no cliente) ou algo específico de alguma categoria
  - [x] Corrigir a causa raiz encontrada; se for só uma mensagem de erro pouco clara devolvida ao cliente, melhorar o detail do 422/403 pra distinguir os casos
  - [x] Testes de regressão cobrindo o caso específico corrigido
  - Notas: não redesenhar as rotas sem antes confirmar que o bug é real — o backend já passou por uma leva de testes destas 9 rotas na Fase 1 (`tests/catalog/test_router_homebrew.py`).
  - Notas: causa raiz real encontrada é específica de `monsters`, não das outras 8 categorias — permissão (`_require_dm`) e escopo de campanha já funcionavam corretamente ponta a ponta em todas as 9 rotas (comprovado por reprodução via httpx simulando o payload exato que `custom-entry-form.tsx` monta para cada categoria). `MonsterCreate.size` era um `str` livre, mas `Monster.size` é uma coluna de enum nativo do banco (`CreatureSize`) — um valor fora do vocabulário SRD (ex. o DM digitando "Grande" em vez de `large`) passava pela validação do Pydantic, era gravado, e só explodia com `LookupError` não tratado (500) ao reler a linha pra montar a resposta, em vez de um 422 limpo. `ItemCreate.item_type` já seguia o padrão correto (tipado como `ItemType`, o enum), então foi usado como referência: `MonsterCreate.size` agora é tipado `CreatureSize`, rejeitando valores inválidos com 422 antes de tocar o banco. As outras 6 categorias da história (spells, items, magic-items, backgrounds, feats, rules) já se comportavam corretamente — `spells`/`items` já tinham 422 claro pra escola/tipo desconhecidos, e o restante não tem validação de vocabulário fixo nenhuma. Nota separada: o comentário em `frontend/src/lib/api/catalog.ts` ("There is no `POST /catalog/{category}` endpoint yet") está desatualizado — a rota existe e funciona; e o formulário genérico usa `<input type="text">` pra campos de enum (`item_type`, `school`, `size`) em vez de `<select>`, o que facilita o DM digitar um valor inválido — isso é uma lacuna de UX do frontend, não coberta por esta história de backend.

- [x] **Como mestre, quero selecionar o alvo de um ataque/magia em combate.** ✅ (2026-08-28)
  - [x] Reproduzir: declarar uma ação com alvo (`declare_action`) num encontro só com monstros vs. um encontro com participantes mistos
  - [x] Investigar se a lista de alvos fica vazia quando o encontro só tem monstros (relacionado à Fase 13 história 3 — jogadores não conseguem ser adicionados ao combate hoje) ou se é um bug isolado de `declare_action`/`_resolve_attack`
  - [x] Corrigir a causa raiz; se for só consequência do gap de participantes (Fase 13), documentar a dependência e não duplicar o fix
  - [x] Teste de regressão cobrindo o caso reproduzido
  - Notas: `declare_action`→`_resolve_attack` (`app/combat/service.py`) já resolve `target_participant_id` corretamente em teste unitário — o bug relatado pode ser só sintoma de encontro sem alvos válidos.
  - Notas: **Não há bug de backend.** Reproduzido diretamente via `CombatService`: criei um encontro só-com-monstros (dois monstros, sem PC) e chamei `declare_action` de um monstro contra o outro — `_resolve_attack`/`_resolve_and_apply_attack` resolvem `target_id`, rolam ataque/dano e aplicam HP normalmente (novo teste `test_declare_action_resolves_target_in_monster_only_encounter` em `backend/tests/combat/test_declare_action.py`, ao lado do já existente `test_declare_monster_attack_uses_stat_block` que cobre um monstro atacando um PC num encontro misto). O `add_participant`/`validate_participant_kind` do backend (`app/combat/service.py`/`domain.py`) já aceita `character_id` sem restrição. A causa raiz real do "alvo vazio" é 100% frontend: `frontend/src/app/campaigns/[campaignId]/combat/[encounterId]/page.tsx` só renderiza `MonsterPicker` para adicionar participantes — não existe um "CharacterPicker" equivalente para adicionar PCs ao encontro pela UI. Isso é exatamente a Fase 13 história 3 ("jogadores não conseguem ser adicionados ao combate hoje"); quando o mestre só consegue adicionar um monstro (ou monstros) ao encontro, a lista de alvos (`otherParticipants`, calculada em `page.tsx`/passada a `ActionPicker`/`LegendaryActionPicker`) fica pequena ou vazia simplesmente porque não há mais ninguém no encontro para mirar — não é um bug de resolução de alvo. Dependência explícita: o fix de UI (adicionar PCs ao combate) pertence à Fase 13 história 3 e não foi feito aqui, para não duplicar aquele trabalho. Sem mudança de comportamento no backend — só teste de regressão comprovando o caminho já correto; sem entrada de changelog (nenhum fix de comportamento para o usuário).

---

## Fase 10 — Ficha do Personagem: Edição, Identidade e Navegação

> Objetivo: fechar o gap real de edição pós-criação da ficha e dar suporte de dados para a reorganização de navegação pedida pelo grupo.

- **Como jogador, quero editar as informações do meu personagem depois de criado (nome, alinhamento, antecedente, atributos-base — não só HP/AC/inspiração).** ✅ (2026-08-28)
  - [x] Expandir `CharacterUpdate` (`app/characters/schemas.py`) para aceitar `name`, `alignment_id`, `background`, e (com validação/aviso de efeitos em cascata) `ability_scores` — todos opcionais, mesmo padrão dos campos já existentes
  - [x] `service.py`: ao editar `ability_scores`, recalcular campos derivados (modificadores, CA se depender de DEX, PV máximo se depender de CON) — reaproveitar a mesma lógica de recálculo já usada na criação
  - [x] Decidir e documentar a política pra edição de raça/classe pós-criação (bloquear, ou permitir com recálculo completo de CA/PV/perícias) — se bloquear, deixar explícito no schema/erro
  - [x] Testes: edição de nome/alinhamento/antecedente simples; edição de ability score recalcula modificadores e campos derivados; dono errado é rejeitado (403)
  - Notas: o modelo `Character.alignment` já é um campo de texto livre (`str | None`), não uma referência a catálogo (`Alignment` não existe como entidade) — `CharacterUpdate` ganhou `alignment: str | None`, não `alignment_id` como o texto original da história sugeria; mesma convenção já usada por `CharacterCreate.alignment`.
  - Notas: **raça/classe seguem bloqueadas para edição pós-criação** — decisão consciente, não omissão. `CharacterUpdate` deliberadamente não expõe `race_id`/`subrace_id`/classes; ambas cascateiam para features, proficiências e (classe) spell slots, superfície bem maior que o recálculo simples desta história. Não há endpoint/campo que aceite a mudança, então tentar editá-los é a mesma coisa que hoje: ignorado silenciosamente pelo schema (campo inexistente), sem 422 dedicado — comportamento documentado no docstring de `CharacterUpdate`/`update_character`.
  - Notas: `ability_scores` no update é uma lista **parcial** (ao contrário de `CharacterCreate.ability_scores`, que exige as 6) — só os atributos informados são sobrescritos; duplicar o mesmo atributo na mesma requisição é 422, e informar um atributo que o personagem não tem (não deveria acontecer, todo personagem nasce com as 6 linhas) também é 422.
  - Notas: reaproveitei `_recalculate_armor_class` (já usado por `update_equipment`) em vez de reimplementar a lógica de CA — chamado incondicionalmente após qualquer edição de `ability_scores` (barato, e correto mesmo quando DEX não foi um dos atributos alterados). PV máximo só é recalculado quando o *modificador* de CON muda (não o score bruto) — ajuste é `delta_modifier * character.level`, a regra do PHB pra uma mudança retroativa de CON valer para todos os níveis já obtidos, independentemente de como o HP de cada nível foi originalmente rolado.

- **Como jogador, quero colocar uma imagem no meu personagem, para ser exibida "redonda" na ficha e (depois) no mapa de sessão.** ✅ (2026-08-28)
  - [x] `Character` ganha campo de imagem (`portrait_key`, seguindo o padrão de `storage_key` já usado por `Handout` — reaproveitar `StorageService`)
  - [x] Migração Alembic
  - [x] `POST /characters/{id}/portrait` (upload multipart, reaproveitando o padrão de upload de Handouts) — só o dono da ficha
  - [x] Testes: upload troca o portrait, remoção volta ao estado sem imagem, dono errado rejeitado (403)
  - Notas: reaproveitado 1:1 o padrão de `HandoutService`/`StorageService` — `portrait_key` nullable em `Character` (migração `68f443f24e1a`), chave de storage `characters/{character_id}/portrait_{uuid}_{filename}`. `POST /characters/{id}/portrait` (multipart, campo `file`) e `DELETE /characters/{id}/portrait`, ambos restritos ao dono da ficha (`_require_own_membership`, mesmo guard já usado por `update_character`/`add_class`). Ao trocar/remover o portrait, o arquivo antigo é apagado do storage (sem órfãos). Sem validação de mimetype/tamanho — mesmo comportamento (deliberadamente permissivo) já adotado pelo upload de `Handout`; fica como gap conhecido compartilhado pelos dois, não reintroduzido aqui. `CharacterRead.portrait_url` resolvido via `StorageService.get_url`, mesmo padrão de `HandoutRead.url`; `CharacterService` passou a aceitar `StorageService` injetável no construtor, com fallback pro serviço configurado (`get_storage_service()`) pra não quebrar as dezenas de `CharacterService()` já instanciados sem storage em outros domínios/testes.

- **Como jogador, quero marcar minhas proficiências com base nas capacidades da minha raça e classe(s), não livremente.** ✅ (2026-08-28)
  - [x] Modelar quais proficiências uma raça/classe *oferece como escolha* (ex. "escolha 2 de: Atletismo, Intimidação...") vs. as que já vêm fixas — gap pré-existente já documentado nas notas da Fase 7 ("não existe endpoint para setar proficiência de perícia... gap pré-existente, fora do escopo desta história")
  - [x] `POST /characters/{id}/proficiencies` (ou equivalente): aceita só proficiências dentro do conjunto de escolha válido pra raça/classe do personagem (422 se fora do conjunto)
  - [x] Testes: escolha dentro do conjunto válido é aceita, escolha fora do conjunto é rejeitada (422), proficiências fixas de raça/classe são aplicadas automaticamente sem exigir escolha
  - Notas: `ProficiencyClass`/`ProficiencyRace` (Fase 7) só modelam grants *fixos* — nenhum "escolha N de [...]" existia no catálogo. Duas tabelas novas em `app/catalog/models.py`: `ProficiencyChoiceGroup` (pertence a exatamente uma classe OU raça via CHECK constraint, carrega `choose_count`) e `ProficiencyChoiceOption` (as opções válidas daquele grupo, FK pra `Proficiency`) — migração `87740a2fcbed`. Escopo deliberadamente limitado a proficiência de **perícia** (`proficiency_type=skill`): é o único tipo com um campo estruturado no personagem (`CharacterSkill`); arma/armadura/ferramenta seguem sem modelagem no personagem, mesmo gap documentado desde a Fase 8 (proficiência de arma em combate resolve direto do catálogo, sem espelhar em `Character`).
  - Notas: `seed_catalog` **não popula** `ProficiencyChoiceGroup`/`ProficiencyChoiceOption` nesta história (dados de "escolha N de" não estão nos JSONs SRD convertidos hoje, `convert_srd.py` nunca os capturou) — mesmo precedente já registrado nas notas da Fase 7 pra `BackgroundProficiency`/`FeatPrerequisite`/`MonsterProficiency` (testados via construção direta). Fica como gap conhecido pra uma história futura de seed. Também descoberto e corrigido inline: proficiências de perícia **fixas** de raça/classe (`ProficiencyClass`/`ProficiencyRace` com `proficiency_type=skill`) nunca eram aplicadas a `CharacterSkill.proficient` na criação do personagem — `create_character` agora aplica (`_fixed_skill_proficiencies`), mas como o seed também não popula nenhum grant fixo de perícia hoje (SRD real não tem nenhum — perícia de classe sempre é escolha, nunca fixa), esse caminho só é exercitado com dados construídos direto no teste, igual aos choice groups.
  - Notas: `CharacterService.set_proficiency_choices` (`POST /characters/{id}/proficiencies`, owner-only) valida contra a união de todos os `ProficiencyChoiceGroup` de raça + classes do personagem — 422 se a perícia escolhida não está em nenhum grupo, 422 também se o número escolhido de um grupo excede seu `choose_count`. Reaproveita `_require_own_membership`/`_CHARACTER_LOAD_OPTIONS` já usados por `add_class`/`level_up`.

- **Como jogador, quero que a ficha do personagem exponha as sessões associadas a ele, para dar suporte à navegação reorganizada pedida no frontend.** ✅ (2026-08-28)
  - [x] Modelar a associação `Character` ↔ `Session` (hoje inexistente — `Character` não tem relação alguma com `Session`) — decidir se é "sessões em que o personagem participou" (derivado de presença em combate/notas) ou uma lista explícita
  - [x] `GET /characters/{id}/sessions` retornando as sessões associadas, na ordem padrão (por `session_number`)
  - [x] Testes: personagem sem sessões associadas retorna lista vazia; associação reflete corretamente participação real
  - Notas: pré-requisito da história de navegação/reorganização do frontend (Fase 10 do `docs/anahita-frontend-backlog.md`) — não pular o desenho dessa associação achando que é só UI.
  - Notas: seguida a recomendação do backlog — associação **derivada** de participação real em combate (`EncounterParticipant.character_id` → `Encounter.session_id` → `Session`), sem tabela/coluna nova nem migração. Query cross-domain pura em `app/queries/character_sessions.py::get_sessions_for_character` (join + `distinct()` + `order_by(session_number)`), chamada por `CharacterService.get_character_sessions` que aplica o mesmo guard de visibilidade de `get_character` (dono da ficha ou DM da campanha, 403 pros demais) e replica o padrão de `SessionService.list_sessions` pra `dm_notes` (só populado pro DM, `None` pros outros, sem persistir a máscara). Endpoint `GET /characters/{id}/sessions` retornando `list[SessionRead]`. Uma sessão só aparece uma vez mesmo com mais de um encontro do personagem nela (dedupe via `distinct()`). Personagem sem participação em nenhum combate retorna lista vazia, não erro.

- **Como jogador, quero reordenar a exibição das sessões na minha ficha para organização pessoal (sem afetar a ordem oficial de `session_number`).**
  - [ ] Campo de ordenação pessoal por personagem (não uma coluna compartilhada em `Session`) — ex. tabela de junção `character_id`/`session_id`/`sort_order`
  - [ ] `PATCH /characters/{id}/sessions/order` (reordenação em lote)
  - [ ] Testes: reordenação não afeta `session_number` global nem a ordem vista por outro personagem/jogador
  - Notas: depende da história anterior (associação `Character`↔`Session`) existir primeiro.

---

## Fase 11 — Catálogo Homebrew: Profundidade e Estrutura

> Objetivo: uma vez corrigido o bug de criação (Fase 9), fechar as lacunas reais de modelagem e permitir exclusão de conteúdo homebrew.

- **Como mestre, quero customizar todos os atributos possíveis de uma raça homebrew (bônus de atributo, traços, sub-raças, idiomas, proficiências, resistências).**
  - [ ] Estender `RaceCreate` (hoje só `name/description/speed/size/darkvision_range`) e adicionar endpoints de anexo pra `RaceAbilityBonus`, `RaceTrait`, `Subrace`/`SubraceTrait`
  - [ ] `POST /catalog/races/{id}/ability-bonuses`, `/traits`, `/subraces` — todos DM-only, só sobre raça homebrew da própria campanha
  - [ ] Modelar proficiências concedidas pela raça (`ProficiencyRace`) e idiomas como campos estruturados (não só `language_desc` livre) na criação/edição de raça homebrew
  - [ ] Testes: raça homebrew ganha bônus de atributo/traço/sub-raça corretamente; tentativa de anexar a raça SRD (não-homebrew) ou de outra campanha é rejeitada

- **Como mestre, quero poder excluir uma raça/classe/magia/... homebrew que eu criei.**
  - [ ] `DELETE /catalog/{races,classes,spells,items,magic-items,monsters,backgrounds,feats,rules}/{id}` para as 9 categorias — reaproveitar o padrão `_require_dm` já usado em `router.py` para create
  - [ ] `service.py`: rejeitar exclusão de conteúdo SRD (`campaign_id IS NULL`) com 403/400; permitir só homebrew da própria campanha
  - [ ] Decidir e implementar a política pra referências existentes (ex. um personagem já usa a raça homebrew que o DM quer apagar) — bloquear com 409, ou permitir e deixar a referência órfã com fallback de exibição
  - [ ] Testes: delete de homebrew da própria campanha funciona; delete de SRD é rejeitado; delete de homebrew de outra campanha é rejeitado (404); delete com referência existente segue a política decidida

---

## Fase 12 — Recursos de Classe e Interatividade Mágica

> Objetivo: recursos de classe e magias devem gerar efeitos reais (ataque, cura, dano, resistência), não só decrementar um contador.

- **Como jogador, quero que recursos de classe que geram ações (ex. Turn Undead via Canalizar Divindade) disparem a ação correspondente, não só decrementem um contador.**
  - [ ] Conectar `CharacterService.use_resource` (hoje só `entry.used += 1`) ao fluxo de `declare_action` do combate — um novo `action_type` (ou reaproveitar `cast_spell_effect`/`attack_spell`) que consome o recurso e resolve o efeito mecânico correspondente numa chamada só
  - [ ] Mapear, pelo menos pro caso citado (Canalizar Divindade → Turn Undead), qual efeito mecânico cada `FeatureOption` de recurso aciona (resistência de mortos-vivos, dano, etc.)
  - [ ] Testes: uso do recurso em combate consome o contador **e** aplica o efeito ao(s) alvo(s) corretamente; uso fora de combate falha com erro claro (ou é tratado como bookkeeping-only, a decidir)

- **Como jogador, quero que magias com alvo apliquem o efeito automaticamente ao alvo em combate (cura, dano com resistência), mantendo a ficha como bookkeeping-only fora de combate.**
  - [ ] Auditar `declare_action`→`_resolve_attack` (`app/combat/service.py`): confirmar se magias de cura/buff (não-ataque) já aplicam efeito ao alvo, ou só as de ataque/dano com resistência
  - [ ] Se cura/buff não estiverem cobertas, estender o fluxo de resolução pra aplicar o efeito (ex. HP gain) ao `target_participant_id` quando a magia não é `attack_roll`/`saving_throw`
  - [ ] Confirmar e documentar que o comportamento da ficha fora de combate (`POST /characters/{id}/spells/{id}/cast`, bookkeeping-only — consome slot, define concentração, calcula DC, sem aplicar efeito a ninguém) já está correto por design, sem mudança de código necessária ali
  - [ ] Testes: magia de cura em combate aplica HP ao alvo corretamente; magia de dano com resistência já testada anteriormente continua passando; cast pela ficha (fora de combate) não altera HP de ninguém

- **Como jogador, quero que a duração de uma magia respeite as regras de tempo do combate (rodadas) quando em combate, e o tempo real quando fora de combate, com contador visível nos segundos finais.**
  - [ ] Modelar duração de magia: quando lançada dentro de um `encounter_id`, duração em rodadas (reaproveitando o padrão de `EncounterParticipantCondition.duration_rounds`, respeitando os segundos-por-turno do encontro); quando fora de combate, duração em tempo real (`expires_at` calculado a partir de `datetime.now(UTC)` + duração da magia)
  - [ ] Expandir o que hoje é só `concentrating_spell_id` (ponteiro booleano-ish) para carregar a duração/expiração ativa
  - [ ] Endpoint ou campo de leitura que informe o tempo restante (rodadas ou segundos) pra UI renderizar o contador
  - [ ] Testes: duração em rodadas decrementa por avanço de turno; duração em tempo real expira corretamente após o tempo passar; leitura do tempo restante bate com o esperado nos dois modos

---

## Fase 13 — Fluxo de Sessões: Fundamentos Faltantes

> Objetivo: fechar as lacunas de gestão básica de sessão e visibilidade de NPC antes do redesign maior (Fase 15).

- **Como mestre, quero concluir uma sessão.**
  - [ ] `SessionStatus` já tem `completed` no enum — adicionar `POST /sessions/{id}/complete` (ou `PATCH` de status) transicionando `in_progress`→`completed`, DM-only
  - [ ] Testes: transição válida funciona; transição de `planned` direto pra `completed` (pulando `in_progress`) é rejeitada ou tratada conforme decisão; jogador não pode concluir (403)

- **Como mestre, quero editar o nome de uma sessão.**
  - [ ] `SessionUpdate` (hoje inexistente) + `PATCH /sessions/{id}` — DM-only, campo `title` (e talvez `scheduled_date`, reaproveitando pro fix da Fase 9)
  - [ ] Testes: edição funciona; jogador não pode editar (403)

- **Como mestre, quero adicionar personagens (jogadores) ao combate, não só monstros/NPCs.**
  - [ ] Backend já aceita (`EncounterParticipantCreate.character_id`) — confirmar que a rota `POST /encounters/{id}/participants` funciona ponta a ponta com `character_id` preenchido (o gap real é de frontend, ver Fase 13 do backlog de frontend); se houver validação faltando (ex. mesmo personagem duplicado no encontro), adicionar
  - [ ] Testes: adicionar personagem funciona; personagem duplicado no mesmo encontro é rejeitado

- **Como mestre, quero que NPCs fiquem ocultos para jogadores até que eu decida revelá-los.**
  - [ ] `NPC` ganha `is_revealed: bool` (default `False`), seguindo o mesmo padrão de `Handout.is_revealed`
  - [ ] Migração Alembic
  - [ ] `GET /campaigns/{id}/npcs` (e detalhe) para jogador só retorna `is_revealed=true`; DM sempre vê tudo
  - [ ] `POST /npcs/{id}/reveal` (ou `PATCH`), DM-only
  - [ ] Testes: jogador não vê NPC oculto na lista nem no detalhe (404 ou filtro, a decidir); DM vê tudo; reveal muda a visibilidade corretamente

---

## Fase 14 — Loot e Inventário Integrado

> Objetivo: reivindicar um item de loot deve de fato colocá-lo no inventário do personagem.

- **Como jogador, quero que ao reivindicar um item de loot ele entre no meu inventário de personagem de verdade.**
  - [ ] Estender `InventoryService.claim_loot_drop` (hoje só marca `LootDrop.claimed_by`) para criar/mesclar o item reivindicado em `CharacterEquipment` (ou tabela de inventário equivalente) do personagem
  - [ ] Tratar os 3 tipos de loot (`item` de catálogo, `magic_item`, custom por nome) na hora de criar a entrada de equipamento
  - [ ] Testes: claim de cada um dos 3 tipos cria a entrada correta no inventário do personagem; claim duplicado continua rejeitado (409, comportamento já existente)

- **Como mestre, quero atribuir um item de loot a qualquer jogador diretamente, não só esperar que ele reivindique.**
  - [ ] Confirmar/formalizar que `claim_loot_drop` já aceita ser chamado pelo DM em nome de qualquer personagem da campanha (regra "próprio jogador ou DM" já existente) — se a checagem de autorização não cobrir esse caso claramente, ajustar
  - [ ] Testes: DM atribui loot a um personagem que não é o seu; jogador tentando atribuir a outro personagem que não o seu é rejeitado (403)

---

## Fase 15 — Redesign de Sessões: Mapas Dinâmicos e Tokens

> Objetivo: repensar o fluxo de sessão como validado com o grupo — mapa com imagem enviada pelo mestre + grid de 1,5m (5ft) sobreposto; tokens posicionáveis vinculados a personagem/NPC/monstro; movimento limitado por deslocamento (`speed`) em combate (por turno) e livre fora de combate; sincronização em tempo real via WebSocket, reaproveitando a infra do combat tracker; mestre pode mover qualquer token a qualquer momento; seleção de alvo (1 ou mais) direto no mapa para magias/ataques. Esta é a maior fase do backlog — trabalhar uma história de fundação por vez, sem pular pra regras de movimento antes do schema/WS básico existirem.

- **Como mestre, quero subir uma imagem de mapa para uma sessão/encontro, com grid de 1,5m sobreposto.**
  - [ ] `app/sessions/models.py` (ou `app/combat/models.py`, a decidir pela relação mais natural): `SessionMap` — `storage_key` (imagem, reaproveitar `StorageService`), `width_px`/`height_px`, `grid_size_px` (tamanho de uma célula de 1,5m em pixels)
  - [ ] Migração Alembic
  - [ ] `POST /sessions/{id}/maps` (ou `/encounters/{id}/maps`) — upload multipart, DM-only
  - [ ] Testes: upload cria o mapa corretamente; jogador não pode subir mapa (403)

- **Como jogador/mestre, quero que cada personagem/NPC/monstro em cena tenha um token posicionável no mapa.**
  - [ ] `MapToken` — posição (`x`/`y` em células de grid), vínculo a `character_id`/`npc_id`/`monster_id` (mutuamente exclusivo, mesmo padrão de `EncounterParticipant`), `map_id`, visibilidade
  - [ ] Migração Alembic
  - [ ] `POST /maps/{id}/tokens`, `PATCH /tokens/{id}` (posição), `DELETE /tokens/{id}` — DM sempre autorizado; jogador só pode mover o próprio token (ver regra de movimento abaixo)
  - [ ] Testes: criação/posicionamento de token de cada tipo (personagem/NPC/monstro); token não pode referenciar mais de um tipo ao mesmo tempo

- **Como jogador, quero que meu token respeite o deslocamento do meu personagem quando estou em combate, e se mova livremente fora de combate; o mestre pode mover qualquer token a qualquer momento.**
  - [ ] Validação de movimento em `PATCH /tokens/{id}`: se o mapa está vinculado a um encontro `active` e é o turno do personagem, limitar a distância percorrida (em células) ao `speed` do personagem (reaproveitar `engine/` pra conversão célula↔pé); fora desse contexto, movimento livre para o dono do personagem; DM sempre livre
  - [ ] Testes: movimento além do speed no próprio turno é rejeitado (422); movimento fora de combate não tem limite; DM move qualquer token mesmo fora do seu turno; jogador não move token de outro jogador (403)

- **Como grupo, quero ver a posição dos tokens atualizando em tempo real para todos os presentes na sessão.**
  - [ ] Estender o protocolo WS do combat tracker (`app/combat/ws_router.py`/`ws_manager.py`) com eventos `token_moved`/`token_added`/`token_removed` (servidor→cliente) e `move_token` (cliente→servidor), reaproveitando a mesma conexão `/ws/combat/{encounter_id}` quando o encontro tem mapa, ou um canal próprio `/ws/map/{map_id}` se o mapa existir fora de um encontro
  - [ ] Testes: mover um token faz broadcast pra todos os clientes conectados; reconexão recebe o estado atual dos tokens via `state_sync` estendido

- **Como mestre/jogador, quero selecionar 1 ou mais alvos diretamente no mapa ao declarar um ataque ou conjurar uma magia.**
  - [ ] Estender `declare_action`/`DeclareActionRequest` pra aceitar uma lista de `target_participant_id`s (hoje singular) quando a ação afeta múltiplos alvos (ex. Fireball em área)
  - [ ] Resolver a lista de alvos válidos a partir dos tokens presentes na célula/área selecionada no mapa (cálculo geométrico simples: distância entre células)
  - [ ] Testes: ação com múltiplos alvos aplica o efeito a cada um corretamente; ação de alvo único continua funcionando com a lista de tamanho 1

Notas gerais da fase: cada história acima deve fechar seu próprio ciclo completo (models → migração → schemas → service → router → testes) antes da próxima começar, mesmo padrão disciplinado das Fases 0-8. A ordem sugerida acima (mapa → token → movimento → tempo real → seleção de alvo) é a ordem de dependência natural.

---

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

- **Como DM, quero distribuir loot (itens do catálogo ou custom) após um combate, incluindo dinheiro.** ✅ (2026-08-24)
  - [x] `app/inventory/models.py`: `LootDrop` (item do catálogo, `MagicItem`, ou nome livre + moeda em copper)
  - [x] Migração Alembic
  - [x] `service.py`/`router.py`: distribuir para personagem (`claimed_by`)
  - [x] Testes: loot de item custom, loot de moeda pura, claim por personagem
  - Notas: `LootDrop` tem `item_id` (`catalog_items`), `magic_item_id` (`catalog_magic_items`) e `custom_item_name`, mutuamente exclusivos entre si — `claim_loot_drop` é permitido para o próprio jogador do personagem ou para o DM; validação de "no máximo um dos três" e "precisa ter item ou moeda" vive em `app.inventory.domain.validate_loot_drop_kind`, mesmo padrão de `combat.domain.validate_participant_kind`. Suporte a `MagicItem` foi adicionado numa segunda migração (`685472c3be8b`) depois da lacuna abaixo ter sido resolvida ainda dentro desta mesma sessão.

---

## Fase 5 — Registro e Lore

> Requisitos levantados e detalhados em `docs/anahita-backend-prd.md` §7.10 (2026-08-24) — decisões: IA de geração de resumo fica fora do escopo (v1 100% manual); Wiki é páginas livres linkáveis ao World; Diário é único e DM-only (sem diários por jogador); Timeline é híbrida (auto-seed de sessões + eventos manuais).

- **Como DM, quero manter um diário privado da campanha, com ou sem vínculo a uma sessão específica.** ✅ (2026-08-24)
  - [x] `app/journal/models.py`: `JournalEntry` (seção 7.10 do PRD)
  - [x] Migração Alembic
  - [x] `schemas.py`/`service.py`/`router.py` — todo o domínio é DM only (create/list/get/update/delete), nunca visível a jogadores
  - [x] Testes: DM cria/lista/edita/apaga; jogador recebe 403 em qualquer rota do domínio
  - Notas: sem `domain.py` — não há invariante não trivial a extrair (diferente do mutual-exclusion de `LootDrop`); a checagem "requester é DM" já cobre tudo. `_require_dm` retorna 403 tanto para não-membro quanto para membro não-DM, sem distinguir os dois casos (evita vazar pra um jogador se uma entrada existe).

- **Como grupo, quero ver a história da campanha até agora, sessão por sessão.** ✅ (2026-08-24)
  - [x] Nenhuma mudança de backend — reaproveita `GET /campaigns/{id}/sessions` (já retorna `summary`, PRD §7.5)
  - [x] Teste: confirmar que a lista de sessões já expõe `summary` para todo membro da campanha (não só o DM) — se não expuser, é a lacuna a fechar aqui
  - Notas: sem lacuna — `SessionService.list_sessions` já retorna `summary` pra todo membro (só `dm_notes` é ocultado de não-DM). Teste `test_player_can_see_summary_for_recap` adicionado em `tests/sessions/test_service.py`.

- **Como grupo, quero uma timeline de eventos da campanha, combinando o que aconteceu em cada sessão com marcos que o mestre adicionar manualmente.** ✅ (2026-08-24)
  - [x] `app/timeline/models.py`: `TimelineEvent` (só eventos manuais são persistidos, seção 7.10 do PRD)
  - [x] Migração Alembic
  - [x] `app/queries/timeline_queries.py`: funde sessões com `summary` (entradas virtuais, `sort_order = session_number * 1000`) com `TimelineEvent` manuais, ordenado por `sort_order`
  - [x] `schemas.py`/`service.py`/`router.py` — leitura para qualquer membro; criar/editar/apagar evento manual é DM only
  - [x] Testes: entrada automática aparece sem persistir nada; evento manual DM-only; ordenação mistura os dois conjuntos corretamente
  - Notas: sem `domain.py` — sem invariante não trivial a extrair, mesma razão do Diário. Entrada automática só é gerada para sessões com `summary` preenchido (sessão sem resumo não aparece na timeline). `PATCH`/`DELETE` de evento manual localizam o evento só pelo id (mesmo padrão de `_require_faction` no domínio de world) e então checam DM da campanha do evento.

- **Como DM, quero criar páginas de wiki com lore livre, linkáveis a NPCs, locais e facções já cadastrados.** ✅ (2026-08-24)
  - [x] `app/wiki/models.py`: `WikiPage`, `WikiPageLink` (seção 7.10 do PRD)
  - [x] Migração Alembic
  - [x] `domain.py` (mutual exclusion de `npc_id`/`location_id`/`faction_id` no link, mesmo padrão de `LootDrop`) /`schemas.py`/`service.py`/`router.py`
  - [x] Slug único por campanha, gerado a partir do título
  - [x] Regra: leitura (`GET /campaigns/{id}/wiki`, `GET /wiki/{id}`) para qualquer membro; criar/editar/apagar página e link é DM only
  - [x] Estender `app/queries/world_queries.py` (busca cross-entidade da Fase 3) com `wiki_page` como quarto `entity_type`
  - [x] Testes: CRUD de página, link mutuamente exclusivo rejeita mais de um alvo, busca cross-entidade encontra página de wiki por título/conteúdo
  - Notas: slug gerado por `slugify()` puro em `domain.py`, com desambiguação por sufixo numérico (`-2`, `-3`...) resolvida no service contra o banco; editar o título regenera o slug. `WikiPage.links` usa `cascade="all, delete-orphan"` (mesmo padrão de `SessionNote`/`Encounter`) em vez de delete manual. Respostas HTTP montam `WikiPageRead` a partir de linhas já carregadas (nunca acessam a relationship `links` preguiçosamente) pra evitar lazy-load fora de contexto async.

---

## Fase 6 — Interatividade de Ficha e Combate

> Objetivo: fechar as lacunas de interação levantadas pelo grupo na ficha de personagem (magias por círculo com limites/slots, itens, moeda) e no fluxo de sessão/combate (abrir sessão, popular e iniciar combate com iniciativa, ações declaradas com resolução automática, rolagens do sistema com opção de digitar manualmente). Depende das Fases 1 (Characters) e 2 (Combat), já completas. Levantado em 2026-08-24 a partir de pedido do grupo — ver também `docs/anahita-frontend-backlog.md` Fase 6 para as telas correspondentes, e Fase 7 para os complementos de sobrevivência/descanso/recursos levantados na mesma sessão.

- **Como jogador, quero gerenciar as magias conhecidas/preparadas da minha ficha, organizadas por círculo, respeitando os limites da minha classe.** ✅ (2026-08-24)
  - [x] `CharacterSpellRead` passa a incluir o círculo (nível) e a flag `ritual`, resolvidos do catálogo (`Spell.level`/`Spell.ritual`) na leitura, sem duplicar dado
  - [x] `PATCH /characters/{id}/spells/{spell_id}` (toggle `prepared`) e `DELETE /characters/{id}/spells/{spell_id}` (esquecer magia) — owner only
  - [x] `engine/spellcasting.py`: fórmula de magias conhecidas (classes com número fixo por nível, ex. Bard/Sorcerer/Warlock) e de magias preparadas (`ability_mod + nível de conjurador`, ex. Cleric/Druid/Paladin/Wizard), a partir da progressão já modelada em `ClassLevel`
  - [x] `service.py`: adicionar/preparar magia acima do limite calculado é rejeitado (422), com mensagem informando o limite atual e quantas já estão preparadas/conhecidas
  - [x] Testes: limite de preparadas/conhecidas por classe e nível, toggle `prepared` respeita o limite, remover magia libera espaço, dono errado rejeitado
  - Notas: known-caster (Bard/Ranger/Sorcerer/Warlock) count vem direto de `ClassLevelResource.resource_key="spells_known"`/`ClassLevelSpellSlot.spell_level=0`, dados que já existiam no SRD raw mas eram descartados por `convert_srd.py` — corrigido inline (regenerado `classes.json`); prepared-caster (Cleric/Druid/Paladin/Wizard) usa a fórmula `ability_mod + nível`. Adicionada coluna `ClassDefinition.spellcasting_ability` (também ausente, mesma causa) para resolver a habilidade de conjuração por classe. Limite só é verificado quando `source_class` corresponde ao índice de uma classe do personagem — sem isso não há progressão pra calcular o limite contra.

- **Como jogador, quero ver quantos slots de magia tenho disponíveis por nível e gastá-los ao conjurar, incluindo ritual (sem custo) e conjuração em nível maior.** ✅ (2026-08-24)
  - [x] `app/characters/models.py`: `CharacterSpellSlot` (`character_id`, `spell_level` 1-9, `used`) — o máximo por nível é derivado de `ClassLevelSpellSlot` na leitura, não persistido
  - [x] Migração Alembic
  - [x] `POST /characters/{id}/spells/{spell_id}/cast` (body: `cast_at_level`, `as_ritual`) — valida magia conhecida/preparada, `cast_at_level >= spell.level`, slot disponível no nível pedido; `as_ritual=true` só é aceito se `Spell.ritual=true` e não consome slot; upcast consome o slot do nível efetivamente escolhido
  - [x] `POST /characters/{id}/rest` (`short`/`long`) — long rest zera `CharacterSpellSlot.used`; short rest não mexe em slots por padrão (Warlock tem regra própria — fora do escopo desta história)
  - [x] Testes: consumo de slot correto, ritual não consome, upcast exige slot do nível maior, sem slot disponível é rejeitado (422), long rest restaura todos os slots
  - Notas: `CharacterRead.spell_slots` soma os slots de cada classe conjuradora do personagem independentemente (não implementa a tabela combinada de conjurador multiclasse do PHB) — documentado no docstring de `CharacterSpellSlot`; exato para personagens de classe única, aproximado para multiclasse com duas classes conjuradoras. `{spell_id}` nas rotas de cast é o id da entrada `CharacterSpell` (mesma convenção do PATCH/DELETE já existentes), não o id do catálogo.

- **Como jogador, quero editar e remover itens do meu inventário, e registrar ganho/gasto de moedas.** ✅ (2026-08-24)
  - [x] `PATCH /characters/{id}/equipment/{equipment_id}` (toggle `equipped`/`attunement`, ajustar `quantity`) e `DELETE /characters/{id}/equipment/{equipment_id}` — owner only
  - [x] `Character` ganha coluna(s) de moeda (decisão de implementação: uma única coluna normalizada em copper, ou cinco colunas cp/sp/ep/gp/pp — seção 7.3 do PRD a atualizar com a escolha)
  - [x] Migração Alembic
  - [x] `POST /characters/{id}/currency` (delta positivo=ganho, negativo=gasto; saldo não pode ficar negativo, 422 se ficaria)
  - [x] Testes: editar/remover item, saldo não fica negativo, ganho/gasto refletem na leitura da ficha
  - Notas: decisão tomada por engenharia — uma única coluna `currency_cp` normalizada em copper, consistente com a convenção já usada para preços de itens do catálogo (`convert_srd._cost_in_cp`); simplifica o saldo pra um inteiro só. Conversão pra denominações (cp/sp/ep/gp/pp) fica pro frontend exibir. PRD §7.3 atualizado com a decisão (e com `CharacterSpellSlot`, que também estava faltando).

- **Como DM, quero abrir uma sessão para ser jogada e iniciar um combate populado com todos os personagens da campanha, exigindo iniciativa antes do primeiro turno.** ✅ (2026-08-24)
  - [x] `Session` ganha `status` (`planned`/`open`/`closed`; seção 7.5 do PRD a atualizar) — `POST /sessions/{id}/open` (DM only)
  - [x] `POST /encounters/{id}/start`: além de mudar `preparing`→`active`, adiciona automaticamente como participante todo personagem (PC) da campanha ainda ausente do encontro (monstros/NPCs continuam adicionados manualmente, como hoje)
  - [x] Encontro só aceita `advance_turn` depois que **todo** participante tem `initiative` definida — novo comando WS `roll_initiative` (jogador rola a própria; DM rola pelas dele e pelos NPCs/monstros)
  - [x] Testes: abrir sessão sem ser DM rejeitado, `start` popula todos os PCs da campanha, `advance_turn` rejeitado enquanto falta iniciativa de algum participante, `roll_initiative` seta o valor e libera o encontro quando completo
  - Notas: `SessionStatus` já existia (`planned`/`in_progress`/`completed`) — reaproveitado em vez de renomear pra `open`/`closed` (mesmo conceito, sem quebrar o enum já em produção); `POST /sessions/{id}/open` faz a transição `planned`→`in_progress`. `EncounterParticipant.initiative` virou nullable (migração) pra permitir participante sem rolagem ainda. `roll_initiative` é o primeiro comando WS não-DM-only — o gate em `ws_router.py` foi ajustado pra distinguir comandos DM-only de comandos de qualquer membro, com posse verificada no service (jogador só a própria ficha, DM qualquer participante).

- **Como jogador/DM, quero declarar ações de combate (ataque com arma, magia, ações especiais) que resolvem automaticamente acerto e dano/efeito.** ✅ (2026-08-24)
  - [x] `ActionType` (`app/combat/domain.py`) ganha `attack_weapon`, `attack_spell`, `grapple`, `shove`, `search` (hoje cobertos genericamente por `attack`/`spell`/`other`)
  - [x] Novo comando WS `declare_action` — `attack_weapon`/`attack_spell`: rolagem de ataque (d20 + bônus do atacante) vs. `armor_class` do alvo; ao acertar, aplica a rolagem de dano da arma/magia; registra tudo (rolagens, alvo, resultado) no `CombatLog`
  - [x] `grapple`/`shove`: teste oposto (Athletics do atacante vs. Athletics/Acrobatics do alvo, à escolha do alvo) resolvido no servidor; aplica a condição `grappled` ou reposiciona o alvo conforme o resultado
  - [x] Testes: ataque acerta/erra conforme AC e aplica o dano certo, grapple/shove aplicam ou não o efeito conforme o teste oposto, ação declarada por quem não é dono do participante é rejeitada (403)
  - Notas: lacuna real descoberta e resolvida inline — `EncounterParticipant` não tinha nenhum jeito de resolver bônus de ataque/perícia pra NPCs/monstros; a exploração revelou que o catálogo **já** modela stat blocks completos de monstro (`Monster`/`MonsterAction`/`MonsterActionDamage`/`MonsterProficiency`, com atributos e `attack_bonus` prontos), só não existia link do participante pro catálogo — adicionada `EncounterParticipant.monster_id` (FK nullable pra `catalog_monsters`) e resolução automática via stat block quando presente. Dano de magia (`attack_spell`) também não tinha estrutura no catálogo (`Spell` só tinha texto livre) — adicionada `SpellDamage` (dado, tipo, escala por nível de slot ou nível de personagem), convertida do SRD raw (`convert_srd.py`/`seed.py`), decisão do usuário via pergunta explícita. Um participante puramente manual (sem `character_id`/`monster_id`) segue exigindo bônus manual no payload (`manual_attack_bonus`/`manual_damage_expression`/`manual_athletics_bonus`/`manual_target_bonus`), também decisão explícita do usuário. Simplificações documentadas nos docstrings: arma finesse sempre usa DEX (regra deixa a critério do jogador); personagem sempre proficiente com arma equipada (sem tabela de proficiência por categoria); grapple/shove sempre usa a melhor defesa do alvo entre Athletics/Acrobatics (sem prompt ao vivo pra escolha); dano de monstro com múltiplos componentes é somado numa expressão só, logado sob o tipo do primeiro. **Adendo (2026-08-25, durante o frontend da mesma fase):** `declare_action` rejeitava com 422 qualquer `action_type` fora de `attack_weapon`/`attack_spell`/`grapple`/`shove` — mas o `action-picker.tsx` do frontend precisa declarar as 7 ações "de sabor" do backlog (dash, dodge, disengage, help, hide, ready, search) também. Adicionado um resolvedor genérico pra essas: só registra a ação no `CombatLog` sem rolar nada, já que não têm rolagem associada nas regras.

- **Como jogador/DM, quero que toda rolagem do sistema (iniciativa, ataque, dano) seja feita automaticamente pelo servidor por padrão, mas possa digitar o resultado manualmente quando preferir.** ✅ (2026-08-24)
  - [x] `engine/dice.py`: parser/roller de expressões (`1d20+5`, `2d6`), RNG injetável para ser determinístico em teste
  - [x] Toda rolagem feita no backend (iniciativa, ataque, dano) aceita um resultado manual opcional no payload — ausente, o servidor rola via `engine/dice.py`; presente, usa o valor informado (`CombatLog.rolled_by_system=false` nesse caso)
  - [x] Regra: jogador só pode informar resultado manual para rolagens do próprio personagem; DM pode para qualquer participante
  - [x] Testes: rolagem automática usa `engine/dice.py` com RNG controlado, resultado manual sobrescreve corretamente e é auditado no log, jogador não pode informar resultado manual de outro participante (403)
  - Notas: em vez de um único campo genérico `manual_result` reaproveitado em todo lugar (como o texto original sugeria), cada comando tem campos manuais nomeados por rolagem (`roll_initiative.initiative`; `declare_action.manual_attack_roll`/`manual_damage_roll`/`manual_target_roll`) — decisão de engenharia, não do usuário: `declare_action` às vezes precisa de duas rolagens manuais na mesma chamada (acerto E dano), o que um campo único não comporta. `CombatLog` ganhou `rolled_by_system` (migração); numa entrada que cobre mais de uma rolagem (ataque + dano), só fica `true` quando todas foram automáticas. RNG injetável é testado diretamente em `tests/engine/test_dice.py` (unitário) — o service não expõe injeção de RNG por fora, então os testes de integração usam os campos manuais pra determinismo, não seed de RNG.

- **Lacuna de visibilidade: jogador deve ver apenas um resumo dos personagens de outros jogadores na campanha, não a ficha completa.** ✅ (2026-08-24)
  - [x] `GET /characters?campaign_id=` hoje retorna `CharacterRead` completo para qualquer membro — restringir: dono da ficha e DM continuam recebendo `CharacterRead` completo; para os demais membros, um `CharacterSummaryRead` (nome, raça, classe(s), nível — sem atributos/HP/spells/equipment)
  - [x] Testes: jogador A não recebe atributos/HP/spells de jogador B na listagem, só o resumo; DM e o próprio dono continuam vendo a ficha completa
  - Notas: `response_model=list[CharacterRead | CharacterSummaryRead]` — o Pydantic v2 "smart union" escolhe o schema certo por instância de retorno (confirmado com teste HTTP end-to-end, não só a nível de service, por ser um ponto sensível a vazamento de dado se a união escolhesse o schema errado).

---

## Fase 7 — Sobrevivência, Descanso e Recursos

> Objetivo: itens de interatividade complementares levantados junto com a Fase 6, mas de escopo próprio (sobrevivência em combate, descanso, recursos de classe, progressão de nível) — separados em fase própria para não inflar a Fase 6 e para poderem ser priorizados/validados com o grupo independentemente dela. Depende da Fase 6 (spell slots e descanso já entram lá; esta fase estende o mesmo `POST /characters/{id}/rest`) e da Fase 2 (Combat). Levantado em 2026-08-24.

- **Como jogador, quero gastar dados de vida num descanso curto para recuperar pontos de vida. ✅ (2026-08-25)**
  - [x] `Character` ganha `hit_dice_used` (dados de vida já gastos; o total disponível é `level`, o dado em si vem do `hit_die` da classe primária — multiclasse com dados de tipos diferentes fica registrado por classe, não só um total agregado)
  - [x] Migração Alembic
  - [x] `POST /characters/{id}/rest` (Fase 6) ganha, no modo `short`, um parâmetro `hit_dice_spent` — rola `hit_dice_spent` dados do tipo certo + modificador de CON cada, soma ao PV atual (capado em `hit_point_max`), marca os dados como usados
  - [x] Modo `long` (já existente da Fase 6) passa também a restaurar até metade do total de dados de vida do personagem (mínimo 1), regra padrão do PHB
  - [x] Testes: gasto de dado de vida cura o esperado e não ultrapassa `hit_point_max`, dados insuficientes disponíveis é rejeitado (422), descanso longo restaura a fração certa
  - Notas: `hit_dice_used` fica em `CharacterClass` (por classe, não em `Character`) para suportar multiclasse com dados de tipos diferentes. `hit_dice_spent` aceita `manual_roll` por classe gasta (mesma convenção de override manual da Fase 6). Restauração do descanso longo distribui a metade (mínimo 1) classe a classe, na ordem em que aparecem no personagem.

- **Como jogador, quero fazer testes de morte automaticamente quando meu personagem chega a 0 pontos de vida. ✅ (2026-08-25)**
  - [x] `Character` ganha `death_save_successes`/`death_save_failures` (0-3, resetados ao estabilizar/curar)
  - [x] `POST /characters/{id}/death-save` — só aceito com `hit_point_current == 0`; rola 1d20 via `engine/dice.py` (Fase 6): 1 conta como duas falhas, 20 restaura 1 PV e consciência, 10+ é sucesso, resto é falha; 3 falhas marca o personagem como morto (estado a definir — reaproveita `EncounterCondition`/campo próprio), 3 sucessos estabiliza
  - [x] Regra: qualquer cura ou dano recebido enquanto em 0 PV zera os contadores (dano quando já em 0 conta como falha adicional, e crítico conta como duas — regra do PHB)
  - [x] Testes: sequência de sucessos estabiliza, sequência de falhas mata, 20 natural restaura 1 PV, 1 natural conta duas falhas, dano em 0 PV zera e conta falha
  - Notas: estado "morto" ficou em campo próprio (`Character.is_dead`), não reaproveitando `EncounterCondition` — o personagem existe fora de combate também, então um campo no próprio `Character` é mais direto que um estado só válido dentro de um encontro. A regra de "dano em 0 PV" é detectada comparando o HP antigo e o novo em `_register_hp_change` (chamado tanto por `update_character` quanto pelo gasto de dados de vida): manter em 0 PV conta como falha adicional, subir acima de 0 zera os contadores. O dobro de falha em crítico não é modelado no editor de HP genérico (`update_character`), que não carrega informação de crítico — só o próprio `death_save` (1 natural) aplica o dobro.

- **Como jogador, quero indicar quando estou concentrando numa magia e receber automaticamente a DC do teste de concentração ao sofrer dano em combate. ✅ (2026-08-25)**
  - [x] `Character` (ou `EncounterParticipant`, para o estado só valer durante o combate — decisão de implementação) ganha `concentrating_spell_id` nullable
  - [x] `POST /characters/{id}/concentration` (iniciar/encerrar concentração numa magia conhecida) e limpar automaticamente ao conjurar outra magia de concentração (só uma por vez, regra do PHB)
  - [x] Ao aplicar dano a um participante concentrando (via `update_participant`/`declare_action` da Fase 6), a resposta do evento inclui a DC do teste de concentração (`max(10, floor(dano/2))`) para o cliente resolver a rolagem de resistência de CON — o servidor não resolve o teste sozinho, só calcula e expõe a DC (o resultado da resistência já é coberto pelo fluxo de rolagem da Fase 6)
  - [x] Testes: dano com concentração ativa retorna a DC correta; dano sem concentração não retorna DC; conjurar nova magia de concentração encerra a anterior
  - Notas: `concentrating_spell_id` ficou em `Character` (não em `EncounterParticipant`) — mais simples e cobre concentração fora de combate também. `CombatService._concentration_dc` é o helper compartilhado usado tanto por `live_update_participant` (WS `update_participant`) quanto por `declare_action`'s `_resolve_and_apply_attack`.

- **Como jogador, quero ver minhas perícias passivas (Percepção, Investigação, Intuição) na minha ficha. ✅ (2026-08-25)**
  - [x] `CharacterRead` ganha `passive_perception`/`passive_investigation`/`passive_insight` (`10 + bônus da perícia correspondente`, mesmo padrão de campo calculado de `CharacterSkillRead.bonus`)
  - [x] Testes: passiva bate com `10 + bonus` da perícia correspondente, inclusive com proficiência/expertise
  - Notas: não existe endpoint para setar proficiência de perícia neste app ainda (gap pré-existente, fora do escopo desta história) — o teste de proficiência escreve direto no `CharacterSkill` via sessão de banco para validar a fórmula.

- **Como jogador, quero subir de nível meu personagem, ganhando pontos de vida e escolhendo melhoria de habilidade ou talento. ✅ (2026-08-25)**
  - [x] `POST /characters/{id}/level-up` (`class_definition_id`, incremento de 1 nível numa classe já possuída ou nova via multiclasse — reaproveita a validação de `add_class`) — recalcula `hit_point_max` (rolagem do dado de vida da classe + modificador de CON, ou média, a decidir) e `proficiency_bonus`
  - [x] Nos níveis de ASI da classe (dado por `ClassLevel`), o corpo aceita `ability_score_increases` (até dois pontos distribuídos) **ou** `feat_id` (mutuamente exclusivos, valida contra o catálogo de Feats e seus pré-requisitos)
  - [x] Testes: subir de nível soma PV corretamente, nível de ASI aceita distribuição de pontos ou talento (não os dois), talento com pré-requisito não satisfeito é rejeitado (422)
  - Notas: HP ganho é rolado via `engine/dice.py` (`1d{hit_die} + CON`, mínimo 1), com `manual_hit_die_roll` como override manual — mesma convenção do resto do app, em vez de usar a média fixa do PHB.

- **Como DM, quero que monstros usem ações lendárias e reações do próprio stat block durante o combate. ✅ (2026-08-25)**
  - [x] Novo comando WS `use_legendary_action`/`trigger_reaction` (DM only, para participantes NPC/monstro) — resolve a partir de `MonsterLegendaryAction`/`MonsterReaction` do catálogo (via `npc_id`/`stat_block_id`), aplicando dano/efeito como uma ação declarada normal (reaproveita a resolução de ataque/dano da Fase 6)
  - [x] Regra: ações lendárias só disponíveis fora do próprio turno do monstro e limitadas ao número descrito no stat block por rodada (contador resetado a cada início de rodada do próprio monstro)
  - [x] Testes: ação lendária disponível só fora do turno do monstro e respeita o limite por rodada, reação dispara e aplica o efeito do stat block
  - Notas: o catálogo não modela um número de ações lendárias por monstro — todo stat block usa um orçamento fixo de 3 por rodada (`CombatService._LEGENDARY_ACTIONS_PER_ROUND`), simplificação documentada. `EncounterParticipant` ganhou `legendary_actions_used`/`reactions_used`, resetados no início do próprio turno em `advance_turn`. `_resolve_attack` foi refatorado em `_resolve_and_apply_attack` (núcleo compartilhado de rolagem/dano/log) para reaproveitar exatamente a resolução de ataque da Fase 6.

- **Como jogador, quero usar recursos de classe em combate (fúria, ki, etc.) com controle de uso e recarga em descanso. ✅ (2026-08-25)**
  - [x] `app/characters/models.py`: `CharacterResource` (`character_id`, `resource_key`, `used`) — o máximo por nível é derivado de `ClassLevelResource` na leitura, mesmo padrão de `CharacterSpellSlot` (Fase 6)
  - [x] Migração Alembic
  - [x] `POST /characters/{id}/resources/{resource_key}/use` — rejeita se já no limite (422)
  - [x] `POST /characters/{id}/rest` (Fase 6/7) restaura os recursos conforme a recarga de cada `resource_key` (curto ou longo — tabela de recarga por recurso, a mapear a partir do SRD)
  - [x] Testes: uso consome corretamente, uso acima do limite é rejeitado, descanso do tipo certo restaura o recurso, descanso do tipo errado não restaura
  - Notas: `ClassLevelResource` carrega várias chaves que não são "recursos consumíveis" (ex. `sneak_attack_dice`, `spells_known`) — só as chaves em `CharacterService._RESOURCE_RECHARGE` (rage_count, ki_points, sorcery_points, action_surges, channel_divinity_charges, indomitable_uses, bardic_inspiration_die) são utilizáveis via este endpoint; a tabela de recarga curto/longo foi mapeada manualmente a partir do PHB, já que o catálogo não carrega esse dado.

---

## Fase 8 — Dashboard e Refinamentos de Ficha

> Levantado pelo grupo em 2026-08-25 (revisão de Dashboard/Ficha em uso). Depende das Fases 1 (Characters), 3 (World), 4 (Handouts), 6 e 7 (spellcasting/rest/resources), todas completas. Vários itens levantados pelo grupo já têm suporte mecânico correto no backend (descanso, bônus de perícia, ataque com arma equipada) — os gaps reais de backend estão listados abaixo; o restante é só integração/UX de frontend (ver `docs/anahita-frontend-backlog.md`, Fase 8).

- **Como jogador, quero ver no dashboard da campanha a próxima sessão, NPCs/locais recentes e handouts pendentes sem o frontend precisar fazer várias chamadas. ✅ (2026-08-25)**
  - [x] `app/queries/dashboard_queries.py`: query cross-domain que resolve a próxima sessão (`scheduled_date` mais próxima ainda não passada, com `status` `planned`/`in_progress`), NPCs/locais mais recentes (`ORDER BY created_at DESC LIMIT N`) e handouts com `is_revealed=false` (contagem + lista), tudo escopado a uma campanha
  - [x] `router.py`: `GET /campaigns/{campaign_id}/dashboard` — visão por papel (DM recebe tudo; jogador recebe só o que já é visível a ele hoje: handouts revelados não entram como "pendente" pra jogador, já que ele nunca via os não revelados)
  - [x] Testes: próxima sessão retorna a mais próxima no futuro (não a mais recente no passado), handouts pendentes só aparecem pro DM, NPCs/locais recentes respeitam o limite e a ordenação
  - Notas: `Session.scheduled_date` (`app/sessions/models.py`) já existe — não é campo novo, só a query de "próxima" que faltava. Reaproveita os modelos de `app/sessions`, `app/world`, `app/handouts` já existentes. Lacuna mecânica encontrada e resolvida inline: `Location` não tinha `created_at` (só `NPC` tinha), então "recentes" não era ordenável — adicionada a coluna (migração `7c1e88f5c532`, com `server_default=now()` pra preencher linhas existentes) e o campo em `LocationRead`. Autorização reaproveita `CampaignService.get_own_membership` (404 se não for membro); `dm_notes` da próxima sessão só aparece pro DM, mesmo padrão de `SessionService.list_sessions`.

- **Como jogador, quero escolher a estratégia de geração de atributos (standard array, point buy, custom ou rolagem) ao criar meu personagem. ✅ (2026-08-25)**
  - [x] `Character`/`CharacterCreate` ganha `generation_method` (enum: `standard_array`/`point_buy`/`custom`/`roll`), persistido para referência futura (nullable, sem afetar personagens já criados)
  - [x] Migração Alembic
  - [x] `domain.py`: quando `generation_method=point_buy`, valida orçamento de 27 pontos (tabela de custo 8–15 do PHB); quando `standard_array`, valida que os 6 valores enviados são exatamente `{15,14,13,12,10,8}` permutados; `custom`/`roll` não validam os valores (o cliente decide os números)
  - [x] Testes: point buy dentro do orçamento passa, acima do orçamento é rejeitado (422); standard array com valores certos passa, com valor fora do conjunto é rejeitado; custom/roll aceitam qualquer combinação
  - Notas: `CharacterCreate.ability_scores` já aceitava os valores finais diretamente — esta história só adicionou validação condicionada ao método declarado, sem mudar o formato do payload de ability scores. Point buy rejeita apenas *acima* do orçamento de 27 pontos (não força gastar todos os pontos) — decisão de implementação por não haver exigência explícita de gasto total no PHB nem no backlog.

- **Como jogador, quero que o subir de nível me pergunte as escolhas mecânicas que ganho no nível (estilo de luta, pacto, domínio etc.), e que essas opções sejam pesquisáveis como o resto do catálogo. ✅ (2026-08-25)**
  - [x] `models.py`: `FeatureOption` (feature-pai + opções nomeadas, ex. "Estilo de Luta: Defesa"/"Estilo de Luta: Duelismo", "Pacto da Lâmina"/"Pacto do Tomo"), `CharacterFeatureChoice` (`character_id`, `feature_id`, `feature_option_id`)
  - [x] Migração Alembic
  - [x] `GET /catalog/features?parent_feature_id=` — lista as opções de uma feature com o mesmo suporte de busca/filtro que as demais categorias de catálogo (reaproveita o padrão de `list_*_translated`)
  - [x] `POST /characters/{id}/level-up`: quando uma feature do nível ganho tem opções (`FeatureOption` associadas), a resposta sinaliza `requires_choice: true` + a lista de opções; o corpo da requisição aceita `feature_choices: [{feature_id, feature_option_id}]`, validado contra as opções reais da feature (422 se a opção não pertence à feature)
  - [x] Testes: nível com feature de escolha exige `feature_choices` (422 se ausente), escolha inválida (opção de outra feature) rejeitada, escolha persistida aparece na leitura da ficha, nível sem feature de escolha não exige nada
  - Notas: **decisão de design tomada com o usuário antes de implementar** (ver pergunta feita em sessão) — em vez de criar um catálogo `FeatureOption` novo e independente, reaproveitamos `catalog_features.parent_feature_id` (campo que já existia no modelo `Feature`, mas nunca era populado pelo seed): o SRD já carrega esse relacionamento pai/opção via `parent.index` em `_data/2014/en/5e-SRD-Features.json`, então `convert_srd.py`/`seed.py` passaram a propagá-lo (`_link_feature_options` no fresh install; `backfill_feature_parent_ids`, idempotente, populou o Postgres de dev já semeado sem trocar nenhum id existente). Isso já linka de graça todos os grupos de escolha do SRD (Fighting Style de fighter/paladin/ranger, Pact Boon, Circle of the Land, Draconic Ancestry, Hunter's Prey/Defensive Tactics/Superior Hunter's Defense etc.) — não só os dois exemplos do backlog. `requires_choice` é sinalizado via 422 (nada é commitado até a escolha chegar), com `detail={"requires_choice": true, "choices": [...]}`; a detecção fica restrita às features da progressão *base* da classe (`ClassLevel.subclass_definition_id IS NULL`) — Eldritch Invocations/Metamagic (escolha múltipla, "choose 2") e escolhas específicas de subclasse (ex. Circle of the Land) ficam fora desta história porque o design assume uma escolha por feature; retomar no fechamento da Fase 8 se o grupo quiser cobrir esses casos. `CharacterFeatureChoiceInput`/`Read` seguem o formato `(feature_id, feature_option_id)` já pedido, ambos FKs pra `catalog_features.id`.

- **Como jogador de Paladin/Cleric, quero que o backend saiba qual opção de Canalizar Divindade eu usei quando tenho mais de uma disponível. ✅ (2026-08-25)**
  - [x] Vincular `FeatureOption` (história anterior) ao recurso `channel_divinity_charges`: `CharacterResource` ou uma tabela de uso dedicada passa a registrar qual `feature_option_id` foi gasto em cada uso
  - [x] `POST /characters/{id}/resources/{resource_key}/use` ganha um `option_id` opcional — obrigatório quando o recurso tem mais de uma opção disponível para o personagem (422 se ausente nesse caso), ignorado/opcional quando só há uma opção ou nenhuma
  - [x] Testes: uso de `channel_divinity_charges` com múltiplas opções exige `option_id`, uso registra qual opção foi gasta, personagem com uma única opção não é obrigado a informar
  - Notas: **decisão tomada com o usuário** (pergunta feita em sessão) — diferente de Fighting Style/Pact Boon, o SRD não marca as opções de Canalizar Divindade (`channel-divinity-turn-undead`, `channel-divinity-preserve-life`, `channel-divinity-sacred-weapon`, `channel-divinity-turn-the-unholy`) com `parent`; curei esse vínculo à mão em `_CHANNEL_DIVINITY_PARENT_OVERRIDES` (`convert_srd.py`) — exaustivo pro SRD 2014 `en` atual, que só tem o domínio Vida (Clérigo) e o juramento Devoção (Paladino) publicados. O seed de classes passou a fazer o link pai/opção com um `features_by_index` por classe inteira (base + subclasses), não mais por lista isolada, já que a opção do Paladino é feature de subclasse mas o pai é da classe base. `CharacterResource` ganhou `last_feature_option_id` (opção mais recente gasta, não histórico completo por uso — suficiente pro pedido da história) via `CharacterService._resource_options`, que resolve as opções disponíveis cruzando os features-pai (`_RESOURCE_OPTION_PARENT_FEATURES`) com as classes/subclasses reais do personagem.

- **Como jogador/DM, quero que toda magia tenha um tipo de ação claro (ataque, resistência ou só conjuração) e um alvo definido (aliado, inimigo, a própria criatura, área), para a UI saber o que pedir ao conjurar. ✅ (2026-08-25)**
  - [x] `Spell` ganha `action_type` (enum: `attack_roll`/`saving_throw`/`cast_only`), `save_ability_score_id` (FK nullable para `AbilityScoreDefinition`) e `target_type` (enum: `self`/`ally`/`enemy`/`area`/`object`)
  - [x] Migração Alembic
  - [x] `convert_srd.py`: derivar os três campos a partir do texto do SRD (heurística por padrões conhecidos + lista manual de exceções) e regenerar `spells.json`; reseed
  - [x] `POST /characters/{id}/spells/{spell_id}/cast` passa a aceitar `target_participant_id` opcional; quando `action_type=saving_throw`, a resposta inclui a DC (`8 + prof + ability_mod` do conjurador), mesmo padrão já usado pela DC de concentração (Fase 7)
  - [x] Testes: spell de ataque (ex. Fire Bolt) tem `action_type=attack_roll`, spell de resistência (ex. Fireball) tem `action_type=saving_throw` + DC calculada corretamente, spell só de efeito (ex. Mage Armor) tem `action_type=cast_only` sem rolagem nenhuma
  - Notas: `action_type` acabou não precisando de heurística nem exceções — o SRD já carrega isso como dado estruturado (`attack_type`/`dc` em `5e-SRD-Spells.json`), então a conversão é direta. `target_type` é, sim, heurístico (o SRD não modela isso): área > dano sem rolagem (auto-hit, ex. Magic Missile) ou ataque/resistência = inimigo > alcance "Self" = self > default aliado; documentado como best-guess no docstring de `SpellTargetType`, não uma codificação exaustiva de regras (PHB permite mais de um tipo de alvo em vários casos, ex. Cure Wounds em si mesmo ou outra criatura). Sem reseed destrutivo: como já havia personagens referenciando `catalog_spells.id` no Postgres de dev, os 3 campos foram adicionados como colunas nullable e populados via `backfill_spell_action_target_types` (idempotente, casa por `index`, nunca troca id) — mesmo padrão da Fase 8 anterior (`backfill_feature_parent_ids`). `cast_spell` mudou de retornar `CharacterRead` direto para `CharacterSpellCastResponse` (`character`+`save_dc`+`target_participant_id`) — breaking change de contrato aceito porque endpoint ainda não tinha consumidor no frontend (Fase 8 do frontend ainda não implementou essa tela). `target_participant_id` é aceito e ecoado de volta sem validação — este endpoint não tem contexto de encontro pra validar contra, é só sinalização pra UI.

- **Como jogador, quero que a CA da minha ficha reflita a armadura/escudo que estou usando, sem precisar editar o valor manualmente. ✅ (2026-08-25)**
  - [x] `PATCH /characters/{id}/equipment/{equipment_id}` (toggle `equipped`): quando o item alternado é do tipo `armor` ou `shield` (ou tem `ArmorDetail` associado no catálogo), recalcula `Character.armor_class` via `engine/armor_class.py::calculate_ac` (base da armadura + mod DEX limitado pelo tipo de armadura + bônus de escudo, somando todos os itens `equipped=true` do personagem)
  - [x] `PATCH /characters/{id}` continua aceitando `armor_class` manual, para casos que o cálculo automático não cobre (armadura mágica com bônus, feature que altera CA)
  - [x] Testes: equipar armadura leve/média/pesada recalcula CA corretamente (limite de mod DEX por tipo), equipar escudo soma bônus, desequipar volta pro cálculo sem o item, override manual via `PATCH /characters/{id}` continua funcionando até o próximo toggle de equipamento
  - Notas: lacuna mecânica encontrada e resolvida inline — `ArmorDetail` (catálogo) não guardava o peso da armadura (leve/média/pesada/escudo) que `calculate_ac` precisa; o SRD já carrega isso (`armor_category`: Light/Medium/Heavy/Shield em `5e-SRD-Equipment.json`), só não era persistido. Adicionado `ArmorDetail.armor_category` (migração + `backfill_armor_categories`, idempotente por `Item.index`, mesmo padrão das outras lacunas da Fase 8 — sem reseed, ids preservados). Recalculo acontece em `add_equipment`/`update_equipment`/`remove_equipment` (não só no toggle citado no backlog) — adicionar um item já `equipped=true` ou remover um item equipado também precisam manter a CA consistente, senão ela ficaria desatualizada nesses dois casos. Múltiplas peças de armadura corporal equipadas ao mesmo tempo (estado não previsto pelo PHB) não é validado/bloqueado — o cálculo só usa a primeira encontrada; escudos múltiplos somam todos.

- **Como QA, quero confirmar que o ataque/dano com arma equipada em combate usa os bônus certos e só rola dano após o acerto ser confirmado. ✅ (2026-08-25)**
  - [x] Auditoria de `declare_action` (`attack_weapon`, Fase 6): confirmar resolução do bônus de ataque/dano a partir da arma `equipped=true` do personagem (proficiência + mod de habilidade correto, incluindo finesse) e que o dano só é rolado/aplicado após o acerto ser confirmado
  - [x] Testes de regressão: trocar a arma equipada em combate e atacar de novo usa os bônus da nova arma; arma sem proficiência aplica só o mod de habilidade (sem bônus de proficiência)
  - Notas: **a auditoria encontrou o caso não coberto que a própria nota previa** — decisão tomada com o usuário em sessão (implementar proficiência real de armas em vez de ajustar o teste pra simplificação existente). O código da Fase 6 somava o bônus de proficiência incondicionalmente (`attack_bonus = ability_mod + proficiency_bonus`, sempre), documentado como simplificação deliberada ("this app doesn't model per-category weapon proficiency"); dano só é rolado dentro do `if hit:` — essa parte já estava correta, confirmado sem mudança. Implementada proficiência de fato: `WeaponDetail` ganha `weapon_category` (simple/martial — mesma lacuna do `ArmorDetail.armor_category` da história anterior, também não persistido embora o SRD já carregue `weapon_category`; migração + `backfill_weapon_categories`, idempotente por `Item.index`). `CombatService._is_weapon_proficient` cruza as classes do personagem com `Proficiency`/`ProficiencyClass`: categoria ampla (`simple-weapons`/`martial-weapons`, via `EquipmentCategory`) cobre a maioria; proficiências de arma específica (ex. Rogue com "Longswords", Wizard com "Daggers") usam `proficiency_type=other` no catálogo (sem FK estruturada pro item) — resolvidas comparando tokens do índice (`"hand-crossbows"` vs item `"crossbow-hand"`, ordem de palavra diferente) via `_weapon_name_tokens`, sem tabela nova. Fora de escopo (não testado/coberto): proficiência de armadura/ferramenta/instrumento — a auditoria e a mudança se limitaram a ataque com arma, que é o que a história pediu.

**Lacunas descobertas na Fase 8 — resolvidas.**

- [x] Escolhas de nível com seleção múltipla (Eldritch Invocations, Metamagic) e escolhas específicas de subclasse (ex. Circle of the Land) agora são detectadas por `POST /characters/{id}/level-up`. ✅ (2026-08-25)
  - Notas: **decisão tomada com o usuário em sessão** (resolver agora, escopo completo). `CharacterFeatureChoice` teve sua unique constraint relaxada de `(character_id, feature_id)` pra `(character_id, feature_id, feature_option_id)` — um personagem pode ter várias escolhas para a mesma feature (migração `54374794b595`). `_apply_feature_choices` agora também inspeciona a progressão da *subclasse* do personagem no mesmo nível (não só a base), cobrindo Circle of the Land. Contagem de escolhas exigidas: `_MULTI_CHOICE_RESOURCE_KEYS` mapeia `Feature.index` → `ClassLevelResource.resource_key` cujo total "conhecido" (`invocations_known`/`metamagic_known`) já existia no catálogo; o delta entre o nível novo e o anterior é quantas escolhas novas são exigidas. Gap de dados descoberto e corrigido: `metamagic-2`/`metamagic-3` (níveis 10/17) concedem mais escolhas mas não listam opções próprias no SRD — as 8 opções de Metamagic só existem sob `metamagic-1` (nível 3); `_MULTI_CHOICE_OPTIONS_SOURCE` redireciona pra lá. Também corrigido en passant: `metamagic-twinned-spell` é a única das 8 opções de Metamagic sem `parent` no SRD (as outras 7 têm) — adicionado a `_FEATURE_PARENT_OVERRIDES` (renomeado de `_CHANNEL_DIVINITY_PARENT_OVERRIDES`, já que passou a cobrir mais de um caso). Repick da mesma opção (na mesma requisição ou reaproveitando uma já escolhida em nível anterior) é rejeitado com 422. Testes cobrem: contagem exigida (1 pick não basta quando são 2), múltiplas escolhas persistidas, pick duplicado rejeitado, e a escolha de subclasse (Circle of the Land) exigida/persistida.

---
