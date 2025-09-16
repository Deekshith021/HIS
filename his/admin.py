# his/admin.py
from django.contrib import admin
from .models import (
    User, Staff, AuditLog, Patient, Visit, MedicalRecord,
    Prescription, MedicationDispense, PharmacyStock, Procurement,
    LabOrder, LabResult, RadiologyOrder, RadiologyReport,
    Invoice, Payment, InsuranceClaim
)
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )

admin.site.register(Staff)
admin.site.register(AuditLog)
admin.site.register(Patient)
admin.site.register(Visit)
admin.site.register(MedicalRecord)
admin.site.register(Prescription)
admin.site.register(MedicationDispense)
admin.site.register(PharmacyStock)
admin.site.register(Procurement)
admin.site.register(LabOrder)
admin.site.register(LabResult)
admin.site.register(RadiologyOrder)
admin.site.register(RadiologyReport)
admin.site.register(Invoice)
admin.site.register(Payment)
admin.site.register(InsuranceClaim)
