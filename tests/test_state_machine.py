import sys
import os
import time
import unittest

# Add parent directory to path to allow module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from follow_controller import FollowController, RoverState
from config import ControlConfig

class TestStateMachine(unittest.TestCase):
    def test_initial_state(self):
        """Verify state machine starts in INITIALIZING."""
        controller = FollowController()
        self.assertEqual(controller.state, RoverState.INITIALIZING)

    def test_transition_to_searching(self):
        """Verify state transitions to SEARCHING on first update loop."""
        controller = FollowController()
        # First update step
        controller.update(
            tracking_box=None,
            front_distance=100.0,
            rear_distance=100.0,
            dt=0.1
        )
        self.assertEqual(controller.state, RoverState.SEARCHING)

    def test_transition_to_tracking_and_following(self):
        """Verify acquisition state transitions (SEARCHING -> TRACKING -> FOLLOWING)."""
        controller = FollowController()
        controller.change_state(RoverState.SEARCHING)
        
        # 1. Update with target box. State should transition to TRACKING.
        box = (270, 120, 100, 240)
        controller.update(box, 100.0, 100.0, 0.033)
        self.assertEqual(controller.state, RoverState.TRACKING)
        self.assertEqual(controller.tracking_confirm_frames, 1)
        
        # 2. Feed target box for remaining 4 frames to hit confirmation threshold (5 frames total)
        for _ in range(4):
            controller.update(box, 100.0, 100.0, 0.033)
            
        self.assertEqual(controller.state, RoverState.FOLLOWING)

    def test_transition_to_lost_target_and_timeout(self):
        """Verify target loss transitions and search timeouts."""
        controller = FollowController()
        controller.change_state(RoverState.FOLLOWING)
        
        # Update with None box -> transitions to LOST_TARGET
        controller.update(None, 100.0, 100.0, 0.033)
        self.assertEqual(controller.state, RoverState.LOST_TARGET)
        
        # Override lost time to force timeout (10 seconds config)
        controller.target_lost_time = time.time() - (ControlConfig.LOST_TARGET_TIMEOUT + 1.0)
        
        # Next update should transition back to SEARCHING
        controller.update(None, 100.0, 100.0, 0.033)
        self.assertEqual(controller.state, RoverState.SEARCHING)

    def test_transition_to_blocked_and_recovery(self):
        """Verify safety override blocking and clearance recovery with hysteresis."""
        controller = FollowController()
        controller.change_state(RoverState.FOLLOWING)
        
        # Normal follow, box height ratio 0.25 (moves forward)
        # Front obstacle is 15 cm (less than 20 cm safety limit)
        box = (270, 120, 100, 120)
        left, right = controller.update(box, 15.0, 100.0, 0.033)
        
        # Should transition to BLOCKED and stop motors
        self.assertEqual(controller.state, RoverState.BLOCKED)
        self.assertEqual(left, 0.0)
        self.assertEqual(right, 0.0)
        
        # Update with obstacle distance at 22 cm.
        # Due to hysteresis (must exceed 25cm to clear BLOCKED), state should remain BLOCKED.
        left, right = controller.update(box, 22.0, 100.0, 0.033)
        self.assertEqual(controller.state, RoverState.BLOCKED)
        self.assertEqual(left, 0.0)
        self.assertEqual(right, 0.0)
        
        # Update with obstacle distance at 27 cm.
        # Should clear BLOCKED and transition to SEARCHING/TRACKING
        controller.update(box, 27.0, 100.0, 0.033)
        self.assertNotEqual(controller.state, RoverState.BLOCKED)

if __name__ == '__main__':
    unittest.main()
