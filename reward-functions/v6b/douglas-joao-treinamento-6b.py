import math


# Velocidade alvo por waypoint — reinvent_base (119 waypoints)
# Action space da v5: retas usam 3.8/4.0, curvas suaves 2.6/2.8, curvas fechadas 1.4/1.6
WP_TARGET_SPEED = [
    4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  # 0-9
    4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  # 10-19
    4.0,  4.0,  2.6,  2.6,  2.6,  2.6,  2.6,  2.6,  2.6,  2.6,  # 20-29
    2.6,  2.6,  4.0,  2.6,  2.6,  2.6,  2.6,  2.6,  2.6,  2.6,  # 30-39
    2.6,  2.6,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  # 40-49
    2.6,  2.6,  2.6,  2.6,  2.6,  4.0,  4.0,  4.0,  4.0,  4.0,  # 50-59
    4.0,  4.0,  4.0,  4.0,  4.0,  2.6,  2.6,  2.6,  2.6,  2.6,  # 60-69
    4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  2.6,  # 70-79
    2.6,  2.6,  2.6,  2.6,  2.6,  2.6,  2.6,  2.6,  2.6,  2.6,  # 80-89
    4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  # 90-99
    4.0,  4.0,  4.0,  2.6,  1.4,  2.6,  1.4,  2.6,  2.6,  4.0,  # 100-109
    4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  4.0,  1.4,  1.4,  # 110-119
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
    steering_angle = params["steering_angle"]

    # 1) Velocidade alvo — penalidade suave, nunca zera o sinal
    wp_idx = closest[1] % len(WP_TARGET_SPEED)
    target_spd = WP_TARGET_SPEED[wp_idx]
    speed_diff = abs(speed - target_spd)
    speed_reward = max(1.0 - (speed_diff / 2.6), 0.1)
    if speed_diff < 0.01:
        speed_reward += 0.5

    # 2) Heading
    next_wp = waypoints[closest[1]]
    prev_wp = waypoints[closest[0]]
    track_dir = math.degrees(math.atan2(next_wp[1] - prev_wp[1], next_wp[0] - prev_wp[0]))
    direction_diff = abs(track_dir - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    heading_reward = max(1.0 - direction_diff / 30.0, 0.0)

    # 3) Steering penalty em retas
    steering_penalty = 0.0
    if target_spd == 4.0:
        steering_penalty = (abs(steering_angle) / 25.0) ** 2 * 0.5

    # 4) Reward ponderado
    reward = 0.60 * speed_reward + 0.40 * heading_reward - steering_penalty

    reward += progress / 100.0

    if progress >= 99.0:
        reward += 100.0 * (100.0 / max(steps, 1)) ** 3

    return float(max(reward, 1e-3))
