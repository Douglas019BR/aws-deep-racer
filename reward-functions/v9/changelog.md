# Changelog v8 → v9

## Problema: modelo estável mas lento

V8 alcançou 93.8% conclusão na evaluation, mas tempos estagnaram em ~11s. Throttle 1.33 ainda domina com 60%. A slow_penalty binária (0.3 se speed < 2.0) fez o modelo evitar retas em vez de ir mais rápido nelas.

---

## Mudanças v8 → v9

### 1. Slow penalty: binária → gradual, em qualquer trecho

**v8:** `0.3 if speed < 2.0 and is_straight else 0.0`
**v9:** `max(0.4 - speed/4.0, 0.0)` — sempre ativa

| Velocidade | v8 penalty | v9 penalty |
|-----------|-----------|-----------|
| 1.33      | 0.3 (reta) / 0.0 (curva) | 0.07 |
| 2.00      | 0.0       | 0.10      |
| 2.67      | 0.0       | 0.07      |
| 4.00      | 0.0       | 0.00      |

Agora o modelo sente pressão pra ir rápido em qualquer lugar, não só em retas. E é gradual — sem descontinuidade.

### 2. Speed reward em curvas: bônus por velocidade

**v8:** Só premia velocidade ideal em curvas
**v9:** Adiciona `(speed/4.0) * 0.3` em curvas

O modelo agora é incentivado a ir o mais rápido possível mesmo em curvas, não só na velocidade "ideal". Curvar a 2.67 dá mais reward que curvar a 1.33.

### 3. Peso do speed_reward: 0.35 → 0.40

Velocidade é o problema #1. Aumenta o peso pra ser o componente dominante.

### 4. Steering penalty em retas: 0.5 → 0.4

Reduz levemente pra não competir tanto com o incentivo de velocidade.

---

## Ponto de partida: clone da v7

A v8 sofreu catastrophic forgetting — LR 0.0003 e entropy 0.025 destruíram o que o modelo já sabia. Reward médio caiu de 105 → 35, conclusão caiu de 57% → 20% ao longo do treino.

A v7 tinha base sólida (38% conclusão training, 75.8% eval). A v9 parte do **clone da v7** com a nova reward, descartando o aprendizado degradado da v8.

## Hiperparâmetros

| Parâmetro | v8 | v9 | Motivo |
|-----------|-----|-----|--------|
| Entropy | 0.025 | **0.015** | Modelo já sabe ficar na pista, só ajustar velocidade |
| LR | 0.0003 | **0.00015** | Meio-termo: aprender o novo sinal sem destruir a v7 |
| Resto | igual | igual | |

Lição da v8: quando muda a reward em cima de um modelo treinado, LR e entropy precisam ser baixos. Valores altos são pra treino do zero.
