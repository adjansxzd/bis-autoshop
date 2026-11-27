# "Sign in with Google"

**It is already set up.** Google Cloud project **AutoShop** (`autoshop-516008`, owner: Adilzhan) has the OAuth client **AutoShop local** for `http://localhost:4200`; its client ID is the default in `backend/config/settings.py`. The button appears on **Sign in** and **Create account**.

**Who can sign in:** while the app is in *Testing* mode, only **test users** can. Add a teammate: Google Cloud → Google Auth Platform → **Audience** → **Test users → Add users** → their Gmail → Save.

The steps below are only needed to create a new client (e.g. for the deployed site — then also add the site's address to *Authorized JavaScript origins*).

## 1. Create the client ID in Google Cloud

1. Open <https://console.cloud.google.com/> and sign in with any Google account (one team member is enough).
2. Top bar → project selector → **New project** → name `AutoShop` → **Create**, then select it.
3. **APIs & Services → OAuth consent screen** (Google Auth Platform → *Branding / Audience*):
   - App name `AutoShop`, user support email = yours, developer email = yours → Save.
   - Audience: **External**. While the app is in *Testing*, add the Google accounts that will sign in (yours and the teammates') under **Test users**.
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**:
   - Application type: **Web application**, name `AutoShop local`.
   - **Authorized JavaScript origins** — add both:
     - `http://localhost:4200`
     - `http://localhost`
   - Redirect URIs: leave empty (we don't use redirects).
   - **Create** → copy the **Client ID** (looks like `1234567890-abc...apps.googleusercontent.com`). The client *secret* is **not** needed.

## 2. Give it to the backend

Create the file `backend/.env` (it is git-ignored, never commit it) with one line:

```
GOOGLE_CLIENT_ID=1234567890-abc...apps.googleusercontent.com
```

Restart `python manage.py runserver`. Open <http://localhost:4200/login> — the **Continue with Google** button is there.

## How it works

1. The site loads Google's script and shows Google's own button.
2. After the user picks an account, Google gives the browser a signed **ID token** for our client ID.
3. The site sends it to `POST /api/auth/google/`. The backend checks the signature, audience (our client ID) and expiry with Google's public keys (`google-auth` library).
4. The user is found by email, or a new **customer** account is created (no password — they sign in with Google). The backend answers with our usual JWT tokens, exactly like a normal sign-in.

No Google password ever reaches our server. Tests: `accounts/tests.py → GoogleSignInTests` (Google's check is mocked, so tests run offline).
