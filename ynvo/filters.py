from django.contrib.admin import SimpleListFilter

from ynvo.models import Client, Project, Task


class ClientFilter(SimpleListFilter):
    title = "client"
    parameter_name = "client"

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return [(client.id, client.name) for client in Client.objects.all()]
        return [
            (client.id, client.name)
            for client in Client.objects.filter(transmitter__user=request.user)
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(client__id=self.value())


class ProjectFilter(SimpleListFilter):
    title = "project"
    parameter_name = "project"

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return [(project.id, project.name) for project in Project.objects.all()]
        return [
            (project.id, project.name)
            for project in Project.objects.filter(
                client__transmitter__user=request.user
            )
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(project__id=self.value())


class TaskFilter(SimpleListFilter):
    title = "task"
    parameter_name = "task"

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return [(task.id, task.name) for task in Task.objects.all()]
        return [
            (task.id, task.name)
            for task in Task.objects.filter(
                project__client__transmitter__user=request.user
            )
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(task__id=self.value())
