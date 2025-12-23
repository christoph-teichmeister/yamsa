from django import forms


class RoomCategoryCreateForm(forms.Form):
    name = forms.CharField(max_length=100)
    emoji = forms.CharField(max_length=10)
    color = forms.CharField(max_length=7, required=False)
    order_index = forms.IntegerField(min_value=0, required=False)
    make_default = forms.BooleanField(required=False)


class RoomCategoryUpdateForm(forms.Form):
    room_category_id = forms.IntegerField(widget=forms.HiddenInput)
    order_index = forms.IntegerField(min_value=0)
    make_default = forms.BooleanField(required=False)
