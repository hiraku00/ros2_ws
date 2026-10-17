"""docs/basics/images/ の図（SVG）を作る（Mac で実行できる。ROS 2 不要）。

数字は手で書かずに、brain.py と同じ判断を再現した simulate_filters.py から出す。

使い方:
    python3 tools/make_basics_figures.py               # 約 1 分
    python3 tools/make_basics_figures.py --only chattering
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
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from simulate_filters import approach, evaluate  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / 'docs' / 'basics' / 'images'

# 色（dataviz の既定パレットの 1〜3 番。ステップ 2 の図と同じ）
BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
INK, INK2, MUTED, GRID = '#0b0b0b', '#52514e', '#9b9a95', '#e4e3df'
SURFACE, PANEL = '#fcfcfb', '#f1efea'
# 指示ごとの色（凡例と文字ラベルを必ず添える）
CMD_COLOR = {'F': AQUA, 'S': BLUE, 'P': ORANGE, 'T': INK}
CMD_NAME = {'F': 'FORWARD', 'S': 'SLOW', 'P': 'STOP', 'T': 'TURN'}

_INSTALLED = {f.name for f in font_manager.fontManager.ttflist}
JP_FONTS = [f for f in ('Hiragino Sans', 'Noto Sans CJK JP', 'IPAexGothic') if f in _INSTALLED]
plt.rcParams.update({
    'font.family': JP_FONTS + ['sans-serif'],
    'font.size': 11,
    'svg.fonttype': 'none',
    'svg.hashsalt': 'basics',
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


def clean(ax, keep=('left', 'bottom')):
    for side in ('top', 'right', 'left', 'bottom'):
        ax.spines[side].set_visible(side in keep)


def box(ax, x, y, w, h, text, fc=PANEL, ec=MUTED, fontsize=11, weight='normal'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.08',
                                fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=fontsize,
            color=INK, weight=weight)


def arrow(ax, x1, y1, x2, y2, color=INK2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops={'arrowstyle': '-|>', 'color': color, 'lw': 1.8, 'mutation_scale': 16})


def cmd_strip(ax, trace, y0=0.0, height=1.0):
    """指示の移り変わりを、色の帯で描く。"""
    for i, (t, _, _, _, c) in enumerate(trace):
        t_next = trace[i + 1][0] if i + 1 < len(trace) else t + 0.2
        ax.add_patch(Rectangle((t, y0), t_next - t, height, color=CMD_COLOR[c], lw=0))


def run_trace(n, h, noise, seed):
    random.seed(seed)
    trace = []
    approach(n, h, noise=noise, trace=trace)
    return trace


# ---------------------------------------------------------------- 01
def fig_nodes_topics():
    fig, ax = plt.subplots(figsize=(9, 3.4))
    box(ax, 0.0, 1.0, 2.2, 1.0, 'talker\n（ノード）', fc='#e3edf9', ec=BLUE, weight='bold')
    box(ax, 3.4, 1.0, 2.2, 1.0, 'my_topic\n（トピック）', fc='#fdeee6', ec=ORANGE, weight='bold')
    box(ax, 6.8, 1.0, 2.2, 1.0, 'listener\n（ノード）', fc='#e3edf9', ec=BLUE, weight='bold')
    arrow(ax, 2.25, 1.5, 3.35, 1.5)
    arrow(ax, 5.65, 1.5, 6.75, 1.5)
    ax.text(2.8, 1.62, '書く', ha='center', va='bottom', color=INK)
    ax.text(6.2, 1.62, '読む', ha='center', va='bottom', color=INK)
    ax.text(1.1, 0.75, 'パブリッシャ\n（書く側）', ha='center', va='top', fontsize=10, color=INK2)
    ax.text(4.5, 0.75, '名前のついた掲示板。\n中身は「メッセージ」', ha='center', va='top',
            fontsize=10, color=INK2)
    ax.text(7.9, 0.75, 'サブスクライバ\n（読む側）', ha='center', va='top', fontsize=10, color=INK2)
    ax.text(1.1, 2.2, 'たとえ: 社員', ha='center', fontsize=10, color=INK2)
    ax.text(4.5, 2.2, 'たとえ: 社内の掲示板', ha='center', fontsize=10, color=INK2)
    ax.text(7.9, 2.2, 'たとえ: 社員', ha='center', fontsize=10, color=INK2)
    ax.set_xlim(-0.2, 9.2)
    ax.set_ylim(-0.3, 2.6)
    ax.axis('off')
    ax.set_title('ノードとトピック（talker が書いた紙を、listener が読む）', color=INK)
    save(fig, 'nodes-topics.svg')


def fig_docker_layers():
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.add_patch(FancyBboxPatch((0, 0), 10, 5, boxstyle='round,pad=0.02,rounding_size=0.15',
                                fc='#f6f5f2', ec=INK2, lw=1.5))
    ax.text(0.3, 4.65, 'Mac（macOS）', fontsize=12, weight='bold', color=INK, va='top')
    ax.text(0.3, 4.2, 'プロンプト: ~/Practice/ros2_ws ❯\n使うもの: docker、git、エディタ',
            fontsize=10, color=INK2, va='top')
    ax.add_patch(FancyBboxPatch((4.6, 0.3), 5.1, 4.4, boxstyle='round,pad=0.02,rounding_size=0.15',
                                fc='#eef3fb', ec=BLUE, lw=1.5))
    ax.text(4.85, 4.45, 'Docker', fontsize=12, weight='bold', color=INK, va='top')
    ax.add_patch(FancyBboxPatch((5.0, 0.6), 4.4, 3.3, boxstyle='round,pad=0.02,rounding_size=0.15',
                                fc='#fdf1ea', ec=ORANGE, lw=1.5))
    ax.text(5.25, 3.65, 'コンテナ ros2（Ubuntu の小部屋）', fontsize=11.5, weight='bold',
            color=INK, va='top')
    ax.text(5.25, 3.15, 'プロンプト: root@xxxx:/#\n使うもの: ros2、colcon\nROS 2 は、ここにある',
            fontsize=10, color=INK2, va='top')
    box(ax, 0.4, 0.7, 3.4, 1.0, 'フォルダ\n~/Practice/ros2_ws', fc='white', fontsize=10)
    box(ax, 5.3, 0.9, 3.8, 0.8, 'フォルダ /root/ros2_ws', fc='white', fontsize=10)
    ax.annotate('', xy=(5.25, 1.3), xytext=(3.85, 1.2),
                arrowprops={'arrowstyle': '<|-|>', 'color': INK, 'lw': 1.8, 'mutation_scale': 16})
    ax.text(4.3, 0.55, '同じ中身（共有）', ha='center', va='top', fontsize=10, color=INK,
            bbox={'boxstyle': 'round,pad=0.2', 'fc': 'white', 'ec': 'none'})
    ax.set_xlim(-0.2, 10.2)
    ax.set_ylim(-0.2, 5.2)
    ax.axis('off')
    ax.set_title('Mac の中に、Ubuntu の小部屋（コンテナ）を作る', color=INK)
    save(fig, 'docker-layers.svg')


# ---------------------------------------------------------------- 02
def fig_corridor_loop():
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.5, 5.2), gridspec_kw={'height_ratios': [1, 1.2]})
    a1.add_patch(Rectangle((0, 0), 40, 1, fc=PANEL, ec=MUTED))
    for wall in (0, 40):
        a1.add_patch(Rectangle((wall - 0.4, -0.3), 0.4 if wall == 0 else 0.4, 1.6, color=INK))
    a1.text(-0.2, 1.45, '壁 (0)', ha='center', va='bottom', fontsize=10, color=INK2)
    a1.text(40.2, 1.45, '壁 (40)', ha='center', va='bottom', fontsize=10, color=INK2)
    a1.text(30, 0.5, '>', ha='center', va='center', fontsize=20, color=BLUE, weight='bold')
    a1.annotate('', xy=(40, -0.6), xytext=(30, -0.6),
                arrowprops={'arrowstyle': '<->', 'color': BLUE, 'lw': 1.5})
    a1.text(35, -0.75, '壁まで ＝ 40 − 30 ＝ 10', ha='center', va='top', fontsize=10, color=INK)
    a1.text(30, 1.4, 'ロボット（位置 30、右向き）', ha='center', va='bottom', fontsize=10, color=INK)
    a1.set_xlim(-2, 42)
    a1.set_ylim(-1.6, 2.1)
    a1.set_xticks(range(0, 41, 10))
    clean(a1, keep=())
    a1.tick_params(left=False, labelleft=False, bottom=False)
    a1.set_title('40 マスの廊下（1 マス ＝ 1）', color=INK, fontsize=11)

    box(a2, 0.0, 0.6, 3.0, 1.2, 'sim_robot\n（体）', fc='#e3edf9', ec=BLUE, weight='bold')
    box(a2, 7.0, 0.6, 3.0, 1.2, 'brain\n（頭）', fc='#e3edf9', ec=BLUE, weight='bold')
    arrow(a2, 3.05, 1.55, 6.95, 1.55)
    arrow(a2, 6.95, 0.85, 3.05, 0.85)
    a2.text(5.0, 1.65, 'distance（壁までの距離）', ha='center', va='bottom', fontsize=10, color=INK)
    a2.text(5.0, 0.75, 'cmd（FORWARD / SLOW / STOP / TURN）', ha='center', va='top',
            fontsize=10, color=INK)
    a2.text(5.0, 0.0, '0.2 秒ごとに、この輪を 1 周 → ロボットが 1 歩動く', ha='center', fontsize=10,
            color=INK2)
    a2.set_xlim(-0.3, 10.3)
    a2.set_ylim(-0.3, 2.2)
    a2.axis('off')
    fig.tight_layout()
    save(fig, 'corridor-loop.svg')


def fig_brain_zones():
    fig, ax = plt.subplots(figsize=(10, 2.9))
    zones = [(0, 3, 'P', 'STOP → 2 秒後 TURN'), (3, 8, 'S', 'SLOW（1 歩 0.2）'),
             (8, 12, 'F', 'FORWARD（1 歩 0.5）')]
    for a, b, c, label in zones:
        ax.add_patch(Rectangle((a, 0), b - a, 1, color=CMD_COLOR[c], alpha=0.25, lw=0))
        ax.text((a + b) / 2, 0.5, label, ha='center', va='center', fontsize=10.5, color=INK,
                weight='bold')
    for x, label in ((3, '入る線 3.0'), (8, '入る線 8.0')):
        ax.axvline(x, color=INK, lw=1.8)
        ax.text(x, 1.08, label, ha='center', va='bottom', fontsize=9.5, color=INK)
    for x, label in ((4, '出る線 4.0'), (9, '出る線 9.0')):
        ax.axvline(x, color=INK2, lw=1.5, ls='--', ymax=0.83)
        ax.text(x + 0.08, -0.12, label, ha='left', va='top', fontsize=9.5, color=INK2)
    ax.add_patch(Rectangle((-0.35, -0.05), 0.35, 1.1, color=INK))
    ax.text(-0.2, 1.08, '壁', ha='center', va='bottom', fontsize=10, color=INK)
    ax.set_xlim(-0.5, 12.2)
    ax.set_ylim(-0.6, 1.5)
    ax.set_yticks([])
    ax.set_xticks(range(0, 13))
    ax.set_xlabel('壁までの距離')
    clean(ax, keep=('bottom',))
    ax.set_title('brain の判断の線（点線の「出る線」は、03 章のヒステリシス）', color=INK)
    save(fig, 'brain-zones.svg')


def fig_approach_timeline():
    trace = run_trace(1, 1.0, 0.0, 0)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.5, 4.6), sharex=True,
                                 gridspec_kw={'height_ratios': [3, 0.6]})
    ts = [p[0] for p in trace]
    a1.plot(ts, [p[1] for p in trace], color=INK, lw=2)
    for y, label in ((8, '8.0'), (3, '3.0')):
        a1.axhline(y, color=MUTED, ls=':', lw=1)
        a1.text(ts[-1] + 0.3, y, label, va='center', fontsize=9, color=INK2)
    a1.set_ylabel('壁までの距離')
    a1.set_ylim(0, 40)
    clean(a1)
    stop = [p for p in trace if p[4] == 'P']
    a1.annotate('STOP（約 2 秒、止まっている）', xy=(stop[len(stop) // 2][0], stop[0][1] + 0.4),
                xytext=(stop[0][0] - 3.5, 16), fontsize=10, color=INK, ha='center',
                arrowprops={'arrowstyle': '-|>', 'color': INK2})
    cmd_strip(a2, trace)
    a2.set_yticks([])
    a2.set_ylim(0, 1)
    clean(a2, keep=('bottom',))
    a2.set_xlabel('時間（秒）')
    starts = {}
    for t, _, _, _, c in trace:
        starts.setdefault(c, t)
    for c, t in starts.items():
        if c != 'T':   # TURN は 1 歩だけで帯が細いので、下に書く
            a2.text(t + 0.15, 0.5, CMD_NAME[c], va='center', fontsize=9,
                    color='white' if c == 'P' else INK, weight='bold')
        else:
            a2.text(t, -0.25, 'TURN', ha='center', va='top', fontsize=9, color=INK, weight='bold')
    a1.set_title('ノイズなしで、壁に向かって走ったとき（下の帯 ＝ brain の指示）', color=INK)
    fig.tight_layout()
    save(fig, 'approach-timeline.svg')


# ---------------------------------------------------------------- 03
def fig_noise_example():
    trace = run_trace(1, 1.0, 0.5, 3)
    part = [p for p in trace if 3.0 <= p[1] <= 9.0]
    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    ts = [p[0] for p in part]
    true = [p[1] for p in part]
    ax.fill_between(ts, [v - 0.5 for v in true], [v + 0.5 for v in true], color=BLUE, alpha=0.12,
                    lw=0)
    ax.plot(ts, true, color=INK, lw=2)
    ax.plot(ts, [p[2] for p in part], 'o', color=BLUE, ms=5)
    ax.text(ts[3], true[3] + 0.75, '青い点 ＝ brain に届いた値（毎回ぶれる）', fontsize=10, color=INK)
    ax.text(ts[-12], true[-12] - 0.85, '黒い線 ＝ 本当の距離\n薄い帯 ＝ ±0.5 の範囲', fontsize=10,
            color=INK, va='top')
    ax.set_xlabel('時間（秒）')
    ax.set_ylabel('壁までの距離')
    clean(ax)
    ax.set_title('ノイズ ±0.5：同じ所でも、届く値は毎回ちがう', color=INK)
    save(fig, 'noise-example.svg')


def _chatter_panel(ax, trace, h, title):
    part = [p for p in trace if p[1] <= 4.8]
    ts = [p[0] for p in part]
    ax.plot(ts, [p[1] for p in part], color=INK, lw=1.5)
    ax.plot(ts, [p[2] for p in part], 'o', color=BLUE, ms=4)
    ax.axhline(3.0, color=INK, lw=1.2)
    ax.text(ts[-1] + 0.15, 3.0, '入る線 3.0', va='center', fontsize=9, color=INK)
    if h:
        ax.axhline(3.0 + h, color=INK2, lw=1.2, ls='--')
        ax.text(ts[-1] + 0.15, 3.0 + h, f'出る線 {3.0 + h:.1f}', va='center', fontsize=9, color=INK2)
    cmd_strip(ax, part, y0=1.6, height=0.35)
    flips = sum(1 for a, b in zip(part, part[1:]) if a[4] == 'P' and b[4] == 'S')
    ax.set_ylim(1.5, 5.4)
    ax.set_ylabel('距離')
    clean(ax)
    ax.set_title(f'{title}　…　STOP の途中で SLOW に戻った回数: {flips} 回', fontsize=10.5,
                 color=INK, loc='left')


def fig_chattering():
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.5, 6.2), sharex=False)
    _chatter_panel(a1, run_trace(1, 0.0, 0.5, 7), 0.0, 'ヒステリシスなし')
    _chatter_panel(a2, run_trace(1, 1.0, 0.5, 7), 1.0, 'ヒステリシスあり（幅 1.0）')
    a2.set_xlabel('時間（秒）')
    handles = [Rectangle((0, 0), 1, 1, color=CMD_COLOR[c]) for c in 'SPT']
    fig.legend(handles, [CMD_NAME[c] for c in 'SPT'], loc='upper center', ncol=3, frameon=False,
               bbox_to_anchor=(0.5, 0.955), title='下の帯の色 ＝ brain の指示', fontsize=9.5)
    fig.suptitle('壁の手前 3.0 付近（青い点 ＝ 届いた値、黒い線 ＝ 本当の距離）', color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    save(fig, 'chattering.svg')


def fig_ma_lag():
    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    styles = [(1, AQUA, '平均なし（N=1）'), (5, BLUE, 'N=5（採用）'), (20, ORANGE, 'N=20')]
    for n, color, label in styles:
        trace = run_trace(n, 0.0, 0.5, 11)
        part = [p for p in trace if p[1] <= 9.0]
        ax.plot([p[1] for p in part], [p[3] for p in part], color=color, lw=1.8, label=label)
        first = next(p for p in part if p[4] == 'P')
        ax.plot(first[1], first[3], 'o', color=color, ms=9, mec='white', mew=1.5, zorder=5)
    ax.plot([0, 9], [0, 9], color=MUTED, lw=1, ls=':')
    ax.text(2.6, 0.7, '点線 ＝ 遅れがなければ、ここに乗る', fontsize=9, color=INK2)
    ax.axhline(3.0, color=INK, lw=1)
    ax.text(8.9, 3.15, '入る線 3.0', va='bottom', fontsize=9, color=INK)
    ax.set_xlim(9.2, -0.2)
    ax.set_ylim(0, 10)
    ax.set_xlabel('本当の距離（右から左へ、壁に近づく）')
    ax.set_ylabel('brain が判断に使う値')
    ax.legend(frameon=False, loc='lower left')
    clean(ax)
    ax.set_title('移動平均の遅れ（● ＝ STOP を始めた所。N が大きいほど、壁に近い）', color=INK)
    save(fig, 'ma-lag.svg')


def _bar_pair(ax1, ax2, labels, left, right, left_label, right_label, highlight, fmt_l, fmt_r,
              right_xlim):
    colors = [ORANGE if i == highlight else BLUE for i in range(len(labels))]
    b1 = ax1.barh(labels, left, color=colors, height=0.55)
    for bar, v in zip(b1, left):
        ax1.text(bar.get_width() + max(left) * 0.02, bar.get_y() + bar.get_height() / 2, fmt_l(v),
                 va='center', fontsize=9.5, color=INK)
    ax1.set_xlim(0, max(left) * 1.3 if max(left) else 1)
    ax1.set_xlabel(left_label)
    ax1.invert_yaxis()
    b2 = ax2.barh(labels, right, color=colors, height=0.55)
    for bar, v in zip(b2, right):
        ax2.text(bar.get_width() + right_xlim * 0.02, bar.get_y() + bar.get_height() / 2,
                 fmt_r(v), va='center', fontsize=9.5, color=INK)
    ax2.set_xlim(0, right_xlim)
    ax2.set_xlabel(right_label)
    for ax in (ax1, ax2):
        clean(ax)


def fig_n_tradeoff():
    ns = [1, 3, 5, 10, 20]
    random.seed(0)                     # simulate_filters.py の main() と同じ順番で乱数を使う
    for h in (0.0, 0.5, 1.0, 2.0):     # （【1】の 4 回ぶんを先に使ってから、【2】を計算する）
        evaluate(1, h)
    chatter = [evaluate(n, 0.0)[0] for n in ns]
    random.seed(0)
    start = []
    for n in ns:
        vals = []
        for _ in range(2000):
            trace = []
            approach(n, 0.0, trace=trace)
            vals.append(next(p[1] for p in trace if p[4] == 'P'))
        start.append(statistics.mean(vals))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.4), sharey=True)
    _bar_pair(a1, a2, [f'N={n}' for n in ns], chatter, start,
              'STOP の途中で SLOW に戻った割合（%）。少ないほど良い',
              'STOP を始めた所の、本当の距離。3.0 に近いほど良い', 2,
              lambda v: f'{v:.1f}%', lambda v: f'{v:.2f}', 3.8)
    a2.axvline(3.0, color=INK2, ls='--', lw=1)
    fig.suptitle('移動平均の個数 N のトレードオフ（ヒステリシスなし、ノイズ ±0.5）', color=INK)
    fig.tight_layout()
    save(fig, 'n-tradeoff.svg')
    return chatter, start


def fig_hysteresis_width():
    fig, ax = plt.subplots(figsize=(9.5, 3.9))
    ax.plot([2.4, 4.6], [0, 0], color=INK2, lw=1.2)
    for x in (2.5, 3.0, 3.5, 4.0, 4.5):
        ax.plot([x, x], [-0.03, 0.03], color=INK2, lw=1)
        ax.text(x, -0.07, f'{x:.1f}', ha='center', va='top', fontsize=9, color=INK2)
    ax.plot([3.0, 3.0], [0.05, 1.0], color=INK, lw=1.5)
    ax.text(3.0, 1.02, '入る線 3.0', ha='center', va='bottom', fontsize=10, color=INK)
    ax.plot([4.0, 4.0], [0.05, 1.0], color=ORANGE, lw=1.5, ls='--')
    ax.text(4.0, 1.02, '出る線 4.0', ha='center', va='bottom', fontsize=10, color=INK)
    rows = [
        (0.85, 3.0, None, 'o', BLUE, '① 届いた値が 3.0 → STOP に入る'),
        (0.55, 3.5, 3.0, 's', INK, '② でも、ノイズで −0.5 小さく見えていたなら、本当は 3.5'),
        (0.25, 4.0, 3.5, 'o', BLUE, '③ 次は、ノイズで ＋0.5 大きく見えると、届く値は 4.0'),
    ]
    for y, x, x_from, marker, color, text in rows:
        if x_from is not None:
            ax.annotate('', xy=(x - 0.03, y), xytext=(x_from, y),
                        arrowprops={'arrowstyle': '->', 'color': INK2, 'lw': 1.3})
        ax.plot(x, y, marker, color=color, ms=9, zorder=5)
        ax.text(4.65, y, text, ha='left', va='center', fontsize=9.5, color=INK)
    ax.text(4.65, 0.06, '→ 出る線が 4.0 より手前だと、③で STOP が途切れる', ha='left', va='center',
            fontsize=9.5, color=INK, weight='bold')
    ax.set_xlim(2.4, 8.4)
    ax.set_ylim(-0.2, 1.15)
    ax.axis('off')
    ax.set_title('出る線を 4.0 にする理由（3.0 ＋ ノイズの全幅 1.0）', color=INK)
    save(fig, 'hysteresis-width.svg')


def fig_hysteresis_compare():
    hs = [0.0, 0.5, 1.0, 2.0]
    random.seed(0)
    rows = [evaluate(1, h) for h in hs]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.1), sharey=True)
    _bar_pair(a1, a2, [f'幅 {h}' for h in hs], [r[0] for r in rows], [r[1] for r in rows],
              'STOP の途中で SLOW に戻った割合（%）', 'いちばん壁に近づいた本当の距離（平均）', 2,
              lambda v: f'{v:.1f}%', lambda v: f'{v:.2f}', 3.8)
    a2.axvline(3.0, color=INK2, ls='--', lw=1)
    fig.suptitle('ヒステリシスの幅をくらべる（平均なし、ノイズ ±0.5、5000 回）', color=INK)
    fig.tight_layout()
    save(fig, 'hysteresis-compare.svg')
    return rows


def fig_aircon():
    rnd = random.Random(5)
    ts = [i * 0.5 for i in range(121)]
    temp = [26.0 + 0.35 * math.sin(i / 9.0) + rnd.uniform(-0.25, 0.25) for i in range(121)]

    def switch(lo, hi):
        state, out = False, []
        for v in temp:
            if not state and v > hi:
                state = True
            elif state and v < lo:
                state = False
            out.append(state)
        return out

    fig, axes = plt.subplots(3, 1, figsize=(9.5, 4.8), sharex=True,
                             gridspec_kw={'height_ratios': [2.2, 0.5, 0.5]})
    a0, a1, a2 = axes
    a0.plot(ts, temp, color=INK, lw=1.5)
    a0.axhline(26.0, color=BLUE, lw=1.2)
    a0.axhline(26.5, color=ORANGE, lw=1.2, ls='--')
    a0.axhline(25.5, color=ORANGE, lw=1.2, ls='--')
    a0.text(60.5, 26.0, '26.0', va='center', fontsize=9, color=INK)
    a0.text(60.5, 26.5, '26.5（ON にする線）', va='center', fontsize=9, color=INK)
    a0.text(60.5, 25.5, '25.5（OFF にする線）', va='center', fontsize=9, color=INK)
    a0.set_ylabel('室温（℃）')
    clean(a0)
    for ax, (lo, hi), name in ((a1, (26.0, 26.0), '線 1 本（26.0）'),
                               (a2, (25.5, 26.5), '線 2 本（25.5 と 26.5）')):
        states = switch(lo, hi)
        for t, on in zip(ts, states):
            if on:
                ax.add_patch(Rectangle((t, 0), 0.5, 1, color=BLUE, lw=0))
        flips = sum(1 for a, b in zip(states, states[1:]) if a != b)
        ax.set_yticks([])
        ax.set_ylim(0, 1)
        clean(ax, keep=('bottom',))
        ax.text(60.5, 0.5, f'{name}: 切り替え {flips} 回', va='center', fontsize=9.5, color=INK)
    a2.set_xlabel('時間（分）　　青い帯 ＝ エアコン ON')
    a0.set_title('エアコンのたとえ（同じ室温の変化で、切り替えの回数をくらべる）', color=INK)
    fig.tight_layout()
    save(fig, 'aircon.svg')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--only', help='この名前の図だけ作る（例: chattering）')
    args = parser.parse_args()
    figures = {
        'nodes-topics': fig_nodes_topics, 'docker-layers': fig_docker_layers,
        'corridor-loop': fig_corridor_loop, 'brain-zones': fig_brain_zones,
        'approach-timeline': fig_approach_timeline, 'noise-example': fig_noise_example,
        'chattering': fig_chattering, 'ma-lag': fig_ma_lag,
        'n-tradeoff': lambda: print('N ごとの（中断 %, STOP を始めた距離）:', fig_n_tradeoff()),
        'hysteresis-width': fig_hysteresis_width,
        'hysteresis-compare': lambda: print('幅ごとの（中断 %, 最接近, -）:', fig_hysteresis_compare()),
        'aircon': fig_aircon,
    }
    for name, make in figures.items():
        if args.only in (None, name):
            make()


if __name__ == '__main__':
    main()
