# his/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser 
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.conf import settings


# Roles
class Role(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    DOCTOR = 'doctor', 'Doctor'
    NURSE = 'nurse', 'Nurse'
    PHARMACIST = 'pharmacist', 'Pharmacist'
    LAB = 'lab', 'Lab Technician'
    FINANCE = 'finance', 'Finance'
    PATIENT = 'patient', 'Patient'
    RECEPTIONIST = 'receptionist', 'Receptionist'

# Custom user
class User(AbstractUser ):
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.PATIENT)
    phone = models.CharField(max_length=20, blank=True)
    employee_id = models.CharField(max_length=20, blank=True, unique=True, null=True)

    def __str__(self):
        # Use full name if available, fallback to username
        fullname = self.get_full_name()
        if fullname:
            return f"{fullname} ({self.role})"
        return f"{self.username} ({self.role})"

# Department model
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    head = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_departments')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

# Staff (for HR)
class Staff(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_profile', null=True, blank=True)
    staff_id = models.CharField(max_length=32, unique=True)
    designation = models.CharField(max_length=120, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shift_start = models.TimeField(null=True, blank=True)
    shift_end = models.TimeField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        name = self.user.get_full_name() if self.user else 'Unknown'
        return f"{self.staff_id} - {name}"

# Leave Management
class LeaveType(models.Model):
    name = models.CharField(max_length=50)
    max_days_per_year = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        user = self.staff.user.username if self.staff and self.staff.user else 'Unknown'
        return f"{user} - {self.start_date} to {self.end_date}"

# Ward and Bed Management
class Ward(models.Model):
    WARD_TYPES = [
        ('general', 'General Ward'),
        ('icu', 'ICU'),
        ('special', 'Special Ward'),
        ('private', 'Private Room'),
    ]

    name = models.CharField(max_length=100)
    ward_type = models.CharField(max_length=20, choices=WARD_TYPES)
    total_beds = models.IntegerField()
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    nurse_in_charge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_wards')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.ward_type})"

    @property
    def available_beds(self):
        return self.total_beds - self.beds.filter(is_occupied=True).count()

class Bed(models.Model):
    bed_number = models.CharField(max_length=20)
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='beds')
    is_occupied = models.BooleanField(default=False)
    is_maintenance = models.BooleanField(default=False)
    bed_type = models.CharField(max_length=50, blank=True)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ['ward', 'bed_number']

    def __str__(self):
        return f"{self.ward.name} - {self.bed_number}"

# Audit logs
class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    model = models.CharField(max_length=128, blank=True)
    object_id = models.CharField(max_length=128, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    details = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        actor = self.actor.username if self.actor else 'System'
        return f"{self.timestamp} - {actor} - {self.action}"

# Patient
class MRNCounter(models.Model):
    """
    Keeps track of the last MRN sequence number for each year.
    Used to generate unique, sequential MRNs like MRN20250001.
    """
    year = models.IntegerField(unique=True)
    last_seq = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.year} - {self.last_seq}"


class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    ]

    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mrn = models.CharField(max_length=32, unique=True, editable=False)  # auto-assigned, not editable
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120, blank=True)
    dob = models.DateField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    contact_number = models.CharField(max_length=30, blank=True)
    emergency_contact = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    aadhar_number = models.CharField(max_length=12, blank=True, unique=True, null=True)
    insurance_number = models.CharField(max_length=50, blank=True)
    allergies = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='patients_created')

    class Meta:
        indexes = [
            models.Index(fields=['mrn']),
            models.Index(fields=['created_at'])
        ]

    def __str__(self):
        return f"{self.mrn} - {self.first_name} {self.last_name or ''}".strip()


# Appointment Management
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments_as_doctor')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    appointment_date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=30)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments_created')

    class Meta:
        unique_together = ['doctor', 'appointment_date']

    def __str__(self):
        doctor_name = self.doctor.get_full_name() if self.doctor else 'Unknown Doctor'
        return f"{self.patient.mrn} - Dr. {doctor_name} - {self.appointment_date}"

# Visit
class Visit(models.Model):
    VISIT_TYPES = [
        ('opd', 'OPD'),
        ('ipd', 'IPD'),
        ('emergency', 'Emergency'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('discharged', 'Discharged'),
        ('referred', 'Referred'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='visits')
    visit_id = models.CharField(max_length=64, unique=True)
    visit_type = models.CharField(max_length=20, choices=VISIT_TYPES, default='opd')
    admitted_at = models.DateTimeField(default=timezone.now)
    discharged_at = models.DateTimeField(null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    attending_doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='visits_attended')
    bed = models.ForeignKey(Bed, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    discharge_summary = models.TextField(blank=True)
    follow_up_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['visit_id']), models.Index(fields=['admitted_at'])]

    def __str__(self):
        return f"{self.visit_id} ({self.patient.mrn})"

# Vitals
class Vitals(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, null=True)  # temporarily allow null
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='vitals_recorded')
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pulse = models.PositiveIntegerField(null=True, blank=True)
    systolic_bp = models.PositiveIntegerField(null=True, blank=True)
    diastolic_bp = models.PositiveIntegerField(null=True, blank=True)
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True)
    oxygen_saturation = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    blood_sugar = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Vitals for {self.visit.patient.mrn} - {self.recorded_at.strftime('%Y-%m-%d %H:%M')}"

# Medical record (EMR)
class MedicalRecord(models.Model):
    RECORD_TYPES = [
        ('consultation', 'Consultation'),
        ('progress_note', 'Progress Note'),
        ('discharge_summary', 'Discharge Summary'),
        ('operation_note', 'Operation Note'),
    ]

    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='medical_records')
    record_type = models.CharField(max_length=30, choices=RECORD_TYPES, default='consultation')
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_records_recorded')
    chief_complaint = models.TextField(blank=True)
    history_present_illness = models.TextField(blank=True)
    examination_findings = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    treatment_plan = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"MR-{self.id} for {self.visit.visit_id}"

# OT (Operation Theatre) Management
class OperationTheatre(models.Model):
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    equipment_details = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Surgery(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='surgeries')
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='surgeries')
    operation_theatre = models.ForeignKey(OperationTheatre, on_delete=models.SET_NULL, null=True)
    primary_surgeon = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='primary_surgeries')
    assisting_surgeons = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='assisting_surgeries')
    anesthesiologist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='anesthesia_cases')
    surgery_name = models.CharField(max_length=255)
    scheduled_date = models.DateTimeField()
    estimated_duration = models.IntegerField(help_text="Duration in minutes")
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    pre_op_notes = models.TextField(blank=True)
    post_op_notes = models.TextField(blank=True)
    complications = models.TextField(blank=True)

    def __str__(self):
        return f"{self.surgery_name} - {self.patient.mrn} - {self.scheduled_date}"

# Prescription & MedicationDispense
class Prescription(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='prescriptions')
    prescribed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='prescriptions_written')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Prescription for {self.visit.patient.mrn} - {self.created_at}"

class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration_days = models.IntegerField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    instructions = models.TextField(blank=True)

class MedicationDispense(models.Model):
    prescription_item = models.ForeignKey(PrescriptionItem,on_delete=models.CASCADE,null=True,blank=True,related_name='dispenses')
    batch_number = models.CharField(max_length=64, blank=True)
    quantity_dispensed = models.DecimalField(max_digits=10, decimal_places=2)
    dispensed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='medication_dispensed')
    dispensed_at = models.DateTimeField(default=timezone.now)
    patient_counseled = models.BooleanField(default=False)

# Pharmacy stock & procurement
class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class PharmacyStock(models.Model):
    medication_name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    batch_number = models.CharField(max_length=64)
    expiry_date = models.DateField(null=True, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    minimum_stock_level = models.DecimalField(max_digits=12, decimal_places=2, default=10)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('medication_name', 'batch_number')

    @property
    def is_low_stock(self):
        return self.quantity <= self.minimum_stock_level

    @property
    def is_expired(self):
        return self.expiry_date and self.expiry_date < timezone.now().date()

class Procurement(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    order_number = models.CharField(max_length=64, unique=True, default='TEMP_ORDER')
    ordered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='procurements_ordered')
    order_date = models.DateField(default=timezone.now)
    expected_delivery = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    invoice_number = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)

class ProcurementItem(models.Model):
    procurement = models.ForeignKey(Procurement, on_delete=models.CASCADE, related_name='items')
    medication_name = models.CharField(max_length=255)
    ordered_quantity = models.DecimalField(max_digits=12, decimal_places=2)
    received_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    batch_number = models.CharField(max_length=64, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

# Lab / Radiology
class LabTest(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    normal_range = models.CharField(max_length=255, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sample_type = models.CharField(max_length=100, blank=True)
    preparation_instructions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class LabOrder(models.Model):
    STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('sample_collected', 'Sample Collected'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='lab_orders')
    tests = models.ManyToManyField(LabTest, through='LabOrderItem')
    ordered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='lab_orders_ordered')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='ordered')
    sample_collected_at = models.DateTimeField(null=True, blank=True)
    sample_collected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='collected_samples')
    priority = models.CharField(max_length=20, choices=[('routine', 'Routine'), ('urgent', 'Urgent'), ('stat', 'STAT')], default='routine')
    created_at = models.DateTimeField(default=timezone.now)

class LabOrderItem(models.Model):
    lab_order = models.ForeignKey(LabOrder, on_delete=models.CASCADE)
    lab_test = models.ForeignKey(LabTest, on_delete=models.CASCADE)
    status = models.CharField(max_length=32, default='ordered')

class LabResult(models.Model):
    lab_order_item = models.ForeignKey(LabOrderItem, on_delete=models.CASCADE, null=True, blank=True)
    result_value = models.CharField(max_length=255, blank=True)
    result_text = models.TextField(blank=True)
    is_abnormal = models.BooleanField(default=False)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='lab_results_reported')
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_results')
    reported_at = models.DateTimeField(default=timezone.now)
    verified_at = models.DateTimeField(null=True, blank=True)

# Radiology
class RadiologyStudy(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, unique=True)
    body_part = models.CharField(max_length=100, blank=True)
    modality = models.CharField(max_length=50)  # X-Ray, CT, MRI, Ultrasound
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    preparation_instructions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class RadiologyOrder(models.Model):
    STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='radiology_orders')
    study = models.ForeignKey(RadiologyStudy, on_delete=models.CASCADE)
    ordered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='radiology_orders_ordered')
    scheduled_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='ordered')
    clinical_indication = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=[('routine', 'Routine'), ('urgent', 'Urgent'), ('stat', 'STAT')], default='routine')
    created_at = models.DateTimeField(default=timezone.now)

class RadiologyReport(models.Model):
    radiology_order = models.OneToOneField(RadiologyOrder, on_delete=models.CASCADE, related_name='report')
    findings = models.TextField()
    impression = models.TextField(default="No impression available")
    recommendations = models.TextField(blank=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='radiology_reports_reported')
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_radiology_reports')
    reported_at = models.DateTimeField(default=timezone.now)
    verified_at = models.DateTimeField(null=True, blank=True)

# Billing / Payments / Invoices / Insurance
class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class TreatmentPackage(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    services = models.ManyToManyField(Service, through='PackageService')
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class PackageService(models.Model):
    package = models.ForeignKey(TreatmentPackage, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='invoices', null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    invoice_number = models.CharField(max_length=64, unique=True)
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices_created')

    class Meta:
        indexes = [models.Index(fields=['invoice_number']), models.Index(fields=['created_at'])]

    @property
    def balance_amount(self):
        return self.total_amount - self.paid_amount

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    package = models.ForeignKey(TreatmentPackage, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('netbanking', 'Net Banking'),
        ('insurance', 'Insurance'),
        ('cheque', 'Cheque'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    payment_number = models.CharField(max_length=50, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default='cash')
    reference_number = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_recorded')
    notes = models.TextField(blank=True)

# Insurance Provider & Claims
class InsuranceProvider(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    claim_submission_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class InsuranceClaim(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('partially_approved', 'Partially Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='insurance_claims')
    provider = models.ForeignKey(InsuranceProvider, on_delete=models.CASCADE, null=True, blank=True)
    claim_number = models.CharField(max_length=128, blank=True)
    policy_number = models.CharField(max_length=100, default='')
    claim_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    submitted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=64, choices=STATUS_CHOICES, default='draft')
    processed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='insurance_claims_submitted')

    def __str__(self):
        return f"Claim {self.claim_number or self.id} - Invoice {self.invoice.invoice_number}"

# System Configuration
class SystemConfiguration(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    data_type = models.CharField(max_length=20, choices=[
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
    ], default='string')
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='system_configurations_updated')

    def __str__(self):
        return f"{self.key} = {self.value}"

# Notification System
class Notification(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_read = models.BooleanField(default=False)
    action_url = models.URLField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"

# Follow-up Management
class FollowUp(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
        ('cancelled', 'Cancelled'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='followups')
    visit = models.ForeignKey(Visit, on_delete=models.SET_NULL, null=True, blank=True)
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followup_patients')
    scheduled_date = models.DateTimeField()
    reason = models.TextField()
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_followups')

    def __str__(self):
        return f"Follow-up: {self.patient.mrn} - {self.scheduled_date}"

# Emergency Contact
class EmergencyContact(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=120)
    relationship = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.patient.mrn}"

class Medication(models.Model):
    name = models.CharField(max_length=255)
    quantity = models.IntegerField(default=0)
    minimum_stock_level = models.IntegerField(default=10)
    
    def __str__(self):
        return self.name
