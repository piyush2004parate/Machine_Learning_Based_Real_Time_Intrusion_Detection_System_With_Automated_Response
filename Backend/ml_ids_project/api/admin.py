from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import redirect
from django.contrib import messages
from .models import NetworkTraffic, ThreatIncident, ResponseRule, LogEntry


@admin.register(NetworkTraffic)
class NetworkTrafficAdmin(admin.ModelAdmin):
	list_display = ("timestamp", "source_ip", "destination_ip", "protocol", "bytes", "status", "severity")
	list_filter = ("status", "severity", "protocol")
	search_fields = ("source_ip", "destination_ip", "protocol")
	ordering = ("-timestamp",)
	change_list_template = "admin/api/networktraffic/change_list.html"

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path(
				"clear/",
				self.admin_site.admin_view(self.clear_all),
				name="api_networktraffic_clear",
			),
		]
		return custom_urls + urls

	def clear_all(self, request):
		deleted_count, _ = NetworkTraffic.objects.all().delete()
		messages.success(request, f"Deleted {deleted_count} traffic records.")
		return redirect(reverse("admin:api_networktraffic_changelist"))


@admin.register(ThreatIncident)
class ThreatIncidentAdmin(admin.ModelAdmin):
	list_display = ("timestamp", "source_ip", "destination_ip", "threat_type", "severity", "status")
	list_filter = ("severity", "status", "threat_type")
	search_fields = ("source_ip", "destination_ip", "threat_type")
	ordering = ("-timestamp",)
	change_list_template = "admin/api/threatincident/change_list.html"

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path(
				"clear/",
				self.admin_site.admin_view(self.clear_all),
				name="api_threatincident_clear",
			),
		]
		return custom_urls + urls

	def clear_all(self, request):
		deleted_count, _ = ThreatIncident.objects.all().delete()
		messages.success(request, f"Deleted {deleted_count} threat incidents.")
		return redirect(reverse("admin:api_threatincident_changelist"))

@admin.register(ResponseRule)
class ResponseRuleAdmin(admin.ModelAdmin):
	list_display = ("name", "condition", "action", "is_active", "triggered_count", "created_at")
	list_filter = ("is_active", "action")
	search_fields = ("name", "condition")
	ordering = ("-created_at",)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
	list_display = ("timestamp", "action", "target", "result", "severity")
	list_filter = ("result", "severity")
	search_fields = ("action", "target", "details")
	ordering = ("-timestamp",)
