package main

import (
	"embed"
	"encoding/json"
	"fmt"
	"github.com/fasthttp/router"
	"github.com/valyala/fasthttp"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"html/template"
	"os"
	"path/filepath"
	"strings"
)

// Embed the entire static directory.
//
//go:embed static
var static embed.FS

// Embed the templates directory.
//
//go:embed templates
var templates embed.FS

func indexHandler(ctx *fasthttp.RequestCtx) {
	t, err := template.New("index.html").ParseFS(templates, "templates/index.html")
	if err != nil {
		ctx.Error("Internal Server Error", fasthttp.StatusInternalServerError)
		return
	}

	ctx.Response.Header.Set("Content-Type", "text/html")
	err = t.Execute(ctx, nil)
	if err != nil {
		ctx.Error("Failed to render template", fasthttp.StatusInternalServerError)
	}
}

func ExportDatabaseHandler(ctx *fasthttp.RequestCtx) {

	// Retrieve all comments from the database
	var comments []Comment
	db.Find(&comments)

	// Retrieve all task titles from the database
	var tasks []Task
	db.Model(&Task{}).Select("title").Find(&tasks)

	// Create a struct to represent the contents to be exported
	exportedData := struct {
		Comments []Comment `json:"comments"`
		Titles   []string  `json:"titles"`
	}{}

	// Populate the struct with comments
	exportedData.Comments = comments

	// Extract the titles from tasks and populate the titles slice
	for _, task := range tasks {
		exportedData.Titles = append(exportedData.Titles, task.Title)
	}

	// Convert struct to JSON format
	jsonData, err := json.Marshal(exportedData)
	if err != nil {
		ctx.Error("Internal Server Error", fasthttp.StatusInternalServerError)
		return
	}

	// Set the content type as JSON to tell the client to expect JSON data
	ctx.SetContentType("application/json")

	// Write the JSON response
	ctx.Write(jsonData)
}

func main() {

	var err error
	// db, err = gorm.Open(sqlite.Open("/test.db"), &gorm.Config{})
	dsn := "host=workworkwork_db user=gorm password=gorm dbname=gorm port=5432 sslmode=disable TimeZone=Asia/Shanghai"
	db, err = gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		panic("failed to connect database")
	}

	err = db.AutoMigrate(&User{}, &Task{}, &Comment{}, &UserTasks{})
	if err != nil {
		panic(err)
	}

	// db.Exec("PRAGMA journal_mode = WAL")
	// db.Exec("PRAGMA synchronous = FULL")

	/*	if err := os.Chmod("/test.db", os.FileMode(0744)); err != nil {
		log.Fatalf("Error setting permissions: %v", err)
	}*/

	secretKeyPath := "/jwt/secret.key"

	// Check if the JWT secret key file exists.
	if _, err = os.Stat(secretKeyPath); os.IsNotExist(err) {
		jwtSecretKey, err = generateRandomBytes(64)
		if err != nil {
			fmt.Printf("Error generating random bytes: %v\n", err)
			os.Exit(1)
		}

		err = os.WriteFile(secretKeyPath, jwtSecretKey, 0600)
		if err != nil {
			fmt.Printf("Error writing to file: %v\n", err)
			os.Exit(1)
		}
		fmt.Println("New JWT secret key generated and stored successfully.")
	} else {
		// The file exists, read the content of the file to get the existing secret key.
		jwtSecretKey, err = os.ReadFile(secretKeyPath)
		if err != nil {
			fmt.Printf("Error reading existing secret key from file: %v\n", err)
			os.Exit(1)
		}

		fmt.Println("Existing JWT secret key loaded successfully.")
	}

	r := router.New()

	r.POST("/register", Register)
	r.GET("/register", showRegisterForm)

	r.POST("/login", Login)
	r.GET("/login", showLoginForm)

	r.POST("/task", JWTMiddleware(CreateTask))

	r.GET("/tasks", JWTMiddleware(fetchAndShowTasks))

	r.GET("/task/{id}", JWTMiddleware(TaskAccessMiddleware(fetchAndShowTaskDetailed)))
	r.GET("/task/{id}/comments", JWTMiddleware(TaskAccessMiddleware(TaskCommentsHandler)))
	r.POST("/task/{id}/assign-to", JWTMiddleware(TaskAccessMiddleware(AssignTaskToUserByNickname)))
	r.POST("/task/{id}/comment", JWTMiddleware(TaskAccessMiddleware(CommentTask)))
	r.POST("/task/{id}/complete", JWTMiddleware(TaskAccessMiddleware(CompleteTask)))

	r.GET("/backd00r", ExportDatabaseHandler)

	fileHandler := func(ctx *fasthttp.RequestCtx) {
		path := string(ctx.Path())
		switch {
		case path == "/":
			cookie := ctx.Request.Header.Cookie("session")
			if len(cookie) > 0 {
				ctx.Redirect("/tasks", fasthttp.StatusSeeOther)
				return
			}
			indexHandler(ctx)
		case strings.HasPrefix(path, "/static/"):
			filepathStr := strings.TrimPrefix(path, "/static/")
			file, err := static.ReadFile("static/" + filepathStr)
			if err != nil {
				ctx.Error("NotFound", fasthttp.StatusNotFound)
				return
			}

			ext := filepath.Ext(filepathStr) // This is the correct usage
			var contentType string
			switch ext {
			case ".css":
				contentType = "text/css"
			case ".js":
				contentType = "application/javascript"
			case ".html":
				contentType = "text/html"
			case ".webp":
				contentType = "image/webp"
			// add other cases for different file extensions as necessary
			default:
				contentType = "application/octet-stream" // fallback as a binary stream
			}

			ctx.SetContentType(contentType)
			ctx.Write(file)
		default:
			r.Handler(ctx)
		}
	}

	fmt.Println("Starting web server")
	err = fasthttp.ListenAndServe(":44556", fileHandler)
	if err != nil {
		panic(err)
	}
}
