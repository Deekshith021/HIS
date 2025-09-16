# his/views.py
from rest_framework import viewsets, permissions, filters, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.views.generic import TemplateView, ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.db.models import Q, Count, Sum, F
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
import uuid
from django.contrib.auth import get_user_model
from django.conf import settings


from .models import (
    User, Staff, AuditLog, Patient, Visit, MedicalRecord, Department,
    Prescription, PrescriptionItem, MedicationDispense, PharmacyStock, Procurement, ProcurementItem,
    LabOrder, LabOrderItem, LabResult, LabTest, RadiologyOrder, RadiologyReport, RadiologyStudy,
    Invoice, InvoiceItem, Payment, InsuranceClaim, InsuranceProvider, Role, Ward, Bed,
    Appointment, Surgery, OperationTheatre, Vitals, Service, TreatmentPackage,
    LeaveRequest, LeaveType, SystemConfiguration, Notification, FollowUp, EmergencyContact
)
from .serializers import (
    UserSerializer, StaffSerializer, AuditLogSerializer, PatientSerializer, VisitSerializer, MedicalRecordSerializer,
    PrescriptionSerializer, MedicationDispenseSerializer, PharmacyStockSerializer, ProcurementSerializer,
    LabOrderSerializer, LabResultSerializer, RadiologyOrderSerializer, RadiologyReportSerializer,
    InvoiceSerializer, PaymentSerializer, InsuranceClaimSerializer, AppointmentSerializer, VitalsSerializer
)

# Custom Pagination
class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

# Permission helpers
class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.ADMIN)

class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.DOCTOR)

class IsNurse(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.NURSE)

class IsPharmacist(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.PHARMACIST)

class IsFinance(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.FINANCE)

class IsLab(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.LAB)

# Utility Functions
def generate_mrn():
    """Generate unique MRN"""
    today = timezone.now().date()
    prefix = today.strftime("%y%m%d")
    last_patient = Patient.objects.filter(mrn__startswith=prefix).order_by('mrn').last()
    if last_patient:
        last_number = int(last_patient.mrn[-4:])
        new_number = last_number + 1
    else:
        new_number = 1
    return f"{prefix}{new_number:04d}"

def generate_visit_id():
    """Generate unique visit ID"""
    today = timezone.now().date()
    prefix = f"V{today.strftime('%y%m%d')}"
    last_visit = Visit.objects.filter(visit_id__startswith=prefix).order_by('visit_id').last()
    if last_visit:
        last_number = int(last_visit.visit_id[-4:])
        new_number = last_number + 1
    else:
        new_number = 1
    return f"{prefix}{new_number:04d}"

def generate_invoice_number():
    """Generate unique invoice number"""
    today = timezone.now().date()
    prefix = f"INV{today.strftime('%y%m%d')}"
    last_invoice = Invoice.objects.filter(invoice_number__startswith=prefix).order_by('invoice_number').last()
    if last_invoice:
        last_number = int(last_invoice.invoice_number[-4:])
        new_number = last_number + 1
    else:
        new_number = 1
    return f"{prefix}{new_number:04d}"

# API ViewSets
User = get_user_model()   # always use the swapped user model

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'first_name', 'last_name', 'email', 'role']

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get('new_password', 'password123')
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password reset successfully'})


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    permission_classes = [IsAdmin]
    pagination_class = CustomPagination

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by('-created_at')
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['mrn', 'first_name', 'last_name', 'contact_number', 'aadhar_number']

    def perform_create(self, serializer):
        if not serializer.validated_data.get('mrn'):
            serializer.validated_data['mrn'] = generate_mrn()
        serializer.validated_data['created_by'] = self.request.user
        serializer.save()

    @action(detail=True, methods=['get'])
    def medical_history(self, request, pk=None):
        patient = self.get_object()
        visits = patient.visits.all().order_by('-admitted_at')[:10]
        visit_serializer = VisitSerializer(visits, many=True)
        return Response(visit_serializer.data)

    @action(detail=True, methods=['get'])
    def active_visits(self, request, pk=None):
        patient = self.get_object()
        active_visits = patient.visits.filter(status='active')
        visit_serializer = VisitSerializer(active_visits, many=True)
        return Response(visit_serializer.data)

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all().order_by('-appointment_date')
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = self.queryset
        if self.request.user.role == Role.DOCTOR:
            queryset = queryset.filter(doctor=self.request.user)
        elif self.request.user.role == Role.PATIENT:
            # Assuming patient has a linked Patient record
            try:
                patient = Patient.objects.get(email=self.request.user.email)
                queryset = queryset.filter(patient=patient)
            except Patient.DoesNotExist:
                queryset = queryset.none()
        return queryset

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        appointment = self.get_object()
        appointment.status = 'confirmed'
        appointment.save()
        return Response({'detail': 'Appointment confirmed'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        appointment.status = 'cancelled'
        appointment.save()
        return Response({'detail': 'Appointment cancelled'})

class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.all().order_by('-admitted_at')
    serializer_class = VisitSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        if not serializer.validated_data.get('visit_id'):
            serializer.validated_data['visit_id'] = generate_visit_id()
        serializer.save()

    @action(detail=True, methods=['post'])
    def discharge(self, request, pk=None):
        visit = self.get_object()
        visit.discharged_at = timezone.now()
        visit.status = 'discharged'
        visit.discharge_summary = request.data.get('discharge_summary', '')
        if visit.bed:
            visit.bed.is_occupied = False
            visit.bed.save()
        visit.save()
        return Response({'detail': 'Patient discharged successfully'})

class VitalsViewSet(viewsets.ModelViewSet):
    queryset = Vitals.objects.all().order_by('-recorded_at')
    serializer_class = VitalsSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.validated_data['recorded_by'] = self.request.user
        serializer.save()

class MedicalRecordViewSet(viewsets.ModelViewSet):
    queryset = MedicalRecord.objects.all().order_by('-created_at')
    serializer_class = MedicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.validated_data['recorded_by'] = self.request.user
        serializer.save()

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all().order_by('-created_at')
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.validated_data['prescribed_by'] = self.request.user
        serializer.save()

    @action(detail=True, methods=['post'])
    def dispense_all(self, request, pk=None):
        prescription = self.get_object()
        dispensed_items = []
        for item in prescription.items.all():
            dispense = MedicationDispense.objects.create(
                prescription_item=item,
                quantity_dispensed=item.quantity,
                dispensed_by=request.user,
                patient_counseled=request.data.get('patient_counseled', False)
            )
            dispensed_items.append(dispense.id)
        return Response({'detail': 'All items dispensed', 'dispensed_items': dispensed_items})

class MedicationDispenseViewSet(viewsets.ModelViewSet):
    queryset = MedicationDispense.objects.all().order_by('-dispensed_at')
    serializer_class = MedicationDispenseSerializer
    permission_classes = [IsPharmacist]
    pagination_class = CustomPagination

class PharmacyStockViewSet(viewsets.ModelViewSet):
    queryset = PharmacyStock.objects.all().order_by('medication_name')
    serializer_class = PharmacyStockSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        low_stock_items = self.queryset.filter(quantity__lte=F('minimum_stock_level'))
        serializer = self.get_serializer(low_stock_items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expired(self, request):
        expired_items = self.queryset.filter(expiry_date__lt=timezone.now().date())
        serializer = self.get_serializer(expired_items, many=True)
        return Response(serializer.data)

class LabOrderViewSet(viewsets.ModelViewSet):
    queryset = LabOrder.objects.all().order_by('-created_at')
    serializer_class = LabOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.validated_data['ordered_by'] = self.request.user
        serializer.save()

    @action(detail=True, methods=['post'])
    def collect_sample(self, request, pk=None):
        lab_order = self.get_object()
        lab_order.sample_collected_at = timezone.now()
        lab_order.sample_collected_by = request.user
        lab_order.status = 'sample_collected'
        lab_order.save()
        return Response({'detail': 'Sample collected successfully'})

class LabResultViewSet(viewsets.ModelViewSet):
    queryset = LabResult.objects.all().order_by('-reported_at')
    serializer_class = LabResultSerializer
    permission_classes = [IsLab]
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.validated_data['reported_by'] = self.request.user
        serializer.save()

class RadiologyOrderViewSet(viewsets.ModelViewSet):
    queryset = RadiologyOrder.objects.all().order_by('-created_at')
    serializer_class = RadiologyOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.validated_data['ordered_by'] = self.request.user
        serializer.save()

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all().order_by('-created_at')
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        if not serializer.validated_data.get('invoice_number'):
            serializer.validated_data['invoice_number'] = generate_invoice_number()
        serializer.validated_data['created_by'] = self.request.user
        serializer.save()

    @action(detail=True, methods=['post'])
    def add_payment(self, request, pk=None):
        invoice = self.get_object()
        amount = float(request.data.get('amount', 0))
        method = request.data.get('method', 'cash')
        
        payment = Payment.objects.create(
            invoice=invoice,
            payment_number=f"PAY{timezone.now().strftime('%y%m%d%H%M%S')}",
            amount=amount,
            method=method,
            recorded_by=request.user
        )
        
        invoice.paid_amount += amount
        if invoice.paid_amount >= invoice.total_amount:
            invoice.status = 'paid'
        elif invoice.paid_amount > 0:
            invoice.status = 'partially_paid'
        invoice.save()
        
        return Response({'detail': 'Payment recorded', 'payment_id': payment.id})

# Authentication Views
class LoginPageView(View):
    template_name = 'login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # Log the login
            AuditLog.objects.create(
                actor=user,
                action='LOGIN',
                details={'ip_address': request.META.get('REMOTE_ADDR')},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return redirect('dashboard')
        else:
            return render(request, self.template_name, {'error': 'Invalid credentials'})

class LogoutView(View):
    def get(self, request):
        if request.user.is_authenticated:
            AuditLog.objects.create(
                actor=request.user,
                action='LOGOUT',
                details={'ip_address': request.META.get('REMOTE_ADDR')},
                ip_address=request.META.get('REMOTE_ADDR')
            )
        logout(request)
        return redirect('/')

# Dashboard Views
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'
    login_url = '/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        
        # Common stats
        context.update({
            'total_patients': Patient.objects.count(),
            'active_visits': Visit.objects.filter(status='active').count(),
            'today_appointments': Appointment.objects.filter(
                appointment_date__date=today
            ).count(),
        })
        
        # Role-specific data
        if user.role == Role.ADMIN:
            context.update({
                'total_staff': Staff.objects.filter(active=True).count(),
                'pending_leave_requests': LeaveRequest.objects.filter(status='pending').count(),
                'low_stock_items': PharmacyStock.objects.filter(
                    quantity__lte=F('minimum_stock_level')
                ).count(),
            })
        
        elif user.role == Role.DOCTOR:
            context.update({
                'my_appointments_today': Appointment.objects.filter(
                    doctor=user, appointment_date__date=today
                ).count(),
                'my_patients': Visit.objects.filter(
                    attending_doctor=user, status='active'
                ).count(),
            })
        
        elif user.role == Role.NURSE:
            context.update({
                'patients_in_ward': Visit.objects.filter(
                    status='active', bed__ward__nurse_in_charge=user
                ).count(),
                'vitals_pending': Visit.objects.filter(
                    status='active', vitals__recorded_at__date__lt=today
                ).count(),
            })
        
        elif user.role == Role.FINANCE:
            context.update({
                'pending_invoices': Invoice.objects.filter(status='sent').count(),
                'today_revenue': Payment.objects.filter(
                    paid_at__date=today
                ).aggregate(total=Sum('amount'))['total'] or 0,
            })
        
        return context

# Patient Management Views
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db import transaction
from .models import Patient, MRNCounter, Visit, Appointment, Department, User, Role


def generate_visit_id():
    # Replace with your actual logic for generating visit IDs
    import uuid
    return str(uuid.uuid4())[:8].upper()


class OPRegistrationView(LoginRequiredMixin, View):
    template_name = 'patient/op_registration.html'

    def get(self, request):
        departments = Department.objects.filter(is_active=True)
        doctors = User.objects.filter(role=Role.DOCTOR, is_active=True)
        return render(request, self.template_name, {
            'departments': departments,
            'doctors': doctors
        })

    def post(self, request):
        with transaction.atomic():  # ensure MRN is unique even under concurrency
            # Generate MRN
            year = timezone.now().year
            counter, created = MRNCounter.objects.select_for_update().get_or_create(year=year)
            counter.last_seq += 1
            counter.save()
            mrn = f"MRN{year}{counter.last_seq:04d}"

            # Create patient
            patient = Patient.objects.create(
                mrn=mrn,
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name', ''),
                age=request.POST.get('age') or None,
                gender=request.POST.get('gender', ''),
                contact_number=request.POST.get('contact_number', ''),
                address=request.POST.get('address', ''),
                created_by=request.user
            )

        # Create visit
        visit = Visit.objects.create(
            patient=patient,
            visit_id=generate_visit_id(),
            visit_type='opd',
            department_id=request.POST.get('department'),
            attending_doctor_id=request.POST.get('doctor'),
            reason=request.POST.get('reason', '')
        )

        # Create appointment if provided
        if request.POST.get('appointment_date'):
            Appointment.objects.create(
                patient=patient,
                doctor_id=request.POST.get('doctor'),
                appointment_date=request.POST.get('appointment_date'),
                reason=request.POST.get('reason', ''),
                created_by=request.user
            )

        return redirect('patient-detail', pk=patient.uid)


class EmergencyRegistrationView(LoginRequiredMixin, View):
    template_name = 'patient/emergency_registration.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # Quick emergency registration with minimal data
        patient = Patient.objects.create(
            mrn=generate_mrn(),
            first_name=request.POST.get('first_name', 'Emergency'),
            age=request.POST.get('age'),
            gender=request.POST.get('gender', ''),
            contact_number=request.POST.get('contact_number', ''),
            created_by=request.user
        )
        
        visit = Visit.objects.create(
            patient=patient,
            visit_id=generate_visit_id(),
            visit_type='emergency',
            reason=request.POST.get('reason', 'Emergency admission')
        )
        
        return JsonResponse({
            'status': 'success',
            'patient_id': str(patient.uid),
            'mrn': patient.mrn,
            'visit_id': visit.visit_id
        })

# Specialized Views for different roles
class WardManagementView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'nurse/ward_management.html'

    def test_func(self):
        return self.request.user.role in [Role.NURSE, Role.ADMIN]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['wards'] = Ward.objects.filter(is_active=True).prefetch_related('beds')
        context['active_patients'] = Visit.objects.filter(
            status='active', visit_type='ipd'
        ).select_related('patient', 'bed__ward')
        return context

from django.db.models import Count

class PharmacyDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'pharmacy/dashboard.html'

    def test_func(self):
        return self.request.user.role in [Role.PHARMACIST, Role.ADMIN]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fix pending prescriptions
        pending_count = Prescription.objects.annotate(
            dispensed_count=Count('items__dispenses')
        ).filter(dispensed_count=0).count()
        
        context.update({
            'pending_prescriptions': pending_count,
            'low_stock_count': PharmacyStock.objects.filter(
                quantity__lte=F('minimum_stock_level')
            ).count(),
            'expired_items': PharmacyStock.objects.filter(
                expiry_date__lt=timezone.now().date()
            ).count(),
            'recent_dispenses': MedicationDispense.objects.filter(
                dispensed_at__date=timezone.now().date()
            ).count()
        })
        return context

class LabDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'lab/dashboard.html'

    def test_func(self):
        return self.request.user.role in [Role.LAB, Role.ADMIN]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'pending_orders': LabOrder.objects.filter(status='ordered').count(),
            'sample_collection_pending': LabOrder.objects.filter(
                status='ordered'
            ).count(),
            'results_pending': LabOrder.objects.filter(
                status__in=['sample_collected', 'in_progress']
            ).count(),
            'today_completed': LabResult.objects.filter(
                reported_at__date=timezone.now().date()
            ).count()
        })
        return context

class SystemConfigView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'admin/system_config.html'

    def test_func(self):
        return self.request.user.role == Role.ADMIN

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['configurations'] = SystemConfiguration.objects.filter(is_active=True)
        return context

# Appointment Management Views
class AppointmentListView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = 'appointment/list.html'
    context_object_name = 'appointments'
    paginate_by = 20

    def get_queryset(self):
        queryset = Appointment.objects.all().order_by('appointment_date')
        if self.request.user.role == Role.DOCTOR:
            queryset = queryset.filter(doctor=self.request.user)
        return queryset

class AppointmentCreateView(LoginRequiredMixin, CreateView):
    model = Appointment
    template_name = 'appointment/create.html'
    fields = ['patient', 'doctor', 'department', 'appointment_date', 'reason']

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

# Billing and Finance Views
class BillingDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'finance/dashboard.html'

    def test_func(self):
        return self.request.user.role in [Role.FINANCE, Role.ADMIN]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        context.update({
            'pending_invoices': Invoice.objects.filter(status='sent').count(),
            'overdue_invoices': Invoice.objects.filter(
                status='sent', due_date__lt=today
            ).count(),
            'today_revenue': Payment.objects.filter(
                paid_at__date=today
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'monthly_revenue': Payment.objects.filter(
                paid_at__month=today.month, paid_at__year=today.year
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'pending_insurance_claims': InsuranceClaim.objects.filter(
                status='submitted'
            ).count()
        })
        return context

class InvoiceCreateView(LoginRequiredMixin, View):
    template_name = 'finance/invoice_create.html'

    def get(self, request):
        visits = Visit.objects.filter(status='active')
        services = Service.objects.filter(is_active=True)
        packages = TreatmentPackage.objects.filter(is_active=True)
        return render(request, self.template_name, {
            'visits': visits,
            'services': services,
            'packages': packages
        })

    def post(self, request):
        visit_id = request.POST.get('visit')
        visit = get_object_or_404(Visit, id=visit_id)
        
        # Create invoice
        invoice = Invoice.objects.create(
            visit=visit,
            patient=visit.patient,
            invoice_number=generate_invoice_number(),
            created_by=request.user
        )
        
        # Add services
        total_amount = 0
        service_ids = request.POST.getlist('services')
        for service_id in service_ids:
            service = Service.objects.get(id=service_id)
            quantity = int(request.POST.get(f'quantity_{service_id}', 1))
            
            InvoiceItem.objects.create(
                invoice=invoice,
                service=service,
                description=service.name,
                quantity=quantity,
                unit_price=service.price,
                total_price=service.price * quantity
            )
            total_amount += service.price * quantity
        
        # Update invoice total
        invoice.subtotal = total_amount
        invoice.tax_amount = total_amount * 0.18  # 18% GST
        invoice.total_amount = total_amount + invoice.tax_amount
        invoice.save()
        
        return redirect('invoice-detail', pk=invoice.id)

# Analytics and Reporting Views
class AnalyticsDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'analytics/dashboard.html'

    def test_func(self):
        return self.request.user.role in [Role.ADMIN, Role.FINANCE]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Date ranges
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)
        last_month = today.replace(day=1) - timedelta(days=1)
        
        # Patient Analytics
        context.update({
            'total_patients': Patient.objects.count(),
            'new_patients_month': Patient.objects.filter(
                created_at__date__gte=last_30_days
            ).count(),
            'active_visits': Visit.objects.filter(status='active').count(),
            'today_admissions': Visit.objects.filter(
                admitted_at__date=today
            ).count(),
            'today_discharges': Visit.objects.filter(
                discharged_at__date=today
            ).count(),
        })
        
        # Financial Analytics
        monthly_revenue = Payment.objects.filter(
            paid_at__month=today.month,
            paid_at__year=today.year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        outstanding_amount = Invoice.objects.exclude(
            status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        context.update({
            'monthly_revenue': monthly_revenue,
            'outstanding_amount': outstanding_amount,
            'insurance_pending': InsuranceClaim.objects.filter(
                status__in=['submitted', 'under_review']
            ).aggregate(total=Sum('claim_amount'))['total'] or 0
        })
        
        # Operational Analytics
        bed_occupancy = Bed.objects.filter(is_occupied=True).count()
        total_beds = Bed.objects.filter(is_maintenance=False).count()
        occupancy_rate = (bed_occupancy / total_beds * 100) if total_beds > 0 else 0
        
        context.update({
            'bed_occupancy_rate': round(occupancy_rate, 1),
            'occupied_beds': bed_occupancy,
            'total_beds': total_beds,
        })
        
        return context

# API Views for AJAX requests
class PatientSearchAPIView(generics.ListAPIView):
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        if len(query) >= 3:
            return Patient.objects.filter(
                Q(mrn__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(contact_number__icontains=query)
            )[:10]
        return Patient.objects.none()

class DoctorAvailabilityAPIView(View):
    def get(self, request):
        doctor_id = request.GET.get('doctor_id')
        date = request.GET.get('date')
        
        if not doctor_id or not date:
            return JsonResponse({'error': 'Missing parameters'})
        
        # Get existing appointments for the doctor on that date
        existing_appointments = Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_date__date=date
        ).values_list('appointment_date', flat=True)
        
        # Generate available slots (9 AM to 5 PM, 30-min slots)
        available_slots = []
        start_time = datetime.strptime(f"{date} 09:00", "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(f"{date} 17:00", "%Y-%m-%d %H:%M")
        
        current_time = start_time
        while current_time < end_time:
            if current_time not in existing_appointments:
                available_slots.append(current_time.strftime("%H:%M"))
            current_time += timedelta(minutes=30)
        
        return JsonResponse({'available_slots': available_slots})

class NotificationAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).order_by('-created_at')[:10]
        
        data = [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'priority': n.priority,
            'created_at': n.created_at.isoformat(),
            'action_url': n.action_url
        } for n in notifications]
        
        return JsonResponse({'notifications': data})

    def post(self, request):
        notification_id = request.data.get('notification_id')
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=request.user
            )
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            return JsonResponse({'status': 'success'})
        except Notification.DoesNotExist:
            return JsonResponse({'error': 'Notification not found'})

# Ward and Bed Management
class BedAssignmentView(LoginRequiredMixin, View):
    def post(self, request):
        visit_id = request.POST.get('visit_id')
        bed_id = request.POST.get('bed_id')
        
        try:
            visit = Visit.objects.get(id=visit_id)
            bed = Bed.objects.get(id=bed_id)
            
            if bed.is_occupied:
                return JsonResponse({'error': 'Bed is already occupied'})
            
            # Free up previous bed if any
            if visit.bed:
                visit.bed.is_occupied = False
                visit.bed.save()
            
            # Assign new bed
            visit.bed = bed
            visit.save()
            
            bed.is_occupied = True
            bed.save()
            
            return JsonResponse({'status': 'success', 'message': 'Bed assigned successfully'})
        
        except (Visit.DoesNotExist, Bed.DoesNotExist):
            return JsonResponse({'error': 'Visit or bed not found'})

# Report Generation Views
class PatientReportView(LoginRequiredMixin, View):
    def get(self, request, patient_id):
        patient = get_object_or_404(Patient, uid=patient_id)
        visits = patient.visits.all().order_by('-admitted_at')
        
        context = {
            'patient': patient,
            'visits': visits,
            'medical_records': MedicalRecord.objects.filter(visit__patient=patient),
            'prescriptions': Prescription.objects.filter(visit__patient=patient),
            'lab_results': LabResult.objects.filter(
                lab_order_item__lab_order__visit__patient=patient
            ),
            'radiology_reports': RadiologyReport.objects.filter(
                radiology_order__visit__patient=patient
            )
        }
        
        return render(request, 'reports/patient_report.html', context)

# List Views for different modules
class PatientsListView(LoginRequiredMixin, ListView):
    model = Patient
    template_name = 'patient/list.html'
    context_object_name = 'patients'
    paginate_by = 25

    def get_queryset(self):
        queryset = Patient.objects.all().order_by('-created_at')
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(mrn__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(contact_number__icontains=search_query)
            )
        return queryset

class UsersListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'admin/users_list.html'
    context_object_name = 'users'
    paginate_by = 25

    def test_func(self):
        return self.request.user.role == Role.ADMIN

class AuditLogListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = AuditLog
    template_name = 'admin/audit_logs.html'
    context_object_name = 'logs'
    paginate_by = 50

    def test_func(self):
        return self.request.user.role == Role.ADMIN

    def get_queryset(self):
        return AuditLog.objects.all().order_by('-timestamp')

# Emergency and Quick Access Views
class QuickAdmitView(LoginRequiredMixin, View):
    def post(self, request):
        # Quick admit for emergencies
        patient_data = {
            'mrn': generate_mrn(),
            'first_name': request.POST.get('first_name', 'Emergency'),
            'last_name': request.POST.get('last_name', 'Patient'),
            'age': request.POST.get('age'),
            'gender': request.POST.get('gender', ''),
            'contact_number': request.POST.get('contact_number', ''),
            'created_by': request.user
        }
        
        patient = Patient.objects.create(**patient_data)
        
        visit = Visit.objects.create(
            patient=patient,
            visit_id=generate_visit_id(),
            visit_type='emergency',
            reason=request.POST.get('reason', 'Emergency admission'),
            department_id=request.POST.get('department') if request.POST.get('department') else None
        )
        
        return JsonResponse({
            'status': 'success',
            'patient_id': str(patient.uid),
            'visit_id': visit.visit_id,
            'mrn': patient.mrn
        })

# Discharge Management
class DischargeView(LoginRequiredMixin, View):
    template_name = 'patient/discharge.html'
    
    def get(self, request, visit_id):
        visit = get_object_or_404(Visit, id=visit_id)
        return render(request, self.template_name, {'visit': visit})
    
    def post(self, request, visit_id):
        visit = get_object_or_404(Visit, id=visit_id)
        
        # Update visit
        visit.discharged_at = timezone.now()
        visit.status = 'discharged'
        visit.discharge_summary = request.POST.get('discharge_summary', '')
        visit.follow_up_date = request.POST.get('follow_up_date') or None
        
        # Free up bed
        if visit.bed:
            visit.bed.is_occupied = False
            visit.bed.save()
            visit.bed = None
        
        visit.save()
        
        # Create follow-up if specified
        if request.POST.get('follow_up_date'):
            FollowUp.objects.create(
                patient=visit.patient,
                visit=visit,
                doctor=visit.attending_doctor,
                scheduled_date=request.POST.get('follow_up_date'),
                reason='Post-discharge follow-up',
                instructions=request.POST.get('follow_up_instructions', ''),
                created_by=request.user
            )
        
        return redirect('visit-detail', pk=visit.id)

class ProcurementViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing procurement records.
    """
    queryset = Procurement.objects.all()
    serializer_class = ProcurementSerializer

class RadiologyReportViewSet(viewsets.ModelViewSet):
    queryset = RadiologyReport.objects.all()
    serializer_class = RadiologyReportSerializer

# his/views.py
from rest_framework import viewsets
from .models import Payment
from .serializers import PaymentSerializer  # you must create this serializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

# his/views.py
from rest_framework import viewsets
from .models import InsuranceClaim  # your model name
from .serializers import InsuranceClaimSerializer  # must create this too

class InsuranceClaimViewSet(viewsets.ModelViewSet):
    queryset = InsuranceClaim.objects.all()
    serializer_class = InsuranceClaimSerializer

from django.shortcuts import render
from .models import AuditLog  # your model

def audit_logs_view(request):
    logs = AuditLog.objects.all().order_by('-timestamp')
    return render(request, 'admin/audit_logs.html', {'audit_logs': logs})

from django.shortcuts import render
from django.db.models import F
from .models import Prescription, Medication, Procurement

def pharmacy_dashboard(request):
    # Get queryset of pending prescriptions (iterable)
    pending_prescriptions = Prescription.objects.filter(status='pending')

    # Get count of pending prescriptions (integer)
    pending_prescriptions_count = pending_prescriptions.count()

    low_stock_medications = Medication.objects.filter(quantity__lt=F('minimum_stock_level'))
    recent_procurements = Procurement.objects.order_by('-order_date')[:10]

    context = {
        'pending_prescriptions': pending_prescriptions,  # queryset
        'pending_prescriptions_count': pending_prescriptions_count,  # integer
        'low_stock_medications': low_stock_medications,
        'recent_procurements': recent_procurements,
    }

    return render(request, 'pharmacy/dashboard.html', context)





