# Horizon Tilda → GetCourse Bridge

Receives quiz leads from the Tilda form webhook and creates the contact
in GetCourse via the API.

## Deploy (Railway)

1. Create a GitHub repo (e.g. `horizon-tilda-bridge`) and upload
   `app.py`, `requirements.txt`, `Procfile`.
2. Railway → New service → deploy from the repo.
3. Variables:
   - `GETCOURSE_API_KEY` — copy from GetCourse → profile → Настройки
     аккаунта → АПИ (the key named "Tilda"). Never commit this value.
   - `GETCOURSE_HOST` — `academy.arghorizon.com`
   - `GETCOURSE_GROUP` — optional GetCourse group for quiz leads
   - `BRIDGE_SECRET` — optional; if set, Tilda must call
     `/tilda-lead?secret=...`
4. Railway → service → Settings → generate a public domain.

## Connect Tilda

Tilda → Express Test page → hidden form block → Content →
"Прием данных из формы" → add **Webhook** recipient with URL:

```
https://<your-railway-domain>/tilda-lead
```

(append `?secret=...` if `BRIDGE_SECRET` is set).

## Test

```bash
curl -X POST https://<your-railway-domain>/tilda-lead \
  -d "Name=Test&Email=test@example.com"
curl https://<your-railway-domain>/health
```

Then check the contact appears in GetCourse.
