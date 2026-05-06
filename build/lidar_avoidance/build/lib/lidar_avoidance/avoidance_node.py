import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from geometry_msgs.msg import Twist
import sensor_msgs_py.point_cloud2 as pc2
import time

class LidarAvoidance(Node):

    def __init__(self):
        super().__init__('lidar_avoidance')

        self.sub = self.create_subscription(
            PointCloud2,
            '/livox/lidar',
            self.lidar_callback,
            10)

        self.pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.get_logger().info("Starting Lidar Avoidance Node")

        self.blocked_start_time = None
        self.turning = False
        self.state = "MOVE"

    def lidar_callback(self, msg):
        self.get_logger().info("Receiving Lidar Data")
        min_dist = 999
        new_state = "MOVE"

        for point in pc2.read_points(msg, skip_nans=True):
            x, y, z = point[0], point[1], point[2]
            y = y * 0.5

            if 5 > x > 0 and abs(y) < 1.0:
                dist = (x**2 + y**2)**0.5
                if dist < min_dist:
                    min_dist = dist

        cmd = Twist()

        if self.turning:
            cmd.linear.x = 1.0
            cmd.angular.z = 2.0

            if time.time() - self.turn_start_time > 2:
                self.turning = False
        else:
                if min_dist < 0.5:  

                    if min_dist < 0.3:
                        cmd.linear.x = 0.0

                        if self.blocked_start_time is None:
                            self.blocked_start_time = time.time()

                        elif time.time() - self.blocked_start_time > 3:
                            new_state = "STOP"
                            self.turning = True
                            self.turn_start_time = time.time()

                    else:
                        cmd.linear.x = 0.4  
                        new_state = "SLOW"
                        self.blocked_start_time = None

                else:
                    new_state = "MOVE"
                    cmd.linear.x = 1.0  
                    self.blocked_start_time = None

        if new_state != self.state:
            self.get_logger().info(f"STATE: {new_state}")
            self.state = new_state

        self.pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = LidarAvoidance()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()