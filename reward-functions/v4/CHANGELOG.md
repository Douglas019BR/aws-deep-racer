# Changelog — v4 (`douglas-joao-treinamento-4.py`)

## Resumo dos resultados da v3

O treinamento v3 rodou 59 iterações (1.180 episódios) na pista re:Invent 2018, com 102.055 steps totais.

### Métricas gerais
- **518 voltas completas** de 1.180 episódios → taxa de conclusão de **43.9%**
- Progresso médio: **59.5%** | Mediano: **67.7%**
- Reward médio: **105.24** | Máximo: **222.01**

### Convergência
- Iterações 0-10: fase exploratória (~10-17% progresso)
- Iterações 11-25: aprendizado acelerando (~25-50%)
- Iterações 26-35: salto grande (59% → 92%)
- Iterações 36-58: modelo maduro, progresso médio >90%, várias iterações com 100%

### Tempos de volta
- **Melhor volta: 7.95s** (episódio 539, 122 steps)
- Média das voltas completas: **9.75s**
- Top 5 mais rápidas: 7.95s, 8.02s, 8.02s, 8.02s, 8.22s — todas entre episódios 503-576

### Problema principal identificado: o modelo convergiu para lentidão

As voltas mais rápidas (7.95-8.22s, ~122-126 steps) aconteceram nas iterações 25-28. Porém, nas iterações finais (40-58), o modelo estabilizou em voltas de **~10s com 150-162 steps** — e essas voltas recebiam **reward mais alto** (218-222) do que as rápidas (146-167).

**Causa raiz:** a fórmula `efficiency = (progress / steps) * 2.5` acumula mais reward total em voltas com mais steps. Uma volta de 150 steps soma mais reward ao longo do caminho do que uma de 122 steps, mesmo que cada step individual tenha reward menor. O modelo aprendeu que ir devagar e seguro maximiza o reward acumulado.

### Estabilidade do simulador
- Média: 66.7ms/step (target: 66.6ms) ✅
- P95: 85ms ✅
- Spike pontual de 1774ms na iteração 57 (sem impacto)

---

## O que mudou da v3 para a v4

### 1. Penalidade de offtrack: `1e-3` → `-1.0`

**Problema:** Retornar `1e-3` (praticamente zero) não diferencia "sair da pista" de "estar muito desalinhado" (que também retorna `1e-3`). O modelo não tinha incentivo forte para evitar offtrack.

**Mudança:** Retorna `-1.0` quando `is_offtrack` ou `all_wheels_on_track == False`. Reward negativo cria um gradiente real de punição — o modelo vai ativamente evitar ações que levem ao offtrack.

### 2. Eficiência: `progress/steps` → projeção de steps totais

**Problema:** `progress/steps` premia cada step individualmente. Uma volta lenta (150 steps) acumula mais reward total do que uma rápida (122 steps), porque tem mais steps recebendo reward. Isso fez o modelo convergir para 10s em vez de 8s.

**Mudança:**
```python
projected_steps = (effective_steps / max(progress, 1.0)) * 100.0
step_efficiency = max(1.0 - (projected_steps - 110.0) / 60.0, 0.0)
```

Em vez de premiar `progress/steps` por step, projeta quantos steps a volta inteira teria no ritmo atual e compara com o target de 110 steps. Isso dá o mesmo reward por step independente de estar no step 10 ou 100 — o que importa é o ritmo.

| Ritmo projetado | step_efficiency |
|-----------------|-----------------|
| 110 steps       | 1.0 (máximo)    |
| 130 steps       | 0.67            |
| 150 steps       | 0.33            |
| 170 steps       | 0.0             |

### 3. Novo componente: speed_bonus quadrático

**Problema:** O `speed_reward` da v3 só premia estar perto da velocidade ótima para a curvatura. Não há incentivo direto para ir rápido — ir a 2.7 numa reta dá reward 0.67, mas ir a 1.5 numa curva forte também dá 1.0.

**Mudança:**
```python
speed_bonus = (speed / 4.0) ** 2
```

| Velocidade | speed_bonus |
|------------|-------------|
| 1.5        | 0.14        |
| 2.7        | 0.46        |
| 4.0        | 1.00        |

O expoente quadrático faz a diferença entre velocidades altas ser muito mais significativa. Combinado com `speed_reward`, o modelo é incentivado a ir rápido E na velocidade certa para a curvatura.

### 4. Penalidade de borda: fixa → progressiva

**Problema:** A v3 aplicava penalidade fixa de 0.2 quando `distance_from_center > 0.4 * track_width`. Isso cria uma descontinuidade — estar a 39% da borda dá 0 de penalidade, estar a 41% dá 0.2.

**Mudança:**
```python
center_ratio = distance_from_center / (0.5 * track_width)
border_penalty = max(center_ratio - 0.6, 0.0) * 0.5
```

| Posição (% da meia-largura) | Penalidade |
|-----------------------------|------------|
| ≤ 60%                       | 0.0        |
| 70%                         | 0.05       |
| 80%                         | 0.10       |
| 90%                         | 0.15       |
| 100% (borda)                | 0.20       |

Gradiente suave — o modelo sente a penalidade aumentar conforme se aproxima da borda, em vez de um degrau abrupto.

### 5. Bônus de volta completa: linear → quadrático

**Problema:** O bônus `15 * (110/steps)` da v3 dava:
- 122 steps → bônus 13.5
- 150 steps → bônus 11.0
- Diferença: apenas 2.5 pontos

**Mudança:**
```python
reward += 20.0 * (110.0 / effective_steps) ** 2
```

| Steps | v3 (bônus) | v4 (bônus) | Diferença |
|-------|-----------|-----------|-----------|
| 110   | 15.0      | 20.0      | +5.0      |
| 122   | 13.5      | 16.3      | +2.8      |
| 135   | 12.2      | 13.3      | +1.1      |
| 150   | 11.0      | 10.8      | -0.2      |
| 170   | 9.7       | 8.4       | -1.3      |

O expoente quadrático amplifica a diferença entre voltas rápidas e lentas. Uma volta de 122 steps agora recebe 6 pontos a mais que uma de 150 steps (vs 2.5 na v3).

### 6. Pesos redistribuídos

| Componente      | v3   | v4   |
|-----------------|------|------|
| speed_reward    | 0.40 | 0.30 |
| efficiency      | 0.50 | 0.30 |
| speed_bonus     | —    | 0.30 |
| border_penalty  | -0.20 (fixa) | -0.00 a -0.20 (progressiva) |

A v3 dava 90% do peso para velocidade + eficiência. A v4 divide em 3 partes iguais: velocidade correta (30%), velocidade alta (30%), e ritmo de steps (30%). Isso evita que um único componente domine.

---

## Resumo das mudanças

```
v3                                →  v4
──────────────────────────────────────────────────
Offtrack: 1e-3 (ignora)           →  -1.0 (punição real)
Eficiência: progress/steps        →  Projeção de steps vs target 110
Sem bônus de velocidade            →  speed_bonus quadrático (speed/4)²
Borda: penalidade fixa 0.2        →  Penalidade progressiva 0.0-0.2
Bônus volta: 15*(110/s) linear    →  20*(110/s)² quadrático
Pesos: 0.40/0.50                  →  0.30/0.30/0.30
~50 linhas                         →  ~55 linhas
```

## Resultado esperado

O modelo deve convergir para voltas de **~8s (120-125 steps)** em vez de 10s, porque:
1. Ir rápido agora é diretamente recompensado (speed_bonus)
2. Voltas lentas não acumulam mais reward total (projeção de steps)
3. O bônus de volta completa favorece fortemente menos steps
4. Offtrack tem punição real, forçando o modelo a aprender limites sem precisar ir devagar
