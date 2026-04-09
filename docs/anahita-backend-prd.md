# Anahita — Backend PRD

## Product Requirements Document | Backend

**Versão:** 1.1
**Data:** 2026-04-08
**Autor:** Felipe Braga

---

## 1. Visão Geral

Anahita é uma plataforma multi-mesa para gerenciamento de campanhas de D&D 5e. Permite que múltiplos Dungeon Masters gerenciem campanhas independentes, com jogadores participando de várias mesas simultaneamente.

### 1.1 Princípio Central

> Não atrapalhar o fluxo da sessão. Tudo que o DM usa durante o jogo precisa ser rápido, com poucos cliques e feedback instantâneo.

### 1.2 Prioridade de Experiência

1. **Rapidez durante a sessão** — combat tracker, quick notes
2. **Preparação pré-sessão** — world-building, plot planning
3. **Compartilhamento com jogadores** — handouts, fichas
4. **Registro pós-sessão** — diário, recap, lore

---

## 2. Stack Tecnológico

| Camada        | Tecnologia                              |
|---------------|----------------------------------------|
| Framework     | Python + FastAPI                       |
| ORM           | SQLAlchemy (async)                     |
| Migrations    | Alembic                               |
| Banco         | PostgreSQL (self-hosted, Docker)       |
| Validação     | Pydantic                              |
| Real-time     | WebSockets nativos (FastAPI/Starlette) |
| Auth          | Própria, strategy pattern extensível   |
| File Storage  | Local (filesystem), extensível p/ S3   |
| Infra         | Docker Compose                         |

### 2.1 Decisões Técnicas Fundamentais

- **Sem Redis.** Combate em turnos é inerentemente síncrono. Postgres é a fonte de verdade para estado de combate. Se o servidor cair, o estado está salvo.
- **Sem JSONB.** Todo o modelo é relacional. Garante portabilidade de banco (SQLite para testes), integridade referencial via FKs e queries previsíveis.
- **Tabelas de junção explícitas** para relacionamentos de world-building. Mais tabelas, mas com FKs reais e sem polimorfismo genérico.
- **Rules engine desacoplada.** Módulo Python puro, sem dependência de FastAPI ou SQLAlchemy. Testável com pytest puro.
- **Storage abstrato.** Interface única para armazenamento de arquivos. Implementação local (filesystem) agora, object storage (S3/R2/B2) no futuro. Arquivos nunca são armazenados no banco — o banco guarda apenas o `storage_key` (string de referência).
- **Sem vendor lock-in.** Nenhuma dependência de serviços gerenciados específicos (Supabase, Vercel, etc.). Tudo roda em Docker Compose numa VPS.

---

## 3. Modelo de Usuários e Acesso

Hierarquia: **User → Campaign (ownership) → CampaignMember (role-based)**.

- Um User pode ser DM em algumas campanhas e jogador em outras.
- O papel (role) é **por campanha**, não global.
- O DM da campanha é o admin daquele espaço: controla visibilidade (notas privadas vs. handouts públicos).
- O token JWT carrega `user_id` mas **não** o role — o role é resolvido no middleware via par `(user_id, campaign_id)` consultando a tabela de memberships.

---

## 4. Autenticação

Sistema próprio, extensível via **strategy pattern**.

### 4.1 Arquitetura

- **AuthStrategy (ABC):** define `authenticate`, `get_current_user`, `refresh_token`.
- **Implementação inicial:** email + senha com JWT.
  - Access token curto + refresh token longo em httpOnly cookie.
  - Refresh token armazenado encriptado no banco.
- **Router de auth desacoplado:** não conhece a estratégia concreta, recebe via dependency injection.

### 4.2 Extensibilidade

- **AuthProvider (tabela):** vincula múltiplos providers a um User (`provider_type`: local, discord, google).
- Para adicionar OAuth2 (ex: Discord), basta registrar uma nova strategy sem tocar nos endpoints.

---

## 5. Armazenamento de Arquivos

### 5.1 Princípio

Arquivos binários (imagens, mapas, tokens) **nunca são armazenados no banco de dados**. O banco guarda apenas um `storage_key` — uma string de referência como `"handouts/campaign_abc/map_01.png"`. O arquivo binário vive no storage.

### 5.2 Interface StorageService

ABC com três métodos:

- `upload(key: str, data: bytes, content_type: str) → str` — grava o arquivo, retorna o key.
- `get_url(key: str) → str` — resolve o key para URL acessível.
- `delete(key: str) → None` — remove o arquivo.

### 5.3 Implementação Local (atual)

**LocalStorageService** salva arquivos em `/data/uploads/{storage_key}`. O Nginx serve diretamente esse diretório como static files em `/files/*` — o request não passa pelo Python.

Organização dos keys por campanha:

```
/data/uploads/
├── handouts/
│   └── {campaign_id}/
│       ├── map_01.png
│       └── letter_from_king.jpg
└── tokens/
    └── {campaign_id}/
        ├── goblin.png
        └── dragon.png
```

### 5.4 Migração Futura (S3/R2/B2)

Criar **S3StorageService** que implementa a mesma interface. Troca via config (variável de ambiente). O `storage_key` no banco permanece idêntico. Nenhum model, schema ou service muda.

---

## 6. Fases de Entrega

### Fase 1 — Fundação

Fichas de personagem, modelo de campanha, convite de jogadores, gestão básica de sessões com notas. Entrega uma ferramenta usável para o DM organizar a mesa.

### Fase 2 — Sessão ao Vivo

Combat tracker (iniciativa, HP, condições, turnos) e quick notes durante a sessão. Design mobile-first para uso na mesa. WebSocket para estado em tempo real.

### Fase 3 — World-building

Locais, NPCs, facções, relacionamentos entre entidades, links com sessões. Mapas como upload de imagens com pins clicáveis. Full-text search via `tsvector` do Postgres.

### Fase 4 — Loot, Inventário e Compartilhamento

Inventário do grupo, distribuição de loot pós-combate, sistema de handouts (conteúdo liberado pelo DM para jogadores).

### Fase 5 — Registro e Lore

Diário de campanha, recaps, timeline de eventos, wiki da campanha. Potencial uso de IA para gerar resumos a partir das notas do DM.

---

## 7. Modelo de Dados

~32 tabelas, organizadas por domínio. Todas relacionais, sem JSONB.

### 7.1 Auth & Users

**User**

| Coluna          | Tipo      | Notas                |
|-----------------|-----------|----------------------|
| id              | UUID (PK) |                      |
| email           | String    | unique               |
| username        | String    | unique               |
| hashed_password | String    |                      |
| created_at      | Timestamp |                      |
| updated_at      | Timestamp |                      |

**AuthProvider**

| Coluna           | Tipo      | Notas                      |
|------------------|-----------|----------------------------|
| id               | UUID (PK) |                            |
| user_id          | FK User   |                            |
| provider_type    | Enum      | local, discord, google     |
| provider_user_id | String    | ID externo do provider     |
| created_at       | Timestamp |                            |

### 7.2 Campaigns & Membership

**Campaign**

| Coluna      | Tipo      | Notas                          |
|-------------|-----------|--------------------------------|
| id          | UUID (PK) |                                |
| name        | String    |                                |
| description | Text      |                                |
| setting     | String    | nullable                       |
| owner_id    | FK User   |                                |
| status      | Enum      | active, paused, archived       |
| created_at  | Timestamp |                                |

**CampaignMember**

| Coluna      | Tipo      | Notas                               |
|-------------|-----------|--------------------------------------|
| id          | UUID (PK) |                                      |
| campaign_id | FK        |                                      |
| user_id     | FK User   |                                      |
| role        | Enum      | dm, player                           |
| joined_at   | Timestamp |                                      |

Constraint: unique `(campaign_id, user_id)`.

**CampaignInvite**

| Coluna      | Tipo      | Notas                    |
|-------------|-----------|--------------------------|
| id          | UUID (PK) |                          |
| campaign_id | FK        |                          |
| invite_code | String    | unique                   |
| role        | Enum      | dm, player               |
| expires_at  | Timestamp |                          |
| used_by     | FK User   | nullable                 |

### 7.3 Characters

**Character**

| Coluna              | Tipo      | Notas              |
|---------------------|-----------|---------------------|
| id                  | UUID (PK) |                     |
| campaign_member_id  | FK        |                     |
| name                | String    |                     |
| race_id             | FK Race   |                     |
| subrace_id          | FK        | nullable            |
| level               | Integer   |                     |
| experience_points   | Integer   |                     |
| alignment           | String    |                     |
| background          | String    |                     |
| hit_point_max       | Integer   |                     |
| hit_point_current   | Integer   |                     |
| temporary_hit_points| Integer   |                     |
| armor_class         | Integer   |                     |
| speed               | Integer   |                     |
| inspiration         | Boolean   |                     |
| proficiency_bonus   | Integer   |                     |
| created_at          | Timestamp |                     |

**CharacterAbilityScore**

| Coluna       | Tipo      | Notas                                      |
|--------------|-----------|---------------------------------------------|
| id           | UUID (PK) |                                             |
| character_id | FK        |                                             |
| ability      | Enum      | str, dex, con, int, wis, cha               |
| base_score   | Integer   |                                             |
| asi_bonus    | Integer   |                                             |
| misc_bonus   | Integer   |                                             |

Uma linha por ability, seis por personagem. Modifiers calculados pela rules engine.

**CharacterSkill**

| Coluna       | Tipo      | Notas                                        |
|--------------|-----------|-----------------------------------------------|
| id           | UUID (PK) |                                               |
| character_id | FK        |                                               |
| skill        | Enum      | acrobatics, animal_handling... (18 skills)    |
| proficient   | Boolean   |                                               |
| expertise    | Boolean   |                                               |

Bônus calculado pela engine (ability modifier + proficiency).

**CharacterClass**

| Coluna              | Tipo      | Notas                                 |
|---------------------|-----------|---------------------------------------|
| id                  | UUID (PK) |                                       |
| character_id        | FK        |                                       |
| class_definition_id | FK        |                                       |
| subclass_id         | FK        | nullable                              |
| level               | Integer   |                                       |

Tabela separada para suportar multiclass.

**CharacterFeature**

| Coluna         | Tipo      | Notas                                    |
|----------------|-----------|-------------------------------------------|
| id             | UUID (PK) |                                           |
| character_id   | FK        |                                           |
| source_type    | Enum      | class, feat                               |
| source_name    | String    |                                           |
| feature_name   | String    |                                           |
| description    | Text      |                                           |
| level_acquired | Integer   |                                           |

Features raciais vêm do catálogo Race/RaceTrait. CharacterFeature armazena apenas features de classe e feats.

**CharacterRaceChoice**

| Coluna        | Tipo      | Notas                                       |
|---------------|-----------|----------------------------------------------|
| id            | UUID (PK) |                                              |
| character_id  | FK        |                                              |
| race_trait_id | FK        |                                              |
| chosen_value  | String    | ex: cantrip escolhido pelo High Elf          |

**CharacterSpell**

| Coluna       | Tipo      | Notas                  |
|--------------|-----------|-------------------------|
| id           | UUID (PK) |                         |
| character_id | FK        |                         |
| spell_id     | FK Spell  |                         |
| prepared     | Boolean   |                         |
| source_class | String    |                         |

**CharacterEquipment**

| Coluna       | Tipo      | Notas        |
|--------------|-----------|---------------|
| id           | UUID (PK) |               |
| character_id | FK        |               |
| item_id      | FK Item   |               |
| equipped     | Boolean   |               |
| quantity     | Integer   |               |
| attunement   | Boolean   |               |

### 7.4 Catálogos de Referência (D&D 5e SRD)

Pré-populados via seeds. Flag `is_custom` para homebrews vinculados a uma campanha.

**Race**

| Coluna          | Tipo      | Notas                        |
|-----------------|-----------|-------------------------------|
| id              | UUID (PK) |                               |
| name            | String    |                               |
| speed           | Integer   |                               |
| size            | Enum      | small, medium                 |
| darkvision_range| Integer   | 0 se não tem                  |
| description     | Text      |                               |
| is_custom       | Boolean   | default false                 |
| campaign_id     | FK        | nullable (null = SRD)         |
| created_by_id   | FK User   | nullable                      |

**RaceTrait**

| Coluna            | Tipo      | Notas                                            |
|-------------------|-----------|---------------------------------------------------|
| id                | UUID (PK) |                                                   |
| race_id           | FK Race   |                                                   |
| trait_name        | String    |                                                   |
| description       | Text      |                                                   |
| mechanical_effect | String    | vocabulário estruturado (resistance:fire, etc.)   |

**Subrace**

| Coluna      | Tipo      | Notas    |
|-------------|-----------|----------|
| id          | UUID (PK) |          |
| race_id     | FK Race   |          |
| name        | String    |          |
| description | Text      |          |

**SubraceTrait**

| Coluna            | Tipo      | Notas    |
|-------------------|-----------|----------|
| id                | UUID (PK) |          |
| subrace_id        | FK        |          |
| trait_name        | String    |          |
| description       | Text      |          |
| mechanical_effect | String    |          |

**RaceAbilityBonus**

| Coluna     | Tipo      | Notas                                             |
|------------|-----------|---------------------------------------------------|
| id         | UUID (PK) |                                                   |
| race_id    | FK        | nullable                                          |
| subrace_id | FK        | nullable                                          |
| ability    | Enum      | str, dex, con, int, wis, cha                      |
| bonus      | Integer   |                                                   |

Constraint: exatamente um dos dois FKs preenchido.

**ClassDefinition**

| Coluna                       | Tipo      | Notas                              |
|------------------------------|-----------|-------------------------------------|
| id                           | UUID (PK) |                                     |
| name                         | String    |                                     |
| hit_die                      | Integer   | 6, 8, 10, 12                       |
| primary_ability              | String    |                                     |
| saving_throw_proficiencies   | String    | par de abilities                    |
| is_custom                    | Boolean   | default false                       |
| created_by_id                | FK User   | nullable                           |
| campaign_id                  | FK        | nullable (null = SRD)              |

**ClassLevelFeature**

| Coluna              | Tipo      | Notas                              |
|---------------------|-----------|-------------------------------------|
| id                  | UUID (PK) |                                     |
| class_definition_id | FK        |                                     |
| level               | Integer   |                                     |
| feature_name        | String    |                                     |
| description         | Text      |                                     |
| mechanical_effect   | String    | vocabulário estruturado             |

**SubclassDefinition**

| Coluna              | Tipo      | Notas                    |
|---------------------|-----------|--------------------------|
| id                  | UUID (PK) |                          |
| class_definition_id | FK        |                          |
| name                | String    |                          |
| description         | Text      |                          |
| is_custom           | Boolean   |                          |
| created_by_id       | FK User   | nullable                 |
| campaign_id         | FK        | nullable                 |

**Spell**

| Coluna        | Tipo      | Notas        |
|---------------|-----------|---------------|
| id            | UUID (PK) |               |
| name          | String    |               |
| level         | Integer   | 0 = cantrip  |
| school        | String    |               |
| casting_time  | String    |               |
| range         | String    |               |
| duration      | String    |               |
| components    | String    |               |
| ritual        | Boolean   |               |
| concentration | Boolean   |               |
| description   | Text      |               |
| higher_levels | Text      | nullable      |

**Item**

| Coluna      | Tipo      | Notas                                            |
|-------------|-----------|---------------------------------------------------|
| id          | UUID (PK) |                                                   |
| name        | String    |                                                   |
| item_type   | Enum      | weapon, armor, gear, consumable, magic_item       |
| rarity      | String    | nullable                                          |
| weight      | Float     |                                                   |
| cost        | Integer   | em copper pieces                                  |
| description | Text      |                                                   |
| properties  | String    | nullable                                          |

**WeaponDetail**

| Coluna            | Tipo      | Notas        |
|-------------------|-----------|---------------|
| id                | UUID (PK) |               |
| item_id           | FK Item   |               |
| damage_dice       | String    | ex: 1d8       |
| damage_type       | String    |               |
| weapon_range      | String    |               |
| weapon_properties | String    |               |

**ArmorDetail**

| Coluna                | Tipo      | Notas    |
|-----------------------|-----------|----------|
| id                    | UUID (PK) |          |
| item_id               | FK Item   |          |
| base_ac               | Integer   |          |
| dex_bonus_cap         | Integer   | nullable |
| stealth_disadvantage  | Boolean   |          |
| strength_requirement  | Integer   | nullable |

### 7.5 Sessions

**Session**

| Coluna         | Tipo      | Notas                                   |
|----------------|-----------|------------------------------------------|
| id             | UUID (PK) |                                          |
| campaign_id    | FK        |                                          |
| session_number | Integer   |                                          |
| title          | String    |                                          |
| scheduled_date | Date      | nullable                                 |
| status         | Enum      | planned, in_progress, completed          |
| dm_notes       | Text      | privado                                  |
| summary        | Text      | público para jogadores                   |
| created_at     | Timestamp |                                          |

**SessionNote**

| Coluna     | Tipo      | Notas                                  |
|------------|-----------|----------------------------------------|
| id         | UUID (PK) |                                        |
| session_id | FK        |                                        |
| author_id  | FK User   |                                        |
| content    | Text      |                                        |
| is_private | Boolean   | true = só o DM vê                      |
| created_at | Timestamp |                                        |

### 7.6 Combat

**Encounter**

| Coluna             | Tipo      | Notas                                |
|--------------------|-----------|---------------------------------------|
| id                 | UUID (PK) |                                       |
| session_id         | FK        |                                       |
| name               | String    |                                       |
| status             | Enum      | preparing, active, completed          |
| current_round      | Integer   |                                       |
| current_turn_order | Integer   |                                       |
| created_at         | Timestamp |                                       |

**EncounterParticipant**

| Coluna               | Tipo      | Notas                                         |
|----------------------|-----------|------------------------------------------------|
| id                   | UUID (PK) |                                                |
| encounter_id         | FK        |                                                |
| character_id         | FK        | nullable (PCs)                                 |
| npc_id               | FK NPC    | nullable (monstros/NPCs)                       |
| name                 | String    | fallback para monstros genéricos               |
| initiative           | Integer   |                                                |
| hit_point_max        | Integer   |                                                |
| hit_point_current    | Integer   |                                                |
| temporary_hit_points | Integer   |                                                |
| armor_class          | Integer   |                                                |
| turn_order           | Integer   |                                                |
| is_active            | Boolean   | false = morto/fugitivo                         |

Regra: um participant é PC **ou** NPC, nunca ambos. Validado na camada de aplicação.

**EncounterCondition**

| Coluna           | Tipo      | Notas                                                 |
|------------------|-----------|--------------------------------------------------------|
| id               | UUID (PK) |                                                        |
| participant_id   | FK        |                                                        |
| condition        | Enum      | blinded, charmed, deafened... (15 condições do 5e)     |
| duration_rounds  | Integer   | nullable (null = indefinido)                           |
| applied_at_round | Integer   |                                                        |

**CombatLog**

| Coluna       | Tipo      | Notas                                                                |
|--------------|-----------|-----------------------------------------------------------------------|
| id           | UUID (PK) |                                                                       |
| encounter_id | FK        |                                                                       |
| round        | Integer   |                                                                       |
| turn_order   | Integer   |                                                                       |
| actor_id     | FK        | EncounterParticipant                                                  |
| action_type  | Enum      | attack, spell, move, dash, dodge, disengage, help, hide, ready, other |
| description  | Text      |                                                                       |
| damage_dealt | Integer   | nullable                                                              |
| damage_type  | String    | nullable                                                              |
| target_id    | FK        | nullable                                                              |
| created_at   | Timestamp |                                                                       |

### 7.7 World-building

**NPC**

| Coluna        | Tipo      | Notas                       |
|---------------|-----------|------------------------------|
| id            | UUID (PK) |                              |
| campaign_id   | FK        |                              |
| name          | String    |                              |
| race          | String    |                              |
| occupation    | String    | nullable                     |
| description   | Text      |                              |
| personality   | Text      | nullable                     |
| is_alive      | Boolean   |                              |
| stat_block_id | FK        | nullable (NPCs com stats)    |
| created_at    | Timestamp |                              |

**Location**

| Coluna             | Tipo      | Notas                                                   |
|--------------------|-----------|----------------------------------------------------------|
| id                 | UUID (PK) |                                                          |
| campaign_id        | FK        |                                                          |
| name               | String    |                                                          |
| location_type      | Enum      | city, town, dungeon, wilderness, building, region, plane |
| description        | Text      |                                                          |
| parent_location_id | FK self   | nullable — hierarquia (região → cidade → taverna)        |

**Faction**

| Coluna          | Tipo      | Notas    |
|-----------------|-----------|----------|
| id              | UUID (PK) |          |
| campaign_id     | FK        |          |
| name            | String    |          |
| description     | Text      |          |
| alignment       | String    | nullable |
| influence_level | String    | nullable |

**Tabelas de Junção (World-building)**

| Tabela                | FKs                          | Campos extras                                                            |
|-----------------------|------------------------------|--------------------------------------------------------------------------|
| NPCFaction            | npc_id, faction_id           | role_in_faction                                                          |
| NPCLocation           | npc_id, location_id          | presence_type (enum: resides, frequents, controls)                       |
| NPCSession            | npc_id, session_id           | appearance_note                                                          |
| LocationSession       | location_id, session_id      | visit_note                                                               |
| FactionRelationship   | faction_a_id, faction_b_id   | relationship_type (enum: allied, hostile, neutral, vassal, trade_partner) |

### 7.8 Handouts

**Handout**

| Coluna       | Tipo      | Notas                                     |
|--------------|-----------|-------------------------------------------|
| id           | UUID (PK) |                                           |
| campaign_id  | FK        |                                           |
| session_id   | FK        | nullable (pode ser geral da campanha)     |
| title        | String    |                                           |
| content      | Text      | nullable (texto do handout)               |
| handout_type | Enum      | text, image, map                          |
| storage_key  | String    | nullable (referência ao arquivo no storage)|
| is_revealed  | Boolean   | default false                             |
| revealed_at  | Timestamp | nullable                                  |
| created_at   | Timestamp |                                           |

O `storage_key` é uma referência abstrata (ex: `handouts/campaign_abc/map.png`). O StorageService resolve para URL ou path. Arquivos binários **nunca** são armazenados no banco.

### 7.9 Inventory

**PartyInventory**

| Coluna      | Tipo      | Notas    |
|-------------|-----------|----------|
| id          | UUID (PK) |          |
| campaign_id | FK        |          |
| item_id     | FK Item   |          |
| quantity    | Integer   |          |
| notes       | String    | nullable |

**LootDrop**

| Coluna           | Tipo      | Notas                          |
|------------------|-----------|--------------------------------|
| id               | UUID (PK) |                                |
| encounter_id     | FK        |                                |
| item_id          | FK        | nullable (itens custom)        |
| custom_item_name | String    | nullable                       |
| quantity         | Integer   |                                |
| currency_cp      | Integer   | tudo convertido pra copper     |
| claimed_by       | FK        | nullable (Character)           |

---

## 8. Rules Engine

Módulo Python puro. Sem imports de FastAPI, SQLAlchemy ou qualquer dependência de I/O. Recebe dataclasses, devolve resultados calculados.

### 8.1 Responsabilidades

| Área               | Descrição                                                                                        |
|--------------------|--------------------------------------------------------------------------------------------------|
| Ability Modifiers  | `(score - 10) // 2`                                                                              |
| Proficiency Bonus  | Baseado no level total do personagem                                                             |
| Skill Bonus        | ability modifier + proficiency (se proficiente) + expertise (se aplicável)                       |
| Armor Class        | Regras por tipo: light (DEX total), medium (DEX até +2), heavy (ignora DEX)                     |
| Hit Points         | Baseado em classe (hit die), level, CON modifier e bônus                                         |
| Attack/Save DC     | Attack roll bonus, spell save DC (8 + proficiency + ability mod)                                 |
| Condições          | Mapeia condições ativas para efeitos mecânicos (blinded → disadvantage em attacks, etc.)         |
| Validações         | Level up, requisitos de multiclass, spells preparadas, attunement slots                          |

### 8.2 Interface

Design funcional — funções puras:

```
calculate_modifier(score: int) → int
calculate_proficiency_bonus(total_level: int) → int
calculate_skill_bonus(ability_mod, proficient, expertise, prof_bonus) → int
calculate_ac(armor: ArmorData, dex_mod, shield, bonuses) → int
calculate_attack_bonus(ability_mod, prof_bonus, bonuses) → int
calculate_save_dc(ability_mod, prof_bonus) → int
get_condition_effects(conditions: list[Condition]) → list[MechanicalEffect]
validate_multiclass(current_classes, new_class, ability_scores) → ValidationResult
```

Tipos de entrada/saída definidos em `engine/types.py` como dataclasses puras.

### 8.3 Class Handlers

Registry de handlers por classe para regras específicas (Sneak Attack, Rage, Wild Shape, etc.).

**Interface ClassHandler:**

```
modify_ac(base_ac: int, context: CharacterContext) → int
modify_attack(base_bonus: int, context: AttackContext) → int
on_level_up(context: LevelUpContext) → LevelUpResult
get_class_resources(level: int) → list[ClassResource]
```

**Handlers do SRD:** classes Python registradas no startup.

**Classes customizadas:** `GenericClassHandler` lê `ClassDefinition` e `ClassLevelFeature` do banco e interpreta `mechanical_effect` via vocabulário declarativo.

**Vocabulário de efeitos mecânicos:**

```
extra_attack, spellcasting, resistance:{type}, bonus_ac:{formula},
proficiency:{skill_or_tool}, darkvision:{range}, speed_bonus:{value},
damage_bonus:{dice}, saving_throw_advantage:{condition}
```

**Resolução no registry:** consulta por `class_definition_id`. Se não encontra handler especializado, usa `GenericClassHandler`. Classes do SRD têm comportamento otimizado em código; classes custom funcionam via dados, sem deploy.

---

## 9. Estrutura do Projeto

```
anahita/
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py            # Settings via pydantic-settings
│   │   │   ├── database.py          # async engine, sessionmaker
│   │   │   ├── dependencies.py      # get_db, get_current_user
│   │   │   ├── security.py          # hashing, JWT encode/decode
│   │   │   └── storage/
│   │   │       ├── base.py          # StorageService ABC
│   │   │       ├── local.py         # LocalStorageService
│   │   │       └── s3.py            # futuro
│   │   ├── auth/
│   │   │   ├── models.py
│   │   │   ├── domain.py
│   │   │   ├── schemas.py
│   │   │   ├── strategies/
│   │   │   │   ├── base.py          # AuthStrategy ABC
│   │   │   │   ├── local.py         # email + senha
│   │   │   │   └── discord.py       # futuro
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── campaigns/
│   │   │   ├── models.py
│   │   │   ├── domain.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── characters/
│   │   │   ├── models.py
│   │   │   ├── domain.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── sessions/
│   │   │   ├── models.py
│   │   │   ├── domain.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── combat/
│   │   │   ├── models.py
│   │   │   ├── domain.py            # CombatState, lógica de turnos
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   ├── ws_manager.py        # WebSocket connection manager
│   │   │   ├── ws_router.py         # WebSocket endpoints
│   │   │   └── router.py            # REST endpoints
│   │   ├── world/
│   │   │   ├── models.py
│   │   │   ├── domain.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── handouts/
│   │   │   ├── models.py
│   │   │   ├── domain.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── inventory/
│   │   │   ├── models.py
│   │   │   ├── domain.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── catalog/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── queries/                  # Queries cross-domain e complexas
│   │   │   ├── world_queries.py
│   │   │   ├── combat_queries.py
│   │   │   └── ...
│   │   └── main.py
│   ├── engine/                        # Python puro, sem dependência de framework
│   │   ├── abilities.py
│   │   ├── armor_class.py
│   │   ├── combat.py
│   │   ├── conditions.py
│   │   ├── hit_points.py
│   │   ├── validation.py
│   │   ├── class_handlers/
│   │   │   ├── base.py               # ClassHandler ABC
│   │   │   ├── generic.py            # GenericClassHandler
│   │   │   ├── fighter.py
│   │   │   ├── wizard.py
│   │   │   └── ...
│   │   ├── types.py                  # dataclasses da engine
│   │   └── registry.py
│   ├── tests/
│   │   ├── engine/                   # testes puros, sem banco
│   │   ├── integration/              # testes com banco
│   │   └── conftest.py
│   ├── seeds/
│   │   ├── spells.py
│   │   ├── items.py
│   │   ├── races.py
│   │   └── classes.py
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   └── ...                           # Detalhado no PRD Frontend
├── docker-compose.yml
└── README.md
```

### 9.1 Convenções por Domínio

| Arquivo      | Responsabilidade                                      |
|-------------|-------------------------------------------------------|
| models.py   | SQLAlchemy models (persistência)                      |
| domain.py   | Objetos de domínio, lógica de negócio                 |
| schemas.py  | Pydantic DTOs (request/response da API)               |
| service.py  | Orquestração + queries simples (3-4 linhas)           |
| router.py   | Endpoints HTTP                                        |

Queries complexas ou cross-domain vão para `app/queries/`.

---

## 10. WebSocket — Combat Tracker e Handouts

### 10.1 Conexão

- Endpoint combat: `/ws/combat/{encounter_id}`
- Auth: token JWT como query param
- Validação: verifica membership na campanha
- `WSConnectionManager`: dict de `encounter_id → list[WebSocket]`

### 10.2 Protocolo de Mensagens — Combat

Envelope: `{ "event_type": "...", "payload": {...} }`

**Servidor → Clientes:**

| Evento                    | Descrição                                    |
|---------------------------|----------------------------------------------|
| state_sync                | Estado completo (conexão + após mudanças)    |
| turn_advanced             | Indica de quem é o turno atual               |
| participant_updated       | HP mudou, condição adicionada/removida       |
| encounter_status_changed  | Combate iniciou/encerrou                     |

**Cliente (DM apenas) → Servidor:**

| Evento              | Descrição                       |
|---------------------|---------------------------------|
| advance_turn        | Próximo turno                   |
| update_participant  | Dano, cura, condição            |
| add_participant     | Monstro entra no combate        |
| remove_participant  | Retira participante             |
| end_encounter       | Encerra o combate               |

### 10.3 Handout Reveal via WebSocket

Durante a sessão (WebSocket de combat ativo), o DM pode revelar handouts. O evento `handout_revealed` é enviado via broadcast para jogadores conectados, com o payload contendo id, título, tipo e URL do conteúdo.

Fora da sessão, jogadores veem handouts revelados normalmente via REST (filtro `is_revealed=true`).

### 10.4 Permissões

Apenas `role=dm` pode enviar comandos. Jogadores são read-only. Validação no servidor a cada mensagem.

### 10.5 Tolerância a Falhas

- Desconexão: reconecta e recebe `state_sync` completo.
- Fonte de verdade: Postgres, não WebSocket.
- Fallback: qualquer estado reconstituível via REST.

---

## 11. Deploy — Docker Compose

### 11.1 Topologia

```
┌─────────┐     ┌─────────┐     ┌──────────┐     ┌──────────┐
│  Nginx  │────▶│ Frontend│     │ Backend  │     │ Postgres │
│ :80/443 │────▶│ :3000   │     │ :8000    │     │ :5432    │
└─────────┘     └─────────┘     └──────────┘     └──────────┘
     │                                │                │
     │          /api/* ──────────────▶│                │
     │          /files/* ─▶ static    │───────────────▶│
     │          /* ──────▶ frontend   │
     │
     └── /data/uploads (read-only, serve static files)
```

### 11.2 Serviços

| Serviço   | Imagem                        | Notas                                        |
|-----------|-------------------------------|----------------------------------------------|
| nginx     | nginx:alpine                  | Reverse proxy, SSL (Let's Encrypt), static   |
| frontend  | Node.js (standalone output)   | `next build` + `next start`                  |
| backend   | Python (uvicorn)              | FastAPI                                       |
| postgres  | postgres:16-alpine            | Volume persistido                             |

### 11.3 Volumes

| Volume        | Montagem                               | Notas                              |
|---------------|----------------------------------------|------------------------------------|
| postgres_data | postgres:/var/lib/postgresql/data      | Dados do banco                     |
| upload_data   | backend:/data/uploads (rw)             | Escrita de arquivos                |
|               | nginx:/data/uploads (ro)               | Serve static files                 |

---

## 12. Glossário

| Termo            | Definição                                                                 |
|------------------|---------------------------------------------------------------------------|
| Campaign         | Uma campanha de D&D 5e com seu próprio mundo, jogadores e sessões        |
| DM               | Dungeon Master — administrador de uma campanha                           |
| Encounter        | Um combate dentro de uma sessão                                          |
| Handout          | Conteúdo (texto/imagem/mapa) revelado pelo DM para jogadores             |
| Membership       | Vínculo de um User com uma Campaign, incluindo role                      |
| Rules Engine     | Módulo Python puro que implementa as mecânicas do D&D 5e                 |
| SRD              | System Reference Document — conteúdo do D&D 5e de uso livre             |
| Seed             | Dados pré-populados do SRD (spells, items, races, classes)               |
| Class Handler    | Componente da engine que implementa regras específicas de uma classe     |
| Generic Handler  | Handler que interpreta classes customizadas via dados do banco           |
| Storage Key      | Referência abstrata a um arquivo no storage (nunca path absoluto)        |
| StorageService   | Interface abstrata para upload/download de arquivos                      |
