# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), e este
projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/) para os
lançamentos oficiais (`release` → `main`), conforme definido em `CLAUDE.md`.

## [Unreleased]

### Added
- Endpoint `GET /auth/me`, retornando o perfil (email, username) do usuário
  autenticado — lacuna identificada pelo frontend, já que o token de acesso
  só carrega o id do usuário.
- Fundação do frontend (Fase 0): projeto Next.js inicializado (App Router,
  TypeScript strict, Tailwind, shadcn-ready), providers (`QueryProvider`,
  `ThemeProvider`) com tema deep navy + gold e DM Sans/Space Mono, landing
  page, cliente de API client-side e server-side com refresh automático de
  token, proteção de rotas via middleware, telas de login/registro, seletor
  de locale do catálogo com invalidação de cache do TanStack Query, e tipos
  TypeScript espelhando os schemas Pydantic do backend (campanhas,
  personagens, catálogo, sessões, e provisórios para combate/world/handouts/
  inventário, que ainda não têm domínio no backend).
- Catálogo SRD 2014 implementado no backend: fundação i18n/custom-scope e
  vocabulário fixo, proficiências (com concessões de classe/raça), raças,
  classes com progressão/features/subclasses, magias, equipamento,
  itens mágicos com variantes, backgrounds, feats, monstros/stat blocks e
  regras de referência, com seed completo em inglês e tradução parcial
  pt-BR.
- Task `test-cov` (via `pytest-cov`) para gerar relatório de cobertura de
  testes em HTML.
- Criação de campanha com o usuário autenticado atribuído automaticamente
  como mestre (DM).
- Geração e resgate de convite de campanha, permitindo que jogadores
  ingressem em uma campanha existente.
- Listagem das campanhas às quais o usuário autenticado pertence.
- Criação de ficha de personagem com validação de referências ao catálogo.
- Modificadores de habilidade e bônus de perícia calculados, expostos na
  ficha de personagem.
- Suporte a multiclasse, com validação de pré-requisitos de atributo por
  classe.
- Sessões de jogo com numeração sequencial por campanha e notas privadas
  do mestre.
- Modelagem completa do catálogo SRD 2014 no PRD do backend (seção 7.4):
  expandido de 4 para as 24 categorias (vocabulário fixo, raças, classes e
  progressão, magias, equipamento e itens mágicos, backgrounds e feats,
  monstros/stat blocks, regras), com padrão relacional de i18n (`_i18n`)
  e regra de conteúdo homebrew sempre preso à campanha.
- `docs/anahita-backend-backlog.md` e `docs/anahita-frontend-backlog.md`:
  backlogs com histórias de usuário em checklist, organizados por fase,
  pensados para retomada entre sessões de desenvolvimento.

### Changed
- PRD do frontend atualizado para acompanhar o catálogo expandido: seletor
  de locale para o conteúdo do catálogo, telas de navegação e criação de
  conteúdo homebrew, wizard de criação de personagem e seleção de monstro
  no combat tracker.

### Fixed
- Testes de autenticação (`tests/auth/test_service.py`) falhavam com
  `greenlet library is required` por falta da extra `asyncio` na dependência
  do SQLAlchemy.
- Chave secreta JWT padrão abaixo do mínimo recomendado, disparando
  `InsecureKeyLengthWarning` do PyJWT.

### Changed
- Padrão `__pycache__` no `.gitignore` ampliado para também casar arquivos,
  não só diretórios.

### Added
- Skills do Claude Code (`commit`, `merge-request`) para padronizar commits
  semânticos e o fluxo de merge request do projeto.

### Added
- Frontend Fase 1 (Campanhas, Personagens, Catálogo): lista/criação de
  campanhas, dashboard, convite/ingresso, shell de campanha (sidebar/
  header/mobile-nav), configurações com lista de membros e geração de
  convite; navegação e busca no catálogo (9 categorias) com detalhe e
  stat block de monstro, criação de homebrew (DM only); wizard de criação
  de personagem guiado pelo catálogo da campanha e ficha de personagem com
  edição inline de PV (mutação otimista); espelho client-side das fórmulas
  da rules engine (`lib/utils/dnd-rules.ts`).
- `GET /campaigns/{id}` (detalhe) e `GET /campaigns/{id}/members` (lista de
  membros), visíveis a qualquer membro da campanha.
- `GET /characters?campaign_id=` (lista de personagens de uma campanha) e
  `PATCH /characters/{id}` (atualização de PV atual/PV temporário/CA/
  inspiration, restrita ao dono da ficha).
- Criação de conteúdo homebrew no catálogo (`POST /catalog/{races,classes,
  spells,items,monsters}`), sempre presa a uma campanha e restrita ao
  mestre; `GET /catalog/{category}` ganhou o parâmetro `campaign_id` para
  escopar a listagem de homebrew à própria campanha (antes vazava homebrew
  de outras campanhas quando `include_custom` estava ativo).

### Added
- `PATCH /campaigns/{id}` (editar nome/descrição/cenário, só o mestre) e
  formulário de edição correspondente em `settings/page.tsx`.
- `GET /auth/users?ids=`, resolvendo perfil público em lote a partir de uma
  lista de ids; a lista de membros da campanha agora mostra o username em
  vez do UUID cru.
- Criação de homebrew para as 4 categorias de catálogo restantes
  (`POST /catalog/{magic-items,backgrounds,feats,rules}`), completando as 9
  categorias com tela dedicada; `GET /catalog/rules` também ganhou o
  parâmetro `campaign_id` para escopar homebrew (único que ainda faltava).
- `POST /characters/{id}/{spells,equipment,features}`, permitindo registrar
  magias conhecidas/preparadas, itens do inventário pessoal e
  características de classe/talento na ficha; a ficha de personagem no
  frontend ganhou as seções correspondentes (antes "em breve").

### Added
- Fase 2 do backend (Sessão ao Vivo), história 1: domínio de combate —
  `Encounter`, `EncounterParticipant`, `EncounterCondition`, `CombatLog`
  (PRD §7.6). CRUD REST fora do fluxo de turno: criar/listar encontros de
  uma sessão, iniciar um encontro (`preparing` → `active`), adicionar/
  atualizar/remover participantes — tudo restrito ao mestre da campanha,
  leitura liberada para qualquer membro. Um participante é PC **ou** NPC,
  nunca ambos, validado em `app/combat/domain.py`.

### Added
- Fase 2 do backend, história 2: combate em tempo real via WebSocket
  (`/ws/combat/{encounter_id}`, PRD §10). Protocolo de envelope
  `{"event_type", "payload"}`; mestre avança turno, aplica dano/cura/
  condição e encerra o combate, tudo transmitido a todos os conectados;
  jogadores só recebem, comandos deles são rejeitados com um evento
  `error`. Reconexão sempre recebe um `state_sync` completo (Postgres
  como fonte de verdade, nunca o WebSocket).

### Added
- Fase 2 do backend, história 3: condições de um participante de combate
  agora resolvem seus efeitos mecânicos (`engine/conditions.py`) a cada
  leitura — um personagem cego, por exemplo, mostra `attack_disadvantage`,
  `attacks_against_advantage` e `auto_fail_save` na ficha do participante.

### Added
- Fase 2 do backend, história 4 (última da fase — Sessão ao Vivo completa):
  log de combate (`GET /encounters/{id}/log`) registrando participante
  entrou/saiu, dano/cura, condição ganha/perdida, avanço de turno e fim de
  encontro, em ordem cronológica. A entrada de log sobrevive à remoção do
  participante que referenciava (`ON DELETE SET NULL`).

### Added
- Fase 2 do frontend (Sessão ao Vivo), história 1: gestão de sessões de
  jogo e suas notas — lista e criação de sessões (mestre), notas por
  sessão com marcação de privada restrita ao mestre (a filtragem em si já
  era feita pelo backend).
- Fase 2 do frontend, história 2: combat tracker mobile-first em tempo
  real via WebSocket (`/ws/combat/{encounter_id}`) — reconexão automática
  com backoff exponencial, resincronização via `state_sync`, iniciativa
  ordenada com destaque do turno atual, barra de PV/CA/condições por
  participante. Ponto de entrada para criar/iniciar um encontro adicionado
  à tela de sessão.
- Fase 2 do frontend, história 3: ações rápidas de dano/cura (presets de
  um toque + valor customizado) e toggle de condição por participante,
  botão fixo de avançar turno, e formulário de adicionar participante com
  busca no catálogo de monstros (autocompleta PV/CA/nome) ou preenchimento
  manual para NPCs sem stat block.
- Fase 2 do frontend, história 4 (última da fase — Sessão ao Vivo
  completa): visão do jogador no combat tracker, sem nenhum controle de
  ação do mestre, atualizada em tempo real pelo mesmo WebSocket.

### Fixed
- `docker compose`: porta 8000 do backend não era publicada para o host —
  o frontend rodando fora do Docker (`npm run dev`) não conseguia
  alcançar a API, quebrando registro e login com um erro genérico de rede.
- `lib/api/campaigns.ts` importava `serverApiFetch` (marcado `server-only`)
  numa função nunca usada (`listCampaignsServer`); como esse arquivo é
  importado por `hooks/use-campaign.ts`, usado em Client Components por
  toda a aplicação, o import vazava para o bundle do cliente e quebrava
  qualquer tela de campanha com o erro "You're importing a component that
  needs server-only". Função morta removida.
- ESLint passou a ignorar `next-env.d.ts` (arquivo auto-gerado pelo Next a
  cada `dev`/`build`, nunca editado à mão), que estava quebrando o lint
  sempre que alguém rodava o servidor de desenvolvimento localmente.

### Added
- Fase 3 do backend, história 1: NPCs com stat block opcional referenciando
  o catálogo de monstros (SRD ou homebrew da própria campanha), locais e
  facções com CRUD básico (mestre cria, qualquer membro lista).
- Fase 3 do backend, história 2: locais organizáveis em hierarquia (região
  → cidade → taverna), com árvore por campanha e prevenção de ciclo ao
  reatribuir o local pai.
- Fase 3 do backend, história 3: NPCs relacionáveis a facções (com papel),
  locais (residente/frequentador/controlador) e sessões (nota de
  aparição), locais relacionáveis a sessões (nota de visita), e relações
  entre facções (aliada, hostil, neutra, vassala, parceira comercial).
- Fase 3 do backend, história 4 (última da fase — World-building
  completo): busca por nome/descrição cross-entidade em NPCs, locais e
  facções de uma campanha, via busca textual do Postgres.
- Fase 3 do frontend, história 1: hub de World com seções de NPCs, locais e
  facções — cadastro de NPC (com busca/seleção de stat block no catálogo de
  monstros), árvore expansível de locais (região → cidade → taverna) e
  lista de facções com suas relações.
- Fase 3 do frontend, história 2 (última da fase — World-building
  completo): busca por nome/descrição combinando NPCs, locais e facções no
  hub de World, com resultados linkando direto para a entidade encontrada.
  Vínculo de NPCs e locais a aparições/visitas de sessão pela UI, e páginas
  de detalhe dedicadas para NPC, local e facção (com sublocais, papéis em
  facções, presença em locais e relações entre facções).
- Fase 4 do backend, história 1: handouts (texto, imagem ou mapa) criados
  pelo mestre com upload de arquivo, visíveis para jogadores só depois de
  revelados.
- Fase 4 do backend, história 2: revelação de handout em tempo real,
  transmitida para jogadores conectados via o WebSocket de combate já
  existente.
- Fase 4 do backend, história 3: inventário compartilhado da campanha,
  gerenciado pelo mestre e visível para todo o grupo.
- Fase 4 do backend, história 4 (última da fase — Loot, Inventário e
  Handouts completo): distribuição de loot após um combate — item do
  catálogo, item mágico ou nome livre, com ou sem moeda — reivindicável
  pelo jogador dono do personagem ou pelo mestre.
- Fase 4 do frontend, história 1 (última da fase — Loot, Inventário e
  Handouts completo): tela de inventário compartilhado da campanha, com
  gestão pelo mestre e reivindicação de loot pelo jogador; tela de
  handouts com criação (texto, imagem ou mapa), revelação pelo mestre e
  atualização em tempo real para os jogadores conectados.
- Fase 5 do backend, história 1: diário privado da campanha, exclusivo do
  mestre e nunca visível a jogadores, com vínculo opcional a uma sessão.
- Fase 5 do backend, história 2: confirmação de que a listagem de sessões
  já expõe o resumo de cada sessão a todo o grupo, base para o recap
  ("a história até agora") do frontend.
- Fase 5 do backend, história 3: timeline híbrida da campanha, combinando
  entradas automáticas geradas a partir do resumo de cada sessão com
  marcos manuais que o mestre adiciona e ordena livremente.
- Fase 5 do backend, história 4 (última da fase — Registro e Lore
  completo): páginas de wiki com lore livre em markdown, escritas pelo
  mestre e visíveis a todo o grupo, linkáveis a NPCs, locais e facções já
  cadastrados, e incluídas na busca cross-entidade da campanha.
- Fase 5 do frontend, história 1: tela de diário privado do mestre, com
  item de menu que só aparece para quem é mestre da campanha.
- Fase 5 do frontend, história 2: tela de recap listando o resumo de cada
  sessão em ordem cronológica, pulando sessões sem resumo ainda.
- Fase 5 do frontend, história 3: tela de timeline combinando entradas
  automáticas (resumo de cada sessão) com marcos manuais que o mestre cria
  e ordena.
- Fase 5 do frontend, história 4 (última da fase — Registro e Lore
  completo): telas de wiki da campanha, com criação e edição pelo mestre
  em markdown, ligação a NPCs/locais/facções existentes navegando direto
  para a tela do World correspondente, e páginas de wiki entrando na busca
  do hub de World.
