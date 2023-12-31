import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import LoadComposableNodes
from launch_ros.actions import Node
from launch_ros.descriptions import ComposableNode
from nav2_common.launch import RewrittenYaml

# launch文件中出现的argument和parameter，虽都译为“参数”，但含义不同：
# - argument：仅限launch文件内部使用，方便在launch中调用某些数值； 
# - parameter：ROS系统的参数，方便在节点见使用某些数值。

def generate_launch_description():
    # Get the launch directory
    bringup_dir = get_package_share_directory('robot_navigation2')

    namespace = LaunchConfiguration('namespace')
    map_yaml_file = LaunchConfiguration('map') #创建了一个 launch 参数，这个参数名为 'map'，map的值将会被传递给map_yaml_file参数（ros2 launch your_launch_file.py map:=/path/to/your/map.yaml）
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')
    container_name = LaunchConfiguration('container_name')
    use_respawn = LaunchConfiguration('use_respawn')
    log_level = LaunchConfiguration('log_level')

    lifecycle_nodes = ['map_server', 'amcl'] #lifecycle_nodes 变量是一个包含要进行生命周期管理的节点名称列表。

    remappings = [('/tf', 'tf'),
                  ('/tf_static', 'tf_static')]

    # Create our own temporary YAML files that include substitutions
    #param_substitutions 是一个字典，用于定义节点参数中的一些值。这些值可以是来自其他变量或者其他来源的参数替换。
    #当节点启动时，它会使用 param_substitutions 中定义的值来替换对应参数的默认值
    param_substitutions = { 
        'use_sim_time': use_sim_time,
        'yaml_filename': map_yaml_file}

    configured_params = RewrittenYaml( #用于从一个 YAML 配置文件中读取参数，并且根据给定的参数重写或修改其中的值
        source_file=params_file, #表示源 YAML 文件的路径
        root_key=namespace, #指定在 YAML 文件中要进行参数重写的根键值或命名空间。它用于定位在 YAML 文件中需要修改的特定部分。
        param_rewrites=param_substitutions, #包含了需要进行替换的参数和它们的值
        convert_types=True) #是否尝试根据参数值的类型进行转换

    stdout_linebuf_envvar = SetEnvironmentVariable(
        'RCUTILS_LOGGING_BUFFERED_STREAM', '1')

    declare_namespace_cmd = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Top-level namespace')

    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map',
        description='Full path to map yaml file to load')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true')

    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(bringup_dir, 'params', 'nav2_params.yaml'),#'params'?
        description='Full path to the ROS2 parameters file to use for all launched nodes')

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart', default_value='true',
        description='Automatically startup the nav2 stack')

    declare_container_name_cmd = DeclareLaunchArgument(
        'container_name', default_value='nav2_container',
        description='the name of conatiner that nodes will load in if use composition')

    declare_use_respawn_cmd = DeclareLaunchArgument(
        'use_respawn', default_value='False',
        description='Whether to respawn if a node crashes. Applied when composition is disabled.')

    declare_log_level_cmd = DeclareLaunchArgument(
        'log_level', default_value='info',
        description='log level')

    load_nodes = GroupAction(
        actions=[
            Node(
                package='nav2_map_server',
                executable='map_server',
                name='map_server',
                output='screen',
                respawn=use_respawn,
                respawn_delay=2.0,
                parameters=[configured_params],
                arguments=['--ros-args', '--log-level', log_level], #--ros-args：告诉节点解析后续参数作为 ROS 2 特定的参数。
                remappings=remappings),
            Node(
                package='nav2_amcl',
                executable='amcl',
                name='amcl',
                output='screen',
                respawn=use_respawn,
                respawn_delay=2.0,
                parameters=[configured_params],
                arguments=['--ros-args', '--log-level', log_level],
                remappings=remappings),
            Node(
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_localization',
                output='screen',
                arguments=['--ros-args', '--log-level', log_level],
                parameters=[{'use_sim_time': use_sim_time},
                            {'autostart': autostart},
                            {'node_names': lifecycle_nodes}])
        ]
    )

    # Create the launch description and populate
    # 创建了一个名为 ld 的启动描述对象，启动描述是一个用于描述如何启动 ROS 2 节点和系统的对象，它包含了所有要执行的动作，如启动节点、设置参数、设置环境变量等。
    # 可以逐步添加各种动作（Actions）到这个描述中，然后将其用于启动你的 ROS 2 节点系统。
    ld = LaunchDescription()

    # Set environment variables
    ld.add_action(stdout_linebuf_envvar)

    # Declare the launch options
    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_map_yaml_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_params_file_cmd)
    ld.add_action(declare_autostart_cmd)
    ld.add_action(declare_container_name_cmd)
    ld.add_action(declare_use_respawn_cmd)
    ld.add_action(declare_log_level_cmd)

    # Add the actions to launch all of the localiztion nodes
    ld.add_action(load_nodes)

    return ld
