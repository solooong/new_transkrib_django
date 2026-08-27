"""Форма загрузки файла и параметров транскрибации."""
from django import forms

from .models import Task

MODEL_CHOICES = [
    ("whisper-large-v3", "whisper-large-v3"),
    ("whisper-medium", "whisper-medium"),
    ("whisper-base", "whisper-base"),
    ("parakeet-tdt-0.6b", "parakeet-tdt-0.6b"),
]

LANGUAGE_CHOICES = [
    ("Русский", "Русский"),
    ("English", "English"),
    ("Deutsch", "Deutsch"),
    ("Español", "Español"),
    ("Türkçe", "Türkçe"),
    ("中文", "中文"),
]

MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024  # 2 ГБ


class UploadForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["input_file", "language", "model", "diarization"]
        widgets = {
            "language": forms.Select(choices=LANGUAGE_CHOICES, attrs={"class": "form-select"}),
            "model": forms.Select(choices=MODEL_CHOICES, attrs={"class": "form-select"}),
            "diarization": forms.CheckboxInput(attrs={"class": "form-check"}),
        }
        labels = {
            "input_file": "Аудио- или видеофайл",
            "language": "Язык речи",
            "model": "Модель распознавания",
            "diarization": "Диаризация спикеров",
        }

    def clean_input_file(self):
        f = self.cleaned_data.get("input_file")
        if f and f.size > MAX_UPLOAD_BYTES:
            raise forms.ValidationError("Файл больше 2 ГБ — сожмите или разрежьте запись.")
        return f
