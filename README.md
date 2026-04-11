# AWS DeepRacer — Modelos de Treinamento

Repositório com reward functions, logs de treinamento e dados de pista para o AWS DeepRacer. (Abril 2026)

Pista: **re:Invent 2018** (reinvent_base) — 17.71m, ~61% reta.

## Estrutura

```
├── reward-functions/     # Reward functions por versão
│   ├── v1/               # Versão inicial
│   ├── v2/
|   ...
│   ├── v6/               # Primeira versão na conta nova (do zero)
│   ├── v7/               # +all_wheels_on_track
│   ...
├── logs/                 # Logs de treinamento (.tar.gz + extraídos)
│   ├── v2/
│   ├── v3/
|   ...
└── tracks/               # Waypoints das pistas (.npy)
    └── reinvent_base.npy
```

Cada versão em `reward-functions/` contém:
- `douglas-joao-treinamento-N.py` — a reward function
- `changelog.md` / `CHANGELOG.md` — análise da versão anterior e justificativa das mudanças
