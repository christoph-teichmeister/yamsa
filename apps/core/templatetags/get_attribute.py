from django import template

register = template.Library()


@register.filter("getattribute")
def getattribute(value, arg):
    """Gets an attribute of an object dynamically from a string name"""

    if hasattr(value, str(arg)):
        return getattr(value, arg)

    if "." in arg:
        split_arg_list = arg.split(".")
        value = value
        for split_arg in split_arg_list:
            if hasattr(value, str(split_arg)):
                value = getattr(value, str(split_arg))
        return value

    raise AttributeError(f"{value} has no attribute {arg}")
