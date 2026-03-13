from django import forms


class RoomCategoryUpdateForm(forms.Form):
    room_category_id = forms.IntegerField(widget=forms.HiddenInput)
    order_index = forms.IntegerField(min_value=0)
    make_default = forms.BooleanField(required=False)
