# Changelog — v3 (`douglas-joao-treinamento-3.py`)

## Resumo dos resultados da v2

O treinamento v2 convergiu com sucesso após ~700 episódios na pista re:Invent 2018, atingindo 100% de voltas completas nas avaliações finais com reward médio ~198. Porém a análise dos logs revelou 5 problemas que atrasaram a convergência e deixam margem para melhorar o tempo de volta.

---

## O que mudou da v2 para a v3

### 1. Heading gate: 30° → 20°

**Problema:** Na re:Invent 2018, a curvatura máxima é 20° (waypoint 106). Um gate de 30° praticamente nunca era ativado — não filtrava comportamento ruim.

**Mudança:** Gate reduzido para 20°. Qualquer desalinhamento acima disso retorna reward mínima imediatamente. Isso dá um sinal mais claro e corta episódios ruins mais cedo, acelerando o aprendizado.

### 2. Look-ahead fixo (5 wp) → adaptativo por velocidade

**Problema:** 5 waypoints = ~0.75m. Em velocidade 4.0 m/s, o carro percorre ~0.6m por step — o look-ahead era menor que 2 steps à frente, insuficiente para antecipar curvas.

**Mudança:**
```python
look_ahead = max(3, int(speed * 2.5))
```

| Velocidade | Look-ahead (waypoints) | Distância (~m) |
|------------|----------------------|----------------|
| 1.5        | 3                    | 0.45           |
| 2.7        | 6                    | 0.90           |
| 4.0        | 10                   | 1.50           |

Em velocidade alta, o modelo "enxerga" mais longe e pode frear antes das curvas.

### 3. Velocidades ótimas alinhadas ao action space

**Problema:** A v2 definia `optimal_speed = 3.5` para curvas de 5-10°, mas 3.5 só existe no action space com ângulo ±14°. O modelo nunca conseguia atingir a velocidade ótima em curvas leves com steering baixo.

**Mudança:** Simplificado para 3 faixas que correspondem exatamente às velocidades do action space:

| Curvatura | v2 (velocidade) | v3 (velocidade) | Disponível no AS |
|-----------|-----------------|-----------------|------------------|
| ≤ 5°     | 4.0             | 4.0             | ✅ (0°, ±7°)     |
| 5° – 15° | 3.5 / 2.7       | **2.7**         | ✅ (todos ângulos)|
| > 15°    | 1.5             | 1.5             | ✅ (todos ângulos)|

A faixa intermediária (5-15°) foi unificada em 2.7 porque é a única velocidade disponível em todos os ângulos de steering, dando ao modelo flexibilidade total para escolher a trajetória.

### 4. Eficiência com piso de steps

**Problema:** Nos primeiros steps, `progress/steps` era extremamente ruidoso (step 1 com 1% progress = reward de 2.5, step 2 com 1% = 1.25). Com peso 0.55, isso dominava o sinal e gerava ruído no início de cada episódio.

**Mudança:**
```python
effective_steps = max(steps, 15)
efficiency = (progress / effective_steps) * 2.5
```

O piso de 15 steps estabiliza o componente nos primeiros momentos do episódio. Após 15 steps, o comportamento é idêntico à v2.

### 5. Penalidade de borda (novo)

**Problema:** A v2 removeu centralização, mas mesmo no modelo convergido (~ep 700+), ~5% dos episódios ainda terminavam em off-track. O modelo não tinha nenhum sinal para evitar as bordas.

**Mudança:** Penalidade leve (-0.2) quando o carro está no último 20% da largura da pista (de cada lado):
```python
if distance_from_center > 0.4 * track_width:
    border_penalty = 0.2
```

Não força centralização (que conflita com racing line), apenas desencoraja andar na borda extrema.

### 6. Pesos ajustados

| Componente | v2   | v3   |
|------------|------|------|
| Velocidade | 0.45 | 0.40 |
| Eficiência | 0.55 | 0.50 |
| Borda      | —    | -0.20 (penalidade) |

O espaço liberado pela redução dos pesos acomoda a penalidade de borda sem inflar a reward total.

---

## Mudanças recomendadas no Action Space

O action space atual tem um gap: velocidade 3.5 só existe em ±14°, e não há velocidade intermediária entre 2.7 e 4.0 para ângulos baixos.

### Action space sugerido (22 ações)

```json
[
  {"speed": 1.5, "steering_angle": -20},
  {"speed": 2.7, "steering_angle": -20},
  {"speed": 1.5, "steering_angle": -15},
  {"speed": 2.7, "steering_angle": -15},
  {"speed": 1.5, "steering_angle": -10},
  {"speed": 2.7, "steering_angle": -10},
  {"speed": 1.5, "steering_angle": -5},
  {"speed": 2.7, "steering_angle": -5},
  {"speed": 4.0, "steering_angle": -5},
  {"speed": 1.5, "steering_angle": 0},
  {"speed": 2.7, "steering_angle": 0},
  {"speed": 4.0, "steering_angle": 0},
  {"speed": 1.5, "steering_angle": 5},
  {"speed": 2.7, "steering_angle": 5},
  {"speed": 4.0, "steering_angle": 5},
  {"speed": 1.5, "steering_angle": 10},
  {"speed": 2.7, "steering_angle": 10},
  {"speed": 1.5, "steering_angle": 15},
  {"speed": 2.7, "steering_angle": 15},
  {"speed": 1.5, "steering_angle": 20},
  {"speed": 2.7, "steering_angle": 20}
]
```

**Mudanças em relação ao AS da v2:**
- Removido 3.5 (não alinha com a reward function e só existia em ±14°)
- Granularidade de steering: 5° em vez de 7° — melhor controle em curvas suaves
- Velocidade 4.0 restrita a ±5° e 0° — só faz sentido em retas
- 22 ações (vs 19 na v2) — aumento pequeno, não impacta convergência significativamente

> **Nota:** Se preferir manter o action space atual de 19 ações, a reward function v3 já funciona — ela foi desenhada para alinhar com as velocidades 1.5, 2.7 e 4.0 que existem no AS atual.

---

## Mudanças recomendadas nos Hyperparameters

### Parâmetros a alterar

| Parâmetro | v2 | v3 (sugerido) | Motivo |
|-----------|-----|---------------|--------|
| `lr` | 0.0002 | **0.0003** | A reward function v3 tem sinal mais limpo (gate mais restritivo, eficiência estabilizada). Um lr levemente maior pode acelerar a convergência inicial sem instabilidade |
| `beta_entropy` | 0.002 | **0.005** | Mais exploração no início. A v2 levou 160 episódios para a primeira volta — mais entropia pode ajudar o modelo a descobrir trajetórias boas mais rápido |
| `num_episodes_between_training` | 20 | **20** | Manter. 20 episódios por iteração funcionou bem |
| `batch_size` | 128 | **128** | Manter |
| `num_epochs` | 10 | **10** | Manter |
| `discount_factor` | 0.99 | **0.999** | Aumentar levemente. Com a penalidade de borda, o modelo precisa considerar consequências mais distantes (andar na borda agora → off-track em 5 steps) |

### Parâmetros a manter

- `loss_type: huber` — robusto a outliers, bom para reward functions com bônus de volta
- `exploration_type: categorical` — adequado para action space discreto
- `stack_size: 1` — sem necessidade de frames empilhados com câmera frontal

### Tempo de treinamento sugerido

A v2 convergiu em ~700 episódios (35 iterações). Com o sinal mais limpo da v3, espera-se convergência em **500-600 episódios**. Recomendo configurar o treinamento para **800 episódios** (40 iterações) para garantir estabilização.

---

## Resumo das mudanças

```
v2                              →  v3
─────────────────────────────────────────────────
Heading gate 30°                →  20°
Look-ahead fixo 5 wp            →  Adaptativo (3-10 wp)
4 faixas de velocidade           →  3 faixas (alinhadas ao AS)
Eficiência sem piso              →  Piso de 15 steps
Sem penalidade de borda          →  -0.2 no último 20% da largura
Pesos: 0.45/0.55                 →  0.40/0.50 + penalidade
~45 linhas                       →  ~50 linhas
```
