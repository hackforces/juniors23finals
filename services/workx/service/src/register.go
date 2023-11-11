package main

import (
	"encoding/json"
	"github.com/valyala/fasthttp"
	"gorm.io/gorm/clause"
	"html/template"
	"regexp"
)

func showRegisterForm(ctx *fasthttp.RequestCtx) {
	t, err := template.New("register.html").ParseFS(templates, "templates/register.html")
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

func Register(ctx *fasthttp.RequestCtx) {
	var user User
	err := json.Unmarshal(ctx.PostBody(), &user)
	if err != nil {
		ctx.Error("Invalid request body", fasthttp.StatusBadRequest)
		return
	}

	validationRegex := regexp.MustCompile(`^[A-Za-z0-9]+$`)
	if !validationRegex.MatchString(user.Username) || !validationRegex.MatchString(user.Password) || !(user.Role == "freelancer" || user.Role == "job-giver") {
		ctx.Error("Invalid data, only alphanumeric characters are allowed and the role must be 'freelancer' or 'job-giver'", fasthttp.StatusBadRequest)
		return
	}

	// Insert the user or update the password if the user already exists
	err = db.Clauses(clause.OnConflict{
		Columns:   []clause.Column{{Name: "username"}},            // Fields to use for the ON CONFLICT condition
		DoUpdates: clause.AssignmentColumns([]string{"password"}), // Fields to update
	}).Create(&user).Error

	if err != nil {
		ctx.Error(err.Error(), fasthttp.StatusInternalServerError)
		return
	}

	// Send response back to the client
	ctx.SetStatusCode(fasthttp.StatusCreated)
	ctx.Response.SetBodyString("User registered successfully")
}
