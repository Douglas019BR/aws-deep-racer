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

        # ── 1) Alinhamento com a pista (gate: desalinhado demais = reward mínima) ──
        next_wp = waypoints[closest[1]]
        prev_wp = waypoints[closest[0]]
        track_dir = math.degrees(
            math.atan2(next_wp[1] - prev_wp[1], next_wp[0] - prev_wp[0])
        )
        direction_diff = abs(track_dir - heading)
        if direction_diff > 180:
            direction_diff = 360 - direction_diff
        if direction_diff > 30:
            return 1e-3

        # ── 2) Curvatura à frente (look-ahead 5 waypoints) ──
        n_wp = len(waypoints)
        far_wp = waypoints[(closest[1] + 5) % n_wp]
        future_dir = math.degrees(
            math.atan2(far_wp[1] - next_wp[1], far_wp[0] - next_wp[0])
        )
        curve_diff = abs(future_dir - track_dir)
        if curve_diff > 180:
            curve_diff = 360 - curve_diff

        # ── 3) Velocidade adaptativa calibrada para re:Invent 2018 ──
        if curve_diff <= 5:
            optimal_speed = 4.0
        elif curve_diff <= 10:
            optimal_speed = 3.5
        elif curve_diff <= 15:
            optimal_speed = 2.7
        else:
            optimal_speed = 1.5

        speed_reward = max(1.0 - abs(speed - optimal_speed) / 4.0, 0.0)

        # ── 4) Eficiência: progress/steps ──
        efficiency = (progress / steps) * 2.5 if steps > 0 else 0.0

        # ── Reward final ──
        reward = 0.45 * speed_reward + 0.55 * efficiency

        # ── Bônus: volta completa — escalonado por steps ──
        if progress >= 99.0:
            reward += max(15.0 * (110.0 / steps), 2.0)

        return float(max(reward, 1e-3))


reward_obj = Reward()


def reward_function(params):
    return reward_obj.reward_function(params)
