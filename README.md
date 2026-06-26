# persoia-auth

Authentification **persoIA** partagée pour les outils (scan-cartes-visites,
marchéspublic, app-plan-areas, …). **Un seul module, zéro dépendance** (stdlib
pure) — `pip install` ou simple copie du fichier dans un bundle PyInstaller.

L'utilisateur s'identifie **une seule fois** ; la clé est stockée dans un
emplacement **commun à tous les outils**, et chacun la relit. Même store que
`persoia-cli`.

## Adopter dans un outil (3 lignes)

```python
import persoia_auth

key = persoia_auth.get_api_key(
    client="mon-outil",                       # slug stable → en-tête X-Persoia-Client (suivi conso)
    client_label="Mon Super Outil",           # nom lisible affiché sur la page de consentement
)
headers = persoia_auth.auth_headers(client="mon-outil")     # {"Authorization": "Bearer …", "X-Persoia-Client": "mon-outil"}
base = persoia_auth.api_base()                              # https://chat.persoia.com/v1 (ou démo)
```

- `get_api_key()` : variable d'environnement → store partagé → (si absent et
  navigateur dispo) **login navigateur** → mémorise et renvoie la clé. Lève
  `MissingKeyError` si aucune clé en mode non interactif. Option `validate=True` :
  vérifie que la clé du store est toujours acceptée par l'API et **re-logue** si
  elle a été révoquée (évite de réutiliser une clé morte).
- `client_label` : **nom lisible** que l'outil *publie* lui-même au login
  (ex. `"Scanner de cartes de visite"`). Il s'affiche sur la page de consentement
  `/cli` **à la place du** `127.0.0.1:<port>` loopback, pour que l'utilisateur
  identifie l'outil qui demande l'accès. Vit dans le code de l'add-on → préservé
  lors des mises à jour. À défaut, le portail retombe sur le slug `client`.
- `auth_headers()` : en-têtes HTTP prêts à l'emploi. `X-Persoia-Client` identifie
  l'outil pour le **suivi de consommation** côté persoIA (sans effet tant que le
  serveur ne l'exploite pas — sans danger).
- `validate_api_key()` : `True`/`False` selon que l'API accepte la clé (faux
  uniquement sur 401/403 ; une API injoignable renvoie `True`).
- `reset()` : purge **clé + base + modèle + tenant** — à utiliser pour **changer
  d'environnement** (démo → prod). `logout()` n'efface que la clé (garde la base).
- `login()` / `logout()` / `load_config()` / `save_config()` / `get_config_path()`
  pour les besoins avancés.

## Où est stockée la clé

| OS | Fichier |
|----|---------|
| Linux / macOS | `~/.config/persoia/config.env` (respecte `XDG_CONFIG_HOME`) |
| Windows | `%APPDATA%\persoia\config.env` |

Format **env**, perms `0600` (Unix) :

```
PERSOIA_API_KEY=persoia_sk_…
PERSOIA_API_BASE=https://chat.persoia.com/v1
```

Surcharges : variables d'environnement `PERSOIA_API_KEY` / `PERSOIA_API_BASE` /
`PERSOIA_MODEL`, et `PERSOIA_CONFIG` pour pointer un autre fichier. L'URL de base
est auto-déduite du préfixe du token (`persoia_demo_sk_` → environnement de démo).

## Login navigateur (sécurité)

`login()` ouvre le portail persoIA `/cli` et reçoit la clé sur un **serveur
loopback éphémère** `127.0.0.1` :

- **le mot de passe n'est jamais vu par l'outil** ;
- `state` anti-CSRF (comparaison à temps constant), **usage unique** ;
- **CORS limité à l'origine du portail** persoIA (hôte validé strictement
  `*.persoia.com`) ;
- gère le preflight *Private Network Access* de Chrome/Edge ;
- adresse IPv4 littérale `127.0.0.1` (pas `localhost`, qui peut résoudre `::1`).

Le flux et les endpoints sont ceux de [`persoia-cli`](https://github.com/FishMoiLaPaix/persoia-cli).

## Bundles (PyInstaller)

Pas de dépendance → vous pouvez soit `pip install persoia-auth`, soit **copier
`persoia_auth.py`** directement dans votre projet/bundle.

## Licence

MIT.
