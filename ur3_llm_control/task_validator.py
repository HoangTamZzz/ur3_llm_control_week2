VALID_SKILLS = ["pick", "place", "home"]
VALID_OBJECTS = ["red_cube", "yellow_cube", "blue_cube"]
VALID_ZONES = ["zone_a", "zone_b", "zone_c"]

class TaskValidator:
    @staticmethod
    def validate(plan_json):
        if not plan_json or "plan" not in plan_json:
            return False, "Invalid JSON structure."
        
        for step in plan_json["plan"]:
            skill = step.get("skill")
            if skill not in VALID_SKILLS:
                return False, f"Invalid skill generated: {skill}"
            
            if skill in ["pick", "place"]:
                obj = step.get("object")
                if obj not in VALID_OBJECTS:
                    return False, f"Invalid object: {obj}"
                    
            if skill == "place":
                zone = step.get("zone")
                if zone not in VALID_ZONES:
                    return False, f"Invalid zone: {zone}"
                    
        return True, "Plan is valid."