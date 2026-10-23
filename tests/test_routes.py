"""
Integration & End-to-End Route Tests for AI Production Planner with Authentication.
"""

import unittest
from app import create_app
from models.models import db, Product, Machine, Worker, Material, Schedule, User
from models.demo_data import load_demo_data, ensure_default_admin

class TestConfig:
    TESTING = True
    SECRET_KEY = 'test-secret-key-for-routes'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    is_vercel = True

class TestAppRoutes(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            load_demo_data()
            ensure_default_admin()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, username='admin', password='admin123'):
        """Helper to log in as admin."""
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def test_unauthenticated_access_redirects_to_login(self):
        """Verify that visitors CANNOT access landing page or protected resources without authentication."""
        # 1. Landing page
        res = self.client.get('/')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))

        # 2. Dashboard
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))

        # 3. AI Planner
        res = self.client.get('/planner')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))

    def test_login_page_renders_without_signup(self):
        """Verify login view renders properly with only login form and no signup."""
        res = self.client.get('/login')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'AI Production Planner', res.data)
        self.assertIn(b'Protected Production Workspace', res.data)
        self.assertIn(b'Username', res.data)
        self.assertIn(b'Password', res.data)
        # Verify no public sign-up form
        self.assertNotIn(b'Sign Up', res.data)
        self.assertNotIn(b'Create an account', res.data)

    def test_authentication_workflow(self):
        """Test invalid credentials rejection and successful login."""
        # Invalid login
        bad_res = self.client.post('/login', data={'username': 'admin', 'password': 'wrongpassword'}, follow_redirects=True)
        self.assertIn(b'Invalid credentials', bad_res.data)

        # Valid login
        good_res = self.login()
        self.assertEqual(good_res.status_code, 200)
        self.assertIn(b'Welcome back', good_res.data)

    def test_authenticated_pages_render(self):
        """Verify all pages render 200 when authenticated."""
        self.login()

        # 1. Home
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'AI-Based Production', res.data)

        # 2. Dashboard
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Production Operations Dashboard', res.data)

        # 3. Products
        res = self.client.get('/products')
        self.assertEqual(res.status_code, 200)

        # 4. Machines
        res = self.client.get('/machines')
        self.assertEqual(res.status_code, 200)

        # 5. Workers
        res = self.client.get('/workers')
        self.assertEqual(res.status_code, 200)

        # 6. Raw Materials
        res = self.client.get('/materials')
        self.assertEqual(res.status_code, 200)

        # 7. Constraints
        res = self.client.get('/constraints')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'HARD CONSTRAINT', res.data)

        # 8. AI Planner
        res = self.client.get('/planner')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Generate Production Plan', res.data)

        # 9. AI Explanation
        res = self.client.get('/ai-explanation')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'How the AI Engine Works', res.data)

    def test_admin_portal_and_credential_change(self):
        """Test admin portal access and changing credentials."""
        self.login()

        # Access admin panel
        admin_res = self.client.get('/admin/')
        self.assertEqual(admin_res.status_code, 200)
        self.assertIn(b'Site Administration', admin_res.data)
        self.assertIn(b'Change Login Credentials', admin_res.data)

        # Update password
        update_res = self.client.post('/admin/credentials', data={
            'username': 'admin',
            'current_password': 'admin123',
            'new_password': 'newpassword456',
            'confirm_password': 'newpassword456'
        }, follow_redirects=True)
        self.assertEqual(update_res.status_code, 200)
        self.assertIn(b'Admin credentials successfully updated', update_res.data)

        # Log out
        self.client.get('/logout', follow_redirects=True)

        # Test login with old password fails
        old_login = self.login(username='admin', password='admin123')
        self.assertIn(b'Invalid credentials', old_login.data)

        # Test login with new password succeeds
        new_login = self.login(username='admin', password='newpassword456')
        self.assertIn(b'Welcome back', new_login.data)

        # Reset password back to admin123
        self.client.post('/admin/credentials', data={
            'username': 'admin',
            'current_password': 'newpassword456',
            'new_password': 'admin123',
            'confirm_password': 'admin123'
        }, follow_redirects=True)

    def test_ai_planner_execution_and_rescheduling(self):
        """Test AI generation and rescheduling with active authentication."""
        self.login()

        with self.app.app_context():
            # Trigger plan generation
            res = self.client.post('/planner/generate', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            
            # Verify schedule generated in database
            schedules = Schedule.query.all()
            self.assertGreaterEqual(len(schedules), 4)

            # Check CSV export
            export_res = self.client.get('/schedule/export')
            self.assertEqual(export_res.status_code, 200)
            self.assertIn(b'Product,Product Code', export_res.data)

            # Check Utilization page
            util_res = self.client.get('/utilization')
            self.assertEqual(util_res.status_code, 200)

            # Test Rescheduling: Mark Machine 1 as Maintenance
            m1 = Machine.query.first()
            self.client.post(f'/machines/toggle-status/{m1.id}', data={'status': 'Maintenance'}, follow_redirects=True)
            m1_updated = db.session.get(Machine, m1.id)
            self.assertEqual(m1_updated.status, 'Maintenance')

            # Regenerate schedule - CSP solver dynamically responds
            res_after = self.client.post('/planner/generate', follow_redirects=True)
            self.assertEqual(res_after.status_code, 200)

    def test_dynamic_calculations_on_new_machine_and_product(self):
        """
        Verify that adding a new custom machine, product, or worker dynamically updates
        the CSP schedule, machine utilization, and dashboard KPI calculations without relying on defaults.
        """
        self.login()

        with self.app.app_context():
            # 1. Add a new custom machine
            add_mach_res = self.client.post('/machines/add', data={
                'name': 'Custom Laser Welder Station',
                'machine_code': 'MAC-WLD-99',
                'machine_type': 'Welding',
                'capacity': '1',
                'available_hours': '8.0',
                'start_time': '08:00',
                'end_time': '17:00',
                'status': 'Available'
            }, follow_redirects=True)
            self.assertEqual(add_mach_res.status_code, 200)

            new_mach = Machine.query.filter_by(machine_code='MAC-WLD-99').first()
            self.assertIsNotNone(new_mach)
            self.assertEqual(new_mach.name, 'Custom Laser Welder Station')

            # 2. Add a compatible technician with required Welding skill
            add_worker_res = self.client.post('/workers/add', data={
                'name': 'Welder Specialist Walter',
                'worker_code': 'WRK-WLD-99',
                'skill': 'Welding',
                'available_hours': '8.0',
                'start_time': '08:00',
                'end_time': '17:00',
                'status': 'Available'
            }, follow_redirects=True)
            self.assertEqual(add_worker_res.status_code, 200)
            new_worker = Worker.query.filter_by(worker_code='WRK-WLD-99').first()
            self.assertIsNotNone(new_worker)

            # 3. Add a new custom product requiring the new machine type
            add_prod_res = self.client.post('/products/add', data={
                'name': 'Titanium Exhaust Manifold',
                'code': 'PRD-EXH-99',
                'quantity': '1',
                'production_time': '2.5',
                'priority': 'High',
                'deadline': '15:00',
                'machine_type': 'Welding',
                'material_id': '',
                'material_quantity': '0'
            }, follow_redirects=True)
            self.assertEqual(add_prod_res.status_code, 200)

            new_prod = Product.query.filter_by(code='PRD-EXH-99').first()
            self.assertIsNotNone(new_prod)
            self.assertEqual(new_prod.status, 'Pending')

            # 4. Verify resources reflect before planning
            prod_list_res = self.client.get('/products')
            self.assertEqual(prod_list_res.status_code, 200)
            self.assertIn(b'Titanium Exhaust Manifold', prod_list_res.data)

            dash_res_before = self.client.get('/dashboard')
            self.assertEqual(dash_res_before.status_code, 200)
            self.assertIn(b'Custom Laser Welder Station', dash_res_before.data)

            # 5. Run the CSP solver on the expanded dataset
            gen_res = self.client.post('/planner/generate', follow_redirects=True)
            self.assertEqual(gen_res.status_code, 200)

            # 6. Verify that the new product was dynamically scheduled onto the new machine & worker
            welding_schedule = Schedule.query.filter_by(product_id=new_prod.id).first()
            self.assertIsNotNone(welding_schedule, "New product must have a scheduled slot")
            self.assertEqual(welding_schedule.machine_id, new_mach.id, "Must be assigned to the new custom machine")
            self.assertEqual(welding_schedule.worker_id, new_worker.id, "Must be assigned to the new custom worker")
            self.assertEqual(welding_schedule.status, 'Scheduled')

            # 7. Check that dashboard and utilization dynamically reflect the new scheduled product & load
            dash_res_after = self.client.get('/dashboard')
            self.assertEqual(dash_res_after.status_code, 200)
            self.assertIn(b'Titanium Exhaust Manifold', dash_res_after.data)

            # 2.5 hours / 8.0 hours = 31.2% utilization for the new welder
            util_res = self.client.get('/utilization')
            self.assertEqual(util_res.status_code, 200)
            self.assertIn(b'Custom Laser Welder Station', util_res.data)
            self.assertIn(b'31.2%', util_res.data)

            # 8. Finished test cleanly

if __name__ == '__main__':
    unittest.main()
