import math


# Velocidade alvo por waypoint — reinvent_base (119 waypoints)
# 4.00 = reta | 2.67 = entrada/saída de curva | 1.33 = apex fechado
WP_TARGET_SPEED = [
    4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00,  # 0-9
    4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00,  # 10-19
    4.00, 4.00, 2.67, 2.67, 2.67, 2.67, 2.67, 2.67, 2.67, 2.67,  # 20-29
    2.67, 2.67, 4.00, 2.67, 2.67, 2.67, 2.67, 2.67, 2.67, 2.67,  # 30-39
    2.67, 2.67, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00,  # 40-49
    2.67, 2.67, 2.67, 2.67, 2.67, 4.00, 4.00, 4.00, 4.00, 4.00,  # 50-59
    4.00, 4.00, 4.00, 4.00, 4.00, 2.67, 2.67, 2.67, 2.67, 2.67,  # 60-69
    4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 2.67,  # 70-79
    2.67, 2.67, 2.67, 2.67, 2.67, 2.67, 2.67, 2.67, 2.67, 2.67,  # 80-89
    4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00,  # 90-99
    4.00, 4.00, 4.00, 2.67, 1.33, 2.67, 1.33, 2.67, 2.67, 4.00,  # 100-109
    4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 4.00, 1.33, 1.33,  # 110-119 (118 é o último)
]


def reward_function(params):
    if params["is_offtrack"]:
        return -1.0

    if not params["all_wheels_on_track"]:
        return 1e-3

    speed = params["speed"]
    heading = params["heading"]
    progress = params["progress"]
    steps = params["steps"]
    waypoints = params["waypoints"]
    closest = params["closest_waypoints"]

    # 1) Velocidade alvo para o waypoint atual
    wp_idx = closest[1] % len(WP_TARGET_SPEED)
    target_spd = WP_TARGET_SPEED[wp_idx]
    speed_diff = abs(speed - target_spd)

    # Corte duro: mais de 1.0 m/s longe do alvo → sem reward
    if speed_diff > 1.0:
        return 1e-3

    speed_reward = 1.0 - speed_diff / 1.0
    if target_spd == 4.0 and speed == 4.0:
        speed_reward += 0.5

    # 2) Heading
    next_wp = waypoints[closest[1]]
    prev_wp = waypoints[closest[0]]
    track_dir = math.degrees(math.atan2(next_wp[1] - prev_wp[1], next_wp[0] - prev_wp[0]))
    direction_diff = abs(track_dir - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff

    if direction_diff > 30:
        return 1e-3

    heading_reward = max(1.0 - direction_diff / 30.0, 0.0)

    # 3) Reward final
    reward = 0.60 * speed_reward + 0.40 * heading_reward
    reward += progress / 100.0

    if progress >= 99.0:
        reward += 100.0 * (100.0 / max(steps, 1)) ** 3

    return float(max(reward, 1e-3))
