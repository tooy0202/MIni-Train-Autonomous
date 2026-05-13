import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import Float32, String
import sensor_msgs_py.point_cloud2 as pc2

class LidarAvoidance(Node):

    def __init__(self):
        super().__init__('lidar_avoidance')

        self.sub = self.create_subscription(
            PointCloud2,
            '/livox/lidar',
            self.lidar_callback,
            10
        )

        self.speed_limit_pub = self.create_publisher(
            Float32,
            '/speed_limit',
            10
        )

        self.obstacle_status_pub = self.create_publisher(
            String,
            '/obstacle_status',
            10
        )

        self.obstacle_distance_pub = self.create_publisher(
            Float32,
            '/obstacle_distance',
            10
        )

        self.state = 'UNKNOWN'

        self.get_logger().info('Lidar Avoidance Node started')

    def lidar_callback(self, msg):
        min_dist = 999.0
        debug_x = 0.0
        debug_y = 0.0
        debug_z = 0.0

        for point in pc2.read_points(msg, skip_nans=True):
            x, y, z = point[0], point[1], point[2]

            if (
                5.0 > x > 0.0 and
                abs(y) < 0.5 and
                0.1 < z < 1.5
            ):
                dist = (x ** 2 + y ** 2) ** 0.5

                if dist < min_dist:
                    min_dist = dist
                    debug_x = x
                    debug_y = y
                    debug_z = z

        status = 'NORMAL'
        speed_limit = 1.0

        # if min_dist <= 0.0 or min_dist == 999.0:
        #     status = 'NORMAL'
        #     speed_limit = 0.0

        if min_dist > 2.0:
            status = 'NORMAL'
            speed_limit = 1.0

        elif min_dist > 1.5:
            status = 'SLOW'
            speed_limit = 0.5

        elif min_dist > 0.7:
            status = 'SLOW'
            speed_limit = 0.25

        else:
            status = 'STOP'
            speed_limit = 0.0

        self.speed_limit_pub.publish(Float32(data=float(speed_limit)))
        self.obstacle_status_pub.publish(String(data=status))
        self.obstacle_distance_pub.publish(Float32(data=float(min_dist)))

        if status != self.state:
            self.get_logger().info(
                f'Obstacle status: {status}, distance: {min_dist:.2f} m, '
                f'speed_limit: {speed_limit:.2f}, '
                f'x={debug_x:.2f}, y={debug_y:.2f}, z={debug_z:.2f}'
            )
            self.state = status

def main(args=None):
    rclpy.init(args=args)
    node = LidarAvoidance()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()