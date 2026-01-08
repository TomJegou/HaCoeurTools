#!/bin/bash

# =======================================================
# Configuration et Verification de l'Argument
# =======================================================

# Verifie si un argument a ete fourni
if [ -z "$1" ]; then
    echo "Erreur: Veuillez fournir le nom du fichier dump memoire."
    echo "Usage: $0 <nom_du_fichier.dmp>"
    exit 1
fi

# Definitions
DUMP_FILE="$1"
VOL_COMMAND_PREFIX="/opt/tools/volatility3/venv/bin/python3 /opt/tools/volatility3/venv/bin/vol -f ${DUMP_FILE}"
TIMEOUT_HASH="60s"      # Duree maximale pour l'extraction de hashdump
TIMEOUT_PER_USER="30s"  # 30 secondes pour CHAQUE utilisateur
EXTRACT_DIR="extracte"  # Dossier de destination pour les extractions
WORDLIST_PATH="/usr/share/wordlists/rockyou.txt"
JOHN_BIN="/opt/tools/john/run/john"

echo "======================================================"
echo "    ANALYSE FORENSIQUE : ${DUMP_FILE}"
echo "======================================================"

# -----------------------------------------------------------------------------
# PARTIE 1: IDENTIFIANTS UNIQUES
# -----------------------------------------------------------------------------
echo "🔎 PARTIE 1: Extraction des identifiants uniques (windows.envars)..."
echo "---"

${VOL_COMMAND_PREFIX} windows.envars | \
    grep -E 'USERNAME|USERDOMAIN|COMPUTERNAME' | \
    awk '
{
    # $4=Variable, $5...=Valeur
    if ($5 != "") {
        printf "%s\t%s\n", $4, substr($0, index($0,$5))
    }
}' | sort | uniq

echo "---"
echo "✅ Fin de la Partie 1."

echo ""
# -----------------------------------------------------------------------------
# PARTIE 2: EXTRACTION ET CAPTURE DES HACHAGES AVEC TIMEOUT
# -----------------------------------------------------------------------------
echo "🔑 PARTIE 2: Tentative d'extraction et de capture des hachages (windows.hashdump) (Max ${TIMEOUT_HASH})..."
echo "---"

HASH_DATA=$(timeout ${TIMEOUT_HASH} ${VOL_COMMAND_PREFIX} windows.hashdump 2>/dev/null)
HASH_EXIT_CODE=$?

if [ ${HASH_EXIT_CODE} -eq 124 ]; then
    echo "⚠️ La commande hashdump a ete interrompue apres ${TIMEOUT_HASH} (Timeout)."
fi

if echo "${HASH_DATA}" | grep -q "^User"; then
    echo "✅ Hachages bruts captures pour la Partie 3."
else
    echo "❌ Aucun hachage n'a pu etre extrait (ou la commande a echoue/timeout)."
fi

echo "---"
echo "✅ Fin de la Partie 2."

echo ""
# -----------------------------------------------------------------------------
# PARTIE 3: TRAITEMENT ET CRACKING INDIVIDUEL PAR UTILISATEUR
# -----------------------------------------------------------------------------
echo "🔨 PARTIE 3: Sauvegarde des hachages et tentative de cracking (Max ${TIMEOUT_PER_USER} par utilisateur)."
echo "---"

# Verifie si des hachages ont ete captures
if echo "${HASH_DATA}" | grep -q "^User"; then

    # --- Sous-Partie 3.1: Preparation ---
    mkdir -p "${EXTRACT_DIR}"
    echo "Dossier '${EXTRACT_DIR}' cree."

    # Fichier d'archive (contient tous les hachages au format John)
    ARCHIVE_HASHDUMP_FILE="${EXTRACT_DIR}/hashdump_NTLM_all.txt"
    > "${ARCHIVE_HASHDUMP_FILE}"

    # Verifie la wordlist une seule fois
    if [ ! -f "${WORDLIST_PATH}" ]; then
        echo "❌ Wordlist introuvable: ${WORDLIST_PATH}. Le cracking John est omis."
        WORDLIST_EXISTS=false
    else
        WORDLIST_EXISTS=true
        echo "Wordlist ${WORDLIST_PATH} trouvee. Debut du cracking..."
    fi

    echo "---"

    # --- Sous-Partie 3.2: Boucle de Traitement et Cracking ---

    # Bloc AWK nettoye (sans espaces non-standard)
    echo "${HASH_DATA}" | tail -n +2 | awk '
    NF >= 4 && $NF != "nthash" {
        NTHASH = $NF;
        LMHASH = $(NF-1);
        RID = $(NF-2);
        USER = "";
        for (i=1; i <= (NF-3); i++) {
            USER = (USER == "" ? $i : USER " " $i);
        }
        print USER "\t" RID "\t" LMHASH "\t" NTHASH
    }' | while IFS=$'\t' read -r USER RID LMHASH NTHASH; do

        SAFE_USER=$(echo "$USER" | tr -d '[:space:]')

        # S'assurer que les variables ne sont pas vides
        if [ -n "${SAFE_USER}" ] && [ -n "${LMHASH}" ] && [ -n "${NTHASH}" ]; then

            # --- Etape A: Sauvegarde (pour l'archivage) ---

            # Fichier individuel (format PWDUMP: User:RID:LM:NT)
            NT_HASH_FILE_PWDUMP="${EXTRACT_DIR}/${SAFE_USER}_hash_NT.txt"
            echo "${SAFE_USER}:${RID}:${LMHASH}:${NTHASH}" > "$NT_HASH_FILE_PWDUMP"

            # Fichier d'archive combine (format JOHN: User:::LM:NT)
            echo "${SAFE_USER}:::${LMHASH}:${NTHASH}" >> "${ARCHIVE_HASHDUMP_FILE}"

            echo "    -> Prepare: ${SAFE_USER}."

            # --- Etape B: Cracking (si la wordlist existe) ---
            if [ "$WORDLIST_EXISTS" = true ]; then

                # Lancer John avec le timeout par utilisateur
                timeout ${TIMEOUT_PER_USER} ${JOHN_BIN} --format=NT --wordlist="${WORDLIST_PATH}" "${NT_HASH_FILE_PWDUMP}" >/dev/null 2>&1

                # Verifier les resultats
                CRACKED_OUTPUT=$(${JOHN_BIN} --show --format=NT "${NT_HASH_FILE_PWDUMP}" 2>/dev/null)

                # Extraire le mot de passe (le 2eme champ)
                CRACKED_PASSWORD=$(echo "${CRACKED_OUTPUT}" | awk -F: '{print $2}')

                # Verifier si le mot de passe a ete trouve
                if [ -n "${CRACKED_PASSWORD}" ] && [ "${CRACKED_PASSWORD}" != "${SAFE_USER}" ]; then
                    echo "    ✅ MOT DE PASSE TROUVE: ${SAFE_USER} -> ${CRACKED_PASSWORD}"
                else
                    echo "    ❌ Mdp non trouve (dans la limite des ${TIMEOUT_PER_USER})."
                fi
            fi

            echo "---" # Separateur par utilisateur
        fi
    done

else
    echo "⏭️ Passage de la Partie 3 : Aucun hachage n'a ete trouve."
fi

echo "======================================================"
# ... (Après la fin de la Partie 3)

echo ""
# -----------------------------------------------------------------------------
# PARTIE 4: ANALYSE INTELLIGENTE (FILTRAGE DU BRUIT)
# -----------------------------------------------------------------------------
echo "🧠 PARTIE 4: Analyse ciblée et filtrage des artefacts..."
echo "---"

# --- 4.1 NETSCAN INTELLIGENT ---
echo "📡 [Réseau] Recherche de connexions suspectes..."

NET_DATA=$(${VOL_COMMAND_PREFIX} windows.netscan 2>/dev/null)

if [ -z "$NET_DATA" ]; then
    echo "   ⚠️ Aucune donnée réseau ou plugin échoué."
else
    # En-tête personnalisé pour rendre la lecture plus facile
    # On utilise printf pour aligner les colonnes (Offset, Proto, LocalIP, LocalPort, RemoteIP, RemotePort, State, PID, Owner)
    HEADER_FMT="      %-10s %-6s %-16s %-8s %-16s %-8s %-12s %-6s %s\n"
    printf "$HEADER_FMT" "OFFSET" "PROTO" "SRC_IP" "PORT" "DST_IP" "PORT" "ETAT" "PID" "PROCESSUS"
    echo "      -------------------------------------------------------------------------------------------------------"

    # Fonction pour afficher les lignes formatées (on garde l'alignement d'origine de Volatility qui est généralement bon, 
    # mais on filtre pour n'avoir que ce qui nous intéresse).
    
    # 1. Connexions établies
    echo "   👉 Connexions ACTIVES (ESTABLISHED) :"
    echo "$NET_DATA" | grep "ESTABLISHED" | awk '{print "      " $0}' || echo "      Aucune."

    # 2. Services d'écoute suspects
    echo "   👉 Services Sensibles (RDP, SSH, Web, etc.) :"
    echo "$NET_DATA" | grep -E ":3389|:22|:8080|:4444|:1337|:80 " | grep "LISTENING" | awk '{print "      " $0}' || echo "      Aucun détecté."
fi
echo "---"
# --- 4.2 CMDLINE SUSPECTE ---
echo "💻 [Processus] Recherche de lignes de commandes douteuses..."

CMD_DATA=$(${VOL_COMMAND_PREFIX} windows.cmdline 2>/dev/null)

if [ -z "$CMD_DATA" ]; then
    echo "   ⚠️ Impossible de lire les lignes de commande."
else
    # On cherche PowerShell (souvent utilisé pour les attaques) et cmd.exe
    echo "   👉 Activité PowerShell / CMD :"
    echo "$CMD_DATA" | grep -iE "powershell|cmd.exe" | grep -v "volatility" | head -n 10 | awk '{print "      " $0}'
    
    # On cherche les indices d'encodage (souvent malveillant) ou téléchargement
    echo "   👉 Arguments suspects (Encoded, Download, Temp) :"
    echo "$CMD_DATA" | grep -iE "\-enc|bypass|hidden|DownloadString|AppData|Temp" | awk '{print "      " $0}'
fi
echo "---"

# --- 4.3 FILESCAN CIBLÉ (CHASSE AU TRÉSOR) ---
echo "📂 [Fichiers] 'Chasse au trésor' dans les dossiers utilisateurs..."

# Ici, on combine deux filtres :
# 1. LE LIEU : On ne regarde que le Bureau, Documents, Téléchargements
# 2. L'OBJET : On ne regarde que les extensions intéressantes (txt, pdf, zip, kdbx, png...)
# 3. LE NOM : On cherche explicitement "flag", "pass", "secret"

${VOL_COMMAND_PREFIX} windows.filescan 2>/dev/null | \
    grep -iE "Desktop|Downloads|Documents|Users" | \
    grep -iE "\.txt|\.rtf|\.pdf|\.kdbx|\.zip|\.rar|\.7z|\.py|\.sh|flag|pass|secret|brouillon" | \
    grep -vE "\.lnk|\.ini|\.sys|\.dll" | \
    sort | uniq | \
    awk '{print "      📍 " $0}'

echo "---"
echo "✅ Fin de l'analyse intelligente."
echo "======================================================"

echo "🌳 PARTIE 7: Arborescence des processus (windows.pstree)..."
echo "---"
# --- 4.4 ARBORESCENCE NETTOYÉE (PSTREE) ---
echo "🌳 [Processus] Arborescence simplifiée (Relations Père-Fils)..."

echo "---"

# On récupère le pstree
# L'astuce AWK :
# 1. Si la ligne commence par "PID", on imprime l'en-tête simplifié.
# 2. Si le 1er champ ($1) contient "*", c'est un enfant. On affiche $1(Arbre) $2(PID) $3(PPID) $4(Nom).
# 3. Sinon, c'est un parent racine. On affiche "" $1(PID) $2(PPID) $3(Nom).

${VOL_COMMAND_PREFIX} windows.pstree 2>/dev/null | awk '
BEGIN { printf "%-10s %-8s %-8s %s\n", "ARBRE", "PID", "PPID", "NOM_PROCESSUS"; print "--------------------------------------------------------" }
/^PID/ { next } # On saute l an-tête original
{
    # Cas 1 : Ligne avec étoiles (enfant) ex: "** 904 560 svchost.exe"
    if ($1 ~ /^\*/) {
        printf "%-10s %-8s %-8s %s\n", $1, $2, $3, $4
    }
    # Cas 2 : Ligne sans étoiles (racine) ex: "4 0 System"
    else {
        printf "%-10s %-8s %-8s %s\n", "", $1, $2, $3
    }
}'

echo "---"
echo "---"
echo "®️ PARTIE 8: Vérification de la persistance (Run Keys)..."
echo "---"
# Affiche les clés 'Run' qui lancent des programmes au démarrage${VOL_COMMAND_PREFIX} windows.registry.printkey --key "Software\Microsoft\Windows\CurrentVersion\Run"
echo "---"
