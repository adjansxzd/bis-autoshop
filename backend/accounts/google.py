"""
"Sign in with Google".

The site shows Google's button; Google gives the browser a signed ID token (a JWT) for our client ID.
The backend checks the token's signature, audience and expiry with Google's public keys
(google-auth library), then finds the user by email or creates a new customer account.
No Google password ever reaches our server.
"""
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework.exceptions import ValidationError

User = get_user_model()


def verify(credential):
    """Returns the token's claims (email, names) or raises ValidationError."""
    if not settings.GOOGLE_CLIENT_ID:
        raise ValidationError({"detail": _("Signing in with Google is not set up on this server.")})
    try:
        claims = id_token.verify_oauth2_token(credential, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
    except ValueError:  # bad signature, wrong audience, expired …
        raise ValidationError({"detail": _("Google sign-in failed. Please try again.")})
    if not claims.get("email") or not claims.get("email_verified"):
        raise ValidationError({"detail": _("This Google account has no confirmed email.")})
    return claims


def user_for(claims):
    """Existing account with this email, or a new customer (no password: they sign in with Google)."""
    email = claims["email"].lower()
    user = User.objects.filter(email__iexact=email).first()
    if user:
        if not user.is_active:
            raise ValidationError({"detail": _("This account is blocked.")})
        return user, False
    base = re.sub(r"[^\w.@+-]", "", email.split("@")[0])[:120] or "user"
    username, n = base, 1
    while User.objects.filter(username__iexact=username).exists():
        n += 1
        username = f"{base}{n}"
    user = User(username=username, email=email, first_name=claims.get("given_name", "")[:150],
                last_name=claims.get("family_name", "")[:150])  # role: customer (default)
    user.set_unusable_password()
    user.save()
    return user, True
