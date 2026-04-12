# Changelog v9 → v10

## Problema: modelo estável mas lento

V9 atingiu 89.2% de taxa de conclusão nas últimas iterações — o modelo sabe andar na pista. Mas a distribuição de throttle piorou a cada versão:

| Versão | 1.33 m/s | 2.67 m/s | 4.00 m/s | Média |
|--------|----------|----------|----------|-------|
| v6     | 43.1%    | 30.7%    | 26.2%    | 2.44  |
| v7     | 56.3%    | 25.9%    | 17.8%    | 2.15  |
| v9     | 70.0%    | 22.0%    | 8.1%     | 1.84  |

O modelo encontrou um ótimo local: 1.33 m/s é a estratégia mais segura. A slow_penalty da v9 (`max(0.4 - speed/4.0, 0.0)`) penalizava 1.33 m/s em apenas 0.07 — insuficiente para competir com o risco percebido de ir mais rápido.

**Objetivo da v10:** tornar 1.33 m/s genuinamente caro, sem destruir o que a v9 aprendeu.

---

## Mudanças v9 → v10

### 1. Slow penalty: muito mais agressiva

**v9:** `max(0.4 - speed/4.0, 0.0)`
**v10:** `max(0.8 - speed/4.0, 0.0)`

| Velocidade | v9 penalty | v10 penalty |
|-----------|-----------|------------|
| 1.33      | 0.07      | **0.47**   |
| 2.00      | 0.10      | **0.30**   |
| 2.67      | 0.07      | **0.13**   |
| 3.20      | 0.00      | 0.00       |
| 4.00      | 0.00      | 0.00       |

Agora 1.33 m/s custa 0.47 por step — é impossível ter reward positivo consistente nessa velocidade. O modelo é forçado a buscar pelo menos 2.67–3.20 m/s para sair do negativo.

### 2. Bônus de velocidade em curvas: 0.3 → 0.5

**v9:** `speed_reward += (speed/4.0) * 0.3`
**v10:** `speed_reward += (speed/4.0) * 0.5`

Curvas representam ~39% da pista. Aumentar o incentivo de velocidade em curvas é crítico para reduzir o tempo total de volta.

### 3. Peso do speed_reward: 0.40 → 0.50

Velocidade é o único objetivo agora. Speed_reward passa a ser o componente dominante absoluto.

### 4. Peso do center_reward: 0.10 → 0.05

O modelo já sabe ficar na pista. Liberar peso para velocidade.

### 5. Peso do heading_reward: 0.30 → 0.25

Reduzido levemente. Heading ainda é necessário para não perder controle em alta velocidade, mas não pode competir com velocidade.

### 6. Steering penalty em retas: 0.4 → 0.3

Reduzido para não penalizar o modelo quando ele precisa fazer micro-correções em alta velocidade.

---

## Ponto de partida: clone da v9

A v9 tem base sólida (89.2% conclusão). Partir do clone dela com a nova reward — o modelo já sabe ficar na pista, só precisa aprender a ir mais rápido.

## Hiperparâmetros

| Parâmetro | v9     | v10        | Motivo |
|-----------|--------|------------|--------|
| Entropy   | 0.015  | **0.01**   | Modelo já explorou o suficiente, focar em explotar velocidade |
| LR        | 0.00015 | **0.0001** | Ligeiramente maior para absorver o novo sinal de velocidade |
| Resto     | igual  | igual      | |

## Impacto esperado na distribuição de throttle

Com slow_penalty de 0.47 em 1.33 m/s, o modelo precisa de speed_reward alto para compensar. Estimativa:

| Throttle | v9 (atual) | v10 (esperado) |
|----------|-----------|----------------|
| 1.33 m/s | 70%       | < 30%          |
| 2.67 m/s | 22%       | ~40%           |
| 4.00 m/s | 8%        | ~30%           |
| Média    | 1.84      | > 2.5          |
