from django.contrib import admin
from apps.assembly.models import AssemblyProcess, AssemblyPart, AssemblyLog

class AssemblyPartInline(admin.TabularInline):
    model = AssemblyPart
    extra = 0
    readonly_fields = ['added_by', 'added_at']

class AssemblyLogInline(admin.TabularInline):
    model = AssemblyLog
    extra = 0
    readonly_fields = ['action_by', 'timestamp', 'action', 'part', 'notes']
    can_delete = False

@admin.register(AssemblyProcess)
class AssemblyProcessAdmin(admin.ModelAdmin):
    list_display = ['id', 'aircraft_type', 'status', 'started_by', 'start_date', 'completed_by', 'completion_date']
    list_filter = ['status', 'aircraft_type']
    search_fields = ['aircraft_type', 'started_by__username', 'completed_by__username']
    readonly_fields = ['started_by', 'start_date', 'completed_by', 'completion_date', 'aircraft']
    inlines = [AssemblyPartInline, AssemblyLogInline]

@admin.register(AssemblyPart)
class AssemblyPartAdmin(admin.ModelAdmin):
    list_display = ['id', 'assembly', 'part', 'added_by', 'added_at']
    list_filter = ['assembly__aircraft_type']
    search_fields = ['assembly__id', 'part__id']
    readonly_fields = ['added_by', 'added_at']

@admin.register(AssemblyLog)
class AssemblyLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'assembly', 'action', 'action_by', 'timestamp', 'part']
    list_filter = ['action', 'assembly__aircraft_type']
    search_fields = ['assembly__id', 'action_by__username', 'notes']
    readonly_fields = ['assembly', 'action_by', 'timestamp', 'action', 'part', 'notes']
