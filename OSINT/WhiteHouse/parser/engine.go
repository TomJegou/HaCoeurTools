package parser

import (
	"bufio"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
)

// Result représente une ligne trouvée avec ses données extraites
type Result struct {
	Source string
	Line   string
	Email  string
	IP     string
	Extras []string // Pour stocker ce qui ressemble à des pseudos ou mots de passe
}

// Regex pour extraire les données courantes
var (
	emailRegex = regexp.MustCompile(`[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`)
	ipRegex    = regexp.MustCompile(`\b(?:\d{1,3}\.){3}\d{1,3}\b`)
)

// SearchInFolder scanne les fichiers avec une option de filtrage par nom de fichier
func SearchInFolder(dataDir, keyword, filterFile string, maxResults int) ([]Result, error) {
	files, _ := os.ReadDir(dataDir)
	keyword = strings.ToLower(keyword)
	resultChan := make(chan Result, 100)
	var wg sync.WaitGroup
	var mu sync.Mutex
	seen := make(map[string]struct{})

	for _, f := range files {
		if f.IsDir() || f.Name() == ".DS_Store" {
			continue
		}

		// FILTRE : Si on a spécifié un fichier et que ce n'est pas celui-là, on passe
		if filterFile != "" && f.Name() != filterFile {
			continue
		}

		wg.Add(1)
		go func(name string) {
			defer wg.Done()
			file, _ := os.Open(filepath.Join(dataDir, name))
			defer file.Close()

			scanner := bufio.NewScanner(file)
			buf := make([]byte, 0, 10*1024*1024)
			scanner.Buffer(buf, 10*1024*1024)

			for scanner.Scan() {
				line := scanner.Text()
				if strings.Contains(strings.ToLower(line), keyword) {
					mu.Lock()
					if _, exists := seen[line]; !exists {
						seen[line] = struct{}{}
						mu.Unlock()

						resultChan <- Result{
							Source: name,
							Line:   line,
							Email:  emailRegex.FindString(line),
							IP:     ipRegex.FindString(line),
						}
					} else {
						mu.Unlock()
					}
				}
			}
		}(f.Name())
	}

	go func() { wg.Wait(); close(resultChan) }()

	var results []Result
	for r := range resultChan {
		results = append(results, r)
		if len(results) >= maxResults {
			break
		}
	}
	return results, nil
}

// GetFileList renvoie simplement la liste des noms de fichiers dans /data
func GetFileList(dataDir string) []string {
	var list []string
	files, _ := os.ReadDir(dataDir)
	for _, f := range files {
		if !f.IsDir() && f.Name() != ".DS_Store" {
			list = append(list, f.Name())
		}
	}
	return list
}
