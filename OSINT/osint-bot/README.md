# OSINT Tool 

Ce projet est un assistant intelligent conçu pour guider vers les meilleurs outils OSINT.

le modèle **Mistral** (via Ollama) et une interface **Streamlit**, ce bot analyse et recommande des outils basés sur deux références majeures du domaine.

## 📚 Sources de données

L'IA base ses recommandations sur la structure et les outils présents dans :
* [OSINT Framework](https://osintframework.com/)
* [Map Malfrat Industries](https://map.malfrat.industries/)

## 🛠️ Stack Technique

* **Langage :** Python 3
* **Interface (GUI) :** Streamlit
* **Moteur IA :** Ollama (Local LLM)
* **Modèle :** Mistral

## ⚙️ Prérequis

Avant de lancer le projet, assurez-vous d'avoir installé :

1.  **Python** (version 3.8 ou supérieure).
2.  **Ollama** : Téléchargeable sur [ollama.com](https://ollama.com).
3.  **Streamlit** : Permet de crée une interface utilisateur
4.  **Fichier Python*** : créer un fichier app.py avec un prompt adapter a votre besoin

## **Démarrer le service Ollama**

1.  **Lancer l'application :**
    Exécutez la commande suivante à la racine du projet :
    ```bash
    python3 -m streamlit run app.py
    ```

2.  **Interagir :**
    Une page web s'ouvrira automatiquement. Posez votre question (ex: *"Je cherche un outil pour trouver des infos sur un pseudo"*) et l'IA vous recommandera les meilleurs outils issus des frameworks OSINT.

## 👤 Auteur

Projet réalisé par CARADEC Florian.
