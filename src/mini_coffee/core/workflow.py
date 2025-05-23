# src/mini_coffee/core/workflow.py
import json
from pathlib import Path

class WorkflowController:
    def __init__(self, arm_controller):
        self.arm = arm_controller
        self.node_path = []
        
    def load_path(self, config_path="config/calibration/nodes.json"):
        with open(config_path, 'r') as f:
            data = json.load(f)
            self.node_path = data['nodes']
            
    def execute_path(self):
        """Move arm through all nodes in sequence"""
        for node in self.node_path:
            self.arm.move_to(**node['arm_coords'])
            self.arm.wait_for_movement()
            
    def generate_recipe(self, node_ids):
        """Create recipe from subset of nodes"""
        return [n for n in self.node_path if n['id'] in node_ids]