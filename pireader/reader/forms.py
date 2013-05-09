from django import forms

class ImportForm(forms.Form):
    opml_file = forms.FileField()
