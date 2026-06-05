"""
Script de pruebas automatizado — Zeptai / Zeptai
Usuario ficticio: testbot@zeptai.test / TestPass2024!
Ejecutar desde el host: python run_tests.py
"""
import requests
import json
import sys
import time
from datetime import datetime

# Forzar UTF-8 en la salida de Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE = "http://localhost:5000"
EMAIL = "testbot@zeptai.test"
PHONE = "+34000000099"
PASSWORD = "TestPass2024!"

results = []
OK  = "[OK]"
ERR = "[ERROR]"
WRN = "[WARN]"

def check(name, response, expected_status=200, check_json=None, check_html=None, check_not_html=None):
    ok = True
    notes = []

    if response.status_code != expected_status:
        ok = False
        notes.append(f"HTTP {response.status_code} (esperado {expected_status})")

    if check_json and response.status_code == expected_status:
        try:
            data = response.json()
            for key, val in check_json.items():
                if key not in data:
                    ok = False
                    notes.append(f"falta clave '{key}' en JSON")
                elif val is not None and data[key] != val:
                    ok = False
                    notes.append(f"'{key}' = {data[key]!r} (esperado {val!r})")
        except Exception as e:
            ok = False
            notes.append(f"JSON inválido: {e}")

    if check_html and response.status_code == expected_status:
        for fragment in check_html:
            if fragment not in response.text:
                ok = False
                notes.append(f"no contiene '{fragment}'")

    if check_not_html and response.status_code == expected_status:
        for fragment in check_not_html:
            if fragment in response.text:
                ok = False
                notes.append(f"contiene '{fragment}' (no debería)")

    status = OK if ok else ERR
    note_str = " — " + "; ".join(notes) if notes else ""
    results.append((status, name, note_str))
    return response if ok else response


# ─────────────────────────────────────────────
# BLOQUE 0: Sin sesión — rutas protegidas
# ─────────────────────────────────────────────
s_anon = requests.Session()

r = s_anon.get(f"{BASE}/dashboard", allow_redirects=False)
check("AUTH [anon] /dashboard redirige al login", r, expected_status=302)

r = s_anon.get(f"{BASE}/api/notifications", allow_redirects=False)
check("AUTH [anon] /api/notifications devuelve 401", r, expected_status=401)

r = s_anon.get(f"{BASE}/api/notifications/unread_count", allow_redirects=False)
check("AUTH [anon] /api/notifications/unread_count devuelve 401", r, expected_status=401)

r = s_anon.get(f"{BASE}/api/metrics/llm", allow_redirects=False)
check("AUTH [anon] /api/metrics/llm devuelve 401", r, expected_status=401)

r = s_anon.get(f"{BASE}/documents", allow_redirects=False)
check("AUTH [anon] /documents redirige", r, expected_status=302)

r = s_anon.get(f"{BASE}/transactions", allow_redirects=False)
check("AUTH [anon] /transactions redirige", r, expected_status=302)


# ─────────────────────────────────────────────
# BLOQUE 1: Login
# ─────────────────────────────────────────────
s = requests.Session()

r = s.post(f"{BASE}/login", data={"email": EMAIL, "password": "WRONG_PASSWORD"}, allow_redirects=True)
check("LOGIN contraseña incorrecta no inicia sesión", r, expected_status=200,
      check_not_html=["Asistente", "/logout"])

r = s.post(f"{BASE}/login", data={"email": EMAIL, "password": PASSWORD}, allow_redirects=True)
check("LOGIN credenciales correctas", r, expected_status=200,
      check_html=["Test Business SL"])


# ─────────────────────────────────────────────
# BLOQUE 2: Páginas web principales
# ─────────────────────────────────────────────
pages = [
    ("/dashboard",    ["Test Business SL", "GASTOS TOTALES"],     "DASHBOARD"),
    ("/wizard",       ["Despierta", "sector", "nombre"],          "WIZARD"),
    ("/marketplace",  ["Agentes", "Activar"],                     "MARKETPLACE"),
    ("/documents",    ["Documentos"],                             "DOCUMENTS"),
    ("/agents",       ["Agentes"],                                "AGENTS"),
    ("/marketing",    ["Marketing", "Reel"],                      "MARKETING"),
    ("/council",      ["Consejo", "Socio", "Gestor"],             "COUNCIL"),
    ("/metrics",      ["Métricas", "LLM"],                        "METRICS"),
    ("/transactions", ["Gastos", "ticket"],                       "TRANSACTIONS"),
    ("/profile",      ["Perfil", "email"],                        "PROFILE"),
    ("/demo",         ["Demo", "seed"],                           "DEMO PANEL"),
]

for path, fragments, label in pages:
    r = s.get(f"{BASE}{path}", allow_redirects=True)
    # Búsqueda case-insensitive
    text_lower = r.text.lower()
    fragments_lower = [f.lower() for f in fragments]
    found = [f for f in fragments_lower if f in text_lower]
    missing = [f for f in fragments if f.lower() not in text_lower]

    ok = r.status_code == 200
    notes = []
    if r.status_code != 200:
        notes.append(f"HTTP {r.status_code}")
    if missing:
        ok = False
        notes.append(f"no contiene: {missing}")
    status = OK if ok else ERR
    note_str = " — " + "; ".join(notes) if notes else ""
    results.append((status, f"PAGE {label} {path}", note_str))


# ─────────────────────────────────────────────
# BLOQUE 3: Bot status activo
# ─────────────────────────────────────────────
r = s.get(f"{BASE}/dashboard", allow_redirects=True)
check("WIZARD bot_status: dashboard muestra 'Asistente Activo'", r,
      check_html=["Asistente Activo"],
      check_not_html=["Asistente Dormido"])


# ─────────────────────────────────────────────
# BLOQUE 4: API de notificaciones
# ─────────────────────────────────────────────
r = s.get(f"{BASE}/api/notifications")
check("NOTIF GET /api/notifications devuelve lista", r,
      check_json=None)
try:
    notifs = r.json()
    if not isinstance(notifs, list):
        results.append((ERR, "NOTIF respuesta es lista JSON", f" — tipo: {type(notifs)}"))
    else:
        results.append((OK, f"NOTIF lista contiene {len(notifs)} notificaciones", ""))
except:
    results.append(("❌", "NOTIF JSON parse error", ""))

r = s.get(f"{BASE}/api/notifications/unread_count")
check("NOTIF GET /api/notifications/unread_count", r,
      check_json={"count": None})

# Marcar todas como leídas
r = s.post(f"{BASE}/api/notifications/mark_all_read")
check("NOTIF POST mark_all_read", r, check_json={"success": True})

# Verificar count = 0 tras marcar
r = s.get(f"{BASE}/api/notifications/unread_count")
try:
    count = r.json().get("count", -1)
    if count == 0:
        results.append((OK, "NOTIF badge = 0 tras mark_all_read", ""))
    else:
        results.append((ERR, "NOTIF badge != 0 tras mark_all_read", f" — count={count}"))
except:
    results.append(("❌", "NOTIF unread_count parse error", ""))

# Marcar notificación inexistente
r = s.post(f"{BASE}/api/notifications/mark_read/999999")
check("NOTIF mark_read id inexistente devuelve 404", r, expected_status=404)


# ─────────────────────────────────────────────
# BLOQUE 5: Métricas LLM
# ─────────────────────────────────────────────
r = s.get(f"{BASE}/api/metrics/llm")
check("METRICS GET /api/metrics/llm", r)
try:
    data = r.json()
    for key in ["by_model", "by_stage", "daily"]:
        if key in data:
            results.append((OK, f"METRICS clave '{key}' presente", ""))
        else:
            results.append((ERR, f"METRICS falta clave '{key}'", ""))
except:
    results.append(("❌", "METRICS JSON parse error", ""))


# ─────────────────────────────────────────────
# BLOQUE 6: Transacciones / Tickets
# ─────────────────────────────────────────────
r = s.get(f"{BASE}/transactions", allow_redirects=True)
check("TICKETS /transactions carga", r)
for provider in ["Amazon AWS", "Microsoft Azure", "Repsol"]:
    if provider in r.text:
        results.append((OK, f"TICKETS proveedor '{provider}' visible", ""))
    else:
        results.append((ERR, f"TICKETS proveedor '{provider}' NO visible", ""))


# ─────────────────────────────────────────────
# BLOQUE 7: Documentos
# ─────────────────────────────────────────────
r = s.get(f"{BASE}/documents", allow_redirects=True)
check("DOCS /documents carga", r)
# Sin documentos generados debe mostrar estado vacío, no error
if "500" in r.text or "Error" in r.text[:200]:
    results.append(("❌", "DOCS /documents contiene error visible", ""))
else:
    results.append(("✅", "DOCS /documents sin errores visibles", ""))

# Borrar documento inexistente
r = s.post(f"{BASE}/delete_document/999999")
check("DOCS delete inexistente devuelve 404", r, expected_status=404)


# ─────────────────────────────────────────────
# BLOQUE 8: Marketplace / Toggle agentes
# ─────────────────────────────────────────────
r = s.post(f"{BASE}/toggle_agent/post_sales")
check("MARKET toggle_agent post_sales", r)
try:
    d = r.json()
    if "active" in d:
        results.append((OK, f"MARKET toggle devuelve active={d['active']}", ""))
    else:
        results.append((ERR, "MARKET toggle sin clave 'active'", f" — {d}"))
except:
    results.append(("❌", "MARKET toggle JSON error", ""))

r = s.post(f"{BASE}/toggle_agent/networker")
check("MARKET toggle_agent networker", r)


# ─────────────────────────────────────────────
# BLOQUE 9: Demo — seed y triggers
# ─────────────────────────────────────────────
r = s.post(f"{BASE}/demo/seed_data")
check("DEMO POST /demo/seed_data", r, expected_status=302)

r = s.post(f"{BASE}/demo/seed_grants")
check("DEMO POST /demo/seed_grants", r, expected_status=302)


# ─────────────────────────────────────────────
# BLOQUE 10: Push VAPID
# ─────────────────────────────────────────────
r = s.get(f"{BASE}/api/push/vapid-public-key")
check("PUSH GET vapid-public-key", r)
try:
    d = r.json()
    if "publicKey" in d:
        val = d["publicKey"]
        if val:
            results.append((OK, "PUSH publicKey presente y no vacía", ""))
        else:
            results.append((WRN, "PUSH publicKey vacía (VAPID no configurado)", ""))
    else:
        results.append((ERR, "PUSH falta clave 'publicKey'", f" — {d}"))
except:
    results.append(("❌", "PUSH JSON parse error", ""))


# ─────────────────────────────────────────────
# BLOQUE 11: Export Excel
# ─────────────────────────────────────────────
r = s.get(f"{BASE}/export_excel")
check("EXCEL GET /export_excel", r)
ct = r.headers.get("Content-Type", "")
if "spreadsheet" in ct or "excel" in ct or "octet" in ct:
    results.append(("✅", f"EXCEL Content-Type correcto: {ct}", ""))
else:
    results.append(("❌", f"EXCEL Content-Type inesperado: {ct}", ""))

# ─────────────────────────────────────────────
# BLOQUE 12: Rutas inexistentes
# ─────────────────────────────────────────────
r = s.get(f"{BASE}/ruta_que_no_existe_xyz")
check("404 ruta inexistente devuelve 404", r, expected_status=404)


# ─────────────────────────────────────────────
# BLOQUE 13: Wizard / save_config
# ─────────────────────────────────────────────
wizard_data = {
    "business_name": "Test Business SL",
    "sector": "Consultoría",
    "tone": "profesional",
    "services": "Desarrollo de software e inteligencia artificial",
    "business_instructions": "Responde siempre en español.",
    "city": "Madrid"
}
r = s.post(f"{BASE}/save_config", data=wizard_data, allow_redirects=True)
check("WIZARD POST /save_config guarda y redirige a dashboard", r,
      check_html=["Test Business SL"])

r = s.get(f"{BASE}/dashboard", allow_redirects=True)
check("WIZARD tras save_config dashboard muestra Asistente Activo", r,
      check_html=["Asistente Activo"],
      check_not_html=["Asistente Dormido"])


# ─────────────────────────────────────────────
# BLOQUE 14: Logout
# ─────────────────────────────────────────────
r = s.get(f"{BASE}/logout", allow_redirects=True)
check("AUTH logout redirige a login", r, check_html=["login", "Login", "Iniciar"])

r = s.get(f"{BASE}/dashboard", allow_redirects=False)
check("AUTH tras logout /dashboard redirige (no accesible)", r, expected_status=302)


# ─────────────────────────────────────────────
# INFORME FINAL
# ─────────────────────────────────────────────
print("\n" + "="*65)
print("  INFORME DE PRUEBAS AUTOMATIZADAS — ZEPTAI")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*65)

passed = sum(1 for r in results if r[0] == OK)
failed = sum(1 for r in results if r[0] == ERR)
warnings = sum(1 for r in results if r[0] == WRN)
total = len(results)

for status, name, note in results:
    print(f"  {status}  {name}{note}")

print("="*65)
print(f"  TOTAL: {total} pruebas | {passed} OK | {failed} ERROR | {warnings} AVISO")
print("="*65)

sys.exit(0 if failed == 0 else 1)
