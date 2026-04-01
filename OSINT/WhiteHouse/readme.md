# 🔍 WhiteHouse | OSINT Tool

[![Go Version](https://img.shields.io/badge/Go-1.20+-00ADD8?style=for-the-badge&logo=go)](https://go.dev/)
[![Security](https://img.shields.io/badge/Focus-OSINT%20%26%20Breach-red?style=for-the-badge)](https://github.com/TomJegou/HaCoeurTools)

**WhiteHoue** est un moteur de recherche ultra-rapide conçu pour scanner des dumps txt,csv,SQL et des bases de données massives (plusieurs Go) sans consommer de ressources disque supplémentaires. 

Contrairement aux solutions classiques, il utilise le **scanning parallèle** pour traiter vos données en temps réel, offrant une interface web moderne et intuitive pour vos investigations OSINT.(plus long pour la recherche)

## ✨ Fonctionnalités

- ⚡ **Scanning Multi-thread** : Utilise 100% de la puissance de votre processeur pour lire les fichiers en simultané.
- 📂 **Filtrage par Base** : Ciblez une base de données spécifique ou scannez tout le dossier `/data`.
- 🧠 **Extraction Intelligente** : Détection automatique et mise en avant des **Emails** et des **Adresses IP** via Regex.
- 🛡️ **Zéro Indexation** : Pas besoin de 10 Go d'espace disque pour un index, le scan se fait "à la volée".
- 🎨 **Interface Moderne** : UI propre avec Tailwind CSS, mode sombre pour les données brutes, et badges de catégories.
- 🚫 **Anti-Doublons** : Filtrage automatique des entrées identiques lors d'une recherche.

## 🚀 Installation & Utilisation

### Préparer vos données (IMPORTANT) ⚠️
Le programme ne peut scanner que les fichiers présents dans le dossier data.

Créez le dossier à la racine de WhiteHoue :
```bash
mkdir data
```
Ajoutez vos leaks : Copiez vos fichiers .txt, .csv, .sql directement dans le dossier /data.

Note : Le dossier data/ est listé dans le .gitignore. Vos fichiers de leaks ne seront jamais envoyés sur GitHub.

### Lancement
```Bash
go mod tidy
go run main.go
```
Accédez à l'outil via votre navigateur : 
```
http://localhost:8080
```

📂 Structure du répertoire
```Plaintext
WhiteHoue/
├── main.go          
├── parser/ 
|   └─ engine.go    
├── templates/       
|   └─ index.html
└── data/            
```
## ⚠️ Sécurité & Confidentialité
Ce projet est destiné à un usage OSINT et éducatif uniquement.

L'outil est conçu pour rester local : aucune donnée ne sort de votre machine.

Assurez-vous de respecter les législations en vigueur concernant la manipulation de données.

Développé pour la suite d'outils HaCoeurTools
