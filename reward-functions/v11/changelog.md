# Changelog v10 → v11

## Problema: penalizar velocidade baixa não funciona

Todas as tentativas de forçar velocidade via penalidade falharam:

| Versão | Abordagem | Resultado |
|--------|-----------|-----------|
| v9 | slow_penalty gradual `max(0.4 - speed/4, 0)` | 1.84 m/s média |
| v10 | slow_penalty agressiva `max(0.8 - speed/4, 0)` | **1.73 m/s** — piorou |

O modelo responde a penalidades de velocidade ficando ainda mais conservador para proteger o reward de conclusão. Penalizar o que ele não deve fazer não ensina o que ele deve fazer.

## Nova abordagem: velocidade alvo por waypoint

Inspirado em reward functions de racing line, mas adaptado para a nossa pista sem precisar de coordenadas XY externas — usa apenas o índice do waypoint mais próximo, que já está disponível nos `params`.

referência : https://github.com/yang0369/AWS_DeepRacer/blob/main/reward_function(1.5).py


### Velocidades alvo calculadas a partir da curvatura da reinvent_base

Os waypoints foram analisados pela mudança de ângulo entre segmentos consecutivos:

| Velocidade | Critério | Waypoints | % da pista |
|-----------|----------|-----------|-----------|
| 4.00 m/s | curva < 5° (reta) | 71 wps | 59.7% |
| 2.67 m/s | curva 5–20° | 44 wps | 37.0% |
| 1.33 m/s | curva > 20° (apex) | 4 wps | 3.4% |

Tempo ótimo estimado com essas velocidades: **~7.0s**

### Como o reward funciona agora

1. Se `speed_diff > 1.0` (mais de 1 m/s longe do alvo) → `1e-3` imediatamente
2. Caso contrário: `speed_reward = 1.0 - speed_diff / 1.0` (linear)
3. Bônus extra `+0.5` por atingir exatamente 4.0 m/s em retas
4. Heading ainda presente (peso 0.40) para não perder controle
5. Bônus de volta: `100 * (100/steps)^3` — **4x mais agressivo que v10**

### Impacto do bônus de volta (comparativo)

| Steps | v10: `25*(120/s)^3` | v11: `100*(100/s)^3` | delta |
|-------|--------------------|--------------------|-------|
| 100   | 43.2               | 100.0              | +56.8 |
| 120   | 25.0               | 57.9               | +32.9 |
| 140   | 15.7               | 36.4               | +20.7 |
| 160   | 10.6               | 24.4               | +13.9 |

A diferença entre completar em 120 vs 160 steps agora vale **33.5 pontos** — impossível de ignorar.

### Por que isso é diferente das versões anteriores

Nas versões anteriores, o modelo podia maximizar o reward indo devagar e completando a volta. Agora:
- Ir a 1.33 m/s em uma reta (target 4.0) → `speed_diff = 2.67 > 1.0` → reward `1e-3` imediatamente
- O modelo **não consegue** ter reward positivo em retas sem ir rápido

## Ponto de partida: clone da v9

A v9 tem a melhor base de "saber ficar na pista" (89.2% conclusão). A v10 não adicionou conhecimento útil — apenas confirmou que penalidades não funcionam.

## Hiperparâmetros

| Parâmetro | v10    | v11        | Motivo |
|-----------|--------|------------|--------|
| Entropy   | 0.01   | **0.02**   | Nova reward muito diferente — precisa explorar mais |
| LR        | 0.0001 | **0.0002** | Aprender o novo sinal de velocidade por waypoint mais rápido |

Entropy mais alta porque a reward mudou estruturalmente — o modelo precisa reaprender quais ações são boas em cada waypoint.
