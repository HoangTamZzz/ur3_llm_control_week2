# UR3 LLM CONTROL (Gắp vật bằng robot UR3e)

Gói ROS 2 này sử dụng MoveIt 2, LLM để lập kế hoạch quỹ đạo và điều khiển cánh tay robot UR3e gắp vật và bỏ vào zone trong không gian 3D bằng ngôn ngữ tự nhiên. Hệ thống được mô phỏng trong môi trường Gazebo.

---

# Cấu trúc thư mục

``` text
ur3_llm_control/
├── package.xml
├── setup.py
├── launch/
│   └── llm_robot.launch.py
├── config/
│   ├── scene.yaml
│   └── student_config.yaml
├── resource/
│   └── ur3_llm_control
└── ur3_llm_control/
    ├── main_node.py
    ├── llm_planner.py
    ├── skill_executor.py
    ├── robot_skills.py
    ├── task_validator.py
    └── spawn_scene.py
```
## Chức năng các file

  File                    Chức năng
  ----------------------- -----------------------------------------------------
  `main_node.py`          Node ROS 2 chính, tiếp nhận lệnh và gọi robot skill
  `llm_planner.py`        Giao tiếp với LLM và tạo task plan dạng JSON
  `task_validator.py`     Kiểm tra skill, object và zone hợp lệ
  `skill_executor.py`     Thực thi tuần tự các skill trong task plan
  `robot_skills.py`       Cài đặt các thao tác `pick`, `place`, `home`
  `spawn_scene.py`        Tạo môi trường và các khối màu trong Gazebo
  `scene.yaml`            Cấu hình vị trí/kích thước vật thể và vùng thao tác
  `student_config.yaml`   Cấu hình sinh viên, mapping và LLM
  `llm_robot.launch.py`   Launch node điều khiển

------------------------------------------------------------------------

# Cài đặt package

1. Yêu cầu hệ thống
- Hệ điều hành: Ubuntu 22.04 (Native hoặc WSL2 trên Windows)
- ROS 2: Humble
- Packages UR: Đã cài đặt sẵn ur_simulation_gz, ur_moveit_config, v.v.

2. Biên dịch gói
Đặt package vào workspace ROS 2:
``` bash
cd ~/ros2_ws/src
```

Sau đó build:
``` bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash

colcon build --symlink-install --packages-select ur3_llm_control
```

3. Khởi chạy mô phỏng
Terminal 1: Mở trình mô phỏng Gazebo và Rviz
``` bash
cd ~/ros2_ws/src
source install/setup.bash
ros2 launch ur_simulation_gz ur_sim_moveit.launch.py ur_type:=ur3e launch_rviz:=true
```
Termminal 2: Spawn khối và chạy node chính điều khiển
``` bash
cd ~/ros2_ws/src
source install/setup.bash
python3 ~/ros2_ws/src/ur3_llm_control/ur3_llm_control/spawn_scene.py
PYTHONUNBUFFERED=1 ros2 run ur3_llm_control main_node
```

Tiếp theo chỉ cần nhập lệnh tại terminal để điều khiển robot:
``` text
[Bạn]: gắp khối đỏ và đặt vào khu b
```

*Lưu ý: Khắc phục lỗi hiển thị đồ họa trên WSL2
- Nếu bạn chạy trên WSL2 và gặp lỗi RViz2 bị màn hình đen, văng (crash) hoặc thu nhỏ thành ô vuông trắng, nguyên nhân là do xung đột card đồ họa ảo.
- Hãy chạy các lệnh sau trong Terminal trước khi lệnh node chính:
export GALLIUM_DRIVER=llvmpipe
export MESA_GL_VERSION_OVERRIDE=3.3
export QT_QPA_PLATFORM=xcb
export LIBGL_ALWAYS_SOFTWARE=1