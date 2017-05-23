from django.contrib import admin

from crashlog.models import ErrorBatch, Error


class ErrorBatchAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'message', 'fmt_last_seen', 'times_seen', 'url', 'server_name')
    list_filter = ('class_name', 'times_seen', 'server_name')
    ordering = ('-last_seen',)

    def fmt_last_seen(self, error_batch):
        return str(error_batch.last_seen)
    fmt_last_seen.admin_order_field = 'last_seen'
    fmt_last_seen.short_description = 'Last seen'

class ErrorAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'message', 'fmt_datetime', 'url', 'server_name')
    list_filter = ('class_name', 'datetime', 'server_name')
    ordering = ('-datetime',)

    def fmt_datetime(self, errors):
        return str(errors.datetime)
    fmt_datetime.admin_order_field = 'datetime'
    fmt_datetime.short_description = 'Datetime'

admin.site.register(ErrorBatch, ErrorBatchAdmin)
admin.site.register(Error, ErrorAdmin)