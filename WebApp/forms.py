from django import forms
from .models import PostTestAnswers, PostTestPassage, PostTestQuestions, PreTestAnswers, PreTestPassage, PreTestQuestions, Teacherrecords
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm
from django.core.exceptions import ValidationError
import re


class SpeechRecognitionForm(forms.Form):
    transcript = forms.CharField(widget=forms.HiddenInput())




class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacherrecords
        fields = ['name', 'username', 'email']




class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput())
    new_password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())


class VerificationCodeForm(forms.Form):
    verification_code = forms.CharField()


class ContentForm(forms.ModelForm):
    class Meta:
        fields = '__all__'


    def __init__(self, *args, **kwargs):
        model_class = kwargs.pop('model_class', None)
        super(ContentForm, self).__init__(*args, **kwargs)
        if model_class:
            self._meta.model = model_class
            self.fields.update(forms.models.fields_for_model(model_class))


class CustomPasswordChangeForm(BasePasswordChangeForm):
    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
       
        if len(new_password) < 8:
            raise ValidationError('The new password must be at least 8 characters long.')
       
        if not re.search(r'[A-Z]', new_password):
            raise ValidationError('The new password must contain at least one uppercase letter.')
       
        if not re.search(r'\d', new_password):
            raise ValidationError('The new password must contain at least one digit.')


        return new_password


class VerificationCodeForm(forms.Form):
    verification_code = forms.CharField(max_length=6)


class PreTestAnswerForm(forms.ModelForm):
    class Meta:
        model = PreTestAnswers
        fields = ['pretest_question', 'pretest_passage', 'pretest_grade_level', 'pretest_answer', 'teacher']


class PreTestPassageForm(forms.ModelForm):
    class Meta:
        model = PreTestPassage
        fields = ['pretest_passage', 'pretest_grade_level', 'pretest_passage_title', 'pretest_passage_prompt', 'teacher']
       
class PreTestQuestionForm(forms.ModelForm):
    class Meta:
        model = PreTestQuestions
        fields = ['pretest_passage', 'pretest_grade_level', 'pretest_question', 'teacher']


class PostTestAnswerForm(forms.ModelForm):
    class Meta:
        model = PostTestAnswers
        fields = ['posttest_answer', 'posttest_question', 'posttest_passage', 'posttest_grade_level']


class PostTestPassageForm(forms.ModelForm):
    class Meta:
        model = PostTestPassage
        fields = ['posttest_passage', 'posttest_grade_level']
       
class PostTestQuestionForm(forms.ModelForm):
    class Meta:
        model = PostTestQuestions
        fields = ['posttest_question', 'posttest_passage', 'posttest_grade_level']
