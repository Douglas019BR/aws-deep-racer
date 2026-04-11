# Changelog v7 → v8

## Problema: modelo convergiu pra lentidão

A v7 resolveu o off-track (38% conclusão vs 2.5% na v6), mas o modelo aprendeu que ir devagar = completar = reward alto. Tempos subiram de 8.94s → 10.21s ao longo do treino. Throttle 1.33 domina com 67%.

---

## Mudanças v7 → v8

### 1. Penalidade por velocidade baixa em retas (novo)

```python
slow_penalty = 0.3 if speed < 2.0 else 0.0
```

Se o carro está numa reta e usando velocidade < 2.0 (basicamente throttle 1.33), perde 0.3 de reward. Isso ataca diretamente o problema de 67% das ações em throttle mínimo.

### 2. Bônus de volta completa: quadrático → cúbico

**v7:** `15 * (130/steps)²`
**v8:** `25 * (120/steps)³`

| Steps | v7 bônus | v8 bônus | Diferença |
|-------|---------|---------|-----------|
| 110   | 20.9    | 30.5    | +9.6      |
| 120   | 17.6    | 25.0    | +7.4      |
| 130   | 15.0    | 19.7    | +4.7      |
| 140   | 12.9    | 15.7    | +2.8      |
| 150   | 11.3    | 12.8    | +1.5      |
| 160   | 9.9     | 10.5    | +0.6      |

O expoente cúbico cria diferença brutal: 120 steps ganha 25.0, 160 steps ganha 10.5. Na v7 a diferença era só 7.7 pontos, agora é 14.5.

### 3. Step cost mais agressivo

**v7:** `(steps/150)² * 0.03`
**v8:** `(steps/130)² * 0.05`

| Steps | v7 custo | v8 custo |
|-------|---------|---------|
| 50    | 0.003   | 0.007   |
| 100   | 0.013   | 0.030   |
| 130   | 0.023   | 0.050   |
| 150   | 0.030   | 0.067   |

Dobra a pressão por step. O modelo sente o custo mais cedo.

### 4. Center reward reduzido: 0.15 → 0.10

Libera peso pra velocidade e heading. Centralização é menos importante que ir rápido.

### 5. Target de steps: 130 → 120

Baseado nos dados da v7: as melhores voltas tinham 111-120 steps. Target mais agressivo.

---

## Hiperparâmetros (sessão v8)

| Parâmetro | v7 | v8 | Motivo |
|-----------|-----|-----|--------|
| Entropy | 0.02 | 0.025 | Subir — modelo precisa re-explorar velocidades altas |
| LR | 0.0002 | 0.0003 | Subir — novo sinal de reward, precisa aprender rápido |
| Batch size | 64 | 64 | Manter |
| Epochs | 5 | 5 | Manter |
| Discount (γ) | 0.99 | 0.99 | Manter |
| Loss | Huber | Huber | Manter |

A entropy e LR sobem porque a reward mudou significativamente. O modelo precisa desaprender "devagar é bom" e re-explorar velocidades altas.

---

## Resultado esperado

- Manter conclusão > 30% (v7 tinha 38%)
- Volta média < 9.0s (v7 convergiu pra 10.2s)
- Throttle 1.33 < 50% (v7 tinha 67%)
- Vel média > 2.2 (v7 caiu pra 1.93)
