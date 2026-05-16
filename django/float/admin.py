from django.contrib import admin
from django import forms
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from .models import Role, Place, Operator, Message, IncidentPatient, Incident, CheckIn, Patrol, UserProfile #, IncidentMessage,
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.db import models
from django.utils.text import Truncator
import csv

@admin.action(description='Download selected as csv')
def download_csv(modeladmin, request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied
    opts = queryset.model._meta
    model = queryset.model
    response = HttpResponse(content_type='text/csv')
    # force download.
    response['Content-Disposition'] = f'attachment;filename={model._meta.model_name}.csv'
    # the csv writer
    writer = csv.writer(response)
    field_names = [field.name for field in opts.fields]
    # Write a first row with header information
    writer.writerow(field_names)
    # Write data rows
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])
    return response
admin.site.add_action(download_csv)

# Create your admin models here.

class RoleAdmin(admin.ModelAdmin):
    list_display = ('title', 'operator_count')

    @admin.display(description="Count")
    def operator_count(self, obj:Role) -> int:
        return len(obj.is_operator_role.all()) or 0

class PlaceAdmin(admin.ModelAdmin):
    class PlaceAdminForm(forms.ModelForm):
        location_longitude = forms.FloatField(
            required=False,
            help_text="Longitude (e.g., 151.2093).",
        )
        location_latitude = forms.FloatField(
            required=False,
            help_text="Latitude (e.g., -33.8688).",
        )

        class Meta:
            model = Place
            fields = "__all__"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if self.instance and self.instance.location:
                self.fields["location_longitude"].initial = self.instance.location.x
                self.fields["location_latitude"].initial = self.instance.location.y

        def clean(self):
            cleaned_data = super().clean()
            lon = cleaned_data.get("location_longitude")
            lat = cleaned_data.get("location_latitude")

            if lon is None and lat is None:
                cleaned_data["location"] = None
                return cleaned_data

            if lon is None or lat is None:
                raise ValidationError("Provide both longitude and latitude.")

            cleaned_data["location"] = Point(lon, lat)
            return cleaned_data

    form = PlaceAdminForm
    list_display = ('place', 'callsign', 'address', 'location')
    fieldsets = (
        ('Basic Information', {
            'fields': ('place', 'callsign')
        }),
        ('Location', {
            'fields': ('address', 'location_longitude', 'location_latitude'),
            'description': 'Enter either an address or GPS coordinates (or both)'
        }),
    )

class OperatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'callsign', 'base', 'role', 'phone', 'email', 'command_weighting', 'last_updated_timestamp',)
    list_filter = ('role', 'base')
    search_fields = ['name', 'callsign',]
    list_editable = ()

class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'recipient', 'reported_location', 'message_entry_timestamp', 'last_updated_user', 'last_updated_timestamp', 'short_display_info',)
    list_editable = ()
    exclude = ('last_updated_user',)
    list_filter = ('sender', 'recipient', 'reported_location')
    search_fields = ['message_info']

    @admin.display(description="Message Info")
    def short_display_info(self, obj:Message) -> str:
        return Truncator(obj.message_info).words(5)

    def save_model(self, request, obj, form, change):
        obj.last_updated_user = request.user
        super().save_model(request, obj, form, change)

class IncidentPatientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'age', 'gender', 'incident_ref', 'last_updated_timestamp',)
    list_filter = ('incident_ref',)
    search_fields = ['name',]

class IncidentAdmin(admin.ModelAdmin):
    list_display = ('id', 'reported_location', 'event_occurance_timestamp', 'patient_ref', 'incident_message_type', 'nature_of_injury', 'has_this_been_escalated', 'is_incident_controlled', 'is_incident_resolved', 'last_updated_timestamp',)
    list_filter = ('reported_location', 'incident_message_type', 'patient_ref', 'has_this_been_escalated', 'is_incident_controlled', 'is_incident_resolved',)
    search_fields = ['reported_location', 'cause_of_injury', 'nature_of_injury', 'effects_of_injury', 'treatment_provided']

# class IncidentMessageAdmin(admin.ModelAdmin):
#     list_display = ('id', 'incident_ref', 'sender', 'recipient', 'reported_location', 'message_entry_timestamp', 'last_updated_timestamp', 'message_info',)
#     list_filter = ('incident_ref',)


class PatrolAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


class CheckInAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'patrol', 'location', 'state')
    #formfield_overrides = {
    #        models.TextField: {"attrs": {"value": },
    #}

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location')

# Register your models here.

admin.site.register(Role, RoleAdmin)
admin.site.register(Place, PlaceAdmin)
admin.site.register(Operator, OperatorAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(IncidentPatient, IncidentPatientAdmin)
admin.site.register(Incident, IncidentAdmin)
admin.site.register(Patrol, PatrolAdmin)
admin.site.register(CheckIn, CheckInAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
# admin.site.register(IncidentMessage, IncidentMessageAdmin)
