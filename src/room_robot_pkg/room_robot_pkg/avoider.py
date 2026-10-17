from collections import deque

from geometry_msgs.msg import Twist
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class Avoider(Node):
    def __init__(self):
        super().__init__('avoider')
        self.avoiding = False                     # いま、回ってよけている最中か
        self.declare_parameter('hysteresis', 0.5)  # 出る線を、入る線（1.5 m）からどれだけ遠くに置くか（m）
        self.history = deque(maxlen=5)
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.create_subscription(LaserScan, 'scan', self.on_scan, 10)

    def on_scan(self, msg):
        front = msg.ranges[0:31] + msg.ranges[330:360]
        nearest = min(front)
        self.history.append(nearest)
        dist = sum(self.history) / len(self.history)
        hysteresis = self.get_parameter('hysteresis').value
        threshold = 1.5 + hysteresis if self.avoiding else 1.5
        out = Twist()
        if dist < threshold:
            self.avoiding = True
            out.linear.x = 0.0
            out.angular.z = 0.5
        else:
            self.avoiding = False
            out.linear.x = 0.3
            out.angular.z = 0.0

        self.pub.publish(out)


def main():
    rclpy.init()
    node = Avoider()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except Exception:
        if rclpy.ok():  # Ctrl+C の終了処理の途中で出る RCLError だけを、無視する
            raise
    node.destroy_node()
    rclpy.try_shutdown()
