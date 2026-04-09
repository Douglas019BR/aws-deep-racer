import math


class Reward:
    def _init_(self):
        self.prev_steering = 0.0
        self.prev_speed = 0.0

    def reward_function(self, params):
        if not params["all_wheels_on_track"] or params["is_offtrack"]:
            return float(-1.0)

        waypoints = params["waypoints"]
        closest = params["closest_waypoints"]
        heading = params["heading"]
        speed = params["speed"]
        steering = abs(params["steering_angle"])
        track_width = params["track_width"]
        distance_from_center = params["distance_from_center"]
        progress = params["progress"]
        steps = params["steps"]

        # ── 1) Heading: alinhamento com a direção da pista ──
        next_wp = waypoints[closest[1]]
        prev_wp = waypoints[closest[0]]
        track_dir = math.degrees(
            math.atan2(next_wp[1] - prev_wp[1], next_wp[0] - prev_wp[0])
        )
        direction_diff = abs(track_dir - heading)
        if direction_diff > 180:
            direction_diff = 360 - direction_diff
        heading_reward = max(1.0 - (direction_diff / 30.0), 0.0)

        # ── 2) Look-ahead: detecta curvatura à frente ──
        n_wp = len(waypoints)
        look_idx = (closest[1] + 5) % n_wp
        far_wp = waypoints[look_idx]
        future_dir = math.degrees(
            math.atan2(far_wp[1] - next_wp[1], far_wp[0] - next_wp[0])
        )
        curve_diff = abs(future_dir - track_dir)
        if curve_diff > 180:
            curve_diff = 360 - curve_diff

        # ── 3) Velocidade adaptativa baseada na curvatura ──
        if curve_diff <= 5:
            optimal_speed = 4.0
        elif curve_diff <= 15:
            optimal_speed = 2.7
        else:
            optimal_speed = 1.3

        speed_diff = abs(speed - optimal_speed) / 4.0
        speed_reward = max(1.0 - speed_diff, 0.0)

        # ── 4) Penalidade: steering alto + velocidade alta ──
        if steering >= 15 and speed >= 2.5:
            speed_reward *= 0.15

        # ── 5) Centralização — contínua e quadrática ──
        center_ratio = distance_from_center / (0.5 * track_width)
        center_reward = max(1.0 - (center_ratio ** 2), 0.0)

        # ── 6) Smooth driving — penaliza mudanças bruscas ──
        steering_change = abs(params["steering_angle"] - self.prev_steering)
        steer_smooth = max(1.0 - (steering_change / 30.0), 0.0)
        speed_change = abs(speed - self.prev_speed)
        speed_smooth = max(1.0 - (speed_change / 2.0), 0.0)
        smooth_reward = 0.6 * steer_smooth + 0.4 * speed_smooth

        self.prev_steering = params["steering_angle"]
        self.prev_speed = speed

        # ── 7) Eficiência: progress/steps ──
        efficiency = 0.0
        if steps > 0:
            efficiency = (progress / steps) * 2.5

        # ── 8) Bônus suave por velocidade (ganho decrescente) ──
        speed_bonus = min(speed / 4.0, 1.0) ** 0.5

        # ── Reward final — soma ponderada ──
        reward = (
            0.12 * heading_reward
            + 0.25 * speed_reward
            + 0.12 * center_reward
            + 0.18 * smooth_reward
            + 0.23 * efficiency
            + 0.10 * speed_bonus
        )

        # ── Bônus: volta completa em poucos steps ──
        if progress >= 99.0:
            reward += 10.0

        return float(max(reward, 1e-3))


reward_obj = Reward()
