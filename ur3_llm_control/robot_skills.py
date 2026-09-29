import time
import math
import subprocess
import threading
import rclpy
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from builtin_interfaces.msg import Duration
from geometry_msgs.msg import PoseStamped, TransformStamped
from sensor_msgs.msg import JointState
from moveit_msgs.msg import RobotState
from moveit_msgs.srv import GetPositionIK
import tf2_ros
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster

class UR3Skills:
    def __init__(self, node):
        self.node = node
        self._action_client = ActionClient(self.node, FollowJointTrajectory, '/joint_trajectory_controller/follow_joint_trajectory')
        self.joint_names = ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']
        
        self.world_name = "empty" 

        # Tọa độ các Zone cố định (Z = 0.027m là chuẩn mặt thảm)
        self.zone_coords = {
            'zone_a': {'x': 0.35, 'y': 0.1, 'z': 0.027},
            'zone_b': {'x': 0.35, 'y': 0.0, 'z': 0.027},
            'zone_c': {'x': 0.35, 'y': -0.1, 'z': 0.027}
        }
        
        # Tọa độ ban đầu các khối (Sẽ tự động cập nhật sau mỗi lượt gắp thả)
        self.cube_coords = {
            'red_cube': {'x': 0.25, 'y': 0.0, 'z': 0.027},
            'yellow_cube': {'x': 0.25, 'y': 0.1, 'z': 0.027},
            'blue_cube': {'x': 0.25, 'y': -0.1, 'z': 0.027}
        }

        self.ik_client = self.node.create_client(GetPositionIK, '/compute_ik')

        # Khóa đồng bộ chống lỗi Race Condition khi thả vật
        self.attach_lock = threading.Lock()

        # Luồng Spin xử lý callback ROS 2
        self._spin_thread = threading.Thread(target=rclpy.spin, args=(self.node,), daemon=True)
        self._spin_thread.start()

        # Bộ lắng nghe TF
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self.node)
        
        # TẠO GRIPPER ẢO: Phát ra một hệ tọa độ TCP cố định
        self.tf_static_broadcaster = StaticTransformBroadcaster(self.node)
        self._spawn_virtual_gripper()
        
        self.attached_cube = None
        self._is_running = True
        
        # Luồng ngầm dính khối màu
        self._attach_thread = threading.Thread(target=self._keep_attached_cube, daemon=True)
        self._attach_thread.start()

    def _spawn_virtual_gripper(self):
        """Hàm sinh ra đầu gắp ảo (TCP) nhô ra 2.5cm từ cổ tay robot"""
        t = TransformStamped()
        t.header.stamp = self.node.get_clock().now().to_msg()
        t.header.frame_id = 'wrist_3_link'
        t.child_frame_id = 'virtual_gripper_tcp'
        
        t.transform.translation.x = 0.0
        t.transform.translation.y = 0.0
        t.transform.translation.z = 0.025 
        
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = 0.0
        t.transform.rotation.w = 1.0
        
        self.tf_static_broadcaster.sendTransform(t)
        self.node.get_logger().info("Đã tạo thành công Gripper Ảo (virtual_gripper_tcp)!")

    def _keep_attached_cube(self):
        """Khóa vị trí khối màu theo Gripper Ảo khi đang gắp di chuyển"""
        warned_tf = False
        while self._is_running:
            with self.attach_lock:
                current_cube = self.attached_cube

            if current_cube:
                try:
                    trans = self.tf_buffer.lookup_transform(
                        'base_link', 
                        'virtual_gripper_tcp', 
                        rclpy.time.Time(),
                        timeout=rclpy.duration.Duration(seconds=0.05)
                    )
                    x = trans.transform.translation.x
                    y = trans.transform.translation.y
                    z = trans.transform.translation.z 
                    
                    with self.attach_lock:
                        if self.attached_cube == current_cube:
                            cmd = f"ign service -s /world/{self.world_name}/set_pose --reqtype ignition.msgs.Pose --reptype ignition.msgs.Boolean --timeout 100 --req 'name: \"{current_cube}\", position: {{x: {x}, y: {y}, z: {z}}}, orientation: {{x: 0, y: 0, z: 0, w: 1}}'"
                            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    warned_tf = False
                except Exception as e:
                    if not warned_tf:
                        self.node.get_logger().warn(f"[LỖI TF] Chưa đọc được vị trí Gripper Ảo: {e}")
                        warned_tf = True
            time.sleep(0.02)

    def _get_moveit_ik(self, x, y, z):
        while not self.ik_client.wait_for_service(timeout_sec=1.0):
            self.node.get_logger().info('Đang chờ service /compute_ik của MoveIt 2...')
            
        req = GetPositionIK.Request()
        req.ik_request.group_name = "ur_manipulator"
        req.ik_request.avoid_collisions = False
        
        # Seed State ép tư thế Elbow-Up
        seed_state = JointState()
        seed_state.name = self.joint_names
        pan_guess = math.atan2(float(y), float(x))
        seed_state.position = [pan_guess, -1.2, 1.5, -1.8, -1.57, 0.0]
        
        robot_state = RobotState()
        robot_state.joint_state = seed_state
        req.ik_request.robot_state = robot_state

        pose = PoseStamped()
        pose.header.frame_id = "base_link"
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.position.z = float(z)
        
        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 1.0
        pose.pose.orientation.z = 0.0
        pose.pose.orientation.w = 0.0
        
        req.ik_request.pose_stamped = pose
        
        future = self.ik_client.call_async(req)
        
        start_time = time.time()
        while not future.done():
            time.sleep(0.01)
            if time.time() - start_time > 5.0:
                self.node.get_logger().error("Hết thời gian chờ MoveIt IK!")
                return None

        response = future.result()
        
        if response and response.error_code.val == 1:
            joint_state = response.solution.joint_state
            target_joints = []
            for name in self.joint_names:
                idx = joint_state.name.index(name)
                target_joints.append(joint_state.position[idx])
            return target_joints
        else:
            val = response.error_code.val if response else "None"
            self.node.get_logger().error(f"MoveIt không tìm thấy nghiệm IK! Mã lỗi: {val}")
            return None

    def _send_goal(self, target, duration=2.0):
        if not self._action_client.wait_for_server(timeout_sec=2.0):
            return
        msg = FollowJointTrajectory.Goal()
        msg.trajectory.joint_names = self.joint_names
        point = JointTrajectoryPoint()
        point.positions = target
        point.time_from_start = Duration(sec=int(duration), nanosec=int((duration % 1) * 1e9))
        msg.trajectory.points.append(point)
        self._action_client.send_goal_async(msg)
        time.sleep(duration + 0.3)

    def _teleport_cube(self, cube_name, coords):
        """Đặt khối màu phẳng tại vị trí chỉ định"""
        x, y, z = coords['x'], coords['y'], coords['z']
        cmd = f"ign service -s /world/{self.world_name}/set_pose --reqtype ignition.msgs.Pose --reptype ignition.msgs.Boolean --timeout 1000 --req 'name: \"{cube_name}\", position: {{x: {x}, y: {y}, z: {z}}}, orientation: {{x: 0, y: 0, z: 0, w: 1}}'"
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.2)

    def home(self):
        joints_home = self._get_moveit_ik(0.2, 0.0, 0.3)
        if joints_home:
            self._send_goal(joints_home, 2.0)

    def pick(self, obj):
        coords = self.cube_coords[obj]
        self.node.get_logger().info(f"[MoveIt 2] Đang di chuyển tới gắp {obj} tại ({coords['x']}, {coords['y']})...")
        
        # 1. Tiếp cận trên không
        joints_above = self._get_moveit_ik(coords['x'], coords['y'], 0.15)
        if joints_above: self._send_goal(joints_above, 2.0)
        
        # 2. Hạ tay xuống gắp
        joints_pick = self._get_moveit_ik(coords['x'], coords['y'], 0.045)
        if joints_pick: self._send_goal(joints_pick, 1.2)
        
        # 3. Kích hoạt dính vật bằng Threading Lock
        time.sleep(0.2)
        self.node.get_logger().info(f"--> ĐÃ GẮP {obj}!")
        with self.attach_lock:
            self.attached_cube = obj
        time.sleep(0.2)
        
        # 4. Nhấc thẳng đứng lên
        if joints_above: self._send_goal(joints_above, 1.2)

    def place(self, obj, zone):
        coords = self.zone_coords[zone]
        self.node.get_logger().info(f"[MoveIt 2] Đang mang {obj} tới {zone}...")
        
        # 1. Tiếp cận trên không ô Zone
        joints_above = self._get_moveit_ik(coords['x'], coords['y'], 0.15)
        if joints_above: self._send_goal(joints_above, 2.0)
        
        # 2. Hạ sát Zone
        joints_place = self._get_moveit_ik(coords['x'], coords['y'], 0.045)
        if joints_place: self._send_goal(joints_place, 1.2)
        
        # 3. Dừng robot 0.3s
        time.sleep(0.3)
        
        # 4. Thả vật an toàn
        self.node.get_logger().info(f"--> ĐÃ THẢ {obj} XUỐNG {zone}!")
        with self.attach_lock:
            self.attached_cube = None
        
        time.sleep(0.15)
        
        # 5. Khóa cố định vị trí khối màu
        self._teleport_cube(obj, coords)
        
        # 6. Cập nhật tọa độ mới vào bộ nhớ
        self.cube_coords[obj] = self.zone_coords[zone].copy()
        self.node.get_logger().info(f"[CẬP NHẬT DỮ LIỆU] Vị trí mới của {obj}: {self.cube_coords[obj]}")

        # 7. Rút tay lên và quay về vị trí Home
        if joints_above: self._send_goal(joints_above, 1.2)
        self.home()