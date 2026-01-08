import streamlit as st
import requests

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="OSINT Private Investigator",
    page_icon="🕵️‍♂️",
    layout="wide"
)

# --- INSTRUCTIONS POUR L'IA (SYSTEM PROMPT) ---
SYSTEM_PROMPT = """
Tu es un Expert Senior en OSINT. Tes deux bibles sont :
1. **OSINT Framework** (https://osintframework.com/)
2. **Map Malfrats Industries** (https://map.malfrats.industries/)

TA MISSION : ANALYSER L'ENTRÉE ET ROUTER VERS LES BONS OUTILS.

---
### LOGIQUE DE DÉCISION (Suis scrupuleusement ces chemins) :

**CAS 1 : L'utilisateur fournit une IMAGE (URL ou description)**
* *Où chercher ?* : OSINT Framework > "Digital Side of Media" > "Images" OU Malfrats > "Images".
* *Types d'outils attendus* : Recherche inversée (Reverse Image Search), Analyse EXIF, Forensics, Géolocalisation visuelle.
* *Exemples* : Google Images, Yandex Images, TinEye, ExifTool, FotoForensics.

**CAS 2 : L'utilisateur fournit une ADRESSE IP**
* *Où chercher ?* : OSINT Framework > "IP Address" OU Malfrats > "Network".
* *Types d'outils attendus* : Géolocalisation, Threat Intelligence, Ports ouverts.
* *Exemples* : IPinfo.io, Shodan, VirusTotal, AbuseIPDB.

**CAS 3 : L'utilisateur fournit un PSEUDO ou un COMPTE SOCIAL (Insta, Twitter...)**
* *Où chercher ?* : OSINT Framework > "Username" OU Malfrats > "Social Networks".
* *Types d'outils attendus* : Énumération de profil, Viewers anonymes (pour Insta), Analyse de tweets.
* *Exemples* : Sherlock, Namechk, WhatsMyName, Instaloader, Imginn.
* *INTERDIT* : Ne propose JAMAIS "HaveIBeenPwned" pour une recherche de profil social !

**CAS 4 : L'utilisateur fournit un EMAIL**
* *Où chercher ?* : OSINT Framework > "Email Address".
* *Types d'outils attendus* : Breach data, Format verification.
* *Exemples* : Hunter.io, Epios, HaveIBeenPwned.

---
### 📝 FORMAT DE RÉPONSE OBLIGATOIRE :

**1. 🎯 Analyse de la Cible**
"J'ai détecté que votre cible est : **[TYPE DÉTECTÉ]**."

**2. 🛠️ Top 3 Outils Recommandés (Basés sur les frameworks)**

**Outil #1 : [Nom de l'outil]**
* 🔗 **Lien** : https://fr.wikipedia.org/wiki/Fonctionnelle
* 📂 **Catégorie Source** : (Ex: "Malfrats > Images" ou "OSINT Framework > Username")
* 💡 **Pourquoi cet outil ?** : [Explication de son rôle précis pour cette donnée]
* 🎓 **Tuto Rapide** :
    1. [Action 1]
    2. [Action 2]
    3. [Action 3]

*(Idem pour Outil #2 et Outil #3)*

**3. ⚠️ Note Légale**
Rappel court sur l'éthique.

Utilise le Markdown pour le gras et les liens.
"""

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.header("📚 Sources Officielles")
    st.markdown("Le bot suit la logique de ces cartes :")
    st.link_button("🌐 OSINT Framework", "https://osintframework.com/")
    st.link_button("🗺️ Map Malfrats Industries", "https://map.malfrats.industries/")
    st.divider()
    st.info("Assurez-vous qu'Ollama tourne en local sur le port 11434.")
    if st.button("🗑️ Nouvelle Enquête"):
        st.session_state.messages = []
        st.rerun()

# --- INTERFACE PRINCIPALE ---
st.title("🕵️‍♂️ Assistant OSINT Intelligent")
st.markdown("""
**Je détecte automatiquement votre type de preuve :**
* 📸 **Image** (URL ou contexte) -> Je cherche des outils de Reverse Search / EXIF.
* 💻 **IP** -> Je cherche des outils de Géolocalisation / Threat Intel.
* 👤 **Pseudo/Social** -> Je cherche des outils de profilage (sans mots de passe).
""")

# Initialisation de l'historique
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage des messages précédents
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie utilisateur
if prompt := st.chat_input("Ex: J'ai une IP 192.168.1.55 OU J'ai une photo de vacances..."):
    # 1. Ajouter le message utilisateur à l'historique
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Appel à l'IA (Ollama)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            with st.spinner("Consultation des cartes OSINT et sélection des outils..."):
                r = requests.post("http://localhost:11434/api/chat", 
                                  json={
                                      "model": "mistral", # Assure-toi d'avoir fait 'ollama pull mistral'
                                      "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *st.session_state.messages],
                                      "stream": False
                                  })
                
                if r.status_code == 200:
                    response_json = r.json()
                    full_response = response_json['message']['content']
                    message_placeholder.markdown(full_response)
                    
                    # Sauvegarde de la réponse
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    st.error(f"Erreur API Ollama: {r.status_code}")
                    
        except requests.exceptions.ConnectionError:
            st.error("❌ Impossible de se connecter à Ollama. Vérifie que l'application tourne (http://localhost:11434).")
        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")