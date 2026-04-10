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

    # 1) Heading — recompensa gradual por alinhamento com a pista
    next_wp = waypoints[closest[1]]
    prev_wp = waypoints[closest[0]]
    track_dir = math.degrees(
        math.atan2(next_wp[1] - prev_wp[1], next_wp[0] - prev_wp[0])
    )
    direction_diff = abs(track_dir - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    heading_reward = max(1.0 - (direction_diff / 25.0), 0.0)

    # 2) Curvatura à frente — look-ahead fixo de 6 waypoints
    n_wp = len(waypoints)
    far_wp = waypoints[(closest[1] + 6) % n_wp]
    future_dir = math.degrees(
        math.atan2(far_wp[1] - next_wp[1], far_wp[0] - next_wp[0])
    )
    curve_diff = abs(future_dir - track_dir)
    if curve_diff > 180:
        curve_diff = 360 - curve_diff

    # 3) Velocidade adaptativa + penalidade de steering em retas
    is_straight = curve_diff < 10
    if is_straight:
        # Reta: premiar velocidade alta (quadrático)
        speed_reward = (speed / 4.0) ** 2
        # Penalizar steering proporcional em retas
        steering_penalty = (abs(steering_angle) / 21.0) ** 2 * 0.5
    else:
        # Curva: premiar velocidade ideal para a curvatura
        ideal = max(1.33, 3.0 - curve_diff * 0.06)
        speed_reward = max(1.0 - abs(speed - ideal) / 3.0, 0.0)
        steering_penalty = 0.0

    # 4) Centralização suave — penaliza distância do centro
    center_ratio = distance_from_center / (0.5 * track_width)
    center_reward = max(1.0 - center_ratio ** 2, 0.0)

    # 5) Step cost progressivo — pressão crescente pra terminar rápido
    step_cost = (steps / 150.0) ** 2 * 0.03

    # Reward ponderado
    reward = (
        0.35 * speed_reward
        + 0.35 * heading_reward
        + 0.15 * center_reward
        - steering_penalty
        - step_cost
    )

    # Bônus de progresso contínuo — cada waypoint avançado vale
    reward += progress / 100.0

    # Bônus de volta completa — escala quadrática com menos steps
    if progress >= 99.0:
        reward += 15.0 * (130.0 / max(steps, 1)) ** 2

    return float(max(reward, 1e-3))
