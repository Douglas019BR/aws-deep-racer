import math


def reward_function(params):
    if params["is_offtrack"]:
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

    # 1) Heading — gradual, não binário
    next_wp = waypoints[closest[1]]
    prev_wp = waypoints[closest[0]]
    track_dir = math.degrees(
        math.atan2(next_wp[1] - prev_wp[1], next_wp[0] - prev_wp[0])
    )
    direction_diff = abs(track_dir - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    heading_reward = max(1.0 - (direction_diff / 30.0), 0.0)

    # 2) Curvatura à frente (look-ahead fixo)
    n_wp = len(waypoints)
    far_wp = waypoints[(closest[1] + 6) % n_wp]
    future_dir = math.degrees(
        math.atan2(far_wp[1] - next_wp[1], far_wp[0] - next_wp[0])
    )
    curve_diff = abs(future_dir - track_dir)
    if curve_diff > 180:
        curve_diff = 360 - curve_diff

    # 3) Velocidade adaptativa — sinal único
    is_straight = curve_diff < 8
    if is_straight:
        speed_reward = (speed / 4.0) ** 1.5
    else:
        ideal = max(1.5, 3.0 - curve_diff * 0.05)
        speed_reward = max(1.0 - abs(speed - ideal) / 2.0, 0.0)

    # 4) Penalizar steering excessivo em retas
    steering_penalty = 0.2 if is_straight and abs(steering_angle) > 10 else 0.0

    # 5) Centralização suave
    center_reward = 1.0 - (distance_from_center / (0.5 * track_width)) ** 2

    # Reward com pesos diferenciados
    reward = (
        0.40 * speed_reward
        + 0.30 * heading_reward
        + 0.20 * center_reward
        - steering_penalty
    )

    # Bônus de progresso contínuo
    reward += progress / 200.0

    # Bônus de volta completa
    if progress >= 99.0:
        reward += 15.0 * (130.0 / max(steps, 1)) ** 2

    return float(max(reward, 1e-3))
