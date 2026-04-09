import math


class Reward:
    def reward_function(self, params):
        # ── Penalidade severa por sair da pista ──
        if not params["all_wheels_on_track"] or params["is_offtrack"]:
            return -1.0

        waypoints = params["waypoints"]
        closest = params["closest_waypoints"]
        heading = params["heading"]
        speed = params["speed"]
        progress = params["progress"]
        steps = params["steps"]
        track_width = params["track_width"]
        distance_from_center = params["distance_from_center"]

        # ── 1) Heading gate: desalinhado > 20° = punição ──
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

        # ── 2) Curvatura à frente (look-ahead adaptativo) ──
        n_wp = len(waypoints)
        look_ahead = max(3, int(speed * 2.5))
        far_wp = waypoints[(closest[1] + look_ahead) % n_wp]
        future_dir = math.degrees(
            math.atan2(far_wp[1] - next_wp[1], far_wp[0] - next_wp[0])
        )
        curve_diff = abs(future_dir - track_dir)
        if curve_diff > 180:
            curve_diff = 360 - curve_diff

        # ── 3) Velocidade adaptativa ──
        if curve_diff <= 5:
            optimal_speed = 4.0
        elif curve_diff <= 15:
            optimal_speed = 2.7
        else:
            optimal_speed = 1.5

        speed_reward = max(1.0 - abs(speed - optimal_speed) / 4.0, 0.0)

        # ── 4) Bônus de velocidade: premiar ir rápido ──
        speed_bonus = (speed / 4.0) ** 2

        # ── 5) Eficiência: progress/steps normalizada ──
        # Target ~120 steps para volta completa (baseado nos dados: melhores voltas = 122-126 steps)
        effective_steps = max(steps, 1)
        projected_steps = (effective_steps / max(progress, 1.0)) * 100.0
        # Quanto menor projected_steps, melhor
        step_efficiency = max(1.0 - (projected_steps - 110.0) / 60.0, 0.0)

        # ── 6) Penalidade progressiva de borda ──
        center_ratio = distance_from_center / (0.5 * track_width)
        border_penalty = max(center_ratio - 0.6, 0.0) * 0.5

        # ── Reward final: prioriza velocidade e eficiência ──
        reward = (
            0.30 * speed_reward
            + 0.30 * speed_bonus
            + 0.30 * step_efficiency
            - border_penalty
        )

        # ── Bônus de volta completa: escala forte com menos steps ──
        if progress >= 99.0:
            # 122 steps (melhor volta) → bônus ~13.5
            # 150 steps (volta lenta) → bônus ~7.3
            reward += 20.0 * (110.0 / effective_steps) ** 2

        return float(max(reward, 1e-3))


reward_obj = Reward()


def reward_function(params):
    return reward_obj.reward_function(params)
