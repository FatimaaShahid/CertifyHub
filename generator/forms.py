from django import forms

class UploadForm(forms.Form):
    template = forms.ImageField(label="Upload Certificate Template")
    data_file = forms.FileField(label="Upload Excel/CSV Data")
