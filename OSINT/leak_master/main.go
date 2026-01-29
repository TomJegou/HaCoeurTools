package main

import (
	"fmt"
	"log"
	"net/http"
)

const PORT = 8080

func main() {
	http.HandleFunc("/", nil)
	http.HandleFunc("/search", nil)
	fmt.Printf("Server is running on port %d 🔥\n", PORT)
	if err := http.ListenAndServe(fmt.Sprintf(":%d", PORT), nil); err != nil {
		log.Fatalf(`http.ListenAndServe(fmt.Sprintf(":%%d", PORT) : %v`, err)
	}
}
