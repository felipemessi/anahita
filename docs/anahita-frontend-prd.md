# Anahita — Frontend PRD

## Product Requirements Document | Frontend

**Versão:** 1.0
**Data:** 2026-04-08
**Autor:** Felipe Braga

---

## 1. Visão Geral

Frontend do Anahita — plataforma multi-mesa para gerenciamento de campanhas de D&D 5e. Interface para DMs e jogadores interagirem com campanhas, fichas de personagem, combat tracker em tempo real, world-building e handouts.

### 1.1 Princípios de UX

1. **Rapidez na sessão.** O combat tracker é mobile-first, com interações de toque otimizadas para uso na mesa de jogo.
2. **Preparação confortável.** Telas de world-building e fichas são desktop-first, com espaço para texto e navegação entre entidades.
3. **Sem obstáculos.** Dados carregam sem spinners sempre que possível (Server Components). Mutações são otimistas.
4. **Visibilidade controlada.** DM vê tudo. Jogadores veem apenas o que foi compartilhado.

---

## 2. Stack Tecnológico

| Camada          | Tecnologia                              |
|-----------------|----------------------------------------|
| Framework       | Next.js (App Router)                   |
| Linguagem       | TypeScript (strict mode)               |
| UI Library      | shadcn/ui (Tailwind + Radix primitives)|
| State/Cache     | TanStack Query (React Query)           |
| Real-time       | WebSocket nativo                       |
| Fontes          | DM Sans (principal) + Space Mono (mono)|
| Deploy          | Docker (standalone output), VPS        |

### 2.1 Decisões Técnicas Fundamentais

- **Sem vendor lock-in.** Nenhuma feature exclusiva da Vercel: sem `next/image` com loader padrão Vercel, sem ISR on-demand via webhook, sem Edge Runtime, sem Vercel Analytics/KV/Blob.
- **Output standalone.** `next build` gera servidor Node.js autocontido. Roda em Docker sem dependência de plataforma.
- **Imagens:** usar `sharp` + loader customizado ou `unpic` em vez do image optimizer da Vercel.
- **App Router com Server Components** para dados estáveis. Client Components com TanStack Query para dados mutáveis. WebSocket para real-time.
- **Node.js runtime** padrão em todas as rotas (nunca Edge Runtime).

---

## 3. Arquitetura de Data Fetching

Abordagem híbrida: server para dados iniciais, client para real-time e mutações.

### 3.1 Server Components (dados estáveis)

Usados para: fichas de personagem, catálogo SRD, lista de sessões, world-building (NPCs, locais, facções), configurações da campanha.

O Server Component faz fetch direto para o backend FastAPI, renderiza HTML e entrega pronto. Sem loading spinner, sem hydration de dados. O token do usuário é propagado via cookies (lido pelo `lib/api/server.ts`).

### 3.2 Client Components + TanStack Query (dados mutáveis)

Usados para: notas de sessão, inventário, edição de ficha, loot.

TanStack Query gerencia cache e revalidação. Mutações otimistas para feedback instantâneo — o dado aparece atualizado na UI antes da resposta do servidor.

O API client (`lib/api/client.ts`) anexa o access token automaticamente e faz refresh transparente ao receber 401.

### 3.3 Client Components + WebSocket (real-time)

Usados para: combat tracker, reveal de handouts durante sessão.

O `CombatProvider` mantém a conexão WebSocket e expõe o estado via React Context. O hook `useCombat()` dá acesso ao estado do encounter e funções de ação. Reconexão automática com `state_sync` na reconexão.

Estado do WebSocket **não** se mistura com o cache do TanStack Query — são fontes de dados independentes.

---

## 4. Autenticação no Frontend

### 4.1 Fluxo

1. Login envia credenciais para o backend.
2. Backend retorna access token + refresh token.
3. **Access token:** em memória (variável JS). Nunca em localStorage (proteção contra XSS).
4. **Refresh token:** em httpOnly cookie, gerenciado pelo backend.

### 4.2 Server-side

O middleware do Next.js lê o cookie de refresh token. O `lib/api/server.ts` resolve o access token via Route Handler interno e o propaga nas chamadas server-side.

### 4.3 Client-side

O `lib/api/client.ts` usa o access token em memória. Ao receber 401, faz refresh automático via endpoint dedicado antes de retentar o request.

### 4.4 Proteção de Rotas

`middleware.ts` do Next.js redireciona para `/auth/login` se não há sessão válida. Rotas públicas: `/`, `/auth/*`, `/join/*`.

---

## 5. Identidade Visual

### 5.1 Tipografia

| Uso       | Fonte      | Notas                    |
|-----------|------------|--------------------------|
| Principal | DM Sans    | Títulos, corpo de texto  |
| Monospace | Space Mono | Dados numéricos, stats   |

### 5.2 Paleta

Customizada via CSS variables do shadcn/ui. Cores primárias: deep navy + gold. Tema dark como padrão (RPG), com suporte a light mode.

### 5.3 Componentes

shadcn/ui como base. Componentes instalados sob `src/components/ui/`. Customizados via Tailwind classes e CSS variables do tema. Sem abstração extra sobre o shadcn — usar diretamente nos componentes de domínio.

---

## 6. Estrutura de Rotas

```
/                              → Landing / dashboard de campanhas
/auth/login                    → Login
/auth/register                 → Registro

/campaigns                     → Lista de campanhas do usuário
/campaigns/[id]                → Dashboard da campanha
/campaigns/[id]/sessions       → Lista de sessões
/campaigns/[id]/sessions/[id]  → Sessão (notas, encounters, handouts)
/campaigns/[id]/combat/[id]    → Combat tracker (WebSocket, fullscreen mobile)
/campaigns/[id]/characters     → Lista de personagens
/campaigns/[id]/characters/[id]→ Ficha de personagem
/campaigns/[id]/world          → Hub de world-building
/campaigns/[id]/world/npcs     → NPCs
/campaigns/[id]/world/locations→ Locais (com hierarquia)
/campaigns/[id]/world/factions → Facções (com relacionamentos)
/campaigns/[id]/inventory      → Inventário do grupo
/campaigns/[id]/handouts       → Handouts (DM: gerencia / Player: visualiza)
/campaigns/[id]/settings       → Config da campanha, membros

/join/[inviteCode]             → Aceitar convite via link
```

### 6.1 Layouts

- **Root layout:** providers (QueryProvider, ThemeProvider), fontes, CSS global.
- **Campaign layout** (`/campaigns/[id]/layout.tsx`): sidebar de navegação da campanha, header com nome da campanha e role do usuário.
- **Combat layout** (`/campaigns/[id]/combat/[id]/layout.tsx`): fullscreen no mobile, esconde sidebar e header. Botão para voltar à visão normal.

---

## 7. Estrutura do Projeto

```
frontend/
├── public/
│   └── fonts/
├── src/
│   ├── app/
│   │   ├── layout.tsx                    # Root layout (providers, fontes)
│   │   ├── page.tsx                      # Landing
│   │   ├── auth/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── campaigns/
│   │   │   ├── page.tsx                  # Lista de campanhas
│   │   │   └── [campaignId]/
│   │   │       ├── layout.tsx            # Sidebar da campanha
│   │   │       ├── page.tsx              # Dashboard
│   │   │       ├── sessions/
│   │   │       │   ├── page.tsx
│   │   │       │   └── [sessionId]/
│   │   │       │       └── page.tsx
│   │   │       ├── combat/
│   │   │       │   └── [encounterId]/
│   │   │       │       ├── layout.tsx    # Fullscreen mobile
│   │   │       │       └── page.tsx
│   │   │       ├── characters/
│   │   │       │   ├── page.tsx
│   │   │       │   └── [characterId]/
│   │   │       │       └── page.tsx
│   │   │       ├── world/
│   │   │       │   ├── page.tsx          # Hub
│   │   │       │   ├── npcs/
│   │   │       │   │   └── page.tsx
│   │   │       │   ├── locations/
│   │   │       │   │   └── page.tsx
│   │   │       │   └── factions/
│   │   │       │       └── page.tsx
│   │   │       ├── inventory/
│   │   │       │   └── page.tsx
│   │   │       ├── handouts/
│   │   │       │   └── page.tsx
│   │   │       └── settings/
│   │   │           └── page.tsx
│   │   └── join/
│   │       └── [inviteCode]/
│   │           └── page.tsx
│   ├── components/
│   │   ├── ui/                           # shadcn/ui (gerados via CLI)
│   │   ├── layout/
│   │   │   ├── campaign-sidebar.tsx
│   │   │   ├── header.tsx
│   │   │   └── mobile-nav.tsx
│   │   ├── characters/
│   │   │   ├── character-sheet.tsx
│   │   │   ├── ability-scores.tsx
│   │   │   ├── skill-list.tsx
│   │   │   └── spell-slots.tsx
│   │   ├── combat/
│   │   │   ├── initiative-tracker.tsx
│   │   │   ├── participant-card.tsx
│   │   │   ├── condition-badges.tsx
│   │   │   ├── damage-dialog.tsx
│   │   │   └── turn-indicator.tsx
│   │   ├── sessions/
│   │   │   ├── session-card.tsx
│   │   │   ├── note-editor.tsx
│   │   │   └── quick-note.tsx
│   │   ├── world/
│   │   │   ├── npc-card.tsx
│   │   │   ├── location-tree.tsx
│   │   │   ├── faction-graph.tsx
│   │   │   └── entity-link-badge.tsx
│   │   ├── handouts/
│   │   │   ├── handout-card.tsx
│   │   │   ├── handout-reveal-button.tsx
│   │   │   └── handout-viewer.tsx
│   │   └── inventory/
│   │       ├── loot-table.tsx
│   │       └── item-card.tsx
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts                 # Client-side fetch (access token em memória)
│   │   │   ├── server.ts                 # Server-side fetch (propaga cookies)
│   │   │   ├── campaigns.ts
│   │   │   ├── characters.ts
│   │   │   ├── sessions.ts
│   │   │   ├── combat.ts
│   │   │   ├── world.ts
│   │   │   ├── handouts.ts
│   │   │   ├── inventory.ts
│   │   │   └── catalog.ts
│   │   ├── ws/
│   │   │   ├── combat-socket.ts          # WebSocket client
│   │   │   └── types.ts                  # Tipos dos eventos WS
│   │   ├── auth/
│   │   │   ├── session.ts                # Leitura do token/cookie
│   │   │   └── middleware.ts             # Proteção de rotas
│   │   └── utils/
│   │       ├── dnd-rules.ts              # Cálculos client-side (modifier, etc.)
│   │       └── formatting.ts             # Formatação de dados D&D
│   ├── hooks/
│   │   ├── use-campaign.ts
│   │   ├── use-character.ts
│   │   ├── use-session.ts
│   │   ├── use-combat.ts                 # WebSocket hook
│   │   ├── use-world.ts
│   │   ├── use-handouts.ts
│   │   └── use-inventory.ts
│   ├── providers/
│   │   ├── query-provider.tsx            # TanStack Query
│   │   ├── combat-provider.tsx           # WebSocket state
│   │   └── theme-provider.tsx
│   ├── types/
│   │   ├── campaign.ts
│   │   ├── character.ts
│   │   ├── session.ts
│   │   ├── combat.ts
│   │   ├── world.ts
│   │   ├── handout.ts
│   │   ├── inventory.ts
│   │   └── catalog.ts
│   └── styles/
│       └── globals.css                   # Tailwind + CSS variables do tema
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

### 7.1 Convenções

| Diretório        | Responsabilidade                                                          |
|-----------------|---------------------------------------------------------------------------|
| app/             | Rotas e layouts (App Router). Sem lógica de negócio.                     |
| components/ui/   | shadcn/ui gerados via CLI. Não editar diretamente.                       |
| components/*/    | Componentes de domínio. Consomem hooks e types.                          |
| lib/api/         | Funções de chamada ao backend. Separadas por domínio.                    |
| lib/ws/          | WebSocket client e tipos de eventos.                                     |
| hooks/           | Custom hooks. Um por domínio. Encapsulam TanStack Query e WebSocket.     |
| providers/       | React Context providers. Montados no root layout.                        |
| types/           | TypeScript types/interfaces. Espelham os schemas do backend.             |

---

## 8. Combat Tracker — UX Mobile-First

A feature de maior prioridade. DM usa na mesa, em tablet ou celular.

### 8.1 Tela Principal

Lista vertical de participantes ordenada por iniciativa. Cada card mostra:

- Nome
- HP atual / HP máximo (barra visual com cor)
- AC (badge)
- Condições ativas (badges com ícones)

O participante do turno atual fica visualmente destacado (borda, cor de fundo diferente).

### 8.2 Ações Rápidas (DM)

Tap no card do participante abre painel de ações:

- **Dano/Cura:** input numérico com botões +/- e confirmação. Ação mais frequente — precisa de menos de 3 taps.
- **Condições:** toggle de badges (blinded, charmed, etc.). Tap para adicionar, tap para remover.
- **Remover:** participante sai do combate (morto/fugitivo).

### 8.3 Controles Globais

- **Avançar turno:** botão fixo no rodapé, sempre acessível. Mostra quem é o próximo.
- **Adicionar participante:** botão no header. Abre form rápido (nome, HP, AC, iniciativa).
- **Encerrar combate:** botão no header com confirmação.

### 8.4 Layout Fullscreen

No mobile, o combat tracker esconde sidebar e header da campanha. Só o tracker ocupa a tela. Botão para voltar à visão normal.

### 8.5 Visão do Jogador (read-only)

Jogadores veem a mesma lista, mas sem controles de ação. Útil para acompanhar a ordem de iniciativa e o estado do combate. Atualiza em tempo real via WebSocket.

---

## 9. Telas Principais

### 9.1 Dashboard de Campanhas (`/campaigns`)

Lista de campanhas do usuário com role (DM/Player), status e data da última sessão. Botão para criar nova campanha ou inserir código de convite.

### 9.2 Dashboard da Campanha (`/campaigns/[id]`)

Visão geral: próxima sessão agendada, personagens ativos, atividade recente. Links rápidos para as seções (sessões, personagens, world, inventário).

Para o DM: notas rápidas, lista de NPCs/locais recém-editados, handouts pendentes de reveal.

### 9.3 Ficha de Personagem (`/campaigns/[id]/characters/[id]`)

Layout tabbed ou scrollable com seções:

- **Cabeçalho:** nome, raça, classe(s), level, XP.
- **Ability Scores:** grid 2x3 com score, modifier e saving throw.
- **Skills:** lista com proficiência/expertise marcadas e bônus calculado.
- **Combat:** AC, HP (editável inline), speed, iniciativa, ataques.
- **Spells:** lista por level com slots, prepared toggle.
- **Equipment:** inventário pessoal com equipped toggle.
- **Features:** lista de features por fonte (classe, raça, feat).

Cálculos de modifier, proficiency, skill bonus feitos client-side via `lib/utils/dnd-rules.ts` (espelho leve da rules engine do backend).

### 9.4 World-building (`/campaigns/[id]/world`)

Hub com três seções navegáveis: NPCs, Locations, Factions.

- **NPCs:** cards com nome, raça, ocupação, facções vinculadas. Busca por nome.
- **Locations:** árvore hierárquica (região → cidade → taverna). Expandir/colapsar.
- **Factions:** lista com relacionamentos entre facções visualizados (graph simples ou lista de relações).

Cada entidade mostra badges de links (em quais sessões apareceu, a que facção pertence, etc.).

### 9.5 Handouts (`/campaigns/[id]/handouts`)

**Visão do DM:** lista de todos os handouts, com toggle reveal/hide. Upload de imagens/mapas. Editor de texto para handouts textuais. Filtro por sessão.

**Visão do jogador:** apenas handouts revelados. Galeria com imagens em tamanho grande, textos formatados.

---

## 10. Responsividade

| Tela               | Desktop-first | Mobile-first | Notas                               |
|--------------------|:-------------:|:------------:|--------------------------------------|
| Combat tracker     |               | ✓            | Fullscreen, touch-optimized          |
| Quick notes        |               | ✓            | Usado durante sessão                 |
| Ficha de personagem| ✓             |              | Muita informação, melhor com espaço  |
| World-building     | ✓             |              | Árvores, grafos, textos longos       |
| Dashboard          | ✓             |              | Overview, links rápidos              |
| Handouts viewer    |               | ✓            | Jogadores veem no celular na mesa    |

Todas as telas são responsivas, mas o ponto de partida do design muda conforme o contexto de uso principal.

---

## 11. Restrições Anti-Vendor-Lock-In

### 11.1 Features do Next.js a Evitar

| Feature                          | Motivo                              | Alternativa                         |
|----------------------------------|-------------------------------------|-------------------------------------|
| `next/image` loader padrão       | Requer Vercel image optimizer       | sharp + loader customizado ou unpic |
| ISR revalidação on-demand        | Funciona parcialmente self-hosted   | Revalidação via TanStack Query      |
| Edge Runtime                     | Requer Vercel edge network          | Node.js runtime padrão              |
| Vercel Analytics                 | Serviço proprietário                | Self-hosted analytics (futuro)      |
| Vercel KV / Blob                 | Storage proprietário                | Postgres + filesystem               |
| Middleware em Edge               | Funciona self-hosted mas com limites| Manter middleware simples (auth)    |

### 11.2 Build e Deploy

```bash
# next.config.ts
output: 'standalone'
```

Gera servidor Node.js autocontido em `.next/standalone/`. Roda com `node server.js`. Empacotado em Docker image leve.

---

## 12. Deploy — Docker Compose (Full Stack)

### 12.1 Topologia

```
┌─────────┐     ┌───────────┐     ┌──────────┐     ┌──────────┐
│  Nginx   │────▶│  Frontend │     │ Backend  │     │ Postgres │
│  :80/443 │────▶│  :3000    │     │ :8000    │     │ :5432    │
└─────────┘     └───────────┘     └──────────┘     └──────────┘
     │                                  │                │
     │         /api/* ─────────────────▶│                │
     │         /ws/*  ─────────────────▶│ (WebSocket)    │
     │         /files/* ─▶ static files │───────────────▶│
     │         /* ────────▶ frontend    │
     │
     └── /data/uploads (ro, serve static)
```

### 12.2 Roteamento Nginx

| Path       | Destino          | Notas                              |
|------------|------------------|------------------------------------|
| `/api/*`   | backend:8000     | Proxy para FastAPI                 |
| `/ws/*`    | backend:8000     | WebSocket upgrade                  |
| `/files/*` | filesystem       | Static files de `/data/uploads`    |
| `/*`       | frontend:3000    | Next.js standalone                 |

### 12.3 Docker Compose

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certs:/etc/letsencrypt:ro
      - upload_data:/data/uploads:ro
    depends_on:
      - frontend
      - backend

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      - NEXT_PUBLIC_API_URL=https://anahita.example.com/api
      - NEXT_PUBLIC_WS_URL=wss://anahita.example.com/ws
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/anahita
      - STORAGE_TYPE=local
      - STORAGE_LOCAL_PATH=/data/uploads
      - JWT_SECRET=${JWT_SECRET}
    volumes:
      - upload_data:/data/uploads
    depends_on:
      - postgres

  postgres:
    image: postgres:17-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=anahita
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
  upload_data:
```

### 12.4 SSL

Let's Encrypt via certbot. Certificados montados no Nginx. Renovação automática via cron ou certbot standalone.

---

## 13. Glossário

| Termo              | Definição                                                                |
|--------------------|--------------------------------------------------------------------------|
| Server Component   | Componente React renderizado no servidor (sem interatividade client)     |
| Client Component   | Componente React com interatividade (`'use client'`)                     |
| TanStack Query     | Library de cache/state para dados assíncronos (antigo React Query)       |
| shadcn/ui          | Coleção de componentes baseados em Radix + Tailwind                     |
| Standalone output  | Build do Next.js que gera servidor Node.js autocontido                  |
| Optimistic update  | UI atualiza antes da confirmação do servidor                            |
| Combat Provider    | React Context que gerencia WebSocket do combat tracker                   |
| Storage Key        | Referência abstrata a um arquivo (sem path absoluto)                    |
