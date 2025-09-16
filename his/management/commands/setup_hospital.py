# his/management/commands/setup_hospital.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import random

from his.models import (
    Department, Staff, Ward, Bed, Patient, Visit, Service, ServiceCategory,
    LabTest, RadiologyStudy, PharmacyStock, Supplier, InsuranceProvider,
    LeaveType, SystemConfiguration, Role
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup Hospital HIS with initial data'

    def add_arguments(self, parser):
        parser.add_argument('--demo-data', action='store_true', help='Create demo patients and visits')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up Hospital HIS...'))

        # Create superuser if not exists
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@hospital.com',
                password='admin123',
                first_name='System',
                last_name='Administrator',
                role=Role.ADMIN
            )
            self.stdout.write(self.style.SUCCESS('Created admin user: admin/admin123'))

        # Create departments
        departments_data = [
            {'name': 'Emergency', 'description': 'Emergency Department'},
            {'name': 'Internal Medicine', 'description': 'Internal Medicine Department'},
            {'name': 'Surgery', 'description': 'Surgical Department'},
            {'name': 'Pediatrics', 'description': 'Children\'s Department'},
            {'name': 'Orthopedics', 'description': 'Orthopedic Department'},
            {'name': 'Cardiology', 'description': 'Heart Department'},
            {'name': 'Neurology', 'description': 'Neurology Department'},
            {'name': 'Radiology', 'description': 'Imaging Department'},
            {'name': 'Laboratory', 'description': 'Lab Services'},
            {'name': 'Pharmacy', 'description': 'Pharmacy Department'},
        ]

        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                name=dept_data['name'],
                defaults=dept_data
            )
            if created:
                self.stdout.write(f'Created department: {dept.name}')

        # Create sample users for different roles
        sample_users = [
            {'username': 'dr.smith', 'role': Role.DOCTOR, 'first_name': 'John', 'last_name': 'Smith', 'email': 'dr.smith@hospital.com'},
            {'username': 'dr.jones', 'role': Role.DOCTOR, 'first_name': 'Sarah', 'last_name': 'Jones', 'email': 'dr.jones@hospital.com'},
            {'username': 'nurse.mary', 'role': Role.NURSE, 'first_name': 'Mary', 'last_name': 'Johnson', 'email': 'nurse.mary@hospital.com'},
            {'username': 'nurse.peter', 'role': Role.NURSE, 'first_name': 'Peter', 'last_name': 'Wilson', 'email': 'nurse.peter@hospital.com'},
            {'username': 'pharma.alex', 'role': Role.PHARMACIST, 'first_name': 'Alex', 'last_name': 'Brown', 'email': 'pharma.alex@hospital.com'},
            {'username': 'lab.tech', 'role': Role.LAB, 'first_name': 'Lisa', 'last_name': 'Davis', 'email': 'lab.tech@hospital.com'},
            {'username': 'finance.mike', 'role': Role.FINANCE, 'first_name': 'Mike', 'last_name': 'Miller', 'email': 'finance.mike@hospital.com'},
            {'username': 'reception', 'role': Role.RECEPTIONIST, 'first_name': 'Anna', 'last_name': 'Garcia', 'email': 'reception@hospital.com'},
        ]

        for user_data in sample_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    **user_data,
                    'password': 'pbkdf2_sha256$600000$xyz$hash',  # password: 'password123'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {user.username}')

        # Create staff profiles
        doctors = User.objects.filter(role=Role.DOCTOR)
        for i, doctor in enumerate(doctors):
            staff, created = Staff.objects.get_or_create(
                user=doctor,
                defaults={
                    'staff_id': f'DOC{i+1:03d}',
                    'designation': 'Consultant',
                    'department': Department.objects.get(name='Internal Medicine'),
                    'joining_date': timezone.now().date() - timedelta(days=random.randint(30, 365))
                }
            )
            if created:
                self.stdout.write(f'Created staff profile: {staff.staff_id}')

        # Create wards and beds
        ward_data = [
            {'name': 'General Ward A', 'ward_type': 'general', 'total_beds': 20},
            {'name': 'General Ward B', 'ward_type': 'general', 'total_beds': 20},
            {'name': 'ICU', 'ward_type': 'icu', 'total_beds': 10},
            {'name': 'Private Room Block', 'ward_type': 'private', 'total_beds': 15},
            {'name': 'Pediatric Ward', 'ward_type': 'special', 'total_beds': 12},
        ]

        for ward_info in ward_data:
            ward, created = Ward.objects.get_or_create(
                name=ward_info['name'],
                defaults={
                    'ward_type': ward_info['ward_type'],
                    'total_beds': ward_info['total_beds'],
                    'department': Department.objects.first()
                }
            )
            if created:
                # Create beds for this ward
                for bed_num in range(1, ward_info['total_beds'] + 1):
                    Bed.objects.create(
                        bed_number=f'{bed_num:02d}',
                        ward=ward,
                        daily_rate=1500 if ward_info['ward_type'] == 'private' else 800
                    )
                self.stdout.write(f'Created ward: {ward.name} with {ward_info["total_beds"]} beds')

        # Create service categories and services
        service_categories = [
            'Consultation',
            'Diagnostic',
            'Procedure',
            'Surgery',
            'Emergency',
        ]

        for cat_name in service_categories:
            ServiceCategory.objects.get_or_create(name=cat_name)

        # Sample services
        services_data = [
            {'name': 'OPD Consultation', 'code': 'OPD001', 'price': 500, 'category': 'Consultation'},
            {'name': 'Emergency Consultation', 'code': 'EMG001', 'price': 1000, 'category': 'Emergency'},
            {'name': 'ICU Admission', 'code': 'ICU001', 'price': 5000, 'category': 'Procedure'},
            {'name': 'X-Ray Chest', 'code': 'XRY001', 'price': 800, 'category': 'Diagnostic'},
            {'name': 'CT Scan Head', 'code': 'CT001', 'price': 3500, 'category': 'Diagnostic'},
            {'name': 'Blood Test - CBC', 'code': 'LAB001', 'price': 400, 'category': 'Diagnostic'},
            {'name': 'Appendectomy', 'code': 'SUR001', 'price': 50000, 'category': 'Surgery'},
        ]

        for service_data in services_data:
            category = ServiceCategory.objects.get(name=service_data['category'])
            Service.objects.get_or_create(
                code=service_data['code'],
                defaults={
                    'name': service_data['name'],
                    'price': service_data['price'],
                    'category': category
                }
            )

        # Create lab tests
        lab_tests = [
            {'name': 'Complete Blood Count', 'code': 'CBC', 'price': 400, 'sample_type': 'Blood'},
            {'name': 'Lipid Profile', 'code': 'LIPID', 'price': 800, 'sample_type': 'Blood'},
            {'name': 'Liver Function Test', 'code': 'LFT', 'price': 600, 'sample_type': 'Blood'},
            {'name': 'Kidney Function Test', 'code': 'KFT', 'price': 500, 'sample_type': 'Blood'},
            {'name': 'Blood Sugar Fasting', 'code': 'BSF', 'price': 200, 'sample_type': 'Blood'},
            {'name': 'Urine Routine', 'code': 'URINE', 'price': 300, 'sample_type': 'Urine'},
            {'name': 'Thyroid Profile', 'code': 'THYROID', 'price': 1200, 'sample_type': 'Blood'},
        ]

        for test_data in lab_tests:
            LabTest.objects.get_or_create(
                code=test_data['code'],
                defaults=test_data
            )

        # Create radiology studies
        radiology_studies = [
            {'name': 'Chest X-Ray', 'code': 'CXR', 'modality': 'X-Ray', 'price': 800},
            {'name': 'CT Head Plain', 'code': 'CTHP', 'modality': 'CT', 'price': 3500},
            {'name': 'MRI Brain', 'code': 'MRIB', 'modality': 'MRI', 'price': 8000},
            {'name': 'Ultrasound Abdomen', 'code': 'USAB', 'modality': 'Ultrasound', 'price': 1500},
            {'name': 'ECG', 'code': 'ECG', 'modality': 'ECG', 'price': 300},
        ]

        for study_data in radiology_studies:
            RadiologyStudy.objects.get_or_create(
                code=study_data['code'],
                defaults=study_data
            )

        # Create pharmacy stock
        medications = [
            {'name': 'Paracetamol 500mg', 'generic': 'Paracetamol', 'price': 2.50, 'selling_price': 3.00},
            {'name': 'Amoxicillin 500mg', 'generic': 'Amoxicillin', 'price': 8.00, 'selling_price': 10.00},
            {'name': 'Omeprazole 20mg', 'generic': 'Omeprazole', 'price': 5.50, 'selling_price': 7.00},
            {'name': 'Atorvastatin 20mg', 'generic': 'Atorvastatin', 'price': 12.00, 'selling_price': 15.00},
            {'name': 'Metformin 500mg', 'generic': 'Metformin', 'price': 3.50, 'selling_price': 4.50},
            {'name': 'Aspirin 75mg', 'generic': 'Aspirin', 'price': 1.80, 'selling_price': 2.20},
        ]

        for med_data in medications:
            PharmacyStock.objects.get_or_create(
                medication_name=med_data['name'],
                batch_number='BATCH001',
                defaults={
                    'generic_name': med_data['generic'],
                    'unit_price': med_data['price'],
                    'selling_price': med_data['selling_price'],
                    'quantity': random.randint(100, 1000),
                    'expiry_date': timezone.now().date() + timedelta(days=random.randint(180, 730))
                }
            )

        # Create suppliers
        suppliers_data = [
            {'name': 'MedSupply Co.', 'contact_person': 'John Supplier', 'phone': '+91-9876543210'},
            {'name': 'PharmaDist Ltd.', 'contact_person': 'Sarah Distributor', 'phone': '+91-9876543211'},
            {'name': 'HealthCorp Supplies', 'contact_person': 'Mike Vendor', 'phone': '+91-9876543212'},
        ]

        for supplier_data in suppliers_data:
            Supplier.objects.get_or_create(
                name=supplier_data['name'],
                defaults=supplier_data
            )

        # Create insurance providers
        insurance_data = [
            {'name': 'HealthFirst Insurance', 'contact_person': 'Claims Manager'},
            {'name': 'MediCare Plus', 'contact_person': 'Policy Handler'},
            {'name': 'Star Health Insurance', 'contact_person': 'Customer Service'},
        ]

        for ins_data in insurance_data:
            InsuranceProvider.objects.get_or_create(
                name=ins_data['name'],
                defaults=ins_data
            )

        # Create leave types
        leave_types = [
            {'name': 'Annual Leave', 'max_days_per_year': 21},
            {'name': 'Sick Leave', 'max_days_per_year': 12},
            {'name': 'Emergency Leave', 'max_days_per_year': 5},
            {'name': 'Maternity Leave', 'max_days_per_year': 180},
        ]

        for leave_data in leave_types:
            LeaveType.objects.get_or_create(
                name=leave_data['name'],
                defaults=leave_data
            )

        # Create system configurations
        configs = [
            {'key': 'hospital_name', 'value': 'City General Hospital', 'description': 'Hospital Name'},
            {'key': 'hospital_address', 'value': '123 Medical Street, Health City', 'description': 'Hospital Address'},
            {'key': 'emergency_contact', 'value': '+91-911-EMERGENCY', 'description': 'Emergency Contact Number'},
            {'key': 'appointment_duration', 'value': '30', 'description': 'Default appointment duration in minutes', 'data_type': 'integer'},
            {'key': 'low_stock_threshold', 'value': '10', 'description': 'Low stock alert threshold', 'data_type': 'integer'},
            {'key': 'invoice_prefix', 'value': 'INV', 'description': 'Invoice number prefix'},
            {'key': 'tax_rate', 'value': '18.0', 'description': 'Tax rate percentage', 'data_type': 'float'},
        ]

        for config_data in configs:
            SystemConfiguration.objects.get_or_create(
                key=config_data['key'],
                defaults=config_data
            )

        # Create demo data if requested
        if options['demo_data']:
            self.create_demo_data()

        self.stdout.write(self.style.SUCCESS('Hospital HIS setup completed successfully!'))
        self.stdout.write(self.style.WARNING('Default login credentials:'))
        self.stdout.write('Admin: admin / admin123')
        self.stdout.write('Doctor: dr.smith / password123')
        self.stdout.write('Nurse: nurse.mary / password123')
        self.stdout.write('Pharmacist: pharma.alex / password123')

    def create_demo_data(self):
        """Create demo patients, visits, and other sample data"""
        self.stdout.write('Creating demo data...')

        # Create demo patients
        demo_patients = [
            {'first_name': 'John', 'last_name': 'Doe', 'age': 45, 'gender': 'M', 'contact_number': '+91-9876543210'},
            {'first_name': 'Jane', 'last_name': 'Smith', 'age': 32, 'gender': 'F', 'contact_number': '+91-9876543211'},
            {'first_name': 'Robert', 'last_name': 'Johnson', 'age': 67, 'gender': 'M', 'contact_number': '+91-9876543212'},
            {'first_name': 'Emily', 'last_name': 'Brown', 'age': 28, 'gender': 'F', 'contact_number': '+91-9876543213'},
            {'first_name': 'Michael', 'last_name': 'Davis', 'age': 54, 'gender': 'M', 'contact_number': '+91-9876543214'},
        ]

        created_patients = []
        for i, patient_data in enumerate(demo_patients):
            patient = Patient.objects.create(
                mrn=f"{timezone.now().strftime('%y%m%d')}{i+1:04d}",
                **patient_data,
                address=f"Demo Address {i+1}, Demo City",
                created_by=User.objects.get(username='admin')
            )
            created_patients.append(patient)
            self.stdout.write(f'Created demo patient: {patient.mrn}')

        # Create demo visits
        for patient in created_patients[:3]:  # Create visits for first 3 patients
            visit = Visit.objects.create(
                patient=patient,
                visit_id=f"V{timezone.now().strftime('%y%m%d')}{patient.mrn[-4:]}",
                visit_type=random.choice(['opd', 'ipd']),
                department=Department.objects.get(name='Internal Medicine'),
                attending_doctor=User.objects.filter(role=Role.DOCTOR).first(),
                reason='Demo visit for system testing'
            )
            self.stdout.write(f'Created demo visit: {visit.visit_id}')

        self.stdout.write(self.style.SUCCESS('Demo data created successfully!'))