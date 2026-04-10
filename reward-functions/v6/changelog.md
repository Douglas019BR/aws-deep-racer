# Changelog v5 → v6

## Pista: re:Invent 2018 (reinvent_base) | Comprimento: 17.71m | ~61% reta

---

## Problemas identificados na v5

| Problema | Dados | Impacto |
|----------|-------|---------|
| Off-track rate 84% | 1949/2320 episódios | Modelo quase nunca completa volta |
| Aprendizado lento | 62 iterações sem 1 volta completa | Reward insuficiente pra guiar no início |
| Offtrack punição fraca (1e-3) | Sem gradiente real de punição | Modelo não aprende a evitar borda |
| Steering 20° domina (36%) | Pista 61% reta mas carro curva sempre | Zigue-zague desperdiça tempo |
| Velocidade caiu no treino | 2.19 → 1.92 média | Modelo aprendeu que devagar = seguro |
| progress/200 fraco demais | Único incentivo de avanço | Não compensa o risco de ir rápido |

---

## Mudanças v5 → v6

### 1. Offtrack: `1e-3` → `-1.0`

**v5:** `return 1e-3` — praticamente zero, modelo ignora
**v6:** `return -1.0` — punição real, cria gradiente forte pra evitar borda

Na v4 isso funcionou bem (12% off-track). A v5 removeu e o off-track explodiu pra 84%.

### 2. Steering penalty proporcional em retas (antes: fixa 0.2)

**v5:** `0.2 if is_straight and abs(steering_angle) > 10 else 0.0` — binário
**v6:** `(abs(steering_angle) / 30.0) ** 2 * 0.5` — quadrático

| Steering | v5 penalty | v6 penalty |
|----------|-----------|-----------|
| 0°       | 0.0       | 0.0       |
| 5°       | 0.0       | 0.01      |
| 10°      | 0.2       | 0.06      |
| 15°      | 0.2       | 0.13      |
| 20°      | 0.2       | 0.22      |
| 25°      | 0.2       | 0.35      |

Gradiente suave — o modelo sente pressão crescente pra reduzir steering em retas.

### 3. Threshold de reta: `< 8` → `< 10`

Pista é 61% reta. Threshold mais generoso captura mais trechos como reta, aplicando speed bonus e steering penalty em mais situações.

### 4. Step cost progressivo (novo)

**v5:** Sem penalidade de steps
**v6:** `(steps / 150) ** 2 * 0.03`

| Steps | Custo acumulado |
|-------|----------------|
| 50    | 0.003          |
| 100   | 0.013          |
| 130   | 0.023          |
| 150   | 0.030          |
| 180   | 0.043          |

Pressão suave mas crescente. Nos primeiros steps é imperceptível, mas a partir de 100+ o modelo sente que cada step extra custa.

### 5. Progresso: `progress/200` → `progress/100`

Dobra o incentivo de avanço. Uma volta completa agora dá +1.0 só de progresso (vs +0.5 na v5). Isso ajuda especialmente no início do treino quando o modelo ainda não completa voltas — cada waypoint avançado vale mais.

### 6. Heading threshold: `/30` → `/25`

**v5:** `max(1.0 - direction_diff / 30.0, 0.0)` — tolerante até 30°
**v6:** `max(1.0 - direction_diff / 25.0, 0.0)` — mais exigente

Heading reward cai pra zero em 25° em vez de 30°. Força alinhamento mais preciso.

### 7. Pesos redistribuídos

| Componente | v5 | v6 | Motivo |
|-----------|-----|-----|--------|
| speed_reward | 0.40 | 0.35 | Equilibrar com heading |
| heading_reward | 0.30 | 0.35 | Heading é crítico pra não sair da pista |
| center_reward | 0.20 | 0.15 | Menos importante que velocidade e direção |
| steering_penalty | -0.20 (fixa) | -0.0 a -0.50 (proporcional) | Gradiente suave |
| step_cost | — | -0.0 a -0.05 | Pressão pra terminar rápido |
| progress | /200 | /100 | Dobro do incentivo |

### 8. Speed reward em retas: `**1.5` → `**2`

Expoente quadrático amplifica a diferença entre velocidades altas:

| Velocidade | v5 (^1.5) | v6 (^2) |
|-----------|----------|---------|
| 1.6       | 0.25     | 0.16    |
| 2.2       | 0.36     | 0.30    |
| 3.0       | 0.52     | 0.56    |
| 3.8       | 0.73     | 0.90    |
| 4.0       | 1.00     | 1.00    |

Na v6, a diferença entre 3.0 e 3.8 é muito maior. Incentiva o modelo a buscar velocidade máxima em retas.

---

## Hyperparameters recomendados (sessão 1)

| Parâmetro | v5 | v6 (sessão 1) | Motivo |
|-----------|-----|---------------|--------|
| Batch size | 64 | 64 | Manter |
| Epochs | 5 | 5 | Manter |
| Learning rate | 0.0001 | 0.0003 | Mais alto no início — modelo precisa aprender rápido |
| Discount factor (γ) | 0.99 | 0.99 | Manter |
| Loss type | Huber | Huber | Manter |
| Entropy | 0.02 | 0.025 | Ligeiramente maior — explorar mais no início |
| Episódios/iteração | 20 | 20 | Manter |

### Plano de sessões (24h total)

| Sessão | Duração | Entropy | LR | Objetivo |
|--------|---------|---------|-----|----------|
| 1 | 1h | 0.025 | 0.0003 | Validar reward + action space |
| 2 | 1.5h | 0.02 | 0.0002 | Ajustar se necessário |
| 3 | 3-4h | 0.015 | 0.0001 | Aprendizado principal |
| 4 | 3-4h | 0.01 | 0.0001 | Refinamento |
| 5 | 3-4h | 0.008 | 0.00005 | Otimização |
| 6 | 1-2h | 0.005 | 0.00005 | Polish final |

## Action Space (manter v5)

Mesmo action space de 19 ações da v5 — simétrico, com 3 opções de reta (3.8, 3.0, 2.2) e steering proporcional à velocidade.

---

## Resultado esperado

- Off-track rate < 30% (vs 84% na v5) graças ao `-1.0`
- Primeira volta completa antes da iteração 20 (vs 63 na v5) graças ao `progress/100`
- Steering 0° > 30% nas últimas iterações (vs 24% na v5) graças à steering penalty proporcional
- Velocidade média > 2.2 (vs 1.92 na v5) graças ao speed reward quadrático
- Melhor volta < 8.5s (vs 8.57s na v5)
