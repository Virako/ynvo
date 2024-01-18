from django.contrib import admin
from django.utils.html import format_html

from ynvo.filters import ClientFilter, ProjectFilter, TaskFilter
from ynvo.forms import CommentAdminForm, TaskAdminForm, WorkAdminForm
from ynvo.models import (
    Client,
    Fee,
    Invoice,
    Transmitter,
    Project,
    Task,
    Comment,
    Work,
)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("alias", "name", "vat", "address", "zipcode", "city")
    show_full_result_count = False
    exclude = ("transmitter",)

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)

        return (
            super()
            .get_queryset(request)
            .with_transmitter()
            .filter(transmitter__user=request.user)
        )

    def save_model(self, request, obj, form, change):
        if not change:  # only set the transmitter when the object is created
            transmitter = Transmitter.objects.get(user=request.user)
            obj.transmitter = transmitter
        super().save_model(request, obj, form, change)


@admin.register(Transmitter)
class TransmitterAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "vat", "address", "zipcode", "city")
    show_full_result_count = False
    exclude = ("user",)

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)

        return super().get_queryset(request).filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not change:  # only set the transmitter when the object is created
            obj.user = request.user
        super().save_model(request, obj, form, change)


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ("ftype", "activity", "price", "amount")
    show_full_result_count = False

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)

        return (
            super().get_queryset(request)
            # .with_transmitter()
            .filter(invoice__invo_from__user=request.user)
        )


class FeeInline(admin.TabularInline):
    model = Fee
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "proforma",
        "year",
        "total",
        "currency",
        "invo_to",
        "project",
        "created",
        "paid",
        "pdf_url",
    )
    show_full_result_count = False
    inlines = [FeeInline]
    list_filter = ("invo_to", "year")
    date_hierarchy = "created"
    exclude = ("invo_from",)

    def pdf_url(self, obj):
        return format_html(
            f"<a target='_blank' href='/ynvo/{obj.year}/{obj.number}/'>GEN</a>"
        )

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)

        return super().get_queryset(request).filter(invo_from__user=request.user)

    def save_model(self, request, obj, form, change):
        if not change:  # only set the transmitter when the object is created
            transmitter = Transmitter.objects.get(user=request.user)
            obj.invo_from = transmitter
        super().save_model(request, obj, form, change)


class TaskInline(admin.TabularInline):
    form = TaskAdminForm
    model = Task
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "client")
    list_filter = [ClientFilter]
    show_full_result_count = False
    inlines = [TaskInline]

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)

        return (
            super().get_queryset(request).filter(client__transmitter__user=request.user)
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "client" and not request.user.is_superuser:
            kwargs["queryset"] = Client.objects.filter(transmitter__user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class WorkInline(admin.TabularInline):
    form = WorkAdminForm
    model = Work
    extra = 1


class CommentInline(admin.TabularInline):
    form = CommentAdminForm
    model = Comment
    extra = 1


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "status", "deadline", "priority")
    list_filter = [ProjectFilter, "status", "deadline"]
    show_full_result_count = False
    inlines = [WorkInline, CommentInline]

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)

        return (
            super().get_queryset(request)
            # .with_transmitter()
            .filter(project__client__transmitter__user=request.user)
        )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("task", "created")
    list_filter = [TaskFilter]
    show_full_result_count = False

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)

        return (
            super().get_queryset(request)
            # .with_transmitter()
            .filter(task__project__client__transmitter__user=request.user)
        )


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ("comment", "task")
    list_filter = [TaskFilter]
    show_full_result_count = False

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)

        return (
            super().get_queryset(request)
            # .with_transmitter()
            .filter(task__project__client__transmitter__user=request.user)
        )
