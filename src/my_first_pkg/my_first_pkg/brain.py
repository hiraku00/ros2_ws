import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String


class Brain(Node):
    def __init__(self):
        super().__init__('brain')
        self.stop_started = None
        self.declare_parameter('turn_distance', 3.0)
        self.declare_parameter('slow_distance', 8.0)
        self.pub = self.create_publisher(String, 'cmd', 10)
        self.create_subscription(Float32, 'distance', self.on_distance, 10)

    def on_distance(self, msg):
        now = self.get_clock().now().nanoseconds / 1e9  # 現在時刻(秒)
        turn = self.get_parameter('turn_distance').value
        slow = self.get_parameter('slow_distance').value
        if msg.data < turn:
            if self.stop_started is None:
                self.stop_started = now
            if now - self.stop_started > 2.0:
                cmd = 'TURN'
            else:
                cmd = 'STOP'
        elif msg.data < slow:
            self.stop_started = None
            cmd = 'SLOW'
        else:
            self.stop_started = None
            cmd = 'FORWARD'
        out = String()
        out.data = cmd
        self.pub.publish(out)


def main():
    rclpy.init()
    node = Brain()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()
