import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MyTalker(Node):
    def __init__(self):
        super().__init__('my_talker')
        self.pub = self.create_publisher(String, 'my_topic', 10)
        self.count = 0
        self.timer = self.create_timer(1.0, self.on_timer)

    def on_timer(self):
        msg = String()
        msg.data = f'Hello from me: {self.count}'
        self.pub.publish(msg)
        self.get_logger().info(f'Publishing: {msg.data}')
        self.count += 1


def main():
    rclpy.init()
    node = MyTalker()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()
