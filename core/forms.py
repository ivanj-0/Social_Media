from django import forms
from .models import Comment, Post, Profile

class CommentForm(forms.ModelForm):
	content = forms.CharField(label ="", widget = forms.Textarea(
	attrs ={
		'class':'form-control',
		'placeholder':'Comment here !',
		'rows':1,
		'cols':5
	}))
	class Meta:
		model = Comment
		fields =['content']


class EditForm(forms.ModelForm):

	class Meta:
		model = Post
		fields =('caption',)

class PrefForm(forms.ModelForm):

	 
	class Meta:
		model = Profile
		fields = ('pref',)
		# widgets = ('pref': forms.RadioSelect(choices=['YES','NO']))
