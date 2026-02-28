from django import forms
from .models import Student, Result   # <-- import both models

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'registration_number', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (css + ' form-control').strip()
            if field.required:
                field.widget.attrs['required'] = 'required'
            if name == 'email':
                field.widget.attrs['autocomplete'] = 'email'
            elif name in ('name', 'first_name', 'last_name'):
                field.widget.attrs['autocomplete'] = 'name'
            else:
                field.widget.attrs.setdefault('autocomplete', 'off')


class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['student', 'course', 'semester', 'score']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (css + ' form-control').strip()
            if field.required:
                field.widget.attrs['required'] = 'required'
