# his/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # API ViewSets
    UserViewSet, StaffViewSet, AuditLogListView, PatientViewSet, VisitViewSet, MedicalRecordViewSet,
    PrescriptionViewSet, MedicationDispenseViewSet, PharmacyStockViewSet, ProcurementViewSet,
    LabOrderViewSet, LabResultViewSet, RadiologyOrderViewSet, RadiologyReportViewSet,
    InvoiceViewSet, PaymentViewSet, InsuranceClaimViewSet, AppointmentViewSet, VitalsViewSet,
    
    # Authentication Views
    LoginPageView, DashboardView, LogoutView,
    
    # Patient Management Views
    OPRegistrationView, EmergencyRegistrationView, PatientsListView, DischargeView,
    
    # Role-specific Views
    WardManagementView, PharmacyDashboardView, LabDashboardView, SystemConfigView,
    BillingDashboardView, AnalyticsDashboardView,
    
    # List Views
    UsersListView, AppointmentListView, AppointmentCreateView,
    
    # Specialized Views
    InvoiceCreateView, BedAssignmentView, PatientReportView, QuickAdmitView,
    
    # API Views
    PatientSearchAPIView, DoctorAvailabilityAPIView, NotificationAPIView
)

# API Router
router = DefaultRouter()
router.register('users', UserViewSet)
router.register('staff', StaffViewSet)
router.register('patients', PatientViewSet)
router.register('visits', VisitViewSet)
router.register('appointments', AppointmentViewSet)
router.register('vitals', VitalsViewSet)
router.register('medical-records', MedicalRecordViewSet)
router.register('prescriptions', PrescriptionViewSet)
router.register('dispenses', MedicationDispenseViewSet)
router.register('pharmacy-stock', PharmacyStockViewSet)
router.register('procurements', ProcurementViewSet)
router.register('lab-orders', LabOrderViewSet)
router.register('lab-results', LabResultViewSet)
router.register('radiology-orders', RadiologyOrderViewSet)
router.register('radiology-reports', RadiologyReportViewSet)
router.register('invoices', InvoiceViewSet)
router.register('payments', PaymentViewSet)
router.register('insurance-claims', InsuranceClaimViewSet)

urlpatterns = [
    # API Routes
    path('api/', include(router.urls)),
    
    # Authentication
    path('login/', LoginPageView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # Patient Management
    path('patients/', PatientsListView.as_view(), name='patients-list'),
    path('patients/<uuid:patient_id>/report/', PatientReportView.as_view(), name='patient-report'),
    path('op-registration/', OPRegistrationView.as_view(), name='op-registration'),
    path('emergency-registration/', EmergencyRegistrationView.as_view(), name='emergency-registration'),
    path('quick-admit/', QuickAdmitView.as_view(), name='quick-admit'),
    path('visits/<int:visit_id>/discharge/', DischargeView.as_view(), name='discharge-patient'),
    
    # Appointments
    path('appointments/', AppointmentListView.as_view(), name='appointments-list'),
    path('appointments/create/', AppointmentCreateView.as_view(), name='appointment-create'),
    
    # Role-specific Dashboards
    path('admin/users/', UsersListView.as_view(), name='users-list'),
    path('admin/audit-logs/', AuditLogListView.as_view(), name='audit-logs'),
    path('admin/system-config/', SystemConfigView.as_view(), name='system-config'),
    
    # Nurse Module
    path('nurse/ward-management/', WardManagementView.as_view(), name='ward-management'),
    path('bed-assignment/', BedAssignmentView.as_view(), name='bed-assignment'),
    
    # Pharmacy Module
    path('pharmacy/dashboard/', PharmacyDashboardView.as_view(), name='pharmacy-dashboard'),
    
    # Lab Module
    path('lab/dashboard/', LabDashboardView.as_view(), name='lab-dashboard'),
    
    # Finance Module
    path('finance/dashboard/', BillingDashboardView.as_view(), name='finance-dashboard'),
    path('finance/invoice/create/', InvoiceCreateView.as_view(), name='invoice-create'),
    
    # Analytics
    path('analytics/', AnalyticsDashboardView.as_view(), name='analytics-dashboard'),
    
    # AJAX/API Endpoints
    path('api/patients/search/', PatientSearchAPIView.as_view(), name='patient-search'),
    path('api/doctor-availability/', DoctorAvailabilityAPIView.as_view(), name='doctor-availability'),
    path('api/notifications/', NotificationAPIView.as_view(), name='notifications'),
    
    # Legacy URLs (for compatibility)
    path('users/', UsersListView.as_view(), name='user-list'),
    path('auditlogs/', AuditLogListView.as_view(), name='auditlog-list'),
    path('lab-orders/', LabDashboardView.as_view(), name='lab_orders'),
    path('radiology-orders/', LabDashboardView.as_view(), name='radiology_orders'),
    path('vitals/', WardManagementView.as_view(), name='vitals'),
    path('patient-monitoring/', WardManagementView.as_view(), name='patient_monitoring'),
    path('appointments/', AppointmentListView.as_view(), name='appointments'),
    path('reports/', AnalyticsDashboardView.as_view(), name='reports'),
    path('pay-bills/', BillingDashboardView.as_view(), name='pay_bills'),
    path('pharmacy-stock/', PharmacyDashboardView.as_view(), name='pharmacy_stock'),
    path('dispense/', PharmacyDashboardView.as_view(), name='dispense'),
    path('procurement/', PharmacyDashboardView.as_view(), name='procurement'),
    path('lab-results/', LabDashboardView.as_view(), name='lab_results'),
    path('invoices/', BillingDashboardView.as_view(), name='invoices'),
    path('payments/', BillingDashboardView.as_view(), name='payments'),
    path('insurance-claims/', BillingDashboardView.as_view(), name='insurance_claims'),
]
