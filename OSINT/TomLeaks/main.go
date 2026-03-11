package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
)

// Mutex pour éviter que les affichages se chevauchent dans le terminal
var printMutex sync.Mutex

func safePrint(format string, a ...interface{}) {
	printMutex.Lock()
	defer printMutex.Unlock()
	fmt.Printf(format, a...)
}

func searchInTxt(filePath string, keyword string, wg *sync.WaitGroup) {
	defer wg.Done() // Signale que cette Goroutine a terminé

	file, err := os.Open(filePath)
	if err != nil {
		safePrint("❌ Erreur (TXT) sur %s : %v\n", filePath, err)
		return
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	lineNum := 1

	for scanner.Scan() {
		line := scanner.Text()
		if strings.Contains(line, keyword) {
			safePrint("📄 [TXT Trouvé] %s (Ligne %d) : %s\n", filePath, lineNum, strings.TrimSpace(line))
		}
		lineNum++
	}
}

func searchInJson(filePath string, searchKey string, wg *sync.WaitGroup) {
	defer wg.Done() // Signale que cette Goroutine a terminé

	data, err := os.ReadFile(filePath)
	if err != nil {
		safePrint("❌ Erreur (JSON) sur %s : %v\n", filePath, err)
		return
	}

	var result map[string]interface{}
	if err := json.Unmarshal(data, &result); err != nil {
		// On ignore silencieusement ou on loggue les fichiers JSON mal formés
		return
	}

	var findKey func(map[string]interface{}, string) (interface{}, bool)
	findKey = func(m map[string]interface{}, keyToFind string) (interface{}, bool) {
		for k, v := range m {
			if k == keyToFind {
				return v, true
			}
			if subMap, ok := v.(map[string]interface{}); ok {
				if val, found := findKey(subMap, keyToFind); found {
					return val, true
				}
			}
		}
		return nil, false
	}

	if val, found := findKey(result, searchKey); found {
		safePrint("⚙️ [JSON Trouvé] %s -> Clé '%s' = %v\n", filePath, searchKey, val)
	}
}

func main() {
	reader := bufio.NewReader(os.Stdin)

	// 🛠️ Paramètres
	// Le dossier cible est fixe (le dossier courant). Changez cette valeur si besoin.
	dossierCible := "C:\\Users\\tomsa\\OneDrive\\Documents\\HaCoeurTools\\OSINT\\TomLeaks"

	fmt.Print("🔎 Mot/terme à chercher dans les .txt et dans les clés JSON (ex: Erreur) : ")
	motCleTXT, _ := reader.ReadString('\n')
	motCleTXT = strings.TrimSpace(motCleTXT)
	if motCleTXT == "" {
		motCleTXT = "Erreur"
	}
	cleJSON := motCleTXT

	var wg sync.WaitGroup

	fmt.Printf("🚀 Lancement de l'analyse dans le dossier : %s\n", dossierCible)
	fmt.Println("--------------------------------------------------")

	// filepath.WalkDir parcourt tous les fichiers et sous-dossiers
	err := filepath.WalkDir(dossierCible, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}

		// On ignore les dossiers (on ne veut traiter que les fichiers)
		if d.IsDir() {
			return nil
		}

		// On lance une Goroutine en fonction de l'extension du fichier
		if strings.HasSuffix(strings.ToLower(path), ".txt") {
			wg.Add(1) // Ajoute 1 au compteur d'attente
			go searchInTxt(path, motCleTXT, &wg)
		} else if strings.HasSuffix(strings.ToLower(path), ".json") {
			wg.Add(1)
			go searchInJson(path, cleJSON, &wg)
		}

		return nil
	})

	if err != nil {
		fmt.Printf("❌ Erreur lors du parcours du dossier : %v\n", err)
	}

	// On attend que tous les fichiers aient été traités
	wg.Wait()
	fmt.Println("--------------------------------------------------")
	fmt.Println("✅ Analyse terminée !")
}
