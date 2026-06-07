import sys
import os
import unittest

# Add parent directory to path to allow module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from motor_controller import MotorController

class TestMotorController(unittest.TestCase):
    def test_motor_controller_init(self):
        """Verify that motor controller initializes in simulation mode without errors."""
        controller = MotorController(sim_mode=True)
        self.assertTrue(controller.sim_mode)
        controller.cleanup()

    def test_motor_controller_speeds(self):
        """Verify that setting speed updates target values correctly."""
        controller = MotorController(sim_mode=True)
        
        # Set positive forward speed
        controller.set_speeds(0.5, 0.7)
        left_avg, right_avg = controller.get_speeds()
        self.assertEqual(left_avg, 0.5)
        self.assertEqual(right_avg, 0.7)
        
        # Check direction pins on simulated channels
        self.assertEqual(controller.left_front.in1.value, 1)
        self.assertEqual(controller.left_front.in2.value, 0)
        
        # Set reverse speeds
        controller.set_speeds(-0.3, -0.4)
        left_avg, right_avg = controller.get_speeds()
        self.assertEqual(left_avg, -0.3)
        self.assertEqual(right_avg, -0.4)
        self.assertEqual(controller.left_front.in1.value, 0)
        self.assertEqual(controller.left_front.in2.value, 1)
        
        controller.cleanup()

    def test_motor_controller_limits(self):
        """Verify speed values outside bounds are safely clamped to [-1.0, 1.0]."""
        controller = MotorController(sim_mode=True)
        
        controller.set_speeds(1.5, -2.5)
        left_avg, right_avg = controller.get_speeds()
        self.assertEqual(left_avg, 1.0)
        self.assertEqual(right_avg, -1.0)
        
        controller.cleanup()

    def test_motor_controller_stop(self):
        """Verify stop function sets all motor speeds to 0."""
        controller = MotorController(sim_mode=True)
        
        controller.set_speeds(0.8, 0.8)
        controller.stop()
        left_avg, right_avg = controller.get_speeds()
        self.assertEqual(left_avg, 0.0)
        self.assertEqual(right_avg, 0.0)
        
        controller.cleanup()

if __name__ == '__main__':
    unittest.main()
