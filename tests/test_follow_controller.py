import sys
import os
import unittest

# Add parent directory to path to allow module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from follow_controller import FollowController, RoverState
from config import ControlConfig

class TestFollowController(unittest.TestCase):
    def test_friction_correction(self):
        """Verify values below threshold are boosted to overcome friction, preserving sign."""
        controller = FollowController()
        
        # 0 should stay 0
        self.assertEqual(controller._apply_friction_correction(0.0), 0.0)
        
        # Value above threshold should be unchanged
        val_high = ControlConfig.MIN_SPEED_THRESHOLD + 0.1
        self.assertEqual(controller._apply_friction_correction(val_high), val_high)
        self.assertEqual(controller._apply_friction_correction(-val_high), -val_high)
        
        # Value below threshold should be boosted to min threshold
        val_low = ControlConfig.MIN_SPEED_THRESHOLD - 0.05
        self.assertEqual(controller._apply_friction_correction(val_low), ControlConfig.MIN_SPEED_THRESHOLD)
        self.assertEqual(controller._apply_friction_correction(-val_low), -ControlConfig.MIN_SPEED_THRESHOLD)

    def test_steering_controller_logic(self):
        """Verify that targeting left/right outputs correct differential speeds."""
        controller = FollowController()
        controller.change_state(RoverState.FOLLOWING)
        
        # Target is in the middle, height is perfect (ratio 0.5)
        # Target x = 320 (middle), Frame width = 640.
        left, right = controller._compute_follow_speeds(
            tracking_box=(320 - 50, 240 - 120, 100, 240),
            is_front_blocked=False,
            is_rear_blocked=False,
            dt=0.1
        )
        # With no error, both speeds should be 0.0
        self.assertAlmostEqual(left, 0.0, places=2)
        self.assertAlmostEqual(right, 0.0, places=2)
        
        # Target is on the right side of the screen (needs to turn right)
        # Left motor speed should increase, right motor speed should decrease
        left, right = controller._compute_follow_speeds(
            tracking_box=(450 - 50, 240 - 120, 100, 240),
            is_front_blocked=False,
            is_rear_blocked=False,
            dt=0.1
        )
        self.assertGreater(left, right)
        
        # Target is on the left side (needs to turn left)
        # Right motor speed should exceed left motor speed
        left, right = controller._compute_follow_speeds(
            tracking_box=(190 - 50, 240 - 120, 100, 240),
            is_front_blocked=False,
            is_rear_blocked=False,
            dt=0.1
        )
        self.assertGreater(right, left)

    def test_speed_controller_logic(self):
        """Verify that distance changes (represented by bounding box size) adjust speed directions."""
        controller = FollowController()
        controller.change_state(RoverState.FOLLOWING)
        
        # Case 1: Target is far away (bounding box height = 120, ratio 0.25 vs desired 0.5)
        # Rover should move forward: speed > 0
        left, right = controller._compute_follow_speeds(
            tracking_box=(320 - 30, 240 - 60, 60, 120),
            is_front_blocked=False,
            is_rear_blocked=False,
            dt=0.1
        )
        self.assertGreater(left, 0.0)
        self.assertGreater(right, 0.0)
        
        # Case 2: Target is too close (bounding box height = 360, ratio 0.75 vs desired 0.5)
        # Rover should move backward: speed < 0 (if not blocked)
        left, right = controller._compute_follow_speeds(
            tracking_box=(320 - 90, 240 - 180, 180, 360),
            is_front_blocked=False,
            is_rear_blocked=False,
            dt=0.1
        )
        self.assertLess(left, 0.0)
        self.assertLess(right, 0.0)

if __name__ == '__main__':
    unittest.main()
