from import_export.widgets import Widget


class HashIdWidget(Widget):
    def render(self, value, obj=None):
        if value is None:
            return None
        return str(value)
