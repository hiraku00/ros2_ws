import rclpy
import random
from rclpy.node import Node
from std_msgs.msg import Float32, String

TRACK = 40  # 廊下の長さ


class SimRobot(Node):
    def __init__(self):
        super().__init__('sim_robot')
        self.x = 2.0        # 今いる位置
        self.heading = 1    # 1: 右向き, -1: 左向き
        self.cmd = 'FORWARD'
        self.pub = self.create_publisher(Float32, 'distance', 10)
        self.create_subscription(String, 'cmd', self.on_cmd, 10)
        self.create_timer(0.2, self.step)

    def on_cmd(self, msg):
        if msg.data == 'TURN' and self.cmd != 'TURN':
            self.heading *= -1  # TURN に切り替わった瞬間だけ向きを反転
        self.cmd = msg.data

    def step(self):
        if self.cmd == 'FORWARD':
            self.x += 0.5 * self.heading
        elif self.cmd == 'SLOW':
            self.x += 0.2 * self.heading
        self.x = max(0.0, min(float(TRACK), self.x))

        dist = (TRACK - self.x) if self.heading == 1 else self.x
        msg = Float32()
        msg.data = float(dist) + random.uniform(-0.5, 0.5)  # センサノイズ
        self.pub.publish(msg)

        line = ['.'] * (TRACK + 1)
        line[int(self.x)] = '>' if self.heading == 1 else '<'
        print(f"|{''.join(line)}| 壁まで={dist:4.1f}  指示={self.cmd}", flush=True)


def main():
    rclpy.init()
    node = SimRobot()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()
