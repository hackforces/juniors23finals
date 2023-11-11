package main

import (
	"encoding/json"
	"errors"
	"github.com/golang-jwt/jwt/v5"
	"github.com/valyala/fasthttp"
	"gorm.io/gorm"
	"strconv"
)

type CommentWithContentString struct {
	TaskID  uint64 `json:"task_id"`
	UserID  uint64
	Content string
}

func GetTaskComments(taskID string) ([]*CommentWithContentString, error) {
	var comments []*Comment
	var commentsWithStringContent []*CommentWithContentString

	// Load comments for the given taskID from the database
	result := db.Find(&comments, "task_id = ?", taskID)
	if result.Error != nil {
		return nil, result.Error
	}

	// Map Comment objects to CommentWithContentString, converting Content to string
	for _, comment := range comments {
		commentWithStringContent := &CommentWithContentString{
			TaskID:  comment.TaskID,
			UserID:  comment.UserID,
			Content: string(comment.Content),
		}
		commentsWithStringContent = append(commentsWithStringContent, commentWithStringContent)
	}

	return commentsWithStringContent, nil
}

func TaskCommentsHandler(ctx *fasthttp.RequestCtx) {
	taskID := ctx.UserValue("id").(string)

	// Get comments for the task
	comments, err := GetTaskComments(taskID)

	// Convert comments to JSON and send the response
	jsonComments, err := json.Marshal(comments)
	if err != nil {
		ctx.Error("Failed to convert comments to JSON", fasthttp.StatusInternalServerError)
		return
	}

	ctx.SetContentType("application/json")
	ctx.SetStatusCode(fasthttp.StatusOK)
	ctx.Write(jsonComments)
}

type tempComment struct {
	Content string `json:"content"`
}

func CommentTask(ctx *fasthttp.RequestCtx) {
	var comment Comment
	var tempComm tempComment
	err := json.Unmarshal(ctx.PostBody(), &tempComm)
	if err != nil {
		ctx.Error("Invalid request body", fasthttp.StatusBadRequest)
		return
	}

	// Extract taskID from the path parameter instead of the request body
	taskIDParam := ctx.UserValue("id").(string)
	taskID, err := strconv.ParseUint(taskIDParam, 10, 32)
	if err != nil {
		ctx.Error("Invalid task ID", fasthttp.StatusBadRequest)
		return
	}
	comment.TaskID = taskID // Assign taskID from URL param to the comment
	comment.Content = []byte(tempComm.Content)

	// Get JWT claims from the context, user ID is already validated by JWTMiddleware and TaskAccessMiddleware
	claims, ok := ctx.UserValue("claims").(jwt.MapClaims)
	if !ok {
		ctx.Error("Unauthorized", fasthttp.StatusUnauthorized)
		return
	}

	// Get user ID from the claims
	userID, ok := claims["id"].(float64)
	if !ok {
		ctx.Error("Unauthorized", fasthttp.StatusUnauthorized)
		return
	}

	comment.UserID = uint64(userID)

	// Check if the task exists and the user is authorized to comment on it
	var task Task
	result := db.First(&task, "id = ?", taskID)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			ctx.Error("Task not found", fasthttp.StatusNotFound)
		} else {
			ctx.Error("Database error", fasthttp.StatusInternalServerError)
		}
		return
	}

	// Create the comment in the database
	result = db.Create(&comment)
	if result.Error != nil {
		ctx.Error("Database error", fasthttp.StatusInternalServerError)
		return
	}
	// db.Exec("PRAGMA wal_checkpoint(FULL)") // Make sure everything is synced for next command
	// crcHash, err := RunCommand("runuser", "-u", "limiteduser", "/companion_app", comment.Content)
	crcHash, err := RunCommand("/companion_app", comment.Content)
	// Send response back to the client
	ctx.SetStatusCode(fasthttp.StatusCreated)
	ctx.Write([]byte("Comment created successfully, hash=" + crcHash))
}
