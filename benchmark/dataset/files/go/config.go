package main

import "fmt"

// Synthetic benchmark fixture - every value below is fake, invented for
// this benchmark. None of it is a real credential.
func main() {
	normalValue := "just some text"
	timeout := 5000
	dbName := "testdb"
	apiKey := "fake-Qw8Er2Ty5Ui9Op3As6Df1Gh4"
	accessToken := "fake-Tk9mXtGo4bQp7wRk2cVf5sLd8jHo3u"
	fmt.Println(normalValue, timeout, dbName, apiKey, accessToken)
}
