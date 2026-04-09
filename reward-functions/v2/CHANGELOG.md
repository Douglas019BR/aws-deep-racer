# Changelog — Função de Recompensa DeepRacer

## v2 (`douglas-joao-treinamento-2.py`)

### Análise da pista: re:Invent 2018 (`reinvent_base.npy`)

Antes de alterar a função, analisamos os 119 waypoints da pista para entender seu perfil:

| Zona | Curvatura | Waypoints | % da pista |
|------|-----------|-----------|------------|
| Reta | < 5° | 72 | 61% |
| Curva suave | 5° – 15° | 46 | 39% |
| Curva fechada | > 15° | 1 | 1% |

- Curvatura máxima: 20° (apenas no waypoint 106)
- Comprimento total: ~17.7m
- Conclusão: pista majoritariamente reta, com curvas suaves e praticamente nenhuma curva fechada

### O que mudou da v1 para a v2

#### Removido
- **Centralização** — recompensar o centro da pista conflita com a linha ideal nas curvas
- **Smooth driving** — o action space já limita transições possíveis, penalizar mudanças bruscas era redundante
- **Speed bonus** — já coberto pelo componente de velocidade adaptativa
- **Penalidade steering + velocidade** — simplificado junto com os demais componentes
- **Estado anterior** (`prev_steering`, `prev_speed`) — não é mais necessário sem smooth driving

#### Simplificado
- **Heading** deixou de ser um componente ponderado e virou um gate binário: desalinhamento > 30° retorna reward mínima imediatamente
- **Componentes ponderados**: de 6 para 2 (velocidade adaptativa + eficiência)
- **Linhas de código**: de ~90 para ~45

#### Calibrado para a pista
- **Faixas de velocidade** passaram de 3 para 4, baseadas na análise de curvatura:

| Curvatura | v1 (velocidade) | v2 (velocidade) |
|-----------|-----------------|-----------------|
| ≤ 5° | 4.0 | 4.0 |
| 5° – 10° | 2.7 | **3.3** |
| 10° – 15° | 2.7 | **2.5** |
| > 15° | 1.3 | **1.5** |

- A faixa 5-10° foi separada e recebeu velocidade mais alta (3.3), já que a pista tem muitas curvas leves onde 2.7 era conservador demais
- **Bônus de volta completa**: de fixo (+10.0) para escalonado por steps, usando 110 steps como referência (`max(15.0 * (110.0 / steps), 2.0)`)

### Motivação

Funções de recompensa complexas com muitos componentes ponderados geram sinais conflitantes que dificultam o aprendizado do modelo. A v2 foca em 2 sinais claros:

1. **Andar na velocidade certa para a curvatura à frente**
2. **Completar a volta no menor número de steps possível**

Sinal mais limpo = convergência mais rápida no treino.

---

## v1 (`douglas-joao-treinamento-1.py`)

Versão inicial com 6 componentes ponderados:
- Heading (0.12)
- Velocidade adaptativa (0.25)
- Centralização (0.12)
- Smooth driving (0.18)
- Eficiência (0.23)
- Speed bonus (0.10)

Bônus fixo de +10.0 por volta completa.
