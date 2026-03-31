from django import forms

from ynvo.models import Comment, Invoice, Task, Work


class InvoiceAdminForm(forms.ModelForm):
    hours = forms.FloatField(
        required=False,
        help_text="Auto-generate fees from client config",
    )

    class Meta:
        model = Invoice
        fields = "__all__"


class TaskAdminForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"size": 12}),
            "description": forms.Textarea(attrs={"rows": 3, "cols": 16}),
            "branch": forms.TextInput(attrs={"size": 12}),
        }


class WorkAdminForm(forms.ModelForm):
    class Meta:
        model = Work
        fields = "__all__"
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 3, "cols": 16}),
        }


class CommentAdminForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = "__all__"
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 3, "cols": 16}),
        }
