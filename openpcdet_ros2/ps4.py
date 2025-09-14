#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist

class PS42Turtle(Node):
    def __init__(self):
        super().__init__('ps4_turtle_ctrl')
        self.pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.sub = self.create_subscription(Joy, '/joy', self.callback, 10)

    def callback(self, joy: Joy):
        twist = Twist()
        # axes[1]: 左搖桿上下 → 前後； axes[0]: 左搖桿左右 → 轉向
        twist.linear.x  = joy.axes[1] * 1.0
        twist.angular.z = joy.axes[0] * 1.0
        self.pub.publish(twist)
        self.get_logger().info(f'cmd_vel ← lin: {twist.linear.x:.2f}, ang: {twist.angular.z:.2f}')

def main(args=None):
    rclpy.init(args=args)
    node = PS42Turtle()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
