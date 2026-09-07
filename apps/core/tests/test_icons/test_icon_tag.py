from django.template import Context, Template


def render(template_string, **context):
    return Template("{% load icon_tags %}" + template_string).render(Context(context))


class TestIconTag:
    def test_it_points_a_use_at_the_sprite(self):
        html = render('{% icon "chevron-down" %}')

        assert "#chevron-down" in html
        assert "icons/sprite.svg" in html
        assert 'class="bi"' in html

    def test_extra_classes_land_next_to_bi(self):
        # `.bi` carries the 1em sizing; the caller's utilities have to survive next to it,
        # because that is what every migrated call site relies on.
        html = render('{% icon "trash" "text-danger-text shrink-0" %}')

        assert 'class="bi text-danger-text shrink-0"' in html

    def test_it_is_hidden_from_assistive_tech(self):
        # Every icon in this app sits next to its own label or in a labelled control.
        html = render('{% icon "gear" %}')

        assert 'aria-hidden="true"' in html
        assert 'focusable="false"' in html

    def test_the_name_may_come_from_a_variable(self):
        html = render("{% icon tab_icon %}", tab_icon="wallet")

        assert "#wallet" in html

    def test_a_name_is_escaped_rather_than_interpolated(self):
        html = render("{% icon evil %}", evil='"><script>alert(1)</script>')

        assert "<script>" not in html
