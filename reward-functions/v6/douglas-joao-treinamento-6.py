import math


def reward_function(params):
    # Punição real por sair da pista
    if params["is_offtrack"]:
        return -1.0

    waypoints = params["waypoints"]
    closest = params["closest_waypoints"]
    heading = params["heading"]
    speed = params["speed"]
    progress = params["progress"]
    steps = params["steps"]
    track_width = params["track_width"]
    distance_from_center = params["distance_from_center"]
    steering_angle = params["steering_angle"]

    # 1) Heading — gradual
    next_wp = waypoints[closest[1]]
    prev_wp = waypoints[closest[0]]
    track_dir = math.degrees(
        math.atan2(next_wp[1] - prev_wp[1], next_wp[0] - prev_wp[0])
    )
    direction_diff = abs(track_dir - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    heading_reward = max(1.0 - (direction_diff / 25.0), 0.0)

    # 2) Curvatura à frente (look-ahead fixo)
    n_wp = len(waypoints)
    far_wp = waypoints[(closest[1] + 6) % n_wp]
    future_dir = math.degrees(
        math.atan2(far_wp[1] - next_wp[1], far_wp[0] - next_wp[0])
    )
    curve_diff = abs(future_dir - track_dir)
    if curve_diff > 180:
        curve_diff = 360 - curve_diff

    # 3) Velocidade adaptativa + penalidade de steering em retas
    # Action space: steering 0/7/14/21°, velocidades 1.33/2.67/4.0
    is_straight = curve_diff < 10
    if is_straight:
        speed_reward = (speed / 4.0) ** 2
        steering_penalty = (abs(steering_angle) / 21.0) ** 2 * 0.5
    else:
        ideal = max(1.33, 3.0 - curve_diff * 0.06)
        speed_reward = max(1.0 - abs(speed - ideal) / 3.0, 0.0)
        steering_penalty = 0.0

    # 4) Centralização suave
    center_ratio = distance_from_center / (0.5 * track_width)
    center_reward = max(1.0 - center_ratio ** 2, 0.0)

    # 5) Step cost progressivo — pressão pra terminar rápido
    step_cost = (steps / 150.0) ** 2 * 0.03

    # Reward ponderado
    reward = (
        0.35 * speed_reward
        + 0.35 * heading_reward
        + 0.15 * center_reward
        - steering_penalty
        - step_cost
    )

    # Bônus de progresso contínuo (mais forte que v5)
    reward += progress / 100.0

    # Bônus de volta completa
    if progress >= 99.0:
        reward += 15.0 * (130.0 / max(steps, 1)) ** 2

    return float(max(reward, 1e-3))
