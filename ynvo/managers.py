from django.db import models


class ClientQuerySet(models.QuerySet):
    def with_transmitter(self):
        return self.select_related("transmitter", "transmitter__user")


class ReadClientManager(models.Manager):
    def get_queryset(self):
        return ClientQuerySet(self.model, using="default")


class WriteClientManager(models.Manager):
    def get_queryset(self):
        return ClientQuerySet(self.model, using="default")


class ProjectQuerySet(models.QuerySet):
    def with_client(self):
        return self.select_related("client")


class ReadProjectManager(models.Manager):
    def get_queryset(self):
        return ProjectQuerySet(self.model, using="default")


class WriteProjectManager(models.Manager):
    def get_queryset(self):
        return ProjectQuerySet(self.model, using="default")


class TaskQuerySet(models.QuerySet):
    def with_project(self):
        return self.select_related("project")


class ReadTaskManager(models.Manager):
    def get_queryset(self):
        return TaskQuerySet(self.model, using="default")


class WriteTaskManager(models.Manager):
    def get_queryset(self):
        return TaskQuerySet(self.model, using="default")


class CommentQuerySet(models.QuerySet):
    def with_task(self):
        return self.select_related("task")


class ReadCommentManager(models.Manager):
    def get_queryset(self):
        return CommentQuerySet(self.model, using="default")


class WriteCommentManager(models.Manager):
    def get_queryset(self):
        return CommentQuerySet(self.model, using="default")


class WorkQuerySet(models.QuerySet):
    def with_task(self):
        return self.select_related("task")


class ReadWorkManager(models.Manager):
    def get_queryset(self):
        return WorkQuerySet(self.model, using="default")


class WriteWorkManager(models.Manager):
    def get_queryset(self):
        return WorkQuerySet(self.model, using="default")
