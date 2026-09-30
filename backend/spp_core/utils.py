def get_semester(request, default=1):
    """Read ?semester= (or the posted field) as an int in 1-8.

    Anything missing, non-numeric or out of range falls back to `default`
    instead of raising, so a mangled URL can't crash a page.
    """
    raw = request.GET.get('semester') or request.POST.get('semester')
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return value if 1 <= value <= 8 else default
