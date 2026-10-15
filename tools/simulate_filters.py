"""ノイズ対策（移動平均・ヒステリシス）の効果を、ROS 2 なしで数値化する検証スクリプト。

brain.py と同じ判断ロジックを純 Python で再現し、壁への接近を多数回シミュレートする。
標準ライブラリのみで動作する（Mac 上でそのまま実行できる）。

    python3 tools/simulate_filters.py
"""
import random
from collections import deque

TURN = 3.0     # この距離未満で STOP に入る
SLOW = 8.0     # この距離未満で SLOW に入る
NOISE = 0.5    # センサーノイズ（±）


def approach(n, hysteresis, noise=NOISE):
    """壁へ向かって走り、TURN が出るまでの指示列と最接近距離を返す。"""
    history = deque(maxlen=n)
    wall = 37.5        # 壁までの真の距離
    cmd = 'F'          # F=FORWARD, S=SLOW, P=STOP, T=TURN
    stop_t = None
    seq, closest = [], wall
    for step in range(1, 400):
        wall = max(0.0, wall - {'F': 0.5, 'S': 0.2}.get(cmd, 0.0))
        closest = min(closest, wall)
        history.append(wall + random.uniform(-noise, noise))
        dist = sum(history) / len(history)
        t = step * 0.2
        threshold = TURN + hysteresis if stop_t is not None else TURN
        if dist < threshold:
            stop_t = t if stop_t is None else stop_t
            cmd = 'T' if t - stop_t > 2.0 else 'P'
        elif dist < SLOW:
            stop_t, cmd = None, 'S'
        else:
            stop_t, cmd = None, 'F'
        seq.append(cmd)
        if cmd == 'T':
            break
    return ''.join(seq), closest


def evaluate(n, hysteresis, trials=5000, noise=NOISE):
    broken = 0          # STOP の途中で SLOW に戻った（チャタリング）回数
    closest_sum = 0.0
    for _ in range(trials):
        seq, closest = approach(n, hysteresis, noise)
        stop_part = seq[seq.find('P'):] if 'P' in seq else ''
        broken += 'PS' in stop_part
        closest_sum += closest
    return 100 * broken / trials, closest_sum / trials


def main():
    random.seed(0)
    print('【1】ヒステリシスの幅 H を変える（平均なし N=1）')
    for h in (0.0, 0.5, 1.0, 2.0):
        broken, closest = evaluate(1, h)
        print(f'  H={h:<3}  STOP が途中で中断した割合 {broken:5.1f}%  最接近の平均 {closest:4.2f}')
    print('【2】移動平均の個数 N を変える（ヒステリシスなし H=0）')
    for n in (1, 3, 5, 10, 20):
        broken, closest = evaluate(n, 0.0)
        print(f'  N={n:<3}  STOP が途中で中断した割合 {broken:5.1f}%  最接近の平均 {closest:4.2f}')
    print('【3】ノイズの大きさを変える（N=1, H=1.0 と N=5, H=0）')
    for noise in (0.2, 0.5, 1.0):
        by_h, _ = evaluate(1, 1.0, noise=noise)
        by_n, _ = evaluate(5, 0.0, noise=noise)
        print(f'  ノイズ±{noise}  ヒステリシスのみ {by_h:5.1f}%  平均のみ {by_n:5.1f}%')


if __name__ == '__main__':
    main()
