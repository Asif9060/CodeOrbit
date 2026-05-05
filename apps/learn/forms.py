"""Learn admin forms."""
from django import forms

from apps.learn.models import Topic


class TopicAdminForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = "__all__"
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "vLargeTextField js-rich-markdown",
                    "rows": 18,
                }
            )
        }

    class Media:
        css = {
            "all": [
                "https://cdn.jsdelivr.net/npm/simplemde@1.11.2/dist/simplemde.min.css",
                "css/admin/learn-topic-editor.css",
            ]
        }
        js = [
            "https://cdn.jsdelivr.net/npm/simplemde@1.11.2/dist/simplemde.min.js",
            "js/admin/learn-topic-editor.js",
        ]
