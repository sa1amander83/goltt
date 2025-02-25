from django.forms import ModelForm, DateInput, ModelMultipleChoiceField
from calendarapp.models import Event, EventMember
from django import forms

from calendarapp.models.event import Tables
from django.forms.widgets import CheckboxSelectMultiple

class EventForm(ModelForm):
    table = forms.ModelChoiceField(
        queryset=Tables.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = Event
        fields = ["title", "description", "start_time", "end_time", 'tables']
        # datetime-local is a HTML5 input type
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Описание"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Примечание или пожелание",
                    "rows": 3,
                }
            ),
            "start_time": forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'step': '1800',  # 30 минут в секундах
                    'min': '09:00',
                    'max': '23:00',
                    'class': 'form-control'
                },
                format='%Y-%m-%dT%H:%M'
            ),
            "end_time": forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'step': '1800',
                    'min': '09:00',
                    'max': '23:00',
                    'class': 'form-control'
                },
                format='%Y-%m-%dT%H:%M'
            ),


        }
        exclude = ["user"]

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        # input_formats to parse HTML5 datetime-local input to datetime field
        self.fields["start_time"].input_formats = ("%Y-%m-%dT%H:%M",)
        self.fields["end_time"].input_formats = ("%Y-%m-%dT%H:%M",)


class AddMemberForm(forms.ModelForm):
    class Meta:
        model = EventMember
        fields = ["user"]
