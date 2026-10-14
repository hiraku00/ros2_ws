import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MyListener(Node):
    def __init__(self):
        super().__init__('my_listener')
        self.sub = self.create_subscription(
            String, 'my_topic', self.on_msg, 10)

    def on_msg(self, msg):
        self.get_logger().info(f'I heard: {msg.data}')


def main():
    rclpy.init()
    node = MyListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()
