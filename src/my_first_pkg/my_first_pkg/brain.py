import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String


class Brain(Node):
    def __init__(self):
        super().__init__('brain')
        self.declare_parameter('turn_distance', 3.0)
        self.declare_parameter('slow_distance', 8.0)
        self.pub = self.create_publisher(String, 'cmd', 10)
        self.create_subscription(Float32, 'distance', self.on_distance, 10)

    def on_distance(self, msg):
        turn = self.get_parameter('turn_distance').value
        slow = self.get_parameter('slow_distance').value
        if msg.data < turn:
            cmd = 'TURN'
        elif msg.data < slow:
            cmd = 'SLOW'
        else:
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
