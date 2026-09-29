import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Lấy đường dẫn thư mục share của package
    pkg_share = get_package_share_directory('ur3_llm_control')
    
    # Đường dẫn mặc định đến các file yaml trong thư mục config
    default_scene_config = os.path.join(pkg_share, 'config', 'scene.yaml')
    default_student_config = os.path.join(pkg_share, 'config', 'student_config.yaml')

    # Khai báo argument để có thể thay đổi đường dẫn config qua dòng lệnh khi cần
    scene_config_arg = DeclareLaunchArgument(
        'scene_config',
        default_value=default_scene_config,
        description='Path to scene configuration file'
    )

    student_config_arg = DeclareLaunchArgument(
        'student_config',
        default_value=default_student_config,
        description='Path to student configuration file'
    )

    # Node chính điều khiển LLM
    ur3_llm_node = Node(
        package='ur3_llm_control',
        executable='ur3_llm_control_node',
        name='ur3_llm_control_node',
        output='screen',
        parameters=[
            LaunchConfiguration('scene_config'),
            LaunchConfiguration('student_config')
        ]
    )

    return LaunchDescription([
        scene_config_arg,
        student_config_arg,
        ur3_llm_node
    ])