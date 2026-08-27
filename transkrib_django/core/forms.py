"""Форма загрузки файла и параметров транскрибации."""
from django import forms

from .models import Task

MODEL_CHOICES = [
    ("tiny", "tiny"),
    ("base", "base"),
    ("small", "small"),
    ("medium", "medium"),
    ("large", "large"),
    ("large-v2", "large-v2"),
    ("large-v3", "large-v3"),
    ("large-v3-turbo", "large-v3-turbo"),
]

LANGUAGE_CHOICES = [
    ("Русский", "Русский"),
    ("English", "English"),
    ("Deutsch", "Deutsch"),
    ("Español", "Español"),
    ("Türkçe", "Türkçe"),
    ("中文", "中文"),
]

DIARIZATION_METHOD_CHOICES = [
    ("spectral", "spectral (по умолчанию)"),
    ("ecapa", "ecapa"),
]

MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024  # 2 ГБ


class UploadForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "input_file", "language", "model", "diarization",
            "diarization_method", "timeout_sec", "gpu_id", "metadata_json"
        ]
        widgets = {
            "language": forms.Select(choices=LANGUAGE_CHOICES, attrs={"class": "form-select"}),
            "model": forms.Select(choices=MODEL_CHOICES, attrs={"class": "form-select"}),
            "diarization": forms.CheckboxInput(attrs={"class": "form-check"}),
            "diarization_method": forms.Select(choices=DIARIZATION_METHOD_CHOICES, attrs={"class": "form-select"}),
            "timeout_sec": forms.NumberInput(attrs={"class": "form-control", "min": "1000", "max": "3600000"}),
            "gpu_id": forms.NumberInput(attrs={"class": "form-control", "min": "0", "max": "7"}),
            "metadata_json": forms.TextInput(attrs={"class": "form-control", "placeholder": '{"key": "value"}'}),
        }
        labels = {
            "input_file": "Аудио- или видеофайл",
            "language": "Язык речи",
            "model": "Модель Whisper",
            "diarization": "Диаризация спикеров",
            "diarization_method": "Метод диаризации",
            "timeout_sec": "Таймаут (мс)",
            "gpu_id": "ID GPU",
            "metadata_json": "Метаданные (JSON)",
        }

    def clean_input_file(self):
        f = self.cleaned_data.get("input_file")
        if f and f.size > MAX_UPLOAD_BYTES:
            raise forms.ValidationError("Файл больше 2 ГБ — сожмите или разрежьте запись.")
        return f

    def clean_metadata_json(self):
        data = self.cleaned_data.get("metadata_json")
        if not data:
            return ""
        import json
        try:
            json.loads(data)
        except json.JSONDecodeError:
            raise forms.ValidationError("Некорректный JSON формат метаданных.")
        return data
