# Central, consistent German date/time formats.
# Applies regardless of UI language (see counterpart file in the other
# language folder) — date format is a business decision for yamsa, not
# a locale feature.
DATE_FORMAT = "d.m.Y"
SHORT_DATE_FORMAT = "d.m.Y"
DATETIME_FORMAT = "d.m.Y H:i"
SHORT_DATETIME_FORMAT = "d.m.Y H:i"
TIME_FORMAT = "H:i"
MONTH_DAY_FORMAT = "d.m."
YEAR_MONTH_FORMAT = "F Y"

DATE_INPUT_FORMATS = [
    "%d.%m.%Y",
    "%d.%m.%y",
]
DATETIME_INPUT_FORMATS = [
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y %H:%M:%S.%f",
    "%d.%m.%Y %H:%M",
]
