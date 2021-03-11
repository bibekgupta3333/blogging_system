from django import forms
from .models import Comment

class CommentCreateForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = (
            "email",
            "user",
            "comment_content",
            "post",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].widget.attrs.update({"class": "form-control"})
        self.fields["user"].widget.attrs.update({"style": "display:none;"})
        self.fields["user"].label = ""
        self.fields["post"].widget.attrs.update({"style": "display:none;"})
        self.fields["post"].label = ""
