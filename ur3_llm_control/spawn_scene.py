import os
import subprocess
import time

# 1. Dọn dẹp không gian cũ
models = ["floor_workspace", "red_cube", "yellow_cube", "blue_cube"]
print("--> Đang dọn dẹp các model cũ...")
for m in models:
    cmd = f"ign service -s /world/empty/remove --reqtype ignition.msgs.Entity --reptype ignition.msgs.Boolean --timeout 500 --req 'name: \"{m}\", type: MODEL'"
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(0.5)

# 2. Tạo Thảm & Zone (Trạng thái tĩnh - Static)
floor_sdf = """<?xml version="1.0" ?>
<sdf version="1.6">
  <model name="floor_workspace">
    <static>true</static>
    <link name="carpet">
      <pose>0.25 0 0.001 0 0 0</pose>
      <visual name="visual">
        <geometry><box><size>0.6 0.6 0.002</size></box></geometry>
        <material><ambient>0.2 0.2 0.2 1</ambient><diffuse>0.2 0.2 0.2 1</diffuse></material>
      </visual>
      <collision name="collision">
        <geometry><box><size>0.6 0.6 0.002</size></box></geometry>
      </collision>
    </link>
    <link name="zone_a">
      <pose>0.35 0.1 0.003 0 0 0</pose>
      <visual name="visual">
        <geometry><box><size>0.08 0.08 0.002</size></box></geometry>
        <material><ambient>0.0 1.0 0.0 1</ambient><diffuse>0.0 1.0 0.0 1</diffuse></material>
      </visual>
    </link>
    <link name="zone_b">
      <pose>0.35 0.0 0.003 0 0 0</pose>
      <visual name="visual">
        <geometry><box><size>0.08 0.08 0.002</size></box></geometry>
        <material><ambient>0.0 1.0 0.0 1</ambient><diffuse>0.0 1.0 0.0 1</diffuse></material>
      </visual>
    </link>
    <link name="zone_c">
      <pose>0.35 -0.1 0.003 0 0 0</pose>
      <visual name="visual">
        <geometry><box><size>0.08 0.08 0.002</size></box></geometry>
        <material><ambient>0.0 1.0 0.0 1</ambient><diffuse>0.0 1.0 0.0 1</diffuse></material>
      </visual>
    </link>
  </model>
</sdf>"""

with open("/tmp/floor_workspace.sdf", "w") as f:
    f.write(floor_sdf)

subprocess.run("ros2 run ros_gz_sim create -world empty -name floor_workspace -file /tmp/floor_workspace.sdf", shell=True)
time.sleep(0.5)

# 3. Tạo 3 Khối màu (static=false, kinematic=true, gravity=false chuẩn mô phỏng)
def make_cube(name, x, y, r, g, b):
    sdf = f"""<?xml version="1.0" ?>
<sdf version="1.6">
  <model name="{name}">
    <static>false</static>
    <link name="link">
      <kinematic>true</kinematic>
      <gravity>true</gravity>
      <visual name="visual">
        <geometry><box><size>0.04 0.04 0.04</size></box></geometry>
        <material>
          <ambient>{r} {g} {b} 1</ambient>
          <diffuse>{r} {g} {b} 1</diffuse>
        </material>
      </visual>
      <collision name="collision">
        <geometry><box><size>0.04 0.04 0.04</size></box></geometry>
      </collision>
    </link>
  </model>
</sdf>"""
    with open(f"/tmp/{name}.sdf", "w") as f:
        f.write(sdf)
    
    cmd = f"ros2 run ros_gz_sim create -world empty -name {name} -file /tmp/{name}.sdf -x {x} -y {y} -z 0.027"
    subprocess.run(cmd, shell=True)
    time.sleep(0.3)

# Spawn 3 khối đứng hàng ngang
make_cube("red_cube", 0.25, 0.0, 1.0, 0.0, 0.0)
make_cube("yellow_cube", 0.25, 0.1, 1.0, 1.0, 0.0)
make_cube("blue_cube", 0.25, -0.1, 0.0, 0.4, 1.0)

print("--> THÀNH CÔNG! Đã khởi tạo hoàn chỉnh không gian.")