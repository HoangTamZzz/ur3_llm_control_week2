import rclpy
from rclpy.node import Node
from .robot_skills import UR3Skills

class LLMRobotControl(Node):
    def __init__(self):
        super().__init__('llm_robot_control')
        self.skills = UR3Skills(self)
        self.get_logger().info("Hệ thống LLM Robot đã sẵn sàng! Chờ lệnh từ người dùng...")

    def parse_natural_language(self, command):
        """Mô phỏng bộ não LLM để hiểu câu lệnh tiếng Việt"""
        command = command.lower()
        
        # Nhận diện Khối màu
        obj = None
        if "đỏ" in command or "red" in command: obj = "red_cube"
        elif "vàng" in command or "yellow" in command: obj = "yellow_cube"
        elif "xanh" in command or "blue" in command: obj = "blue_cube"

        # Nhận diện Zone
        zone = None
        if "zone a" in command or "khu a" in command: zone = "zone_a"
        elif "zone b" in command or "khu b" in command: zone = "zone_b"
        elif "zone c" in command or "khu c" in command: zone = "zone_c"

        return obj, zone

    def run_chat_loop(self):
        self.skills.home()
        while rclpy.ok():
            cmd = input("\n[Bạn]: ")
            if cmd.lower() in ['exit', 'quit', 'thoát']:
                break
            
            obj, zone = self.parse_natural_language(cmd)
            
            if obj and zone:
                print(f"[LLM]: Đã hiểu! Đang tiến hành gắp '{obj}' và đặt vào '{zone}'.")
                self.skills.pick(obj)
                self.skills.place(obj, zone)
            else:
                print("[LLM]: Xin lỗi, tôi không nghe rõ màu sắc của khối hoặc tên zone. Bạn nói lại nhé!")

def main():
    rclpy.init()
    node = LLMRobotControl()
    
    # Chạy vòng lặp chat trong luồng chính
    try:
        node.run_chat_loop()
    except KeyboardInterrupt:
        pass
    
    rclpy.shutdown()

if __name__ == '__main__':
    main()