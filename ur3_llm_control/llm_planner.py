import json
import requests

class LLMPlanner:
    def __init__(self, node):
        self.node = node
        
        # Lấy thông số cấu hình từ ROS 2 Parameters (khai báo trong student_config.yaml)
        self.api_url = node.get_parameter('llm_config.api_endpoint').value
        self.api_key = node.get_parameter_or('llm_config.api_key', 'YOUR_9ROUTER_API_KEY').value
        self.model_name = node.get_parameter('llm_config.model_name').value

        self.system_prompt = """
        You are a robot task planner for a UR3 robot.
        Convert human instructions into a JSON execution plan.

        AVAILABLE SKILLS:
        - {"skill": "pick", "object": "<object_name>"}
        - {"skill": "place", "object": "<object_name>", "zone": "<zone_name>"}
        - {"skill": "home"}

        AVAILABLE OBJECTS: "red_cube", "yellow_cube", "blue_cube"
        AVAILABLE ZONES: "zone_a", "zone_b", "zone_c"

        CRITICAL RULES:
        1. ALWAYS add {"skill": "home"} as the final step of EVERY plan.
        2. IF the user mentions "student ID" or "MSSV" (Student ID Rule P=5):
           You MUST generate exact 7 steps in this order:
           - pick blue_cube -> place blue_cube in zone_a
           - pick yellow_cube -> place yellow_cube in zone_b
           - pick red_cube -> place red_cube in zone_c
           - home()

        OUTPUT FORMAT:
        Output ONLY valid JSON without markdown block wrappers:
        {
          "plan": [
            {"skill": "pick", "object": "red_cube"},
            {"skill": "place", "object": "red_cube", "zone": "zone_b"},
            {"skill": "home"}
          ]
        }
        """

    def generate_plan(self, user_command):
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_command}
            ]
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.node.get_logger().info(f"Sending request to LLM API for command: '{user_command}'...")
        
        try:
            # Bổ sung timeout=10s để tránh bị treo vô hạn nếu không kết nối được API
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            llm_output = response.json()["choices"][0]["message"]["content"].strip()
            
            # Xử lý cắt bỏ định dạng Markdown ```json nếu LLM lỡ sinh ra
            if llm_output.startswith("```json"):
                llm_output = llm_output[7:]
            if llm_output.startswith("```"):
                llm_output = llm_output[3:]
            if llm_output.endswith("```"):
                llm_output = llm_output[:-3]
                
            return json.loads(llm_output.strip())
            
        except requests.exceptions.Timeout:
            self.node.get_logger().error("LLM API call timed out after 60 seconds!")
            return None
        except Exception as e:
            self.node.get_logger().error(f"Error communicating with LLM: {e}")
            return None