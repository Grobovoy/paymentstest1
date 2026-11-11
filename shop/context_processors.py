from .models import Profile


def shop_nav(request):
    email = request.session.get("email")
    profile = Profile.objects.filter(email=email).first() if email else None
    return {"current_profile": profile}
