# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), e este
projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/) para os
lançamentos oficiais (`release` → `main`), conforme definido em `CLAUDE.md`.

## [Unreleased]

### Added
- Retrato do personagem no frontend (Fase 10): `lib/api/characters.ts`
  ganha `uploadCharacterPortrait`/`removeCharacterPortrait` (multipart,
  mesmo padrão de upload de Handouts), com os hooks
  `useUploadCharacterPortrait`/`useRemoveCharacterPortrait`. Novo
  `components/characters/character-avatar.tsx` (avatar circular,
  `border-radius: 50%`, placeholder de iniciais quando sem imagem —
  reaproveitável nos tokens do mapa da Fase 15) e
  `components/characters/character-portrait.tsx` (upload/troca/remoção),
  agora no cabeçalho de `character-sheet.tsx`. `Character.portrait_url`
  espelha o `CharacterRead.portrait_url` já resolvido pelo backend.
- Escolha de proficiências no frontend (Fase 10): novo
  `GET /characters/{id}/proficiencies` no backend (owner-only), retornando
  os grupos "escolha N de [...]" válidos da raça/classe do personagem —
  faltava uma forma de descobrir o conjunto válido antes de submeter ao
  `POST` já existente. `components/characters/proficiency-choices.tsx`
  substitui o campo livre por uma lista das opções realmente oferecidas,
  com perícias já escolhidas marcadas e não editáveis (o backend não
  permite desfazer uma escolha).
- Revelação de NPCs no frontend (Fase 13): `npc-card.tsx` ganha badge
  "Oculto"/"Revelado" e botão "Revelar" (ambos DM-only), consumindo o
  `POST /npcs/{id}/reveal` já existente no backend. A listagem de NPCs do
  jogador (`world/npcs/page.tsx`) já mostrava só NPCs revelados sem
  mudança adicional, já que `GET /campaigns/{id}/npcs` filtra
  server-side. Fecha a Fase 13 do frontend (Fluxo de Sessões).
- `CharacterPicker` no combate (Fase 13, frontend): novo
  `components/combat/character-picker.tsx`, ao lado do `MonsterPicker`
  existente, listando os personagens da campanha via `useCharacters` e
  autopreenchendo nome/PV máximo/CA a partir da ficha ao selecionar um. A
  página de combate ganha uma alternância "Monstro/NPC" / "Personagem" no
  painel de adicionar participante. Fecha a lacuna de seleção de alvo em
  combate identificada na Fase 9 — um encontro agora pode ter
  participantes-personagem, populando o dropdown de alvo do `ActionPicker`.
- Conclusão de sessão no frontend (Fase 13): `completeSession` em
  `lib/api/sessions.ts` (`POST /sessions/{id}/complete`) e o hook
  `useCompleteSession`; botão "Concluir sessão" na página de detalhe da
  sessão, visível pro DM quando `status === "in_progress"`.
- Edição do nome de sessão no frontend (Fase 13): `updateSession` em
  `lib/api/sessions.ts` (`PATCH /sessions/{id}`) e o hook
  `useUpdateSession`; título estático da página de detalhe da sessão
  trocado por um campo editável, visível só pro DM.
- Visibilidade de NPCs para o mestre (Fase 13): `NPC` ganha `is_revealed`
  (default `False`), seguindo o mesmo padrão de `Handout.is_revealed`.
  `GET /campaigns/{id}/npcs` filtra NPCs não revelados para não-DM (sem
  erro); novo endpoint `GET /npcs/{id}` retorna 404 para não-DM em NPC
  oculto, mesmo padrão de `HandoutService.get_handout`. Novo endpoint
  `POST /npcs/{id}/reveal`, DM-only.
- Validação de personagem duplicado em combate (Fase 13): `POST
  /encounters/{id}/participants` (`CombatService.add_participant`) agora
  rejeita (422) adicionar um `character_id` que já é participante do mesmo
  encontro. Confirmado ponta a ponta que a rota já aceitava `character_id`
  para adicionar jogadores (PCs) ao combate, não só monstros/NPCs — a
  lacuna real relatada era de frontend (falta um `CharacterPicker`),
  desbloqueando aquele trabalho.
- Endpoint `POST /sessions/{id}/complete` (Fase 13), DM-only, transicionando
  uma sessão `in_progress`→`completed`. Qualquer outra transição de origem
  (ex. `planned`→`completed` direto, pulando `open_session`) é rejeitada
  com 422, mantendo a máquina de estado previsível.
- Schema `SessionUpdate` + endpoint `PATCH /sessions/{id}` (Fase 13),
  DM-only, permitindo editar `title` e `scheduled_date` de uma sessão já
  criada — reaproveitável para corrigir a data de sessões criadas sem
  data (Fase 9).
- Profundidade de raça homebrew (Fase 11): `RaceCreate` estendido com
  `age`/`alignment_desc`/`size_description`/`language_desc` e listas
  estruturadas `language_ids`/`proficiency_ids` (validadas contra o
  catálogo, 422 se desconhecidas); nova junction `RaceLanguage` para
  idiomas concedidos por raça, espelhando `ProficiencyRace`. Endpoints
  `POST /catalog/races/{id}/ability-bonuses`, `/traits` e `/subraces`
  (este último aceitando bônus/traços de sub-raça aninhados no mesmo
  payload) — todos DM-only, restritos à raça homebrew da própria
  campanha do requisitante.
- Edição de informações do personagem no frontend (Fase 10): novo componente
  `character-info-editor.tsx` na ficha, permitindo editar nome, alinhamento,
  antecedente e atributos-base via `PATCH /characters/{id}`. Alterar um
  atributo-base exige confirmação (aviso de que CA/PV máximo/perícias podem
  mudar) antes de enviar; nome/alinhamento/antecedente enviam direto. Raça e
  classe seguem bloqueadas para edição (decisão do backend).
- Endpoint `PATCH /characters/{id}/sessions/order` (Fase 10), permitindo ao
  jogador reordenar pessoalmente a exibição das sessões na ficha do seu
  personagem, sem afetar `Session.session_number` (a ordem oficial/
  compartilhada) nem a visão de qualquer outro personagem/jogador/DM. Nova
  tabela de junção `character_session_orders` (`character_id`/`session_id`/
  `sort_order`); `GET /characters/{id}/sessions` passa a respeitar essa
  ordem pessoal quando existir, caindo para `session_number` como default
  caso contrário. Owner-only — nem o DM da campanha pode setá-la. Fecha as
  5 histórias da Fase 10 (backend).
- Endpoint `GET /characters/{id}/sessions` (Fase 10), listando as sessões em
  que um personagem participou de fato — derivado de participação em
  combate (`EncounterParticipant` → `Encounter` → `Session`), sem tabela ou
  lista explícita a manter em dia, ordenado por `session_number`. Mesmo
  guard de visibilidade de `GET /characters/{id}` (dono da ficha ou DM da
  campanha).
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
- Navegação da ficha de personagem (Fase 10, frontend): o cabeçalho da
  página de ficha ganha um dropdown "Sessões" isolado
  (`character-sessions-dropdown.tsx`, consumindo o novo
  `GET /characters/{id}/sessions`) com overflow interno para a lista de
  sessões do personagem, e um menu hambúrguer (`app-nav-menu.tsx`) que
  agrupa a navegação geral da campanha (hoje em `campaign-sidebar.tsx`)
  num painel overlay que fecha em Escape/clique fora, sem deslocar o
  conteúdo da ficha. Escopo limitado à página da ficha — o layout de
  campanha (`header.tsx`/`campaign-sidebar.tsx`/`mobile-nav.tsx`)
  continua servindo as demais páginas sem alteração.
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
- Criação de monstro homebrew (`POST /catalog/monsters`) com um `size`
  fora do vocabulário SRD (ex. um valor digitado errado) derrubava o
  servidor com erro 500 em vez de rejeitar com 422 — o campo agora é
  validado contra a lista de tamanhos válidos antes de tocar o banco
  (Fase 9).
- (Fase 9) Sessão criada pelo formulário rápido, sem data marcada, nunca
  aparecia no card "próxima sessão" do dashboard da campanha — agora ela
  aparece normalmente (atrás de qualquer sessão já datada). Também
  corrigido um caso em que uma sessão marcada para "hoje" podia não
  aparecer dependendo do fuso horário de quem a criou.
- (Fase 9) Criação de monstro homebrew no formulário do catálogo podia
  falhar com um erro genérico ao digitar um "Tamanho" inválido (ex. um
  valor fora do vocabulário SRD) — os campos de "Tamanho" (monstros),
  "Tipo" (equipamento) e "Escola" (magias) agora são seletores com as
  opções válidas, em vez de texto livre, e a mensagem de erro exibida
  reflete o motivo real retornado pela API em vez de um texto genérico.
- (Fase 9) Link para "Configurações" da campanha (editar nome, descrição e
  cenário) estava pouco visível na navegação, misturado sem destaque a
  outros 10 itens de conteúdo — agora aparece como uma ação exclusiva do
  mestre, separada visualmente das demais seções na barra lateral.

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
- Fase 6 do backend, história 1: gerenciamento de magias conhecidas e
  preparadas na ficha, organizadas por círculo, respeitando o limite de
  cada classe (fixo por nível, ou ability modifier + nível de conjurador).
- Fase 6 do backend, história 2: slots de magia por círculo, gastos ao
  conjurar (com ritual sem custo e conjuração em nível maior) e restaurados
  num descanso longo.
- Fase 6 do backend, história 3: edição e remoção de itens do inventário
  pessoal, e registro de ganho/gasto de moeda na ficha.
- Fase 6 do backend, história 4: abertura de sessão pelo mestre, início de
  combate populando automaticamente todos os personagens da campanha, e
  exigência de rolagem de iniciativa de todo participante antes do
  primeiro turno.
- Fase 6 do backend, história 5: declaração de ações de combate (ataque
  com arma, com magia, agarrar, empurrar) com resolução automática de
  acerto e dano/efeito no servidor, incluindo ataques de monstros do
  catálogo.
- Fase 6 do backend, história 6: toda rolagem do servidor (iniciativa,
  ataque, dano, teste oposto) é automática por padrão, com opção de
  digitar o resultado manualmente por rolagem.
- Fase 6 do backend, história 7 (última da fase — Interatividade de Ficha
  e Combate completa): na listagem de personagens da campanha, jogadores
  veem só um resumo (nome, raça, classe(s), nível) dos personagens de
  outros jogadores — a ficha completa continua visível só pro dono e pro
  mestre.
- Fase 6 do frontend, história 1: gerenciamento de magias conhecidas na
  ficha, organizadas por círculo, com busca por classe/círculo/nome,
  preparar/despreparar, remover e ver detalhes.
- Fase 6 do frontend, história 2: indicador de slots de magia por círculo
  na ficha, com botão de conjurar (incluindo ritual sem custo e
  conjuração em nível maior) e descanso curto/longo.
- Fase 6 do frontend, história 3: edição e remoção de itens do
  inventário pessoal na ficha, e registro de ganho/gasto de moeda.
- Fase 6 do frontend, história 4: botão de abrir sessão para o mestre, e
  aviso pedindo a rolagem de iniciativa de cada participante antes do
  combate poder avançar de turno.
- Fase 6 do frontend, história 5: seletor de ações de combate (ataque com
  arma, manual ou com magia, agarrar, empurrar, e as ações sem rolagem
  associada) para quem está no turno, com o resultado aparecendo em
  tempo real pra todo mundo conectado.
- Fase 6 do frontend, história 6 (última da fase — Interatividade de
  Ficha e Combate completa): na lista de personagens da campanha,
  jogadores veem só um resumo dos personagens de outros jogadores, e são
  levados direto pra ficha do próprio personagem quando têm só um na
  campanha; toda rolagem de combate (ataque, dano, teste oposto,
  iniciativa) pode ser digitada manualmente em vez de deixar o sistema
  rolar.
- Fase 7 do backend, história 1: gasto de dados de vida num descanso
  curto para recuperar pontos de vida, com descanso longo restaurando até
  metade do total de dados (mínimo 1).
- Fase 7 do backend, história 2: testes de morte automáticos ao chegar a
  0 pontos de vida (1 natural conta duas falhas, 20 natural restaura 1 PV
  e a consciência), estabilizando com 3 sucessos ou marcando o personagem
  como morto com 3 falhas.
- Fase 7 do backend, história 3: concentração numa magia conhecida,
  encerrada automaticamente ao conjurar outra magia de concentração, com
  a DC do teste de concentração exposta ao sofrer dano em combate.
- Fase 7 do backend, história 4: perícias passivas (Percepção,
  Investigação, Intuição) calculadas na ficha do personagem.
- Fase 7 do backend, história 5: subida de nível de um personagem numa
  classe já possuída ou nova via multiclasse, recalculando pontos de
  vida e bônus de proficiência, com melhoria de habilidade ou escolha de
  talento nos níveis que concedem essa opção.
- Fase 7 do backend, história 6: monstros usando ações lendárias fora do
  próprio turno (respeitando o limite por rodada) e reações do próprio
  stat block durante o combate.
- Fase 7 do backend, história 7 (última da fase — Sobrevivência,
  Descanso e Recursos completa): uso de recursos de classe em combate
  (fúria, ki, pontos de feitiçaria, e outros) com controle de limite por
  nível e recarga em descanso curto ou longo, conforme o recurso.
- Fase 7 do frontend, história 1: indicador de dados de vida disponíveis
  na ficha, com botão pra gastar num descanso curto e recuperar pontos
  de vida.
- Fase 7 do frontend, história 2: testes de morte na ficha ao chegar a 0
  pontos de vida, com marcadores de sucesso/falha e estados visuais de
  estável e morto.
- Fase 7 do frontend, história 3: indicador de concentração numa magia
  na ficha e no rastreador de combate, com a DC do teste de concentração
  e um atalho pra rolar a resistência de Constituição quando o
  personagem toma dano concentrando.
- Fase 7 do frontend, história 4: perícias passivas (Percepção,
  Investigação, Intuição) na ficha do personagem.
- Fase 7 do frontend, história 5: subida de nível guiada pela ficha,
  escolhendo a classe, e melhoria de habilidade ou talento do catálogo
  nos níveis que concedem essa opção.
- Fase 7 do frontend, história 6: ações lendárias e reações de monstros
  disparadas pelo rastreador de combate, com contador de uso por rodada.
- Fase 7 do frontend, história 7 (última da fase — Sobrevivência,
  Descanso e Recursos completa): recursos de classe (fúria, ki, e
  outros) usáveis e acompanháveis na ficha e durante a declaração de
  ação em combate.
- Fase 8 do backend, história 1: dashboard de campanha combinando a
  próxima sessão, NPCs/locais recentes e handouts pendentes numa única
  chamada, com visão diferente para mestre e jogador.
- Fase 8 do backend, história 2: escolha da estratégia de geração de
  atributos (standard array, point buy, custom ou rolagem) na criação de
  personagem, com validação de orçamento de pontos e do conjunto de
  valores para os dois primeiros métodos.
- Fase 8 do backend, história 3: subida de nível perguntando escolhas
  mecânicas com opções nomeadas (estilo de luta, pacto, domínio de
  clérigo e outras), incluindo escolhas múltiplas simultâneas
  (invocações élficas, metamagia) e escolhas específicas de subclasse.
- Fase 8 do backend, história 4: registro de qual opção de Canalizar
  Divindade foi usada, exigida quando o personagem tem mais de uma
  disponível.
- Fase 8 do backend, história 5: magias classificadas por tipo de ação
  (ataque, resistência ou só conjuração) e tipo de alvo, com a DC de
  resistência retornada ao conjurar.
- Fase 8 do backend, história 6: classe de armadura recalculada
  automaticamente ao equipar ou desequipar armadura e escudo.
- Fase 8 do backend, história 7 (última da fase até aqui — auditoria de
  Sobrevivência/Combate): bônus de proficiência no ataque com arma
  passa a considerar se o personagem realmente é proficiente com a arma
  equipada, em vez de assumir proficiência sempre.
- Fase 8 do frontend, história 1: dashboard da campanha mostrando a
  próxima sessão, NPCs/locais recentes e handouts pendentes de verdade,
  em vez dos placeholders "em breve".
- Fase 8 do frontend, história 2: opção de multiclasse na subida de
  nível, adicionando uma classe nova em vez de só subir uma já
  existente.
- Fase 8 do frontend, história 3: subida de nível perguntando as
  escolhas mecânicas que o personagem ganha (estilo de luta, pacto de
  bruxo, domínio de clérigo e outras), com busca quando há muitas
  opções.
- Fase 8 do frontend, história 4: histórico de rolagens recentes
  reposicionado para o rodapé da ficha, sem competir com o resto do
  conteúdo.
- Fase 8 do frontend, história 5: animação de dado rolando antes do
  resultado aparecer, em todo ponto de rolagem da ficha e do combate.
- Fase 8 do frontend, história 6: escolha da estratégia de geração de
  atributos (array padrão, compra de pontos, rolagem ou livre) na
  criação de personagem.
- Fase 8 do frontend, história 7: perícias com proficiência e
  especialização em destaque visual na ficha.
- Fase 8 do frontend, história 8: confirmação antes de disparar um
  descanso curto ou longo, já que isso reseta pontos de vida, espaços
  de magia e recursos.
- Fase 8 do frontend, história 9: escolha de qual opção de Canalizar
  Divindade usar, quando o personagem tem mais de uma disponível.
- Fase 8 do frontend, história 10: escolha do alvo ao conjurar uma
  magia de efeito (aliado, inimigo ou área) durante o combate, com a CD
  de resistência exibida e um atalho pra rolar a resistência do alvo.
- Fase 8 do frontend, história 11 (correção): preparar uma magia
  específica deixou de afetar visualmente as demais magias da lista
  enquanto a chamada estava em andamento.
- Fase 8 do frontend, história 12: magias conhecidas organizadas em
  seções recolhíveis por círculo, com confirmação antes de adicionar
  uma magia de um círculo que o personagem ainda não conjura.
- Fase 8 do frontend, história 13: classe de armadura na ficha
  atualizada automaticamente ao equipar ou desequipar armadura.
- Fase 8 do frontend, história 14: registro de ganho e gasto de moeda
  por denominação (cobre, prata, ouro, platina), em vez de só um valor
  abstrato.
- Fase 8 do frontend, história 15 (última da fase — Dashboard e
  Refinamentos de Ficha completa): busca no catálogo de talentos da
  campanha ao adicionar uma característica avulsa à ficha, em vez de
  digitar o nome livremente.
- Fase 10 do backend, primeira história: edição pós-criação da ficha do
  personagem (nome, alinhamento, antecedente e atributos-base), com
  recálculo automático dos campos derivados afetados — modificadores,
  classe de armadura (quando depende de Destreza) e pontos de vida
  máximos (quando o modificador de Constituição muda, retroativo a todos
  os níveis já obtidos). Raça e classe continuam bloqueadas para edição
  pós-criação nesta história.
- Fase 10 do backend, história 2: upload de uma imagem de retrato para o
  personagem, exibida na ficha; enviar uma nova imagem substitui a
  anterior, e o jogador pode removê-la e voltar ao estado sem imagem.
  Só o dono da ficha pode alterá-la.
- Fase 10 do backend, história 3: proficiências de perícia agora respeitam
  as capacidades da raça/classe do personagem, em vez de livres. Novo
  `POST /characters/{id}/proficiencies` aceita apenas perícias dentro do
  conjunto de escolha ("escolha N de [...]") oferecido pela raça e
  classe(s) do personagem, rejeitando o resto com 422; perícias concedidas
  sem escolha são aplicadas automaticamente na criação do personagem.
- Fase 11 do backend, segunda história: exclusão de conteúdo homebrew do
  catálogo (`DELETE /catalog/{races,classes,spells,items,magic-items,
  monsters,backgrounds,feats,rules}/{id}`), DM-only e restrita à própria
  campanha. Conteúdo SRD nunca pode ser excluído (403); homebrew de outra
  campanha retorna 404, sem confirmar sua existência para quem não é
  membro. Exclusão é bloqueada com 409 quando uma raça, classe, magia,
  item, item mágico ou monstro homebrew ainda está referenciado (por um
  personagem, seu inventário, um loot drop, um encontro ou um NPC).
