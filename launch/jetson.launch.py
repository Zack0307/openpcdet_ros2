from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import  LaunchConfiguration

from launch_ros.actions import Node

import xacro
import os
from ament_index_python.packages import get_package_share_directory

from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare



print("---------------------Jetson TX2-NX Start---------------------")

def generate_launch_description():
    
    # 找到 urdf/xacro 路徑
    urdf_path = os.path.join(get_package_share_directory('openpcdet_ros2'),'urdf','my_robot.urdf.xacro')
    
    #rviz
    rviz_config_path = os.path.join(get_package_share_directory('openpcdet_ros2'),'rviz','autoware.rviz')
    
    #rplidar launch file path
    rplidar_ros_path = os.path.join(get_package_share_directory('rplidar_ros'),'launch','rplidar_c1_launch.py')

    #lidar frame
    frame_id = LaunchConfiguration('frame_id', default='laser')

    #仿真時間,真實機器人不需要時間
    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value = 'False')

    # 用 xacro 解析
    doc = xacro.process_file(urdf_path)
    robot_description_config = doc.toprettyxml(indent='  ')

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        node_executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_config}]
    )

    DeclareLaunchArgument(
            'frame_id',
            default_value=frame_id,
            description='Specifying frame_id of lidar'),

    #declare gui_arg
    gui_arg = DeclareLaunchArgument(
        'gui',
        default_value='True',
        description='Flag to enable joint_state_publisher_gui'
    )

    # Depending on gui parameter, either launch joint_state_publisher or joint_state_publisher_gui
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        node_executable='joint_state_publisher',
        output='screen'
        # condition=UnlessCondition(LaunchConfiguration('gui'))
    )

    # joint_state_publisher_gui_node = Node(
    #     package='joint_state_publisher_gui',
    #     node_executable='joint_state_publisher_gui',
    #     condition=IfCondition(LaunchConfiguration('gui'))
    # )

    rviz_node = Node(
        package='rviz2',
        node_executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_path],
    )

    imu_filter_config = os.path.join(              
        get_package_share_directory('openpcdet_ros2'),
        'param',
        'imu_filter_param.yaml'
    ) 

    #rplidar launch
    rplidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(rplidar_ros_path)
    )

    driver_node = Node(
        package='openpcdet_ros2',
        node_executable='ps4_turtle',
        emulate_tty=True
    )

    imu_filter_node = Node(
        package='imu_filter_madgwick',
        node_executable='imu_filter_madgwick_node',
        parameters=[imu_filter_config]
    )

    ps4_joy_node = Node(
        package='joy',
        node_executable='joy_node',
    )

    robot_localization_node = Node(
        package='robot_localization',
        node_executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[os.path.join(get_package_share_directory('robot_localization'), 'params' , 'ekf.yaml'), {'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    ## ***** File paths ******
    # 找到cartographer功能包的地址
    pkg_share = FindPackageShare('cartographer_ros').find('cartographer_ros')
    ## ***** Nodes *****
    #=====================声明三个节点，cartographer/occupancy_grid_node/rviz_node=================================
    cartographer_node = Node(
        package = 'cartographer_ros',
        node_executable = 'cartographer_node',
        arguments = [
            '-configuration_directory', FindPackageShare('cartographer_ros').find('cartographer_ros') + '/configuration_files',
            '-configuration_basename', 'backpack_2d.lua'],
        remappings = [
            ('odom', '/odometry/filtered')
            ],
          
        output = 'screen'
        )
    cartographer_occupancy_grid_node = Node(
        package = 'cartographer_ros',
        node_executable = 'occupancy_grid_node',
        parameters = [
            {'use_sim_time': False},
            {'resolution': 0.05}],
    )


    return LaunchDescription([
        # gui_arg,
        # joint_state_publisher_node,
        # joint_state_publisher_gui_node,
        # robot_state_publisher_node,
        use_sim_time_arg,
        cartographer_node,
        cartographer_occupancy_grid_node,
        rplidar_launch,
        robot_localization_node,
        rviz_node,
        driver_node,
        # imu_filter_node,
        ps4_joy_node
    ])
