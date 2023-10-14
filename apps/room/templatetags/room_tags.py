from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def parse_user_text(context, user_name: str, start_of_sentence: bool = False):
    request = context.get("request")

    if request.user.name == user_name:
        you = "you" if not start_of_sentence else "You"
        user_text = f'<span class="me-involved">{you}</span>'
    else:
        user_text = f"<strong>{user_name}</strong>"

    return user_text