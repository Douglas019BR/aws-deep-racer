# Changelog v6 → v7

## Única mudança

### `all_wheels_on_track` como aviso prévio

**v6:** Só verificava `is_offtrack` → `-1.0`. Sem sinal intermediário.
**v7:** Adiciona check de `all_wheels_on_track == False` → `1e-3` (reward quase zero, mas não negativo).

Isso cria um gradiente de 3 níveis:
1. Na pista, rodas dentro → reward normal
2. Rodas saindo da pista → `1e-3` (aviso: "volta pro centro")
3. Offtrack → `-1.0` (punição real)

O modelo agora tem um sinal de "estou quase saindo" antes de receber a punição máxima. Isso deve reduzir o off-track rate sem sacrificar velocidade.

## Tudo mais igual à v6

Reward function, pesos, action space, tudo mantido.
