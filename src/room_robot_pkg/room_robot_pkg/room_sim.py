"""2D の部屋のシミュレータ。

/cmd_vel (Twist) を受けてロボットを動かし、LiDAR を模擬して /scan (LaserScan) に送る。
部屋の様子は SVG / HTML にして、output_dir に毎秒書き出す。
"""
import math
import os
import random

from geometry_msgs.msg import Twist
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

ROOM_SIZE = 20.0
ROBOT_RADIUS = 0.3
NUM_RAYS = 360
RANGE_MIN = 0.1

# 障害物（部屋の座標。単位は m）
CIRCLES = [(3.0, 13.0, 1.5)]            # (中心 x, 中心 y, 半径)
RECTS = [(14.0, 2.0, 17.0, 5.0)]        # (x の小, y の小, x の大, y の大)

SCALE = 30  # SVG の 1 m あたりのピクセル数


def build_segments():
    """壁と四角い障害物を、線分 (x1, y1, x2, y2) の集まりにする。"""
    segments = []
    boxes = [(0.0, 0.0, ROOM_SIZE, ROOM_SIZE)] + RECTS
    for x1, y1, x2, y2 in boxes:
        segments += [
            (x1, y1, x2, y1), (x2, y1, x2, y2),
            (x2, y2, x1, y2), (x1, y2, x1, y1),
        ]
    return segments


SEGMENTS = build_segments()


def ray_segment(px, py, dx, dy, seg):
    """レーザー（原点 p、向き d）が線分に当たるまでの距離。当たらなければ None。"""
    x1, y1, x2, y2 = seg
    ex, ey = x2 - x1, y2 - y1
    denom = dx * ey - dy * ex
    if abs(denom) < 1e-12:
        return None  # 平行
    t = ((x1 - px) * ey - (y1 - py) * ex) / denom
    u = ((x1 - px) * dy - (y1 - py) * dx) / denom
    if t >= 0.0 and 0.0 <= u <= 1.0:
        return t
    return None


def ray_circle(px, py, dx, dy, circle):
    """レーザーが円に当たるまでの距離。当たらなければ None。"""
    cx, cy, r = circle
    fx, fy = px - cx, py - cy
    b = fx * dx + fy * dy
    c = fx * fx + fy * fy - r * r
    disc = b * b - c
    if disc < 0.0:
        return None
    t = -b - math.sqrt(disc)
    return t if t >= 0.0 else None


def cast_ray(px, py, angle, range_max):
    """1 本のレーザーの距離。range_max を超えたら inf。"""
    dx, dy = math.cos(angle), math.sin(angle)
    best = math.inf
    for seg in SEGMENTS:
        t = ray_segment(px, py, dx, dy, seg)
        if t is not None and t < best:
            best = t
    for circle in CIRCLES:
        t = ray_circle(px, py, dx, dy, circle)
        if t is not None and t < best:
            best = t
    if best < RANGE_MIN or best > range_max:
        return math.inf
    return best


def hits_something(x, y):
    """ロボット（円）が、壁や障害物にめり込んでいるか。"""
    r = ROBOT_RADIUS
    if x < r or y < r or x > ROOM_SIZE - r or y > ROOM_SIZE - r:
        return True
    for cx, cy, cr in CIRCLES:
        if math.hypot(x - cx, y - cy) < cr + r:
            return True
    for x1, y1, x2, y2 in RECTS:
        nx = min(max(x, x1), x2)
        ny = min(max(y, y1), y2)
        if math.hypot(x - nx, y - ny) < r:
            return True
    return False


class RoomSim(Node):
    def __init__(self):
        super().__init__('room_sim')
        self.declare_parameter('noise', 0.0)           # ranges に足す乱数の幅（±noise）
        self.declare_parameter('range_max', 12.0)
        self.declare_parameter('cmd_timeout', 0.5)     # この秒数 /cmd_vel が来なければ止まる
        self.declare_parameter('output_dir', '/root/ros2_ws/output')

        self.x, self.y, self.theta = 10.0, 10.0, 0.0   # 部屋の真ん中、+x 向き
        self.linear = 0.0
        self.angular = 0.0
        self.last_cmd_time = None
        self.last_ranges = []
        self.turning = False

        self.scan_pub = self.create_publisher(LaserScan, '/scan', 10)
        self.create_subscription(Twist, '/cmd_vel', self.on_cmd, 10)

        self.dt = 0.1
        self.create_timer(self.dt, self.step)
        self.create_timer(1.0, self.write_output)
        self.get_logger().info('room_sim 起動。output_dir に毎秒 room.svg / index.html を書き出します')

    def on_cmd(self, msg):
        self.linear = msg.linear.x
        self.angular = msg.angular.z
        self.last_cmd_time = self.get_clock().now()

    def step(self):
        # 指示が途絶えたら止まる（暴走防止）
        timeout = self.get_parameter('cmd_timeout').value
        if self.last_cmd_time is not None:
            age = (self.get_clock().now() - self.last_cmd_time).nanoseconds / 1e9
            if age > timeout:
                self.linear = 0.0
                self.angular = 0.0

        # Twist を積分して、位置と向きを更新
        self.theta += self.angular * self.dt
        nx = self.x + self.linear * math.cos(self.theta) * self.dt
        ny = self.y + self.linear * math.sin(self.theta) * self.dt
        if not hits_something(nx, ny):
            self.x, self.y = nx, ny

        # 回り始めた・やめた瞬間だけ、位置をログに出す（図は 1 秒おきで、瞬間を見失うため）
        turning = abs(self.angular) > 1e-9
        if turning != self.turning:
            self.turning = turning
            what = '回り始めた' if turning else '回るのをやめた'
            self.get_logger().info(
                f'{what}: x={self.x:.2f} y={self.y:.2f} θ={math.degrees(self.theta) % 360:.0f}°')

        self.publish_scan()

    def publish_scan(self):
        range_max = self.get_parameter('range_max').value
        noise = self.get_parameter('noise').value
        increment = 2.0 * math.pi / NUM_RAYS

        ranges = []
        for i in range(NUM_RAYS):
            r = cast_ray(self.x, self.y, self.theta + i * increment, range_max)
            if math.isfinite(r) and noise > 0.0:
                r += random.uniform(-noise, noise)
            ranges.append(r)
        self.last_ranges = ranges

        msg = LaserScan()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'laser'
        msg.angle_min = 0.0
        msg.angle_max = 2.0 * math.pi - increment
        msg.angle_increment = increment
        msg.time_increment = 0.0
        msg.scan_time = self.dt
        msg.range_min = RANGE_MIN
        msg.range_max = float(range_max)
        msg.ranges = ranges
        if rclpy.ok():  # Ctrl+C の終了処理の途中なら、送らない
            self.scan_pub.publish(msg)

    def write_output(self):
        svg = self.make_svg()
        out_dir = self.get_parameter('output_dir').value
        os.makedirs(out_dir, exist_ok=True)
        html = (
            '<!DOCTYPE html><html><head><meta charset="utf-8">'
            '<meta http-equiv="refresh" content="1">'
            '<title>room_sim</title></head>'
            '<body style="margin:0;background:#222">' + svg + '</body></html>'
        )
        for name, text in (('room.svg', svg), ('index.html', html)):
            tmp = os.path.join(out_dir, name + '.tmp')
            with open(tmp, 'w', encoding='utf-8') as f:
                f.write(text)
            os.replace(tmp, os.path.join(out_dir, name))  # 書きかけをブラウザが読まないように

    def make_svg(self):
        size = ROOM_SIZE * SCALE

        def sx(x):
            return x * SCALE

        def sy(y):
            return size - y * SCALE  # SVG は下向きが +y なので反転

        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size:.0f}" height="{size:.0f}" '
            f'viewBox="0 0 {size:.0f} {size:.0f}">',
            f'<rect width="{size:.0f}" height="{size:.0f}" fill="#fafafa" '
            f'stroke="#333" stroke-width="4"/>',
        ]
        for x1, y1, x2, y2 in RECTS:
            parts.append(
                f'<rect x="{sx(x1):.1f}" y="{sy(y2):.1f}" width="{(x2 - x1) * SCALE:.1f}" '
                f'height="{(y2 - y1) * SCALE:.1f}" fill="#8d6e63"/>')
        for cx, cy, r in CIRCLES:
            parts.append(
                f'<circle cx="{sx(cx):.1f}" cy="{sy(cy):.1f}" '
                f'r="{r * SCALE:.1f}" fill="#8d6e63"/>')

        # レーザー（5 本に 1 本だけ描く）。当たらなかった(inf)ものは range_max まで薄く描く
        range_max = self.get_parameter('range_max').value
        for i in range(0, len(self.last_ranges), 5):
            r = self.last_ranges[i]
            hit = math.isfinite(r)
            length = r if hit else range_max
            a = self.theta + i * 2.0 * math.pi / NUM_RAYS
            ex = self.x + length * math.cos(a)
            ey = self.y + length * math.sin(a)
            color = '#e53935' if hit else '#bdbdbd'
            parts.append(
                f'<line x1="{sx(self.x):.1f}" y1="{sy(self.y):.1f}" '
                f'x2="{sx(ex):.1f}" y2="{sy(ey):.1f}" stroke="{color}" stroke-width="0.7"/>')

        # ロボット（円と、向きを示す線）
        hx = self.x + ROBOT_RADIUS * 1.6 * math.cos(self.theta)
        hy = self.y + ROBOT_RADIUS * 1.6 * math.sin(self.theta)
        parts.append(
            f'<circle cx="{sx(self.x):.1f}" cy="{sy(self.y):.1f}" '
            f'r="{ROBOT_RADIUS * SCALE:.1f}" fill="#1e88e5"/>')
        parts.append(
            f'<line x1="{sx(self.x):.1f}" y1="{sy(self.y):.1f}" '
            f'x2="{sx(hx):.1f}" y2="{sy(hy):.1f}" stroke="#0d47a1" stroke-width="3"/>')
        parts.append(
            f'<text x="8" y="18" font-size="13" fill="#333">'
            f'x={self.x:.2f} y={self.y:.2f} θ={math.degrees(self.theta) % 360:.0f}°</text>')
        parts.append('</svg>')
        return '\n'.join(parts)


def main(args=None):
    rclpy.init(args=args)
    node = RoomSim()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except Exception:
        if rclpy.ok():  # Ctrl+C の終了処理の途中で出る RCLError だけを、無視する
            raise
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
