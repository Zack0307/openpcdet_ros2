#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist
from rclpy.clock import Clock
from std_msgs.msg import String, Float32, Int32, Bool
from sensor_msgs.msg import Imu,MagneticField, JointState
from openpcdet_ros2.Rosmaster_Lib import Rosmaster
import signal
import sys

class PS4Turtle(Node):
    def __init__(self):
        super().__init__('ps4_turtle_ctrl')
        
        self.car = Rosmaster()
        # 啟動背景線程讀取串口數據
        self.car.create_receive_threading()
        self.pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.sub = self.create_subscription(Joy, '/joy', self.joy_callback, 10)
        self.servo_pub  =  self.create_publisher(Float32, '/Servo_angle', 10)
        self.esc_pub = self.create_publisher(Float32, '/ESC_speed', 10)
        self.EdiPublisher = self.create_publisher(Float32,"edition",100)
        self.volPublisher = self.create_publisher(Float32,"/voltage",100)
        self.staPublisher = self.create_publisher(JointState,"joint_states",100)
        self.velPublisher = self.create_publisher(Twist,"vel_raw",50)
        self.imuPublisher = self.create_publisher(Imu,"/imu/data_raw",100)
        self.magPublisher = self.create_publisher(MagneticField,"/imu/mag",100)
        self.timer = self.create_timer(0.005, self.pub_data)
        self.vol_timer = self.create_timer(1.0, self.battery_voltage)

        self.imu_link = "imu_link"
        self.Prefix = " "
        
    def pub_data(self):
        time_stamp = Clock().now()

        imu = Imu()

        twist = Twist()

        battery = Float32()
        
        edition = Float32()
        mag = MagneticField()
        state = JointState()
        state.header.stamp = time_stamp.to_msg()
        state.header.frame_id = "joint_states"
        if len(self.Prefix)==0:
            state.name = ["back_right_joint", "back_left_joint","front_left_steer_joint","front_left_wheel_joint",
                            "front_right_steer_joint", "front_right_wheel_joint"]
        else:
            state.name = [self.Prefix+"back_right_joint",self.Prefix+ "back_left_joint",self.Prefix+"front_left_steer_joint",self.Prefix+"front_left_wheel_joint",
                            self.Prefix+"front_right_steer_joint", self.Prefix+"front_right_wheel_joint"]
        
        #print ("mag: ",self.car.get_magnetometer_data())       
        edition.data = self.car.get_version()*1.0
        # battery.data = self.car.get_battery_voltage()*1.0
        ax, ay, az = self.car.get_accelerometer_data()
        gx, gy, gz = self.car.get_gyroscope_data()
        mx, my, mz = self.car.get_magnetometer_data()
        mx = mx * 1.0
        my = my * 1.0
        mz = mz * 1.0
        vx, vy, angular = self.car.get_motion_data()
        '''print("vx: ",vx)
        print("vy: ",vy)
        print("angular: ",angular)'''
        # 发布陀螺仪的数据
        # Publish gyroscope data
        imu.header.stamp = time_stamp.to_msg()
        imu.header.frame_id = self.imu_link
        imu.linear_acceleration.x = ax*1.0
        imu.linear_acceleration.y = ay*1.0
        imu.linear_acceleration.z = az*1.0
        imu.angular_velocity.x = gx*1.0
        imu.angular_velocity.y = gy*1.0
        imu.angular_velocity.z = gz*1.0

        mag.header.stamp = time_stamp.to_msg()
        mag.header.frame_id = self.imu_link
        mag.magnetic_field.x = mx*1.0
        mag.magnetic_field.y = my*1.0
        mag.magnetic_field.z = mz*1.0

        yaw,roll,pitch = self.car.get_imu_attitude_data()
        
        # 将小车当前的线速度和角速度发布出去
        # Publish the current linear vel and angular vel of the car
        # twist.linear.x = vx *1.0
        # twist.linear.y = vy *1.0
        #axes[1]: 左搖桿上下 → 前後
        #axes[2]: 右搖桿左右 → 轉向
        # twist.linear.x = joy.axes[0] *1.0
        # # twist.linear.y = joy.axes[1] *1.0
        # twist.angular.z = joy.axes[1]*1.0    
        # self.velPublisher.publish(twist)
        # self.get_logger().info(f'cmd_vel ← lin: {twist.linear.x:.2f}, ang: {twist.angular.z:.2f}')
        
        self.imuPublisher.publish(imu)
        self.magPublisher.publish(mag)
        # self.get_logger().info(f'accelerometer_data:{ax:.2f},{ay:.2f},{az:.2f}')
        # self.get_logger().info(f'Yaw Roll Pitch:{yaw:.2f},{roll:.2f},{pitch:.2f}')
        # self.volPublisher.publish(battery)
        # print(battery)

    def battery_voltage(self):
        battery = Float32()
        battery.data = self.car.get_battery_voltage()*1.0
        self.volPublisher.publish(battery)
        # self.get_logger().info(f'voltage:{battery.data:.2f} V')
        self.timer = self.create_timer(600.0, self.battery_voltage)


    def cmd_vel_callback(self,msg):
        # 小车运动控制，订阅者回调函数
        # Car motion control, subscriber callback function
        if not isinstance(msg, Twist): return
        # 下发线速度和角速度
        # Issue linear vel and angular vel
        vx = msg.linear.x*1.0
        #vy = msg.linear.y/1000.0*180.0/3.1416    #Radian system
        vy = msg.linear.y*1.0
        angular = msg.angular.z*1.0     # wait for chang
        self.car.set_car_motion(vx, vy, angular)
    
    def Buzzercallback(self,msg):
        if not isinstance(msg, Bool): return
        if msg.data:
            for i in range(3): self.car.set_beep(1)
        else:
            for i in range(3): self.car.set_beep(0)


    def joy_callback(self, joy: Joy):
        twist = Twist()
        #axes[1]: 左搖桿上下 → 前後
        #axes[2]: 右搖桿左右 → 轉向
        twist.linear.x  = joy.axes[1] * 1.0
        twist.angular.z = joy.axes[2] * 1.0
        
        speed = self.ps4_map_to_esc(joy.axes[1])
        angle = self.ps4_map_to_servo(joy.axes[2])
        #封裝成ros訊息
        esc_msg = Float32() 
        esc_msg.data = speed
        servo_msg = Float32()
        servo_msg.data = angle
        
        self.servo_pub.publish(servo_msg)
        self.esc_pub.publish(esc_msg)
        self.pub.publish(twist)
        
        self.car.set_pwm_servo(4,  angle)
        self.car.set_pwm_servo(3,  speed)
        # self.get_logger().info(f'cmd_vel ← lin: {twist.linear.x:.2f}, ang: {twist.angular.z:.2f}')
        # self.get_logger().info(f'speed:{speed}')
    
    def ps4_map_to_servo(self,  joy_value):
        angle = 90 + joy_value * 90
        return angle
    
    def ps4_map_to_esc(self, joy_data):
        if abs(joy_data) < 0.1:
            speed = 90.0
        else:
            speed  =  20 *(- joy_data)  +  90
        return speed 

def main(args=None):
    rclpy.init(args=args)
    node = PS4Turtle()
    # node.battery_voltage()

    # 定義安全關閉
    def shutdown_handler(sig, frame):
        node.get_logger().info("Shutting down ps4_turtle...")
        try:
            # 停止馬達
            node.car.set_car_motion(0.0, 0.0, 0.0)
            node.car.set_pwm_servo(3, 90)  # 停止 ESC
            node.car.set_pwm_servo(4, 90)  # 歸中舵機

            #publish other data
            # node.pub_data()
        except Exception as e:
            node.get_logger().warn(f"Error while stopping car: {e}")
        finally:
            node.destroy_node()
            rclpy.shutdown()
            sys.exit(0)

    # 註冊 SIGINT (Ctrl+C) 和 SIGTERM (ros2 launch 停止時會送)
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        shutdown_handler(signal.SIGINT, None)
