"""docs/room-robot/images/ の図（SVG）を作る（Mac で実行できる。ROS 2 不要）。

図の数字は、手で書かずに、room_sim と同じ計算（simulate_avoider_filters.py）から出す。

使い方:
    python3 tools/make_room_robot_figures.py              # 約 3〜4 分（比較の図で 100 回ずつ走らせる）
    python3 tools/make_room_robot_figures.py --trials 10  # 軽く、試す
"""
import argparse
import math
from pathlib import Path
import random
import statistics
import sys

import matplotlib

matplotlib.use('Agg')
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle, Wedge  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from simulate_avoider_filters import cast_ray, run  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / 'docs' / 'room-robot' / 'images'

# 色（dataviz の既定パレットの 1〜3 番。緑は薄いので、必ず文字ラベルを添える）
BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
HIT_RED = '#e34948'   # room_sim のブラウザ表示と同じく、当たったレーザーは赤
INK, INK2, MUTED, GRID = '#0b0b0b', '#52514e', '#9b9a95', '#e4e3df'
SURFACE, OBSTACLE = '#fcfcfb', '#c9c2b6'

_INSTALLED = {f.name for f in font_manager.fontManager.ttflist}
JP_FONTS = [f for f in ('Hiragino Sans', 'Noto Sans CJK JP', 'IPAexGothic') if f in _INSTALLED]

plt.rcParams.update({
    'font.family': JP_FONTS + ['sans-serif'],
    'font.size': 11,
    'svg.fonttype': 'none',      # 文字を、文字のまま残す（画像を拡大しても、にじまない）
    'svg.hashsalt': 'room-robot',
    'axes.edgecolor': MUTED,
    'axes.labelcolor': INK2,
    'xtick.color': INK2,
    'ytick.color': INK2,
    'figure.facecolor': SURFACE,
    'axes.facecolor': SURFACE,
})


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, format='svg', bbox_inches='tight', metadata={'Date': None})
    plt.close(fig)
    print('書き出し:', OUT / name)


def draw_room(ax, grid=True):
    ax.add_patch(Rectangle((0, 0), 20, 20, fill=False, lw=3, ec=INK))
    ax.add_patch(Circle((3, 13), 1.5, color=OBSTACLE))
    ax.add_patch(Rectangle((14, 2), 3, 3, color=OBSTACLE))
    ax.set_xlim(-1, 21)
    ax.set_ylim(-1, 21)
    ax.set_aspect('equal')
    ax.set_xticks(range(0, 21, 5))
    ax.set_yticks(range(0, 21, 5))
    if grid:
        ax.grid(color=GRID, lw=0.8)
        ax.set_axisbelow(True)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.set_xlabel('x（m）')
    ax.set_ylabel('y（m）')


def draw_robot(ax, x, y, theta, r=0.3, color=BLUE):
    ax.add_patch(Circle((x, y), r, color=color, zorder=5))
    ax.annotate('', xy=(x + 1.4 * math.cos(theta), y + 1.4 * math.sin(theta)), xytext=(x, y),
                arrowprops={'arrowstyle': '-|>', 'color': color, 'lw': 2}, zorder=6)


def fig_room_map():
    fig, ax = plt.subplots(figsize=(6.2, 6.2))
    draw_room(ax)
    draw_robot(ax, 10, 10, 0)
    ax.text(10, 9.0, 'スタート (10, 10)\n右向き（θ = 0°）', ha='center', va='top', color=INK)
    ax.text(3, 13, '円の障害物\n中心 (3, 13)\n半径 1.5', ha='center', va='center', fontsize=9, color=INK)
    ax.text(15.5, 3.5, '四角の\n障害物', ha='center', va='center', fontsize=9, color=INK)
    ax.text(20.3, 16, '壁\nx = 20', ha='left', va='center', color=INK2)
    ax.text(0, -0.4, '(0, 0)', ha='center', va='top', fontsize=9, color=INK2)
    ax.text(20, 20.4, '(20, 20)', ha='center', va='bottom', fontsize=9, color=INK2)
    ax.set_title('部屋の地図（20 m × 20 m。1 マス = 5 m）', color=INK, pad=12)
    save(fig, 'room-map.svg')


def fig_lidar_index():
    fig, ax = plt.subplots(figsize=(6.4, 6.0))
    ax.add_patch(Wedge((0, 0), 3.2, -30, 30, color=BLUE, alpha=0.15))
    ax.add_patch(Circle((0, 0), 0.35, color=BLUE, zorder=5))
    rays = [(0, 'ranges[0]\n正面（0°）'), (30, 'ranges[30]\n左に 30°'), (90, 'ranges[90]\n左（90°）'),
            (180, 'ranges[180]\n後ろ（180°）'), (270, 'ranges[270]\n右（270°）'),
            (330, 'ranges[330]\n右に 30°（= 330°）')]
    for deg, label in rays:
        a = math.radians(deg)
        ax.plot([0, 3.2 * math.cos(a)], [0, 3.2 * math.sin(a)], color=INK2, lw=1.2)
        ha = 'left' if math.cos(a) > 0.3 else ('right' if math.cos(a) < -0.3 else 'center')
        va = 'bottom' if math.sin(a) > 0.3 else ('top' if math.sin(a) < -0.3 else 'center')
        ax.text(3.35 * math.cos(a), 3.35 * math.sin(a), label, ha=ha, va=va, fontsize=10,
                color=INK)
    ax.add_patch(FancyArrowPatch((2.2, 0.4), (0.4, 2.2), connectionstyle='arc3,rad=0.35',
                                 arrowstyle='-|>', mutation_scale=14, color=MUTED))
    ax.text(1.75, 1.75, '番号は\n反時計回りに\n増える', fontsize=9, color=INK2, ha='center')
    ax.text(1.6, -0.15, '前方 61 本', color=BLUE, fontsize=10, ha='center', va='top', weight='bold')
    ax.text(0, -4.3, '前方 61 本 ＝ ranges[0〜30]（31 本）＋ ranges[330〜359]（30 本）',
            ha='center', color=INK, fontsize=10)
    ax.set_xlim(-5.2, 6.4)
    ax.set_ylim(-4.7, 4.4)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('レーザーの番号と向き（真上から見た図）', color=INK)
    save(fig, 'lidar-index.svg')


def fig_scan_start():
    fig, ax = plt.subplots(figsize=(6.2, 6.2))
    draw_room(ax, grid=False)
    x0, y0 = 10.0, 10.0
    n_inf = 0
    for i in range(360):
        a = math.radians(i)
        r = cast_ray(x0, y0, a, 12.0)
        if math.isfinite(r):
            ax.plot([x0, x0 + r * math.cos(a)], [y0, y0 + r * math.sin(a)], color=HIT_RED, lw=0.4,
                    alpha=0.6)
        else:
            n_inf += 1
            ax.plot([x0, x0 + 12 * math.cos(a)], [y0, y0 + 12 * math.sin(a)], color=MUTED, lw=0.4,
                    alpha=0.6)
    ax.add_patch(Circle((x0, y0), 12, fill=False, ls=':', ec=INK2, lw=1))
    ax.plot([x0, 20], [y0, y0], color=INK, lw=3)
    ax.text(15, 10.4, 'ranges[0] = 10.0 m', color=INK, ha='center', va='bottom', weight='bold',
            bbox={'boxstyle': 'round,pad=0.2', 'fc': SURFACE, 'ec': 'none', 'alpha': 0.9})
    a = math.radians(45)
    ax.plot([x0, x0 + 12 * math.cos(a)], [y0, y0 + 12 * math.sin(a)], color=INK, lw=3, ls='--')
    ax.text(14.6, 17.4, 'ranges[45] = inf\n（角まで 14.14 m。\n12 m より遠い）', color=INK, fontsize=9.5,
            ha='right', va='bottom', bbox={'boxstyle': 'round,pad=0.2', 'fc': SURFACE,
                                           'ec': 'none', 'alpha': 0.9})
    draw_robot(ax, x0, y0, 0)
    ax.axis('off')
    fig.text(0.5, 0.06, f'赤い線: 距離が測れた（ブラウザの画面と同じ色）　灰色の線: inf（12 m より遠い）… inf は {n_inf} 本\n'
             '点線の円: range_max = 12 m（これより遠いと測れない）', ha='center', va='top', fontsize=9.5,
             color=INK2)
    ax.set_title('スタート位置から出る 360 本のレーザー', color=INK)
    save(fig, 'scan-start.svg')


def fig_twist():
    cases = [((0.5, 0.0), 'まっすぐ進む'), ((0.0, 0.5), 'その場で、左回り'),
             ((0.0, -0.5), 'その場で、右回り'), ((0.5, 0.5), '進みながら、左へ曲がる')]
    fig, axes = plt.subplots(1, 4, figsize=(11, 3.4))
    for ax, ((lin, ang), name) in zip(axes, cases):
        x = y = th = 0.0
        xs, ys = [x], [y]
        for _ in range(30):                      # 3 秒ぶん
            th += ang * 0.1
            x += lin * math.cos(th) * 0.1
            y += lin * math.sin(th) * 0.1
            xs.append(x)
            ys.append(y)
        ax.add_patch(Circle((0, 0), 0.3, color=BLUE, alpha=0.35))
        if lin > 0:
            ax.plot(xs, ys, color=BLUE, lw=2)
            ax.annotate('', xy=(xs[-1], ys[-1]), xytext=(xs[-3], ys[-3]),
                        arrowprops={'arrowstyle': '-|>', 'color': BLUE, 'lw': 2})
        else:
            rad = 0.6 if ang > 0 else -0.6
            ax.add_patch(FancyArrowPatch((0.75, 0), (0, 0.75 * (1 if ang > 0 else -1)),
                                         connectionstyle=f'arc3,rad={rad}', arrowstyle='-|>',
                                         mutation_scale=16, color=BLUE, lw=2))
        ax.annotate('', xy=(0.7, 0), xytext=(0, 0), arrowprops={'arrowstyle': '-|>', 'color': INK2,
                                                                'lw': 1})
        ax.set_xlim(-1.0, 1.9)
        ax.set_ylim(-1.2, 1.7)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(f'{name}\nlinear.x = {lin}　angular.z = {ang}', fontsize=10, color=INK)
    fig.suptitle('Twist の 2 つの数字と、3 秒間の動き（灰色の矢印 = 最初の向き）', color=INK, y=1.04)
    save(fig, 'twist.svg')


def fig_speed_step():
    fig, ax = plt.subplots(figsize=(9, 2.4))
    ax.plot([0, 0.5], [0, 0], color=INK2, lw=1.5)
    for k in range(11):
        d = 0.05 * k
        ax.plot(d, 0, 'o', color=BLUE if k else INK2, ms=8, zorder=3)
        if k in (0, 1, 2, 5, 10):
            ax.text(d, -0.035, f'{0.1 * k:.1f} 秒\n{d:.2f} m', ha='center', va='top', fontsize=9,
                    color=INK2)
    ax.annotate('', xy=(0.05, 0.03), xytext=(0, 0.03), arrowprops={'arrowstyle': '<->',
                                                                   'color': ORANGE, 'lw': 1.5})
    ax.text(0.025, 0.04, '1 歩 = 0.05 m\n（0.1 秒）', ha='center', va='bottom', fontsize=9.5,
            color=INK)
    ax.annotate('', xy=(0.5, 0.11), xytext=(0, 0.11), arrowprops={'arrowstyle': '<->',
                                                                  'color': BLUE, 'lw': 1.5})
    ax.text(0.25, 0.118, '10 歩 = 1 秒で 0.5 m', ha='center', va='bottom', fontsize=10, color=INK,
            weight='bold')
    ax.set_xlim(-0.03, 0.53)
    ax.set_ylim(-0.11, 0.16)
    ax.axis('off')
    ax.set_title('linear.x = 0.5（m/秒）のとき、0.1 秒ごとの位置', color=INK)
    save(fig, 'speed-step.svg')


def fig_wall_stop():
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.add_patch(Rectangle((20, 9.3), 0.25, 1.4, color=INK))
    ax.text(20.12, 10.75, '壁\nx = 20', ha='center', va='bottom', color=INK)
    ax.add_patch(Circle((19.65, 10), 0.3, color=BLUE, alpha=0.85))
    ax.add_patch(Circle((19.70, 10), 0.3, fill=False, ls='--', ec=ORANGE, lw=1.5))
    ax.plot(19.65, 10, 'o', color='white', ms=4, zorder=6)
    ax.annotate('', xy=(19.95, 9.55), xytext=(19.65, 9.55), arrowprops={'arrowstyle': '<->',
                                                                        'color': INK2})
    ax.text(19.6, 9.55, '半径 0.3 m', ha='right', va='center', fontsize=9.5, color=INK2)
    ax.annotate('', xy=(20, 10.45), xytext=(19.65, 10.45), arrowprops={'arrowstyle': '<->',
                                                                       'color': BLUE})
    ax.text(19.6, 10.45, 'ranges[0] = 0.35 m\n（中心から壁まで）', ha='right', va='center', fontsize=9.5,
            color=INK)
    ax.text(19.3, 10.0, '止まった位置\nx = 19.65', ha='right', va='center', color=INK)
    ax.text(19.55, 9.05, 'オレンジの点線 = 次の 1 歩（x = 19.70）。\n'
            '計算では 19.70000000000007 となり、壁にめり込む判定で取り消し', ha='center', va='top',
            fontsize=9, color=INK2)
    ax.set_xlim(18.6, 20.6)
    ax.set_ylim(8.5, 11.1)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('壁の手前で止まる（ロボットは、半径 0.3 m の円）', color=INK)
    save(fig, 'wall-stop.svg')


def fig_avoider_path():
    trace = []
    run('min', 1, 0.0, 0, 150.0, trace=trace)
    fig, ax = plt.subplots(figsize=(6.2, 6.2))
    draw_room(ax)
    ax.plot([p[1] for p in trace], [p[2] for p in trace], color=BLUE, lw=2)
    first = next(p for p in trace if p[3])
    ax.plot(10, 10, 'o', color=INK, ms=7)
    ax.text(10, 9.3, 'スタート', ha='center', va='top', color=INK)
    ax.plot(first[1], first[2], 'o', color=ORANGE, ms=9, zorder=6)
    ax.text(first[1] - 0.4, first[2] - 0.6, f'最初に回り始めた所\n(x = {first[1]:.2f})', ha='right',
            va='top', color=INK, fontsize=9.5)
    end = trace[-1]
    ax.plot(end[1], end[2], 's', color=INK, ms=7)
    ax.text(end[1] + 0.5, end[2] - 0.5, '150 秒後', ha='left', va='top', color=INK, fontsize=9.5)
    for k in (400, 700, 1000, 1300):
        p, q = trace[k], trace[k + 5]
        if (p[1], p[2]) != (q[1], q[2]):
            ax.annotate('', xy=(q[1], q[2]), xytext=(p[1], p[2]),
                        arrowprops={'arrowstyle': '-|>', 'color': BLUE, 'lw': 2,
                                    'mutation_scale': 16})
    ax.set_title('avoider（最小値のみ、ノイズなし）が 150 秒で走った道すじ', color=INK, fontsize=10.5)
    save(fig, 'avoider-path.svg')


def fig_robot_width_angle():
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.add_patch(Wedge((0, 0), 2.1, -30, 30, color=BLUE, alpha=0.12))
    ax.add_patch(Circle((0, 0), 0.3, color=BLUE))
    ax.plot([0, 1.5], [0.3, 0.3], color=INK2, lw=1, ls=':')
    ax.plot([0, 1.5], [-0.3, -0.3], color=INK2, lw=1, ls=':')
    ax.plot([0, 1.5], [0, 0.3], color=ORANGE, lw=2)
    ax.plot([0, 1.5], [0, -0.3], color=ORANGE, lw=2)
    ax.plot([1.5, 1.5], [-0.3, 0.3], color=INK, lw=1)
    ax.text(1.55, 0, '1.5 m 先で、\nロボットの幅（0.6 m）が\n通る所', va='center', fontsize=9.5, color=INK)
    ax.text(0.75, 0.38, '左右に 約 11° ずつ', ha='center', va='bottom', color=INK, weight='bold')
    ax.text(1.85, 1.15, '見ている範囲 ±30°\n（11° に、余裕を足した）', ha='center', fontsize=9.5, color=INK2)
    ax.set_xlim(-0.5, 3.2)
    ax.set_ylim(-1.3, 1.6)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('前方を、何度まで見ればよいか', color=INK)
    save(fig, 'robot-width-angle.svg')


def fig_turn_timeline():
    cases = [('最小値のみ・ノイズなし', 'min', 1, 0.0), ('最小値のみ・ノイズ 0.5', 'min', 1, 0.5),
             ('最小値の移動平均 N=5・ノイズ 0.5', 'min', 5, 0.5)]
    fig, axes = plt.subplots(3, 1, figsize=(9, 5.4), sharex=True)
    for ax, (name, mode, n, noise) in zip(axes, cases):
        trace = []
        _, starts, _ = run(mode, n, noise, 0, 60.0, trace=trace)
        start = None                              # 「回る」の区間を、柱（長方形）で描く
        for t, _, _, turning in trace + [(60.0, 0, 0, False)]:
            if turning and start is None:
                start = t
            elif not turning and start is not None:
                ax.add_patch(Rectangle((start, 0), max(t - start, 0.12), 1, color=BLUE, lw=0))
                start = None
        ax.set_yticks([0, 1], ['進む', '回る'])
        ax.set_ylim(-0.15, 1.25)
        ax.set_xlim(25, 60)
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
        ax.text(25.3, 1.12, f'{name}　…　60 秒で「回り始めた」{starts} 回', fontsize=10, color=INK,
                va='bottom')
    axes[-1].set_xlabel('時間（秒）　※ 0〜25 秒は、まっすぐ進むだけなので省略')
    fig.suptitle('「回る」と「進む」の切り替わり（青い柱 1 本 = 1 回の回転）', color=INK)
    fig.tight_layout()
    save(fig, 'turn-timeline.svg')


def fig_min_bias():
    rnd = random.Random(1)
    one = [2.0 + rnd.uniform(-0.5, 0.5) for _ in range(61)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.6), gridspec_kw={'width_ratios': [1.35, 1]})
    a1.scatter(one, [rnd.uniform(-0.25, 0.25) for _ in one], s=28, color=BLUE, alpha=0.7, lw=0)
    a1.axvline(2.0, color=INK, lw=1.5)
    a1.text(2.0, 0.42, '本当の距離 2.00 m', ha='center', color=INK, fontsize=9.5)
    m = min(one)
    a1.scatter([m], [0], s=110, color=ORANGE, zorder=5, ec='white', lw=1.5)
    a1.text(m, -0.38, f'最小値 {m:.2f} m\n← これが選ばれる', ha='left', va='top', color=INK, fontsize=9.5)
    a1.set_xlim(1.35, 2.65)
    a1.set_ylim(-0.75, 0.6)
    a1.set_yticks([])
    for side in ('top', 'right', 'left'):
        a1.spines[side].set_visible(False)
    a1.set_xlabel('測った距離（m）')
    a1.set_title('1 回の測定: 61 本の点（ノイズ ±0.5 m）', color=INK, fontsize=10.5)
    counts = [1, 5, 20, 61]

    def mean_bias(n):  # n 本の最小値が、平均でどれだけ近くにずれるか（5000 回）
        return statistics.mean(min(rnd.uniform(-0.5, 0.5) for _ in range(n)) for _ in range(5000))

    bias = [mean_bias(n) for n in counts]
    bars = a2.barh([f'{n} 本' for n in counts], [-b for b in bias], color=BLUE, height=0.55)
    for bar, b in zip(bars, bias):
        a2.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2, f'{-b:.2f} m 近く見える',
                va='center', fontsize=9.5, color=INK)
    a2.invert_yaxis()
    a2.set_xlim(0, 0.75)
    for side in ('top', 'right'):
        a2.spines[side].set_visible(False)
    a2.set_xlabel('最小値が、本当より近く見える量（m）')
    a2.set_title('本数が多いほど、最小値は近くにずれる\n（5000 回の平均）', color=INK, fontsize=10.5)
    fig.tight_layout()
    save(fig, 'min-bias.svg')
    return [round(-b, 2) for b in bias]


def fig_average_danger():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.9), gridspec_kw={'width_ratios': [1, 1.3]})
    a1.add_patch(Rectangle((1.43, -1.1), 0.08, 2.2, color=INK))
    a1.add_patch(Circle((0, 0), 0.12, color=BLUE))
    for deg in (0, 10, 20, 30):
        a = math.radians(deg)
        length = 1.43 / math.cos(a)
        a1.plot([0, 1.43], [0, length * math.sin(a)], color=BLUE if deg == 0 else ORANGE, lw=2)
        a1.text(1.58, length * math.sin(a), f'{deg}°: {length:.2f} m', va='center', fontsize=9.5,
                color=INK)
    a1.text(1.47, -1.2, '壁（正面まで 1.43 m）', ha='center', va='top', fontsize=9.5, color=INK2)
    a1.set_xlim(-0.3, 2.6)
    a1.set_ylim(-1.5, 1.2)
    a1.set_aspect('equal')
    a1.axis('off')
    a1.set_title('斜めのレーザーほど、長くなる', color=INK, fontsize=10.5)

    scan = [3.0] * 61
    scan[30] = 0.5
    a2.bar(range(61), scan, color=BLUE, width=0.8)
    a2.bar([30], [0.5], color=ORANGE, width=0.8)
    a2.axhline(1.5, color=INK2, ls='--', lw=1)
    a2.text(61.5, 1.5, '判断の線 1.5 m', va='center', fontsize=9, color=INK2)
    avg = sum(scan) / len(scan)
    a2.axhline(avg, color=BLUE, lw=1.5)
    a2.text(61.5, avg, f'平均 {avg:.2f} m\n→「進む」', va='center', fontsize=9, color=INK)
    a2.text(31.5, 0.55, '細い柱（0.5 m）', fontsize=9, color=INK, va='bottom')
    a2.set_xlim(-1, 75)
    a2.set_ylim(0, 3.6)
    a2.set_xticks([])
    for side in ('top', 'right'):
        a2.spines[side].set_visible(False)
    a2.set_ylabel('距離（m）')
    a2.set_xlabel('前方 61 本（左から右へ）')
    a2.set_title('細い物は、平均だと見のがす（最小値なら 0.50 m で気づく）', color=INK, fontsize=10.5)
    fig.tight_layout()
    save(fig, 'average-danger.svg')
    return round(avg, 2)


def fig_filter_compare(trials):
    cases = [('最小値のみ（ノイズなし）', 'min', 1, 0.0, 1), ('最小値のみ', 'min', 1, 0.5, trials),
             ('移動平均 N=5（採用）', 'min', 5, 0.5, trials), ('移動平均 N=20', 'min', 20, 0.5, trials),
             ('61 本の平均', 'avg', 1, 0.5, trials)]
    rows = []
    for name, mode, n, noise, k in cases:
        res = [run(mode, n, noise, s, 60.0) for s in range(k)]
        dist = 20 - statistics.mean(r[0] for r in res)
        rows.append((name, dist, statistics.mean(r[1] for r in res), min(r[2] for r in res)))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.6), sharey=True)
    names = [r[0] for r in rows]
    colors = [ORANGE if '採用' in r[0] else BLUE for r in rows]
    b1 = a1.barh(names, [r[1] for r in rows], color=colors, height=0.55)
    a1.axvline(1.5, color=INK2, ls='--', lw=1)
    a1.text(1.5, -0.62, '判断の線 1.5 m', ha='center', va='bottom', fontsize=9, color=INK2)
    for bar, r in zip(b1, rows):
        note = '（押し当たりあり）' if r[3] < 0.31 else ''
        a1.text(bar.get_width() + 0.03, bar.get_y() + bar.get_height() / 2, f'{r[1]:.2f} m{note}',
                va='center', fontsize=9.5, color=INK)
    a1.set_xlim(0, 2.9)
    a1.set_xlabel('回り始めたとき、壁まで何 m あったか（大きいほど手前）')
    a1.invert_yaxis()
    b2 = a2.barh(names, [r[2] for r in rows], color=colors, height=0.55)
    for bar, r in zip(b2, rows):
        a2.text(bar.get_width() + 0.4, bar.get_y() + bar.get_height() / 2, f'{r[2]:.1f} 回',
                va='center', fontsize=9.5, color=INK)
    a2.set_xlim(0, 30)
    a2.set_xlabel('60 秒間に「回り始めた」回数（少ないほど、揺れが少ない）')
    for ax in (a1, a2):
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
    fig.suptitle(f'方法ごとの比較（ノイズ 0.5、各 {trials} 回の平均）', color=INK)
    fig.tight_layout()
    save(fig, 'filter-compare.svg')
    return rows


def print_compare(rows):
    for name, dist, starts, closest in rows:
        print(f'  {name}: 壁まで {dist:.2f} m、回数 {starts:.1f}、最近接 {closest:.2f} m')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--trials', type=int, default=100, help='比較の図で、走らせる回数')
    parser.add_argument('--only', help='この名前の図だけ作る（例: scan-start）')
    args = parser.parse_args()
    figures = {
        'room-map': fig_room_map, 'lidar-index': fig_lidar_index, 'scan-start': fig_scan_start,
        'twist': fig_twist, 'speed-step': fig_speed_step, 'wall-stop': fig_wall_stop,
        'avoider-path': fig_avoider_path, 'robot-width-angle': fig_robot_width_angle,
        'turn-timeline': fig_turn_timeline,
        'min-bias': lambda: print('最小値のずれ（1, 5, 20, 61 本）:', fig_min_bias()),
        'average-danger': lambda: print('細い柱の例の平均:', fig_average_danger()),
        'filter-compare': lambda: print_compare(fig_filter_compare(args.trials)),
    }
    for name, make in figures.items():
        if args.only in (None, name):
            make()


if __name__ == '__main__':
    main()
