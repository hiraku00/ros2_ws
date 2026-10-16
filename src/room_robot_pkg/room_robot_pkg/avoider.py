from collections import deque

from geometry_msgs.msg import Twist
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class Avoider(Node):
    def __init__(self):
        super().__init__('avoider')
        self.history = deque(maxlen=5)
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.create_subscription(LaserScan, 'scan', self.on_scan, 10)

    def on_scan(self, msg):
        front = msg.ranges[0:31] + msg.ranges[330:360]
        nearest = min(front)
        self.history.append(nearest)
        dist = sum(self.history) / len(self.history)
        out = Twist()
        if dist < 1.5:
            out.linear.x = 0.0
            out.angular.z = 0.5
        else:
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
    node.destroy_node()
    rclpy.try_shutdown()
