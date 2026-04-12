# Changelog v6b

## Conceito: melhor base + melhor reward

A v5 (conta anterior) terminou com:
- Steps médios: 143 (melhor já registrado na conta anterior)
- Taxa 100% nas últimas 50 iters: 81.5%
- Throttle médio: 1.95

Melhor que a v9 da conta nova em steps (143 vs 156). O clone da v5 é uma base
potencialmente mais forte para aplicar a abordagem de velocidade por waypoint.

## Diferença crítica: action space da v5

A v5 usava velocidades contínuas diferentes da v6+:
- Retas: 3.8, 4.0
- Curvas suaves: 2.6, 2.8
- Curvas fechadas: 1.4, 1.6

A `WP_TARGET_SPEED` foi ajustada para esse action space:
- Retas → 4.0 (era 4.0 na v12 também — igual)
- Curvas → 2.6 (era 2.67 na v12 — ajustado)
- Apex → 1.4 (era 1.33 na v12 — ajustado)

A penalidade de velocidade usa divisor 2.6 (range do action space da v5)
em vez de 2.67.

## Estrutura idêntica à v12

Mesma lógica que provou funcionar:
- Penalidade suave: `max(1.0 - speed_diff/2.6, 0.1)` — nunca zera o gradiente
- Bônus por velocidade exata: +0.5
- Steering penalty em retas: `(steering/25)^2 * 0.5`
- Bônus de volta: `100*(100/steps)^3`

## Hiperparâmetros

| Parâmetro | Valor | Motivo |
|-----------|-------|--------|
| Entropy | 0.015 | Base já treinada, menos exploração necessária |
| LR | 0.0001 | Conservador — não destruir o aprendizado da v5 |
