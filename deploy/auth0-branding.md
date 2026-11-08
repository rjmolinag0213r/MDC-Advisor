# Auth0 login page branding

The Auth0 hosted login (tenant `dev-knpwtmv0ymv0quu4`) is themed to match the MDC Pathways design.
Changes are applied through the Management API with the Auth0 CLI; nothing in this repo is secret.

| Setting | API | Value |
|---|---|---|
| Theme (colors, sharp borders, logo, background) | `POST /branding/themes` (theme `MDC Pathways`) | white primary button with dark label, sand `#f0a874` links and focus, deep purple `#2a0a3a` card, 1px white hairlines, MDC "MD" logo, synthwave background |
| Login text | `PUT /prompts/login/custom-text/en` | "Welcome back · Log in to the MDC Student Hub to see your plan and progress." |
| Sign-up text | `PUT /prompts/signup/custom-text/en` | "Create your account · Save your MDC plan and pick up where you left off, on any device." |
| Tenant name and logo | `PATCH /tenants/settings` | `friendly_name: MDC Student Hub` |
| Experience | `PATCH /prompts` | `universal_login_experience: new` |

Images load from the public repo (`raw.githubusercontent.com/.../Ricardo_2026/mdc-pathways/images/`). Once the site has
an HTTPS domain, point `logo_url` and `background_image_url` at it instead.

The small red triangle in the corner of the Auth0 page appears because the Google login uses Auth0's shared development keys. To remove it, create
a Google OAuth client and paste its ID and secret in **Auth0 Dashboard → Authentication → Social → google-oauth2**.

To change the theme: `auth0 api get branding/themes/default`, edit the JSON, then
`auth0 api patch branding/themes/<themeId> --data @theme.json`.
