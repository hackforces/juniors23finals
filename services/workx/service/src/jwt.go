package main

import (
	"crypto/rand"
	"fmt"
	"github.com/golang-jwt/jwt/v5"
	"github.com/valyala/fasthttp"
	"time"
)

var jwtSecretKey []byte

func generateRandomBytes(n int) ([]byte, error) {
	b := make([]byte, n)
	_, err := rand.Read(b)
	if err != nil {
		return nil, err
	}
	return b, nil
}

func generateJWT(user User) (string, error) {
	token := jwt.New(jwt.SigningMethodHS256)

	claims := token.Claims.(jwt.MapClaims)
	claims["username"] = user.Username
	claims["role"] = user.Role // Add the user role to the JWT claims
	claims["exp"] = time.Now().Add(time.Hour * 72).Unix()
	claims["id"] = user.ID

	return token.SignedString(jwtSecretKey)
}

func parseJWT(tokenString string) (jwt.MapClaims, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("Unexpected signing method: %v", token.Header["alg"])
		}
		return jwtSecretKey, nil
	})

	// Check if parsing was successful and the token is valid
	if err != nil {
		return nil, err
	}

	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		return claims, nil
	}

	return nil, fmt.Errorf("Invalid token")
}

func JWTMiddleware(next fasthttp.RequestHandler) fasthttp.RequestHandler {
	return func(ctx *fasthttp.RequestCtx) {
		tokenCookie := ctx.Request.Header.Cookie("session")
		if len(tokenCookie) == 0 {
			ctx.Error("Unauthorized", fasthttp.StatusUnauthorized)
			return
		}

		claims, err := parseJWT(string(tokenCookie))
		if err != nil {
			ctx.Error("Unauthorized", fasthttp.StatusUnauthorized)
			return
		}

		// Store the claims for use in the next handler if they are not nil
		if claims != nil {
			ctx.SetUserValue("claims", claims)
		} else {
			ctx.Error("Unauthorized", fasthttp.StatusUnauthorized)
			return
		}

		next(ctx)
	}
}
