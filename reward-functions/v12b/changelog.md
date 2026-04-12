# Changelog v12b

## Hipótese paralela à v12 — Racing line com coordenadas XY

Enquanto a v12 ensina velocidade por índice de waypoint, a v12b vai além: define
**onde exatamente na pista** o carro deve estar em cada ponto, além da velocidade alvo.

## Racing line calculada para reinvent_base

A linha foi calculada a partir dos waypoints da pista com a seguinte lógica:

| Situação | Posição na pista | t (inner→outer) |
|----------|-----------------|-----------------|
| Reta | Centro | 0.5 |
| Entrada de curva | Lado externo | 0.8 |
| Apex | Lado interno | 0.1 |
| Saída de curva | Lado externo | 0.8 |

Tempo estimado seguindo a linha perfeitamente: **6.54s** (vs ~7.0s só por waypoint)

## Diferença em relação à v12

| Componente | v12 | v12b |
|-----------|-----|------|
| Velocidade alvo | por índice de waypoint | por ponto da racing line (XY) |
| Posição na pista | não considera | recompensa por seguir a linha |
| Heading | alinhado com a pista | alinhado com a racing line |
| Pesos | speed 0.60 / heading 0.40 | speed 0.40 / line 0.35 / heading 0.25 |

## Ponto de partida: clone da v9

Mesma base da v12 — modelo que sabe ficar na pista.

## Hiperparâmetros

| Parâmetro | Valor | Motivo |
|-----------|-------|--------|
| Entropy | 0.02 | Racing line é nova informação — precisa explorar |
| LR | 0.0002 | Aprender a nova geometria |
