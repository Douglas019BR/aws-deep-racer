# Changelog v4 → v5

## Pista: Indy (deepracerindy) | Comprimento: 17.71m

---

## Problemas identificados na v4

| Problema | Impacto |
|----------|---------|
| Heading gate binário (>20° = 1e-3) | Modelo evita curvas agressivas, prefere ir devagar |
| `speed_reward` e `speed_bonus` conflitantes | Sinais opostos em curvas — modelo fica confuso |
| 77.5% das ações usam throttle mínimo (1.5) | Carro anda quase sempre na velocidade mais baixa |
| `step_efficiency` com target de 110 steps | Irrealista — voltas reais precisam de ~140-150 steps |
| Pesos iguais (0.30/0.30/0.30) | Sem prioridade clara de otimização |
| Modelo degrada após iteração ~10 | Overfitting / catastrophic forgetting |

## Mudanças na reward function v5

### 1. Heading gradual (antes: gate binário)
- **v4:** `direction_diff > 20 → return 1e-3`
- **v5:** `heading_reward = max(1.0 - direction_diff / 30.0, 0.0)` — decaimento suave

### 2. Sinal único de velocidade (antes: dois sinais conflitantes)
- **v4:** `speed_reward` + `speed_bonus` separados com sinais opostos em curva
- **v5:** Um único `speed_reward` adaptativo — retas premiam velocidade alta, curvas premiam velocidade ideal

### 3. Penalidade de steering em retas (novo)
- Penaliza steering >10° em trechos retos para reduzir zigue-zague
- v4 não tinha isso — 97% das ações usavam steering ≥7°

### 4. Look-ahead fixo (antes: variável com speed)
- **v4:** `look_ahead = max(3, int(speed * 2.5))` — instável pois muda com a velocidade
- **v5:** Look-ahead fixo de 6 waypoints — sinal consistente

### 5. Pesos diferenciados
- **v4:** speed 0.30 / heading 0.30 / efficiency 0.30
- **v5:** speed 0.40 / heading 0.30 / center 0.20 — velocidade é prioridade

### 6. Bônus de progresso contínuo (novo)
- `progress / 200.0` — incentiva avançar mesmo sem completar volta

### 7. Target de steps ajustado
- **v4:** 110 steps (irrealista)
- **v5:** 130 steps (mais próximo da realidade com velocidade maior)

### 8. Removido `step_efficiency` como componente separado
- Era quase sempre ~0 com o target errado, não contribuía

---

## Hyperparameters recomendados

| Parâmetro | v4 | v5 (recomendado) | Motivo |
|-----------|-----|-------------------|--------|
| Batch size | 128 | 64 | Menor = atualizações mais frequentes, melhor generalização |
| Epochs | 10 | 5 | Reduzir para evitar overfitting |
| Learning rate | 0.0003 | 0.0001 | Mais baixo para estabilizar a política |
| Discount factor (γ) | 0.999 | 0.99 | Focar mais em recompensas imediatas |
| Loss type | Huber | Huber | Manter — robusto a outliers |
| Entropy | 0.005 | 0.02 | 4x maior — v4 parou de explorar muito cedo |
| Num episodes per iteration | 20 | 20 | OK |
| Max iterations | 38 | 18 | Parar antes — v4 degradou após iter 10 |

### Justificativas

- **Batch size 128 → 64:** Batch grande demais com 20 episódios por iteração significa poucas atualizações de gradiente. Batch 64 dobra o número de updates, ajudando o modelo a aprender mais rápido.
- **Learning rate 0.0003 → 0.0001:** Na v4 o modelo oscilava muito nas iterações finais (reward -7 a 95). LR menor estabiliza.
- **Epochs 10 → 5:** Com 10 epochs o modelo fazia muitas passagens sobre os mesmos dados, causando overfitting. 5 é suficiente com batch menor.
- **Discount factor 0.999 → 0.99:** γ=0.999 faz o modelo valorizar demais recompensas futuras distantes. Com pista curta (17.71m), 0.99 é mais adequado — foca no curto prazo e aprende a curvar corretamente.
- **Entropy 0.005 → 0.02:** Este é o problema mais grave da v4. Entropy 0.005 é extremamente baixo — o modelo parou de explorar muito cedo e convergiu para throttle=1.5 em 77.5% das ações. Com 0.02 o modelo será forçado a experimentar velocidades maiores por mais tempo antes de convergir.
- **Max 18 iterações:** Monitorar a partir da iteração 10. Se reward médio de avaliação não subir após 3 iterações consecutivas, parar.

---

## Action Space recomendado

### v4 (atual) — 19 ações
- 7 ângulos de steering: -21°, -14°, -7°, 0°, 7°, 14°, 21°
- 4 velocidades: 1.5, 2.7, 3.5, 4.0
- Problema: 77.5% das ações usavam throttle 1.5. Ações com velocidade alta quase nunca eram escolhidas.

### v5 (recomendado) — 19 ações (clone, mesma quantidade)

| #  | Steering | Velocidade | Uso |
|----|----------|------------|-----|
|  0 | 0°       | 3.8        | Reta — velocidade máxima |
|  1 | 0°       | 3.0        | Reta — velocidade alta |
|  2 | 0°       | 2.2        | Reta — velocidade média |
|  3 | 5°       | 3.2        | Ajuste mínimo direita rápido |
|  4 | -5°      | 3.2        | Ajuste mínimo esquerda rápido |
|  5 | 10°      | 2.6        | Curva suave direita |
|  6 | -10°     | 2.6        | Curva suave esquerda |
|  7 | 10°      | 1.8        | Curva suave direita lento |
|  8 | -10°     | 1.8        | Curva suave esquerda lento |
|  9 | 15°      | 2.0        | Curva média direita |
| 10 | -15°     | 2.0        | Curva média esquerda |
| 11 | 20°      | 1.6        | Curva forte direita |
| 12 | -20°     | 1.6        | Curva forte esquerda |
| 13 | 25°      | 1.4        | Curva muito forte direita |
| 14 | -25°     | 1.4        | Curva muito forte esquerda |
| 15 | 7°       | 2.8        | Curva leve direita rápido |
| 16 | -7°      | 2.8        | Curva leve esquerda rápido |
| 17 | 0°       | 1.6        | Frenagem / preparação de curva |
| 18 | 0°       | 4.0        | Reta — velocidade total |

**Princípios do redesign:**
- Simétrico (esquerda/direita) — pista Indy tem curvas nos dois sentidos
- Velocidade mínima subiu: 1.4 só em curvas >25°, retas forçam ≥2.2
- Mais steering alto + velocidade baixa = curvas mais seguras
- Mais steering baixo + velocidade alta = retas mais rápidas
- 3 opções de reta (3.8, 3.0, 2.2) para o modelo aprender a acelerar gradualmente
- Ação 17 (frenagem) para transição reta→curva sem sair da pista
- Removidas combinações inúteis da v4 (ex: steering -21° com throttle 1.5 era 17% das ações — agora steering alto sempre tem velocidade proporcional)

---

## Checklist pré-treinamento

- [ ] Configurar action space (Opção A ou B)
- [ ] Definir hyperparameters conforme tabela
- [ ] Pista: Indy
- [ ] Max iterations: 18
- [ ] Monitorar: se reward médio de avaliação não subir após 3 iterações consecutivas, parar
- [ ] Objetivo: velocidade média >2.5, taxa de conclusão >85%
