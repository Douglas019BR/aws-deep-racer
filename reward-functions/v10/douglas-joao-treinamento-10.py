import math


def reward_function(params):
    # Punição real por sair da pista
    if params["is_offtrack"]:
        return -1.0

    # Aviso prévio — rodas saindo mas ainda não offtrack
    if not params["all_wheels_on_track"]:
        return 1e-3

    waypoints = params["waypoints"]
    closest = params["closest_waypoints"]
    heading = params["heading"]
    speed = params["speed"]
    progress = params["progress"]
    steps = params["steps"]
    track_width = params["track_width"]
    distance_from_center = params["distance_from_center"]
    steering_angle = params["steering_angle"]

    # 1) Heading — alinhamento com a pista
    next_wp = waypoints[closest[1]]
    prev_wp = waypoints[closest[0]]
    track_dir = math.degrees(
        math.atan2(next_wp[1] - prev_wp[1], next_wp[0] - prev_wp[0])
    )
    direction_diff = abs(track_dir - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    heading_reward = max(1.0 - (direction_diff / 25.0), 0.0)

    # 2) Curvatura à frente — look-ahead de 6 waypoints
    n_wp = len(waypoints)
    far_wp = waypoints[(closest[1] + 6) % n_wp]
    future_dir = math.degrees(
        math.atan2(far_wp[1] - next_wp[1], far_wp[0] - next_wp[0])
    )
    curve_diff = abs(future_dir - track_dir)
    if curve_diff > 180:
        curve_diff = 360 - curve_diff

    # 3) Velocidade — prioridade máxima
    is_straight = curve_diff < 10
    if is_straight:
        # Reta: quadrático, só 4.0 m/s dá reward máximo
        speed_reward = (speed / 4.0) ** 2
        steering_penalty = (abs(steering_angle) / 21.0) ** 2 * 0.3
    else:
        # Curva: velocidade ideal mas com forte bônus por ir acima do mínimo
        ideal = max(1.33, 3.0 - curve_diff * 0.06)
        speed_reward = max(1.0 - abs(speed - ideal) / 3.0, 0.0)
        speed_reward += (speed / 4.0) * 0.5  # bônus de velocidade em curvas (era 0.3)
        steering_penalty = 0.0

    # 4) Penalidade agressiva por velocidade baixa — sempre ativa
    # v9: max(0.4 - speed/4.0, 0.0) → máx 0.07 em 1.33
    # v10: max(0.8 - speed/4.0, 0.0) → máx 0.47 em 1.33 — torna 1.33 muito caro
    slow_penalty = max(0.8 - speed / 4.0, 0.0)

    # 5) Centralização suave — peso reduzido, velocidade é prioridade
    center_ratio = distance_from_center / (0.5 * track_width)
    center_reward = max(1.0 - center_ratio ** 2, 0.0)

    # 6) Step cost progressivo
    step_cost = (steps / 130.0) ** 2 * 0.05

    # Reward ponderado — velocidade domina
    reward = (
        0.50 * speed_reward      # era 0.40 — velocidade é o único objetivo agora
        + 0.25 * heading_reward  # era 0.30 — reduzido mas mantido pra não perder controle
        + 0.05 * center_reward   # era 0.10 — quase irrelevante
        - steering_penalty
        - slow_penalty
        - step_cost
    )

    # Bônus de progresso contínuo
    reward += progress / 100.0

    # Bônus de volta completa — cúbico, fortemente favorece menos steps
    if progress >= 99.0:
        reward += 25.0 * (120.0 / max(steps, 1)) ** 3

    return float(max(reward, 1e-3))
