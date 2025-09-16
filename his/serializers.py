# his/serializers.py
from rest_framework import serializers
from .models import (
    User, Staff, AuditLog, Patient, Visit, MedicalRecord, Department,
    Prescription, PrescriptionItem, MedicationDispense, PharmacyStock, Procurement, ProcurementItem,
    LabOrder, LabOrderItem, LabResult, LabTest, RadiologyOrder, RadiologyReport, RadiologyStudy,
    Invoice, InvoiceItem, Payment, InsuranceClaim, InsuranceProvider, Ward, Bed,
    Appointment, Surgery, OperationTheatre, Vitals, Service, TreatmentPackage,
    LeaveRequest, LeaveType, SystemConfiguration, Notification, FollowUp, EmergencyContact
)

# User Serializer
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 
                  'role', 'phone', 'employee_id', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']
    
    def get_full_name(self, obj):
        return obj.get_full_name()

# Department Serializer
class DepartmentSerializer(serializers.ModelSerializer):
    head_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'head', 'head_name', 'description', 'is_active', 'created_at']
    
    def get_head_name(self, obj):
        return obj.head.get_full_name() if obj.head else None

# Staff Serializer
class StaffSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    department_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Staff
        fields = ['id', 'user', 'user_details', 'staff_id', 'designation', 
                  'department', 'department_name', 'joining_date', 'salary', 
                  'shift_start', 'shift_end', 'active']
    
    def get_department_name(self, obj):
        return obj.department.name if obj.department else None

# AuditLog Serializer
class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = ['id', 'actor', 'actor_name', 'action', 'model', 'object_id', 
                  'timestamp', 'details', 'ip_address']
        read_only_fields = ['id', 'timestamp']
    
    def get_actor_name(self, obj):
        return obj.actor.get_full_name() if obj.actor else 'System'

# EmergencyContact Serializer
class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ['id', 'name', 'relationship', 'phone', 'email', 'address', 'is_primary']

# Patient Serializer
class PatientSerializer(serializers.ModelSerializer):
    age_display = serializers.SerializerMethodField()
    emergency_contacts = EmergencyContactSerializer(many=True, read_only=True)
    active_visits_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = ['uid', 'mrn', 'first_name', 'last_name', 'dob', 'age', 'age_display',
                  'gender', 'blood_group', 'contact_number', 'emergency_contact', 
                  'email', 'address', 'aadhar_number', 'insurance_number', 
                  'allergies', 'medical_history', 'created_at', 'created_by',
                  'emergency_contacts', 'active_visits_count']
        read_only_fields = ['uid', 'created_at', 'created_by']
    
    def get_age_display(self, obj):
        if obj.age:
            return f"{obj.age} years"
        return None
    
    def get_active_visits_count(self, obj):
        return obj.visits.filter(status='active').count()

# Ward Serializer
class WardSerializer(serializers.ModelSerializer):
    available_beds = serializers.ReadOnlyField()
    nurse_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Ward
        fields = ['id', 'name', 'ward_type', 'total_beds', 'available_beds', 
                  'department', 'nurse_in_charge', 'nurse_name', 'is_active']
    
    def get_nurse_name(self, obj):
        return obj.nurse_in_charge.get_full_name() if obj.nurse_in_charge else None

# Bed Serializer
class BedSerializer(serializers.ModelSerializer):
    ward_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Bed
        fields = ['id', 'bed_number', 'ward', 'ward_name', 'is_occupied', 
                  'is_maintenance', 'bed_type', 'daily_rate', 'patient_name']
    
    def get_ward_name(self, obj):
        return obj.ward.name if obj.ward else None
    
    def get_patient_name(self, obj):
        if obj.is_occupied:
            # Assuming Visit model has ForeignKey to Bed with related_name='visits'
            active_visit = obj.visits.filter(status='active').first() if hasattr(obj, 'visits') else None
            if active_visit:
                patient = active_visit.patient
                return f"{patient.first_name} {patient.last_name}"
        return None

# Appointment Serializer
class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'patient_name', 'doctor', 'doctor_name', 
                  'department', 'department_name', 'appointment_date', 
                  'duration_minutes', 'reason', 'status', 'notes', 
                  'created_at', 'created_by']
        read_only_fields = ['id', 'created_at', 'created_by']
    
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"
    
    def get_doctor_name(self, obj):
        return obj.doctor.get_full_name() if obj.doctor else None
    
    def get_department_name(self, obj):
        return obj.department.name if obj.department else None

# Visit Serializer
class VisitSerializer(serializers.ModelSerializer):
    patient_details = PatientSerializer(source='patient', read_only=True)
    doctor_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    bed_info = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Visit
        fields = ['id', 'patient', 'patient_details', 'visit_id', 'visit_type', 
                  'admitted_at', 'discharged_at', 'department', 'department_name',
                  'attending_doctor', 'doctor_name', 'bed', 'bed_info', 'reason', 
                  'status', 'discharge_summary', 'follow_up_date', 'duration']
        read_only_fields = ['id', 'duration']
    
    def get_doctor_name(self, obj):
        return obj.attending_doctor.get_full_name() if obj.attending_doctor else None
    
    def get_department_name(self, obj):
        return obj.department.name if obj.department else None
    
    def get_bed_info(self, obj):
        if obj.bed:
            ward_name = obj.bed.ward.name if obj.bed.ward else ''
            return f"{ward_name} - {obj.bed.bed_number}"
        return None
    
    def get_duration(self, obj):
        if obj.discharged_at and obj.admitted_at:
            duration = obj.discharged_at - obj.admitted_at
            return duration.days
        return None

# Vitals Serializer
class VitalsSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.SerializerMethodField()
    blood_pressure = serializers.SerializerMethodField()
    
    class Meta:
        model = Vitals
        fields = ['id', 'visit', 'recorded_by', 'recorded_by_name', 'temperature', 
                  'pulse', 'systolic_bp', 'diastolic_bp', 'blood_pressure',
                  'respiratory_rate', 'oxygen_saturation', 'blood_sugar', 
                  'weight', 'height', 'notes', 'recorded_at']
        read_only_fields = ['id', 'recorded_at', 'recorded_by']
    
    def get_recorded_by_name(self, obj):
        return obj.recorded_by.get_full_name() if obj.recorded_by else None
    
    def get_blood_pressure(self, obj):
        if obj.systolic_bp and obj.diastolic_bp:
            return f"{obj.systolic_bp}/{obj.diastolic_bp}"
        return None

# MedicalRecord Serializer
class MedicalRecordSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.SerializerMethodField()
    visit_info = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalRecord
        fields = ['id', 'visit', 'visit_info', 'record_type', 'recorded_by', 
                  'recorded_by_name', 'chief_complaint', 'history_present_illness',
                  'examination_findings', 'diagnosis', 'treatment_plan', 
                  'notes', 'created_at']
        read_only_fields = ['id', 'created_at', 'recorded_by']
    
    def get_recorded_by_name(self, obj):
        return obj.recorded_by.get_full_name() if obj.recorded_by else None
    
    def get_visit_info(self, obj):
        return f"{obj.visit.visit_id} - {obj.visit.patient.mrn}"

# PrescriptionItem Serializer
class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = ['id', 'medication_name', 'dosage', 'frequency', 'duration_days', 
                  'quantity', 'instructions']

# Prescription Serializer
class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, read_only=True)
    prescribed_by_name = serializers.SerializerMethodField()
    visit_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = ['id', 'visit', 'visit_info', 'prescribed_by', 'prescribed_by_name', 
                  'notes', 'created_at', 'items']
        read_only_fields = ['id', 'created_at', 'prescribed_by']
    
    def get_prescribed_by_name(self, obj):
        return obj.prescribed_by.get_full_name() if obj.prescribed_by else None
    
    def get_visit_info(self, obj):
        return f"{obj.visit.visit_id} - {obj.visit.patient.mrn}"

# MedicationDispense Serializer
class MedicationDispenseSerializer(serializers.ModelSerializer):
    medication_name = serializers.SerializerMethodField()
    patient_info = serializers.SerializerMethodField()
    dispensed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicationDispense
        fields = ['id', 'prescription_item', 'medication_name', 'batch_number', 
                  'quantity_dispensed', 'dispensed_by', 'dispensed_by_name',
                  'dispensed_at', 'patient_counseled', 'patient_info']
        read_only_fields = ['id', 'dispensed_at', 'dispensed_by']
    
    def get_medication_name(self, obj):
        return obj.prescription_item.medication_name if obj.prescription_item else None
    
    def get_patient_info(self, obj):
        if obj.prescription_item and obj.prescription_item.prescription and obj.prescription_item.prescription.visit:
            patient = obj.prescription_item.prescription.visit.patient
            return f"{patient.mrn} - {patient.first_name} {patient.last_name}"
        return None
    
    def get_dispensed_by_name(self, obj):
        return obj.dispensed_by.get_full_name() if obj.dispensed_by else None

# PharmacyStock Serializer
class PharmacyStockSerializer(serializers.ModelSerializer):
    stock_status = serializers.SerializerMethodField()
    expiry_status = serializers.SerializerMethodField()
    
    class Meta:
        model = PharmacyStock
        fields = ['id', 'medication_name', 'generic_name', 'manufacturer', 
                  'batch_number', 'expiry_date', 'quantity', 'unit_price', 
                  'selling_price', 'minimum_stock_level', 'last_updated',
                  'stock_status', 'expiry_status']
    
    def get_stock_status(self, obj):
        return 'low' if obj.is_low_stock else 'normal'
    
    def get_expiry_status(self, obj):
        return 'expired' if obj.is_expired else 'valid'

# ProcurementItem Serializer
class ProcurementItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcurementItem
        fields = ['id', 'medication_name', 'ordered_quantity', 'received_quantity', 
                  'unit_price', 'batch_number', 'expiry_date']

# Procurement Serializer
class ProcurementSerializer(serializers.ModelSerializer):
    items = ProcurementItemSerializer(many=True, read_only=True)
    supplier_name = serializers.SerializerMethodField()
    ordered_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Procurement
        fields = ['id', 'supplier', 'supplier_name', 'order_number', 'ordered_by', 
                  'ordered_by_name', 'order_date', 'expected_delivery', 'received_date',
                  'status', 'total_amount', 'invoice_number', 'notes', 'items']
        read_only_fields = ['id', 'ordered_by']
    
    def get_supplier_name(self, obj):
        return obj.supplier.name if obj.supplier else None
    
    def get_ordered_by_name(self, obj):
        return obj.ordered_by.get_full_name() if obj.ordered_by else None

# LabTest Serializer
class LabTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTest
        fields = ['id', 'name', 'code', 'department', 'normal_range', 'unit', 
                  'price', 'sample_type', 'preparation_instructions', 'is_active']

# LabOrderItem Serializer
class LabOrderItemSerializer(serializers.ModelSerializer):
    test_details = LabTestSerializer(source='lab_test', read_only=True)
    result = serializers.SerializerMethodField()
    
    class Meta:
        model = LabOrderItem
        fields = ['id', 'lab_test', 'test_details', 'status', 'result']
    
    def get_result(self, obj):
        if hasattr(obj, 'result'):
            return {
                'value': obj.result.result_value,
                'text': obj.result.result_text,
                'is_abnormal': obj.result.is_abnormal,
                'reported_at': obj.result.reported_at
            }
        return None

# LabOrder Serializer
class LabOrderSerializer(serializers.ModelSerializer):
    items = LabOrderItemSerializer(source='laborderitem_set', many=True, read_only=True)
    ordered_by_name = serializers.SerializerMethodField()
    patient_info = serializers.SerializerMethodField()
    sample_collected_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = LabOrder
        fields = ['id', 'visit', 'patient_info', 'ordered_by', 'ordered_by_name',
                  'status', 'sample_collected_at', 'sample_collected_by',
                  'sample_collected_by_name', 'priority', 'created_at', 'items']
        read_only_fields = ['id', 'created_at', 'ordered_by']
    
    def get_ordered_by_name(self, obj):
        return obj.ordered_by.get_full_name() if obj.ordered_by else None
    
    def get_patient_info(self, obj):
        return f"{obj.visit.patient.mrn} - {obj.visit.patient.first_name} {obj.visit.patient.last_name}"
    
    def get_sample_collected_by_name(self, obj):
        return obj.sample_collected_by.get_full_name() if obj.sample_collected_by else None

# LabResult Serializer
class LabResultSerializer(serializers.ModelSerializer):
    test_name = serializers.SerializerMethodField()
    patient_info = serializers.SerializerMethodField()
    reported_by_name = serializers.SerializerMethodField()
    verified_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = LabResult
        fields = ['id', 'lab_order_item', 'test_name', 'patient_info', 'result_value', 
                  'result_text', 'is_abnormal', 'reported_by', 'reported_by_name',
                  'verified_by', 'verified_by_name', 'reported_at', 'verified_at']
        read_only_fields = ['id', 'reported_at', 'reported_by']
    
    def get_test_name(self, obj):
        return obj.lab_order_item.lab_test.name if obj.lab_order_item and obj.lab_order_item.lab_test else None
    
    def get_patient_info(self, obj):
        patient = None
        if obj.lab_order_item and obj.lab_order_item.lab_order and obj.lab_order_item.lab_order.visit:
            patient = obj.lab_order_item.lab_order.visit.patient
        if patient:
            return f"{patient.mrn} - {patient.first_name} {patient.last_name}"
        return None
    
    def get_reported_by_name(self, obj):
        return obj.reported_by.get_full_name() if obj.reported_by else None
    
    def get_verified_by_name(self, obj):
        return obj.verified_by.get_full_name() if obj.verified_by else None

# RadiologyStudy Serializer
class RadiologyStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = RadiologyStudy
        fields = ['id', 'name', 'code', 'body_part', 'modality', 'price', 
                  'preparation_instructions', 'is_active']

# RadiologyOrder Serializer
class RadiologyOrderSerializer(serializers.ModelSerializer):
    study_details = RadiologyStudySerializer(source='study', read_only=True)
    ordered_by_name = serializers.SerializerMethodField()
    patient_info = serializers.SerializerMethodField()
    
    class Meta:
        model = RadiologyOrder
        fields = ['id', 'visit', 'patient_info', 'study', 'study_details',
                  'ordered_by', 'ordered_by_name', 'scheduled_date', 'completed_at',
                  'status', 'clinical_indication', 'priority', 'created_at']
        read_only_fields = ['id', 'created_at', 'ordered_by']
    
    def get_ordered_by_name(self, obj):
        return obj.ordered_by.get_full_name() if obj.ordered_by else None
    
    def get_patient_info(self, obj):
        return f"{obj.visit.patient.mrn} - {obj.visit.patient.first_name} {obj.visit.patient.last_name}"

# RadiologyReport Serializer
class RadiologyReportSerializer(serializers.ModelSerializer):
    study_name = serializers.SerializerMethodField()
    patient_info = serializers.SerializerMethodField()
    reported_by_name = serializers.SerializerMethodField()
    verified_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = RadiologyReport
        fields = ['id', 'radiology_order', 'study_name', 'patient_info', 'findings', 
                  'impression', 'recommendations', 'reported_by', 'reported_by_name',
                  'verified_by', 'verified_by_name', 'reported_at', 'verified_at']
        read_only_fields = ['id', 'reported_at', 'reported_by']
    
    def get_study_name(self, obj):
        return obj.radiology_order.study.name if obj.radiology_order and obj.radiology_order.study else None
    
    def get_patient_info(self, obj):
        patient = None
        if obj.radiology_order and obj.radiology_order.visit:
            patient = obj.radiology_order.visit.patient
        if patient:
            return f"{patient.mrn} - {patient.first_name} {patient.last_name}"
        return None

    def get_reported_by_name(self, obj):
        return obj.reported_by.get_full_name() if obj.reported_by else None

    def get_verified_by_name(self, obj):
        return obj.verified_by.get_full_name() if obj.verified_by else None

class ServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = ['id', 'name', 'code', 'category', 'category_name', 'price',
                  'department', 'department_name', 'is_active']

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_department_name(self, obj):
        return obj.department.name if obj.department else None

class InvoiceItemSerializer(serializers.ModelSerializer):
    service_name = serializers.SerializerMethodField()
    package_name = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceItem
        fields = ['id', 'service', 'service_name', 'package', 'package_name',
                  'description', 'quantity', 'unit_price', 'total_price']

    def get_service_name(self, obj):
        return obj.service.name if obj.service else None

    def get_package_name(self, obj):
        return obj.package.name if obj.package else None

class PaymentSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.SerializerMethodField()
    invoice_number = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ['id', 'invoice', 'invoice_number', 'payment_number', 'amount',
                  'method', 'reference_number', 'paid_at', 'recorded_by',
                  'recorded_by_name', 'notes']
        read_only_fields = ['id', 'paid_at', 'recorded_by']

    def get_recorded_by_name(self, obj):
        return obj.recorded_by.get_full_name() if obj.recorded_by else None

    def get_invoice_number(self, obj):
        return obj.invoice.invoice_number if obj.invoice else None

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    patient_name = serializers.SerializerMethodField()
    visit_info = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    balance_amount = serializers.ReadOnlyField()

    class Meta:
        model = Invoice
        fields = ['id', 'visit', 'visit_info', 'patient', 'patient_name',
                  'invoice_number', 'invoice_date', 'due_date', 'subtotal',
                  'tax_amount', 'discount_amount', 'total_amount', 'paid_amount',
                  'balance_amount', 'status', 'notes', 'created_at', 'created_by',
                  'created_by_name', 'items', 'payments']
        read_only_fields = ['id', 'created_at', 'created_by', 'balance_amount']

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return None

    def get_visit_info(self, obj):
        return obj.visit.visit_id if obj.visit else None

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

class InsuranceClaimSerializer(serializers.ModelSerializer):
    provider_name = serializers.SerializerMethodField()
    invoice_number = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    submitted_by_name = serializers.SerializerMethodField()

    class Meta:
        model = InsuranceClaim
        fields = ['id', 'invoice', 'invoice_number', 'patient_name', 'provider',
                  'provider_name', 'claim_number', 'policy_number', 'claim_amount',
                  'approved_amount', 'submitted_at', 'status', 'processed_at',
                  'rejection_reason', 'notes', 'submitted_by', 'submitted_by_name']
        read_only_fields = ['id', 'submitted_at', 'submitted_by']

    def get_provider_name(self, obj):
        return obj.provider.name if obj.provider else None

    def get_invoice_number(self, obj):
        return obj.invoice.invoice_number if obj.invoice else None

    def get_patient_name(self, obj):
        if obj.invoice and obj.invoice.patient:
            return f"{obj.invoice.patient.first_name} {obj.invoice.patient.last_name}"
        return None

    def get_submitted_by_name(self, obj):
        return obj.submitted_by.get_full_name() if obj.submitted_by else None

class LeaveRequestSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    leave_type_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    duration_days = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = ['id', 'staff', 'staff_name', 'leave_type', 'leave_type_name',
                  'start_date', 'end_date', 'duration_days', 'reason', 'status',
                  'approved_by', 'approved_by_name', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_staff_name(self, obj):
        if obj.staff and obj.staff.user:
            return obj.staff.user.get_full_name()
        return None

    def get_leave_type_name(self, obj):
        return obj.leave_type.name if obj.leave_type else None

    def get_approved_by_name(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else None

    def get_duration_days(self, obj):
        if obj.start_date and obj.end_date:
            return (obj.end_date - obj.start_date).days + 1
        return None

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'priority', 'is_read', 'action_url',
                  'created_at', 'read_at']
        read_only_fields = ['id', 'created_at']

class FollowUpSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = FollowUp
        fields = ['id', 'patient', 'patient_name', 'visit', 'doctor', 'doctor_name',
                  'scheduled_date', 'reason', 'instructions', 'status', 'completed_at',
                  'notes', 'created_at', 'created_by']
        read_only_fields = ['id', 'created_at', 'created_by']

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return None

    def get_doctor_name(self, obj):
        return obj.doctor.get_full_name() if obj.doctor else None
