import streamlit as st
import requests
import json
import re
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="OPI - OSINT Private Investigator",
    page_icon="🕵️‍♂️",
    layout="wide"
)

# --- CSS PERSONNALISÉ ---
st.markdown("""
<style>
    .stChatMessage { border-radius: 12px; margin-bottom: 8px; }
    .target-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: bold;
        margin: 4px;
    }
    .badge-ip { background: #1a3a5c; color: #4fc3f7; border: 1px solid #4fc3f7; }
    .badge-email { background: #1a3a2c; color: #66bb6a; border: 1px solid #66bb6a; }
    .badge-pseudo { background: #3a1a3a; color: #ce93d8; border: 1px solid #ce93d8; }
    .badge-image { background: #3a2a1a; color: #ffb74d; border: 1px solid #ffb74d; }
    .badge-domain { background: #1a2a3a; color: #90caf9; border: 1px solid #90caf9; }
    .badge-unknown { background: #2a2a2a; color: #bdbdbd; border: 1px solid #bdbdbd; }
</style>
""", unsafe_allow_html=True)

# --- DÉTECTION DU TYPE DE CIBLE ---
def detect_target_type(text):
    text_lower = text.lower()
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    domain_pattern = r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b'
    url_pattern = r'https?://[^\s]+'

    if re.search(ip_pattern, text):
        return "ip"
    if re.search(email_pattern, text):
        return "email"
    if re.search(url_pattern, text_lower) and any(ext in text_lower for ext in ['.jpg', '.png', '.jpeg', '.gif', '.webp', '.bmp']):
        return "image"
    if any(kw in text_lower for kw in ['photo', 'image', 'screenshot', 'capture', 'img', 'picture']):
        return "image"
    if any(kw in text_lower for kw in ['pseudo', 'username', 'profil', 'compte', 'instagram', 'twitter', 'facebook', 'tiktok', '@', 'linkedin']):
        return "pseudo"
    if re.search(domain_pattern, text) and any(kw in text_lower for kw in ['site', 'domaine', 'domain', 'url', 'web']):
        return "domain"
    return "unknown"

def extract_tools_from_response(response_text):
    """Extrait les noms d'outils et leurs liens depuis la réponse de l'IA."""
    tools = []
    tool_name_pattern = r'\*{0,2}Outil\s*#\d+\s*:\s*([^\*\n\r]+)\*{0,2}'
    link_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    url_label_pattern = r'(?:🔗[^\:]*:\s*)(https?://[^\s\n]+)'

    tool_names = re.findall(tool_name_pattern, response_text, re.IGNORECASE)
    links = re.findall(link_pattern, response_text)
    url_labels = re.findall(url_label_pattern, response_text)

    seen_names = set()
    for name in tool_names:
        name = name.strip().strip('*').strip()
        if name and name not in seen_names and len(name) < 60:
            seen_names.add(name)
            url = None
            for link_text, link_url in links:
                if any(part.lower() in name.lower() or name.lower() in link_text.lower()
                       for part in name.split()):
                    url = link_url
                    break
            if not url and url_labels:
                url = url_labels[0]
            tools.append({"name": name, "url": url})

    if not tools and links:
        for link_text, link_url in links[:4]:
            if link_text not in seen_names:
                seen_names.add(link_text)
                tools.append({"name": link_text, "url": link_url})

    return tools[:5]

TARGET_LABELS = {
    "ip": ("💻 Adresse IP", "badge-ip"),
    "email": ("📧 Email", "badge-email"),
    "pseudo": ("👤 Pseudo / Compte Social", "badge-pseudo"),
    "image": ("📸 Image / Photo", "badge-image"),
    "domain": ("🌐 Domaine / Site Web", "badge-domain"),
    "unknown": ("❓ Type non détecté", "badge-unknown"),
}

TARGET_ICONS = {
    "ip": "💻", "email": "📧", "pseudo": "👤",
    "image": "📸", "domain": "🌐", "unknown": "❓"
}

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
Tu es "OPI", un Expert Senior en OSINT et investigation numérique avec 15 ans d'expérience.
Tes références principales sont l'OSINT Framework (osintframework.com) et la Map Malfrats Industries (map.malfrats.industries).

## 🎯 TON COMPORTEMENT CONVERSATIONNEL

Tu es INTERACTIF. Avant de donner des outils, tu POSES DES QUESTIONS si tu manques d'informations cruciales.

**Quand poser des questions ?**
- Si le type de cible est ambigu (pseudo ou email ?)
- Si l'objectif de l'enquête n'est pas clair (trouver un propriétaire ? détecter une menace ? retrouver une personne ?)
- Si tu as besoin de contexte supplémentaire pour affiner les outils
- Si plusieurs approches existent et que l'utilisateur doit choisir

**Règle d'or** : Pose 1 à 3 questions MAX. Sois direct et synthétique dans tes questions.

---

## 🧠 LOGIQUE DE DÉCISION OSINT

### CAS 1 : ADRESSE IP
- Sources: OSINT Framework > "IP Address" | Malfrats > "Network"
- Outils prioritaires: IPinfo.io, Shodan.io, AbuseIPDB, VirusTotal, Censys
- Questions à poser si besoin: "S'agit-il d'une IP suspecte (attaque) ou d'une IP à identifier (propriétaire) ?"

### CAS 2 : EMAIL
- Sources: OSINT Framework > "Email Address"
- Outils prioritaires: Hunter.io, HaveIBeenPwned, Epieos, Holehe, EmailRep.io
- Questions à poser si besoin: "Cherches-tu à vérifier si l'email a fuité, ou à retrouver la personne derrière ?"

### CAS 3 : PSEUDO / COMPTE SOCIAL
- Sources: OSINT Framework > "Username" | Malfrats > "Social Networks"
- Outils prioritaires: Sherlock, WhatsMyName, Namechk, Maigret, Social-Analyzer
- IMPORTANT: Ne propose JAMAIS HaveIBeenPwned pour un pseudo social
- Questions à poser si besoin: "Sur quelle plateforme as-tu trouvé ce pseudo ? Le but est de trouver d'autres comptes liés ?"

### CAS 4 : IMAGE / PHOTO
- Sources: OSINT Framework > "Digital Side of Media" > "Images" | Malfrats > "Images"
- Outils prioritaires: Google Images (reverse), Yandex Images, TinEye, FotoForensics, ExifTool
- Questions à poser si besoin: "As-tu l'URL de l'image ou le fichier ? Cherches-tu son origine ou des métadonnées EXIF ?"

### CAS 5 : DOMAINE / SITE WEB
- Sources: OSINT Framework > "Domain Name" | Malfrats > "Domain"
- Outils prioritaires: Whois, ViewDNS.info, DNSDumpster, Shodan, Wayback Machine
- Questions à poser si besoin: "Veux-tu identifier le propriétaire, cartographier l'infrastructure, ou retrouver un contenu supprimé ?"

---

## 📝 FORMAT DE RÉPONSE (quand tu as assez d'infos)

**1. 🎯 Analyse de la Cible**
Résume ce que tu as compris de la cible et de l'objectif.

**2. 🛠️ Top 3-5 Outils Recommandés**

Pour chaque outil:
**Outil #N : [Nom]**
* 🔗 **Lien direct** : [URL]
* 📂 **Source OSINT** : [OSINT Framework > Catégorie] ou [Malfrats > Catégorie]
* 💡 **Utilité spécifique** : [Pourquoi cet outil pour CE cas précis]
* 🎓 **Procédure en 3 étapes** :
  1. [Étape concrète]
  2. [Étape concrète]
  3. [Ce qu'on cherche dans les résultats]

**3. 🔄 Stratégie d'Investigation Suggérée**
Un ordre logique d'utilisation des outils (workflow).

**4. ⚠️ Rappel Éthique & Légal**
Court rappel sur l'éthique OSINT.

**5. ❓ Questions de suivi**
Si pertinent, propose 1-2 pistes d'approfondissement sous forme de questions.

---
Utilise le Markdown. Sois précis, concret, et adapte-toi au niveau de l'utilisateur.
Si l'utilisateur répond à une question que tu as posée, intègre sa réponse dans ton analyse affinée.
"""

# --- INITIALISATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "detected_targets" not in st.session_state:
    st.session_state.detected_targets = []
if "target_per_message" not in st.session_state:
    st.session_state.target_per_message = []
if "search_history" not in st.session_state:
    # Format: [{"query": str, "target_type": str, "tools": [{"name": str, "url": str|None}], "time": str}]
    st.session_state.search_history = []

# --- SIDEBAR ---
with st.sidebar:
    st.header("🕵️‍♂️ OPI")
    st.markdown("---")

    st.subheader("📚 Sources Officielles")
    st.link_button("🌐 OSINT Framework", "https://osintframework.com/", use_container_width=True)
    st.link_button("🗺️ Map Malfrats", "https://map.malfrats.industries/", use_container_width=True)

    st.markdown("---")
    st.subheader("⚙️ Configuration")
    model_choice = "mistral"
    st.caption("🤖 Modèle : **Mistral**")
    temperature = st.slider("Créativité (Temperature)", 0.0, 1.0, 0.3, 0.05,
                            help="0 = réponses précises, 1 = plus créatif")

    st.markdown("---")

    # --- HISTORIQUE DES RECHERCHES ---
    st.subheader("🗂️ Historique des Recherches")

    if st.session_state.search_history:
        col_hist1, col_hist2 = st.columns(2)
        with col_hist1:
            st.caption(f"**{len(st.session_state.search_history)}** recherche(s)")
        with col_hist2:
            if st.button("🗑️ Vider", use_container_width=True):
                st.session_state.search_history = []
                st.rerun()

        for entry in reversed(st.session_state.search_history):
            icon = TARGET_ICONS.get(entry["target_type"], "❓")
            label, css = TARGET_LABELS.get(entry["target_type"], TARGET_LABELS["unknown"])
            short_query = entry["query"][:32] + ("…" if len(entry["query"]) > 32 else "")

            with st.expander(f"{icon} {short_query}", expanded=False):
                st.markdown(f'<span class="target-badge {css}">{label}</span>', unsafe_allow_html=True)
                st.caption(f"🕐 {entry['time']}")
                if entry["tools"]:
                    st.markdown("**🛠️ Outils proposés :**")
                    for tool in entry["tools"]:
                        if tool.get("url"):
                            st.markdown(f"• [{tool['name']}]({tool['url']})")
                        else:
                            st.markdown(f"• {tool['name']}")
                else:
                    st.caption("_(questions de clarification posées)_")
    else:
        st.caption("Aucune recherche pour le moment.")

    st.markdown("---")
    if st.button("🗑️ Nouvelle Enquête", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.session_state.detected_targets = []
        st.session_state.target_per_message = []
        st.rerun()

    st.markdown("---")
    st.info("💡 **Conseil** : Décris ta cible avec un maximum de contexte pour obtenir les meilleurs outils.")

# --- INTERFACE PRINCIPALE ---
st.title("🕵️‍♂️ OPI — OSINT Private Investigator")
st.markdown("""
> *Décrivez votre cible et votre objectif. Je vous guiderai avec les meilleurs outils OSINT, basés sur les frameworks de référence.*
""")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown('<span class="target-badge badge-ip">💻 IP</span>', unsafe_allow_html=True)
with col2:
    st.markdown('<span class="target-badge badge-email">📧 Email</span>', unsafe_allow_html=True)
with col3:
    st.markdown('<span class="target-badge badge-pseudo">👤 Pseudo</span>', unsafe_allow_html=True)
with col4:
    st.markdown('<span class="target-badge badge-image">📸 Image</span>', unsafe_allow_html=True)
with col5:
    st.markdown('<span class="target-badge badge-domain">🌐 Domaine</span>', unsafe_allow_html=True)

st.markdown("---")

# --- AFFICHAGE CONVERSATION ---
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            targets = st.session_state.get("target_per_message", [])
            msg_index = i // 2
            if msg_index < len(targets) and targets[msg_index] != "unknown":
                t = targets[msg_index]
                label, css = TARGET_LABELS.get(t, TARGET_LABELS["unknown"])
                st.markdown(f'<span class="target-badge {css}">Cible détectée : {label}</span>', unsafe_allow_html=True)
        st.markdown(message["content"])

# --- EXEMPLES ---
examples = [
    "J'ai une IP suspecte : 185.220.101.45 — je veux savoir si c'est un nœud Tor ou un serveur malveillant",
    "J'ai trouvé un pseudo 'shadow_wolf99' sur Telegram, je veux trouver ses autres comptes",
    "J'ai une URL d'image bizarre : https://example.com/photo.jpg — besoin d'analyser les métadonnées",
    "Email inconnu : contact@domaine-bizarre.ru — est-il lié à des fuites de données ?",
]

if not st.session_state.messages:
    st.markdown("**💡 Exemples de requêtes :**")
    cols = st.columns(2)
    for idx, ex in enumerate(examples):
        with cols[idx % 2]:
            if st.button(f"📌 {ex[:60]}...", key=f"ex_{idx}", use_container_width=True):
                st.session_state.prefill = ex
                st.rerun()

prefill_value = st.session_state.pop("prefill", "")

if prompt := st.chat_input("Décrivez votre cible : IP, email, pseudo, image, domaine...") or prefill_value:
    if prefill_value and not prompt:
        prompt = prefill_value

    target_type = detect_target_type(prompt)
    st.session_state.detected_targets.append(target_type)
    st.session_state.target_per_message.append(target_type)

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        if target_type != "unknown":
            label, css = TARGET_LABELS[target_type]
            st.markdown(f'<span class="target-badge {css}">Cible détectée : {label}</span>', unsafe_allow_html=True)
        st.markdown(prompt)

    # --- APPEL IA ---
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        context_message = f"""
[CONTEXTE DE SESSION]
- Type de cible détecté automatiquement: {TARGET_LABELS.get(target_type, ('Inconnu', ''))[0]}
- Nombre de messages dans cette session: {len(st.session_state.messages)}
- Historique disponible: {'Oui' if len(st.session_state.messages) > 1 else 'Non (premier message)'}

[MESSAGE UTILISATEUR]
{prompt}
"""
        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in st.session_state.messages[:-1]:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
        api_messages.append({"role": "user", "content": context_message})

        try:
            with st.spinner("🔍 Analyse OSINT en cours..."):
                r = requests.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": model_choice,
                        "messages": api_messages,
                        "stream": True,
                        "options": {"temperature": temperature, "num_ctx": 4096}
                    },
                    stream=True,
                    timeout=120
                )

                if r.status_code == 200:
                    for line in r.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                if 'message' in chunk and 'content' in chunk['message']:
                                    full_response += chunk['message']['content']
                                    message_placeholder.markdown(full_response + "▌")
                                if chunk.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue

                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

                    # --- SAUVEGARDE DANS L'HISTORIQUE ---
                    tools_found = extract_tools_from_response(full_response)
                    st.session_state.search_history.append({
                        "query": prompt,
                        "target_type": target_type,
                        "tools": tools_found,
                        "time": datetime.now().strftime("%d/%m %H:%M")
                    })

                    word_count = len(full_response.split())
                    st.caption(f"📊 ~{word_count} mots | Mistral | T°: {temperature}")

                else:
                    st.error(f"❌ Erreur API Ollama: {r.status_code} — {r.text}")

        except requests.exceptions.ConnectionError:
            st.error("""
❌ **Impossible de se connecter à Ollama.**

Vérifiez que :
1. Ollama est installé : https://ollama.ai/
2. Le service tourne : `ollama serve`
3. Le modèle est téléchargé : `ollama pull mistral`
4. Le port 11434 est accessible
            """)
        except requests.exceptions.Timeout:
            st.error("⏱️ Timeout — Mistral met trop de temps à répondre. Vérifiez les ressources de votre machine.")
        except Exception as e:
            st.error(f"⚠️ Erreur inattendue : {e}")
