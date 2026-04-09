import math


class Reward:
    def reward_function(self, params):
        if not params["all_wheels_on_track"] or params["is_offtrack"]:
            return 1e-3

        waypoints = params["waypoints"]
        closest = params["closest_waypoints"]
        heading = params["heading"]
        speed = params["speed"]
        progress = params["progress"]
        steps = params["steps"]
        track_width = params["track_width"]
        distance_from_center = params["distance_from_center"]

        # ── 1) Heading gate: 20° (mais restritivo que v2) ──
        next_wp = waypoints[closest[1]]
        prev_wp = waypoints[closest[0]]
        track_dir = math.degrees(
            math.atan2(next_wp[1] - prev_wp[1], next_wp[0] - prev_wp[0])
        )
        direction_diff = abs(track_dir - heading)
        if direction_diff > 180:
            direction_diff = 360 - direction_diff
        if direction_diff > 20:
            return 1e-3

        # ── 2) Curvatura à frente (look-ahead adaptativo por velocidade) ──
        n_wp = len(waypoints)
        look_ahead = max(3, int(speed * 2.5))
        far_wp = waypoints[(closest[1] + look_ahead) % n_wp]
        future_dir = math.degrees(
            math.atan2(far_wp[1] - next_wp[1], far_wp[0] - next_wp[0])
        )
        curve_diff = abs(future_dir - track_dir)
        if curve_diff > 180:
            curve_diff = 360 - curve_diff

        # ── 3) Velocidade adaptativa alinhada ao action space ──
        if curve_diff <= 5:
            optimal_speed = 4.0
        elif curve_diff <= 15:
            optimal_speed = 2.7
        else:
            optimal_speed = 1.5

        speed_reward = max(1.0 - abs(speed - optimal_speed) / 4.0, 0.0)

        # ── 4) Eficiência com piso de steps ──
        effective_steps = max(steps, 15)
        efficiency = (progress / effective_steps) * 2.5

        # ── 5) Penalidade de borda (último 20% da largura) ──
        border_penalty = 0.0
        if distance_from_center > 0.4 * track_width:
            border_penalty = 0.2

        # ── Reward final ──
        reward = 0.40 * speed_reward + 0.50 * efficiency - border_penalty

        # ── Bônus: volta completa escalonado ──
        if progress >= 99.0:
            reward += max(15.0 * (110.0 / effective_steps), 2.0)

        return float(max(reward, 1e-3))


reward_obj = Reward()


def reward_function(params):
    return reward_obj.reward_function(params)
