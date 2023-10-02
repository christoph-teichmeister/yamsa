from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def parse_user_text(context, user_name: str, start_of_sentence: bool = False):
    request = context.get("request")

    if request.user.name == user_name:
        you = "you" if not start_of_sentence else "you".capitalize()
        user_text = f'<span class="me-involved">{you}</span>'
        if start_of_sentence:
            user_text += " owe"
    else:
        user_text = f"<strong>{user_name}</strong>"
        if start_of_sentence:
            user_text += " owes"

    return user_text
