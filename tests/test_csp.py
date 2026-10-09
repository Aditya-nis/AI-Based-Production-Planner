"""
Comprehensive Unit & Integration Tests for AI CSP Production Planner.

Tests 10 critical scenarios required by project specification:
1. Valid production schedule generation
2. Machine time conflict detection
3. Worker time conflict detection
4. Insufficient machine hours detection
5. Insufficient worker hours detection
6. Missing / Insufficient raw material detection
7. Deadline violation detection
8. Machine incompatibility detection
9. Worker skill mismatch detection
10. Unsolvable scenario with conflict diagnosis
"""

import unittest
from ai_engine.csp_scheduler import CSPVariable, Domain, ProductionCSP, CSPScheduler
from ai_engine.constraints import (
    check_machine_conflict,
    check_worker_conflict,
    check_machine_compatibility,
    check_worker_skill,
    check_machine_capacity,
    check_worker_hours,
    check_material_availability,
    check_deadline,
    check_machine_status,
    check_worker_status,
    check_all_constraints
)

class MockModel:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class TestCSPPlanner(unittest.TestCase):
    def setUp(self):
        # Create standard test resources
        self.machine1 = MockModel(id=1, name="Assembly M1", machine_code="M1", machine_type="Assembly",
                                  capacity=1, available_hours=8.0, start_time="08:00", end_time="17:00", status="Available")
        self.machine2 = MockModel(id=2, name="Cutting M2", machine_code="M2", machine_type="Cutting",
                                  capacity=1, available_hours=8.0, start_time="08:00", end_time="17:00", status="Available")

        self.worker1 = MockModel(id=1, name="Alice", worker_code="W1", skill="Assembly",
                                 available_hours=8.0, start_time="08:00", end_time="17:00", status="Available")
        self.worker2 = MockModel(id=2, name="Bob", worker_code="W2", skill="Cutting",
                                 available_hours=8.0, start_time="08:00", end_time="17:00", status="Available")

        self.material1 = MockModel(id=1, name="Chips", material_code="MAT1", quantity=10.0, unit="units", minimum_quantity=1.0)
        self.material2 = MockModel(id=2, name="Wood", material_code="MAT2", quantity=20.0, unit="pcs", minimum_quantity=2.0)

        self.context = {
            'machines_dict': {1: self.machine1, 2: self.machine2},
            'workers_dict': {1: self.worker1, 2: self.worker2},
            'materials_dict': {1: self.material1, 2: self.material2}
        }

    # Test 1: Valid Schedule
    def test_valid_production_schedule(self):
        prod1 = MockModel(id=1, name="Laptop", code="P1", quantity=1, production_time=2.0,
                          priority="High", deadline="14:00", machine_type="Assembly",
                          material_id=1, material_quantity=2.0, status="Pending")
        prod2 = MockModel(id=2, name="Chair", code="P2", quantity=1, production_time=2.0,
                          priority="Medium", deadline="15:00", machine_type="Cutting",
                          material_id=2, material_quantity=4.0, status="Pending")

        scheduler = CSPScheduler(db_session=None)
        res = scheduler.run_scheduler(
            [prod1, prod2],
            [self.machine1, self.machine2],
            [self.worker1, self.worker2],
            [self.material1, self.material2]
        )
        self.assertTrue(res['success'])
        self.assertEqual(len(res['solution']), 2)
        self.assertTrue(res['statistics']['solution_found'])

    # Test 2: Machine Conflict Prevention
    def test_machine_conflict(self):
        val1 = {'machine_id': 1, 'machine_name': 'M1', 'worker_id': 1, 'worker_name': 'W1', 'start_time': '09:00', 'end_time': '11:00'}
        val2_overlapping = {'machine_id': 1, 'machine_name': 'M1', 'worker_id': 2, 'worker_name': 'W2', 'start_time': '10:00', 'end_time': '12:00'}
        var1 = MockModel(name="Task A")
        assignments = {var1: val1}
        ok, reason = check_machine_conflict(val2_overlapping, assignments)
        self.assertFalse(ok)
        self.assertIn("already assigned", reason)

    # Test 3: Worker Conflict Prevention
    def test_worker_conflict(self):
        val1 = {'machine_id': 1, 'machine_name': 'M1', 'worker_id': 1, 'worker_name': 'W1', 'start_time': '09:00', 'end_time': '11:00'}
        val2_overlapping = {'machine_id': 2, 'machine_name': 'M2', 'worker_id': 1, 'worker_name': 'W1', 'start_time': '10:00', 'end_time': '12:00'}
        var1 = MockModel(name="Task A")
        assignments = {var1: val1}
        ok, reason = check_worker_conflict(val2_overlapping, assignments)
        self.assertFalse(ok)
        self.assertIn("already assigned", reason)

    # Test 4: Insufficient Machine Hours
    def test_insufficient_machine_hours(self):
        mach = MockModel(name="M1", available_hours=4.0)
        ok, reason = check_machine_capacity(mach, assigned_hours=3.0, new_hours=2.0)
        self.assertFalse(ok)
        self.assertIn("exceeded", reason)

    # Test 5: Insufficient Worker Hours
    def test_insufficient_worker_hours(self):
        worker = MockModel(name="W1", available_hours=5.0)
        ok, reason = check_worker_hours(worker, assigned_hours=4.0, new_hours=2.0)
        self.assertFalse(ok)
        self.assertIn("exceeded", reason)

    # Test 6: Missing / Insufficient Raw Material
    def test_material_availability(self):
        task = MockModel(material_id=1, material_quantity=15.0)  # inventory only has 10.0
        ok, reason = check_material_availability(task, allocated_materials={}, raw_materials_dict=self.context['materials_dict'])
        self.assertFalse(ok)
        self.assertIn("Insufficient material", reason)

    # Test 7: Deadline Violation
    def test_deadline_violation(self):
        task = MockModel(name="P1", deadline="12:00")
        val = {'end_time': '13:00'}
        ok, reason = check_deadline(val, task)
        self.assertFalse(ok)
        self.assertIn("past deadline", reason)

    # Test 8: Machine Incompatibility
    def test_machine_incompatibility(self):
        task = MockModel(required_machine_type="Drilling")
        ok, reason = check_machine_compatibility(task, self.machine1)  # machine1 is Assembly
        self.assertFalse(ok)
        self.assertIn("does not match", reason)

    # Test 9: Worker Skill Mismatch
    def test_worker_skill_mismatch(self):
        task = MockModel(required_skill="Drilling", required_machine_type="Drilling")
        ok, reason = check_worker_skill(task, self.worker1)  # worker1 has skill Assembly
        self.assertFalse(ok)
        self.assertIn("does not match", reason)

    # Test 10: Impossible Scenario Diagnostics
    def test_impossible_scenario_diagnostics(self):
        # Machine in maintenance, no compatible alternative
        self.machine1.status = "Maintenance"
        prod1 = MockModel(id=1, name="Laptop", code="P1", quantity=1, production_time=2.0,
                          priority="High", deadline="14:00", machine_type="Assembly",
                          material_id=1, material_quantity=2.0, status="Pending")
        scheduler = CSPScheduler(db_session=None)
        res = scheduler.run_scheduler(
            [prod1],
            [self.machine1],
            [self.worker1],
            [self.material1]
        )
        self.assertFalse(res['success'])
        self.assertIn('conflicting_constraints', res['diagnostics'])
        self.assertTrue(len(res['diagnostics']['conflicting_constraints']) > 0)

if __name__ == '__main__':
    unittest.main()
