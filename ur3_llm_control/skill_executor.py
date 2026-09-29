from .robot_skills import UR3Skills

class SkillExecutor:
    def __init__(self, node):
        self.skills = UR3Skills(node)

    def execute_plan(self, plan_json):
        print("\nEXECUTION:")
        all_success = True

        for step in plan_json["plan"]:
            skill = step["skill"]
            status = "FAILED"

            if skill == "home":
                log_str = "home()"
                print(f"{log_str:<30} ........ ", end="", flush=True)
                status = self.skills.home()
                
            elif skill == "pick":
                obj = step["object"]
                log_str = f"pick({obj})"
                print(f"{log_str:<30} ........ ", end="", flush=True)
                status = self.skills.pick(obj)
                
            elif skill == "place":
                obj = step["object"]
                zone = step["zone"]
                log_str = f"place({obj}, {zone})"
                print(f"{log_str:<30} ........ ", end="", flush=True)
                status = self.skills.place(obj, zone)

            print(status)
            if status != "SUCCESS":
                all_success = False
                break
                
        if all_success:
            print("\nTASK SUCCESS\n")
        else:
            print("\nTASK FAILED\n")