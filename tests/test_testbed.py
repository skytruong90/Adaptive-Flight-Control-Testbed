import unittest
from testbed import Controller, simulate, metrics


class TestbedTests(unittest.TestCase):
    def test_actuator_saturation(self):
        c = Controller(True)
        self.assertLessEqual(abs(c.update(100, 0, 0, 0.02)), 1.0)

    def test_adaptive_gain_changes(self):
        rows = simulate(15, 0.05, True)
        self.assertNotEqual(rows[0]["kp"], rows[-1]["kp"])

    def test_metrics_finite(self):
        m = metrics(simulate(3, 0.05, False))
        self.assertGreaterEqual(m["rms_tracking_error_deg"], 0)


if __name__ == "__main__":
    unittest.main()
