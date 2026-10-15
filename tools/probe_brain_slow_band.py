"""本物の brain に距離を直接送り、SLOW の出る線（ヒステリシス）の効果を確かめる。

sim_robot は使わない。真の距離を 8.3（SLOW に入る線 8.0 と、出る線 9.0 の間）に置き、
ノイズ ±1.0 を載せて送り、指示が SLOW ↔ FORWARD で切り替わった回数を数える。

コンテナの中で、`source` を済ませたうえで実行する。

    python3 tools/probe_brain_slow_band.py

他のノードと混ざらないよう、専用の ROS_DOMAIN_ID で動かす。終了時に、自分が起動した brain は止める。
期待する結果: hysteresis=0.0 で数十回（乱数で変わる）、hysteresis=1.0 で 0 回。
"""
import os
import random
import signal
import subprocess
import time

os.environ['ROS_DOMAIN_ID'] = '77'   # rclpy を読み込む前に設定する（他のノードと通信を分ける）

import rclpy                          # noqa: E402
from rclpy.node import Node           # noqa: E402
from std_msgs.msg import Float32, String  # noqa: E402

TRUE_DISTANCE = 8.3   # 8.0（入る線）と 9.0（出る線）の間
NOISE = 1.0


def run(hysteresis):
    rclpy.init()
    node = Node('probe')
    pub = node.create_publisher(Float32, 'distance', 10)
    cmds = []
    node.create_subscription(String, 'cmd', lambda m: cmds.append(m.data), 10)

    # 自分専用のプロセスグループで brain を起動し、終了時にまとめて止める
    brain = subprocess.Popen(['ros2', 'run', 'my_first_pkg', 'brain'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
    try:
        time.sleep(3)
        subprocess.run(['ros2', 'param', 'set', '/brain', 'hysteresis', str(hysteresis)],
                       stdout=subprocess.DEVNULL, check=True)

        def send(value, times):
            for _ in range(times):
                msg = Float32()
                msg.data = value
                pub.publish(msg)
                rclpy.spin_once(node, timeout_sec=0.02)
                time.sleep(0.02)

        send(5.0, 20)       # まず SLOW 状態にする（平均 N=5 を、5.0 で満たす）
        cmds.clear()
        for _ in range(300):
            send(TRUE_DISTANCE + random.uniform(-NOISE, NOISE), 1)
    finally:
        os.killpg(brain.pid, signal.SIGINT)
        brain.wait(timeout=10)
        node.destroy_node()
        rclpy.shutdown()

    flips = sum(1 for a, b in zip(cmds, cmds[1:]) if a != b)
    print(f'hysteresis={hysteresis}: 帯の中で指示が切り替わった回数 = {flips}（内訳 {sorted(set(cmds))}）')


if __name__ == '__main__':
    random.seed(0)
    for h in (0.0, 1.0):
        run(h)
