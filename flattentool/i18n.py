import gettext
from pathlib import Path

domain = "flatten-tool"
locale_dir = str(Path(__file__).parent / "locale")

try:
    # If we can get the language from Django use that
    from django.core.exceptions import ImproperlyConfigured
    from django.utils.translation import get_language

    try:
        get_language()
    except ImproperlyConfigured:
        raise ImportError

    # We set up the translations ourselves, instead of using Django's gettext
    # function, so that we can have a custom domain and locale directory.
    translations = {}
    translations["en"] = gettext.translation(domain, locale_dir, languages=["en"])
    translations["es"] = gettext.translation(domain, locale_dir, languages=["es"])

    def _(text):
        lang = get_language()
        if lang not in translations:
            lang = "en"
        return translations[lang].gettext(text)


except ImportError:
    # If there's no Django, call gettext.translation without a languages array,
    # and it will pick one based on the environment variables.
    t = gettext.translation(domain, locale_dir)
    _ = t.gettext
