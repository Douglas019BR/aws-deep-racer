# Changelog v11 → v12

## Problema: corte duro destruiu o gradiente de aprendizado

A v11 introduziu velocidade alvo por waypoint — boa ideia — mas com corte duro:
`if speed_diff > 1.0: return 1e-3`

Resultado: taxa de conclusão caiu de 98.3% → 38.5% e continuou caindo ao longo do treino.

| Bloco v11    | Taxa 100% |
|-------------|-----------|
| iter 1–50   | 80.0%     |
| iter 51–100 | 89.2%     |
| iter 201–250| 56.7%     |
| iter 401–450| 28.3%     |
| iter 601–621| 34.6%     |

Quando o modelo errava a velocidade por >1 m/s, recebia `1e-3` — sem sinal de heading, sem sinal de progresso. Parou de aprender a ficar na pista.

O throttle médio melhorou (1.73 → 1.86) e o mínimo de steps foi 117 — a ideia funciona, a implementação não.

---

## Mudança v11 → v12: penalidade suave em vez de corte duro

**v11:** `if speed_diff > 1.0: return 1e-3`
**v12:** `speed_reward = max(1.0 - (speed_diff / 2.67), 0.1)`

| Speed | Target | v11 reward | v12 reward |
|-------|--------|-----------|-----------|
| 1.33  | 4.00   | **0.001** | 0.10      |
| 2.00  | 4.00   | **0.001** | 0.25      |
| 2.67  | 4.00   | **0.001** | 0.50      |
| 3.33  | 4.00   | 0.33      | 0.75      |
| 4.00  | 4.00   | 1.00      | 1.00 (+0.5 bônus) |

O modelo agora **sempre recebe gradiente** — mesmo indo devagar numa reta, sabe que precisa ir mais rápido. E o heading e progresso continuam contribuindo, então ele não perde o aprendizado de ficar na pista.

O piso de `0.1` garante que nunca há um "buraco" de reward que confunda o modelo.

---

## Plano de treinamento: 8h na v12

Com 10h restantes, usar 8h na v12 e guardar 2h para ajuste fino ou v13.

**Ponto de partida:** clone da v9 — melhor base de "saber ficar na pista".
A v11 não é boa base porque desaprendeu a completar voltas.

## Hiperparâmetros

| Parâmetro | v11    | v12        | Motivo |
|-----------|--------|------------|--------|
| Entropy   | 0.02   | **0.015**  | Menos exploração — reward mais suave já guia melhor |
| LR        | 0.0002 | **0.0002** | Manter — precisa aprender o sinal de velocidade por waypoint |
