# Seguridad, protección contra bots y centro de mando

Guía para configurar Cloudflare y el servidor de asansal.com. Sigue las partes en orden: cada una funciona por sí sola, y la web sigue funcionando entre una y otra.

## Qué hace ya el código

| Medida | Cómo funciona |
|---|---|
| Analítica sin cookies | Cada visitante se identifica con un hash de (sal aleatoria del día + IP + navegador). La sal se borra a los dos días, la IP nunca se guarda. Datos en `data/analytics.db` (SQLite, fuera de git). |
| Filtro de bots en la analítica | Los navegadores automáticos y las vistas previas de enlaces no cuentan como visitas; se registran aparte como "bots descartados". |
| Límite del chatbot | 5 preguntas escritas por IP y día. Las 3 sugerencias no cuentan y se responden desde la caché (Gemini solo se llama la primera vez por idioma, y otra vez cuando cambia la base de conocimiento). |
| "No soy un robot" | Al llegar a 5, el chat muestra Cloudflare Turnstile. Si se supera, 5 más (10 en total). Sin claves de Turnstile, el límite se queda en 5. |
| Tope global | Máximo 300 llamadas a Gemini al día para toda la web (protege tu factura aunque alguien use muchas IPs). |
| Preguntas largas | Más de 500 caracteres: se rechazan sin llamar a Gemini. |
| Panel privado | Escucha solo en 127.0.0.1 (no accesible desde fuera) y exige la cabecera de Cloudflare Access con tu email. |

Los límites se pueden cambiar sin tocar código con variables de entorno: `CHAT_TYPED_LIMIT`, `CHAT_VERIFIED_LIMIT`, `CHAT_DAILY_CAP`.

---

## Parte 1. Ajustes de Cloudflare (sin código)

Panel de Cloudflare → selecciona `asansal.com`.

### 1.1 Mira el modo SSL (no lo cambies todavía)

**SSL/TLS → Overview.** Apunta qué modo aparece: *Flexible*, *Full* o *Full (strict)*.

- Debe quedar en **Full**. **No pongas Full (strict)** mientras la web no vaya por el túnel: el certificado del servidor no es válido para Cloudflare y la web da error 526 (comprobado). Full (strict) se activa en la Parte 3.

### 1.2 HTTPS siempre y versión mínima de TLS

**SSL/TLS → Edge Certificates:**

- **Always Use HTTPS:** On (probablemente ya lo está: `http://` ya redirige a `https://`).
- **Minimum TLS Version:** TLS 1.2.
- **Automatic HTTPS Rewrites:** On.
- **HTTP Strict Transport Security (HSTS):** Enable HSTS →
  - Max Age: **6 months**
  - Include subdomains: **On** (todos tus subdominios pasan por Cloudflare con HTTPS)
  - Preload: **Off** (es difícil de deshacer)
  - No-Sniff header: **On**

HSTS hace que el navegador recuerde que tu web solo funciona con HTTPS y no intente nunca la versión sin cifrar.

### 1.3 Cabeceras de seguridad

Streamlit no deja añadir cabeceras, así que las pone Cloudflare.

**Rules → Overview → Create rule → Response Header Transform Rule**

Escribe los nombres y valores a mano: al copiarlos y pegarlos se pueden colar caracteres invisibles y Cloudflare los rechaza ("invalid header name").

- Nombre: `Cabeceras de seguridad`
- If incoming requests match: **Custom filter expression** → `Hostname` `equals` `asansal.com`
- Then → **Set static** (una fila por cabecera):

| Cabecera | Valor | Para qué sirve |
|---|---|---|
| `X-Frame-Options` | `SAMEORIGIN` | Ninguna otra web puede meter la tuya en un marco invisible para engañar a los visitantes (clickjacking). |
| `Content-Security-Policy` | `frame-ancestors 'self'` | Lo mismo, en la versión moderna. |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Al pulsar un enlace externo, la otra web solo ve "asansal.com", no la URL completa. |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | La página no puede pedir cámara, micrófono ni ubicación. |

Deploy. Comprueba desde tu terminal: `curl -sI https://asansal.com | grep -iE "x-frame|content-security|referrer|strict"`.

### 1.4 Bots

Menú nuevo de Cloudflare: **Security → Settings** (filtro *Bot traffic* si aparece).

- **Bot Fight Mode:** On. Bloquea bots conocidos y maliciosos. Los "verified bots" (Google, Bing, LinkedIn para las vistas previas) siguen pasando.
- **Block AI bots:** tu decisión. Recomiendo **dejarlo desactivado**: que los buscadores con IA conozcan tu perfil te puede traer reclutadores.
- **Security Level:** en el menú nuevo lo gestiona Cloudflare; si no aparece, no hace falta nada.

**Managed rules (WAF):** son de pago. No hacen falta aquí: protegen sobre todo formularios y bases de datos, y la web pública no tiene ninguna de las dos cosas.

### 1.5 Límite de peticiones (contra inundaciones)

**Security → Security rules → Create rule → Rate limiting rule** (el plan gratuito permite una y solo deja filtrar por *URI Path*, en todos los subdominios a la vez):

- Nombre: `Limite portada`
- Field **URI Path** · Operator **equals** · Value `/`
- Characteristics: **IP**
- Rate: **20 requests** cada **10 seconds**
- Action: **Block** durante **10 seconds**

Solo cuenta las cargas de la portada, no los ~30 archivos que pide Streamlit (ni los de lab.asansal.com) al abrir la página, así que no bloquea a nadie que recargue. Una persona pide `/` una vez por visita; más de 20 veces en 10 segundos es un script.

### 1.6 robots.txt

Streamlit no puede servir archivos en la raíz, así que el archivo está en `static/robots.txt` (servido en `/app/static/robots.txt`) y Cloudflare redirige a él.

**Rules → Overview → Create rule → Redirect Rule:**

- Nombre: `robots.txt`
- Custom filter expression: `Hostname` `equals` `asansal.com` **And** `URI Path` `equals` `/robots.txt`
- Then: **Static** · URL `https://asansal.com/app/static/robots.txt` · Status code **301** · Preserve query string: Off
- Deploy.

---

## Parte 2. Cloudflare Turnstile ("no soy un robot" del chatbot)

1. Panel de Cloudflare (nivel de cuenta, no de dominio) → **Turnstile → Add widget**.
2. Nombre: `asansal.com chatbot` · Hostnames: `asansal.com` · Widget mode: **Managed** · Pre-clearance: No.
3. Copia la **Site Key** y la **Secret Key**.
4. En el servidor, añádelas a `/opt/Personal_Website/.streamlit/secrets.toml`:

```toml
TURNSTILE_SITE_KEY = "0x4AAAA..."
TURNSTILE_SECRET_KEY = "0x4AAAA..."
PANEL_ALLOWED_EMAIL = "tu-email@ejemplo.com"
```

5. `sudo systemctl restart miweb.service`

Sin estas claves la web funciona igual, con el límite en 5 preguntas y sin verificación.

---

## Parte 3. Túnel de Cloudflare y centro de mando

El túnel hace que el servidor abra él mismo una conexión saliente hacia Cloudflare. Así el panel (y después la web) no necesitan ningún puerto abierto a internet.

### 3.1 Antes de empezar: mira cómo está montado el servidor

```bash
sudo ss -tlnp                 # qué programas escuchan en qué puertos
systemctl cat miweb.service   # usuario y comando de la web
ls /etc/nginx/sites-enabled 2>/dev/null; which caddy cloudflared
```

### 3.2 Instala cloudflared y crea el túnel

El servidor es **Oracle Linux** (usuario `opc`, gestor de paquetes `dnf`):

```bash
curl -fsSL https://pkg.cloudflare.com/cloudflared.repo | sudo tee /etc/yum.repos.d/cloudflared.repo
sudo dnf install -y cloudflared
# Alternativa si falla el repositorio (mira la arquitectura con: uname -m)
# sudo dnf install -y https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-aarch64.rpm

cloudflared tunnel login                 # abre un enlace: elige asansal.com
cloudflared tunnel create asansal        # apunta el TUNNEL_ID que devuelve
cloudflared tunnel route dns asansal panel.asansal.com
```

Configuración: copia `deploy/cloudflared-config.yml` a `/etc/cloudflared/config.yml`, cambia `TUNNEL_ID` (dos veces) y mueve el archivo de credenciales:

```bash
sudo mkdir -p /etc/cloudflared
sudo cp ~/.cloudflared/TUNNEL_ID.json /etc/cloudflared/
sudo cp /opt/Personal_Website/deploy/cloudflared-config.yml /etc/cloudflared/config.yml
sudo nano /etc/cloudflared/config.yml    # pon el TUNNEL_ID
sudo cloudflared service install
sudo systemctl enable --now cloudflared
```

### 3.3 Arranca el panel

```bash
sudo cp /opt/Personal_Website/deploy/panel.service /etc/systemd/system/panel.service
sudo systemctl daemon-reload
sudo systemctl enable --now panel.service
```

Para que el despliegue automático también reinicie el panel, el usuario de GitHub Actions necesita permiso sin contraseña. Con `sudo visudo -f /etc/sudoers.d/deploy` :

```
opc ALL=(root) NOPASSWD: /usr/bin/systemctl restart miweb.service, /usr/bin/systemctl restart panel.service
```

### 3.4 Protege el panel con Cloudflare Access

**Antes de abrir panel.asansal.com en el navegador:**

1. Panel de Cloudflare → **Zero Trust** (la primera vez pide elegir un nombre de equipo y el plan **Free**, 0 €; puede pedir una tarjeta pero no cobra).
2. **Access → Applications → Add an application → Self-hosted.**
   - Application name: `Centro de mando`
   - Session duration: `1 week`
   - Public hostname: subdomain `panel`, domain `asansal.com`
3. **Policies → Add a policy:**
   - Name: `Solo yo` · Action: **Allow**
   - Include: **Emails** → tu email
4. Login methods: **One-time PIN** (te llega un código por email; no hace falta nada más).
5. Save.

Abre `https://panel.asansal.com`: Cloudflare te pide el email, te manda un código, y entras al panel. Cualquier otra persona se queda en la pantalla del código.

El panel además comprueba por su cuenta la cabecera que añade Access (`PANEL_ALLOWED_EMAIL` en secrets.toml) y solo escucha en 127.0.0.1, así que no se puede saltar Access entrando por otra vía.

### 3.5 (Recomendado) Pasa también la web pública al túnel

Cuando el panel funcione, descomenta las líneas de `asansal.com` y `www.asansal.com` en `/etc/cloudflared/config.yml` y:

```bash
cloudflared tunnel route dns -f asansal asansal.com
cloudflared tunnel route dns -f asansal www.asansal.com
sudo systemctl restart cloudflared
```

Después, si nada más usa esos puertos (revisa lo que salió en 3.1), cierra los puertos web en Oracle Cloud (**Networking → Virtual Cloud Networks → Security Lists**) y en el firewall del servidor. Con eso:

- El tráfico Cloudflare → servidor va cifrado dentro del túnel (resuelve el modo *Flexible*).
- Nadie puede saltarse Cloudflare atacando la IP del servidor.
- La IP que usa el límite del chatbot (`CF-Connecting-IP`) ya no se puede falsificar.

---

## Parte 4. Mantenimiento del servidor

```bash
# SSH solo con clave (debe salir "passwordauthentication no")
sudo sshd -T | grep -E "passwordauthentication|permitrootlogin"

# Actualizaciones de seguridad automáticas (Oracle Linux)
sudo dnf install -y dnf-automatic
sudo sed -i 's/^upgrade_type.*/upgrade_type = security/; s/^apply_updates.*/apply_updates = yes/' /etc/dnf/automatic.conf
sudo systemctl enable --now dnf-automatic.timer

# Bloqueo de IPs que fallan el login SSH (fail2ban viene de EPEL)
sudo dnf install -y oracle-epel-release-el$(rpm -E %rhel) && sudo dnf install -y fail2ban
printf '[sshd]\nenabled = true\n' | sudo tee /etc/fail2ban/jail.d/sshd.local
sudo systemctl enable --now fail2ban
```

En Google Cloud (proyecto de la API de Gemini): **Billing → Budgets & alerts**, crea un presupuesto pequeño (por ejemplo 5 €/mes) con aviso por email al 50 % y al 100 %.
