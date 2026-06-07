import sys
import os
import unittest

# Add parent directory to path to allow module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ultrasonic import UltrasonicSensor

class TestUltrasonicSensor(unittest.TestCase):
    def test_ultrasonic_sensor_init(self):
        """Verify ultrasonic sensor initializes in simulation mode successfully."""
        sensor = UltrasonicSensor(17, 27, label="TestSensor", sim_mode=True)
        self.assertTrue(sensor.sim_mode)
        sensor.close()

    def test_ultrasonic_filter_logic(self):
        """Verify that the median filter correctly eliminates spikes and noise."""
        sensor = UltrasonicSensor(17, 27, label="TestSensor", sim_mode=True)
        
        # We override read_distance_raw to return a custom sequence of values
        raw_reads = [10.0, 300.0, 12.0]
        read_index = 0
        
        def mock_read_distance_raw():
            nonlocal read_index
            val = raw_reads[read_index]
            read_index = (read_index + 1) % len(raw_reads)
            return val
            
        # Bind the mock method to the instance
        sensor.read_distance_raw = mock_read_distance_raw
        
        # Median of [10.0, 300.0, 12.0] is 12.0
        filtered = sensor.read_distance_filtered()
        self.assertEqual(filtered, 12.0)
        
        sensor.close()

if __name__ == '__main__':
    unittest.main()
