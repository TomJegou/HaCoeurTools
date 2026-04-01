package main

import (
	"html/template"
	"log"
	"net/http"
	"os"
	"time"

	"MaisonBlanche/parser" // Vérifie bien le nom de ton module dans go.mod
)

type PageData struct {
	Query        string
	Results      []parser.Result
	Files        []string // Liste de tous les fichiers pour le menu déroulant
	SelectedFile string   // Le fichier actuellement filtré
	SearchTime   string
	Error        string
	HasSearched  bool
}

func main() {
	// Création du dossier data s'il n'existe pas
	_ = os.Mkdir("data", 0755)

	http.HandleFunc("/", handleSearch)

	port := ":8080"
	log.Printf("🚀 Serveur léger démarré sur http://localhost%s", port)
	log.Fatal(http.ListenAndServe(port, nil))
}

func handleSearch(w http.ResponseWriter, r *http.Request) {
	queryStr := r.URL.Query().Get("q")
	filterFile := r.URL.Query().Get("file") // Nouveau paramètre de filtre

	data := PageData{
		Query:        queryStr,
		Files:        parser.GetFileList("data"),
		SelectedFile: filterFile,
		HasSearched:  false,
	}

	if queryStr != "" && len(queryStr) > 2 {
		data.HasSearched = true
		start := time.Now()

		// On passe le filtre à la fonction de recherche
		results, err := parser.SearchInFolder("data", queryStr, filterFile, 100)

		data.SearchTime = time.Since(start).String()
		if err != nil {
			data.Error = "Erreur lors de la lecture."
		} else {
			data.Results = results
		}
	}

	tmpl, _ := template.ParseFiles("templates/index.html")
	tmpl.Execute(w, data)
}
