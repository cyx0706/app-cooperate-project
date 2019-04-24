from django import forms
from app_api.models import *

class PhotoForm(forms.ModelForm):

    class Meta:
        model = PostPhotos
        fields = '__all__'
        labels = {
            'post_id': "帖子id",
        }
        widgets = {
            'pic': forms.ClearableFileInput(attrs={'multiple': True}),
        }
    # img = forms.ImageField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

class CommentForm(forms.ModelForm):

    class Meta:
        model = FloorComments
        exclude = ['replied_comment']
        error_messages = {
            '__all__': {'required': "不能为空"},
            'create_time': {'invalid': "格式错误"},
        }


    replied_comment = forms.ChoiceField(label="回复", help_text="0为1级评论, 填对应id表示回复对应评论")

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['replied_comment'].choices = tuple([(str(x), x) for x in FloorComments.objects.filter(replied_comment=0).values_list('id',flat=True)]+[(0,0)])
        self.initial['replied_comment'] = [0]

    def clean_reply_id(self):
        reply_id = self.cleaned_data['replied_comment'] # 回复的id
        comment = self.cleaned_data['reply'] # 回复的楼层
        if int(reply_id) != 0:
            floor_comment = FloorComments.objects.get(id=reply_id)
            print(floor_comment.reply)
            if floor_comment.reply != comment:
                raise forms.ValidationError("请保持回复的楼层一致")
        return reply_id