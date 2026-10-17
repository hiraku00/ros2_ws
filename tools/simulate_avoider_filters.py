"""avoider の判断（最小値・平均・移動平均）を、ROS 2 なしで比べる（Mac で実行できる）。

room_sim と同じ世界の計算（room_sim.py の cast_ray / hits_something）を、そのまま使う。
rclpy などは、使わないので、空の部品に差し替えて、import だけ通す。

使い方:
    python3 tools/simulate_avoider_filters.py                  # 3 つの比較（既定）
    python3 tools/simulate_avoider_filters.py --trials 20 --seconds 40
"""
import argparse
from collections import deque
import math
from pathlib import Path
import random
import statistics
import sys
import types

for name in ('rclpy', 'rclpy.node', 'rclpy.executors', 'geometry_msgs',
             'geometry_msgs.msg', 'sensor_msgs', 'sensor_msgs.msg'):
    sys.modules[name] = types.ModuleType(name)
sys.modules['rclpy.node'].Node = object
sys.modules['rclpy.executors'].ExternalShutdownException = Exception
sys.modules['geometry_msgs.msg'].Twist = object
sys.modules['sensor_msgs.msg'].LaserScan = object
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src' / 'room_robot_pkg'))

from room_robot_pkg.room_sim import cast_ray, hits_something  # noqa: E402

DT = 0.1
THRESHOLD = 1.5


def run(mode, n, noise, seed, seconds, trace=None, hysteresis=0.0):
    """1 回ぶんの走行。mode: 'min'（最小値の移動平均。n=1 なら平均なし）か 'avg'（61 本の平均）。

    trace にリストを渡すと、0.1 秒ごとの (時刻, x, y, 回っているか) を追加する（図を作るため）。
    hysteresis は、回っている間だけ使う「出る線」の幅（m）。0 なら、入る線と出る線が同じ。
    """
    rnd = random.Random(seed)
    history = deque(maxlen=n)
    x, y, theta = 10.0, 10.0, 0.0
    t, previous = 0.0, False
    first_x, starts, closest = None, 0, math.inf
    while t < seconds:
        full = [cast_ray(x, y, theta + math.radians(i), 12.0) for i in range(360)]
        closest = min(closest, min(full))  # ノイズのない、本当の最近接距離
        front = full[0:31] + full[330:360]
        if noise > 0:
            front = [v + rnd.uniform(-noise, noise) if math.isfinite(v) else v for v in front]
        if mode == 'min':
            history.append(min(front))
            nearest = sum(history) / len(history)
        else:
            nearest = sum(front) / len(front)
        turning = nearest < (THRESHOLD + hysteresis if previous else THRESHOLD)
        if trace is not None:
            trace.append((t, x, y, turning))
        if turning and not previous:
            starts += 1
            if first_x is None:
                first_x = x
        previous = turning
        linear, angular = (0.0, 0.5) if turning else (0.3, 0.0)
        theta += angular * DT
        nx = x + linear * math.cos(theta) * DT
        ny = y + linear * math.sin(theta) * DT
        if not hits_something(nx, ny):
            x, y = nx, ny
        t += DT
    return first_x, starts, closest


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--trials', type=int, default=100, help='ノイズありの試行回数')
    parser.add_argument('--hysteresis', action='store_true',
                        help='ヒステリシスの幅をくらべる表を出す（移動平均 N=5、ノイズ 0.5）')
    parser.add_argument('--seconds', type=float, default=60.0, help='1 回の走行時間（秒）')
    args = parser.parse_args()

    cases = [
        ('最小値のみ', 'min', 1, 0.0, 1),
        ('最小値のみ', 'min', 1, 0.5, args.trials),
        ('最小値の移動平均', 'min', 5, 0.5, args.trials),
        ('最小値の移動平均', 'min', 20, 0.5, args.trials),
        ('61 本の平均', 'avg', 1, 0.0, 1),
        ('61 本の平均', 'avg', 1, 0.5, args.trials),
    ]
    if args.hysteresis:
        compare_hysteresis(args.trials, args.seconds)
        return
    print(f'{args.seconds:.0f} 秒の走行。壁は x=20、判断の線は {THRESHOLD} m')
    print('方法                N  noise 回数 | 最初に回り始めた x（平均 / 最小〜最大） | '
          '回り始めた回数（平均） | 本当の最近接（最小）')
    for label, mode, n, noise, trials in cases:
        results = [run(mode, n, noise, seed, args.seconds) for seed in range(trials)]
        xs = [r[0] for r in results if r[0] is not None]  # 時間内に一度も回らなかった回は除く
        starts = [r[1] for r in results]
        closest = [r[2] for r in results]
        first = (f'{statistics.mean(xs):.2f} / {min(xs):.2f}〜{max(xs):.2f}' if xs
                 else '（時間内に回らなかった）')
        print(f'{label:<14} {n:>3}  {noise:>4} {trials:>4} | '
              f'{first}'
              f'            | {statistics.mean(starts):>6.1f}'
              f'               | {min(closest):.2f}')


def first_turn_degrees(trace):
    """最初の「回る」が続いた歩数から、1 回目に回った角度（度）を出す（1 歩で 0.5 × 0.1 rad）。"""
    steps, started = 0, False
    for _, _, _, turning in trace:
        if turning:
            started = True
            steps += 1
        elif started:
            break
    return math.degrees(steps * 0.5 * DT)


def compare_hysteresis(trials, seconds):
    print('ヒステリシスの幅（移動平均 N=5、ノイズ 0.5）')
    print('幅   出る線 | 回り始めた回数（平均 / 最小〜最大） | 最初の回転（平均） | 本当の最近接（最小）')
    rows = []
    for h in (0.0, 0.25, 0.5, 1.0):
        res = []
        for seed in range(trials):
            trace = []
            _, starts, closest = run('min', 5, 0.5, seed, seconds, trace=trace, hysteresis=h)
            res.append((starts, first_turn_degrees(trace), closest))
        counts = [r[0] for r in res]
        row = (h, statistics.mean(counts), min(counts), max(counts),
               statistics.mean(r[1] for r in res), min(r[2] for r in res))
        rows.append(row)
        print(f'{h:4} {1.5 + h:5.2f} m | {row[1]:5.1f} / {row[2]}〜{row[3]}'
              f'                    | {row[4]:5.1f}°          | {row[5]:.2f}')
    return rows


if __name__ == '__main__':
    main()
