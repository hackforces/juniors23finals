package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/golang-jwt/jwt/v5"
	"github.com/valyala/fasthttp"
	"gorm.io/gorm"
	"html/template"
	"strconv"
)

func TaskAccessMiddleware(next fasthttp.RequestHandler) fasthttp.RequestHandler {
	return func(ctx *fasthttp.RequestCtx) {
		// Extract taskID from the path parameter.
		taskIDParam := ctx.UserValue("id")
		if taskIDParam == nil {
			ctx.Error("Task ID is required", fasthttp.StatusBadRequest)
			return
		}

		// Convert taskIDParam to string and then to uint
		taskID, err := strconv.ParseUint(taskIDParam.(string), 10, 32)
		if err != nil {
			ctx.Error("Invalid task ID", fasthttp.StatusBadRequest)
			return
		}

		// Extract user ID from JWT claims stored previously by JWTMiddleware in the context.
		claims, ok := ctx.UserValue("claims").(jwt.MapClaims)
		if !ok {
			ctx.Error("Unauthorized", fasthttp.StatusUnauthorized)
			return
		}

		userID, ok := claims["id"].(float64) // ID from JWT claims is float64
		if !ok {
			ctx.Error("Unauthorized", fasthttp.StatusUnauthorized)
			return
		}

		// Check if there's an entry in UserTasks for the task and the user.
		var userTask UserTasks
		result := db.Where("user_id = ? AND task_id = ?", uint(userID), uint(taskID)).First(&userTask)
		if result.Error != nil {
			// If no entry is found, restrict access.
			ctx.Error("Access to the task is restricted", fasthttp.StatusUnauthorized)
			return
		}

		// If the entry exists, allow the request to proceed to the next handler.
		next(ctx)
	}
}

func CreateTask(ctx *fasthttp.RequestCtx) {
	var task Task
	err := json.Unmarshal(ctx.PostBody(), &task)
	task.Status = "open"
	if err != nil {
		ctx.Error("Invalid request body", fasthttp.StatusBadRequest)
		return
	}

	db.Create(&task)

	// Get JWT claims from the context
	claims, ok := ctx.UserValue("claims").(jwt.MapClaims)
	if !ok {
		ctx.Error("Unauthorized", fasthttp.StatusUnauthorized)
		return
	}

	// Get user ID from the claims
	userID, ok := claims["id"].(float64) // The ID claim must be a float64 because of JSON's number type
	if !ok {
		ctx.Error("Auth error?", fasthttp.StatusUnauthorized)
		return
	}

	// Automatically create an entry in UserTasks for the creator
	userTask := UserTasks{UserID: uint(userID), TaskID: task.ID}
	db.Create(&userTask)

	// Send response back to the client
	ctx.SetStatusCode(fasthttp.StatusCreated)
	ctx.Write([]byte("Task created successfully"))

}

func AssignTaskToUserByNickname(ctx *fasthttp.RequestCtx) {
	// Extract taskID from the path parameter.
	taskIDParam := ctx.UserValue("id").(string)
	taskID, err := strconv.ParseUint(taskIDParam, 10, 32)
	if err != nil {
		ctx.Error("Invalid task ID", fasthttp.StatusBadRequest)
		return
	}

	// Parse request body to get the nickname of the user to whom the task is to be assigned.
	var requestBody struct {
		Nickname string `json:"nickname"`
	}
	if err := json.Unmarshal(ctx.PostBody(), &requestBody); err != nil {
		ctx.Error("Invalid request body", fasthttp.StatusBadRequest)
		return
	}

	// Find the user by nickname
	var user User
	result := db.Where("username = ?", requestBody.Nickname).First(&user)
	if errors.Is(result.Error, gorm.ErrRecordNotFound) {
		ctx.SetStatusCode(fasthttp.StatusOK)
		ctx.SetContentType("application/json")
		ctx.Write([]byte(fmt.Sprintf(`{"success": false, "message": "User with nickname '%s' not found"}`, requestBody.Nickname)))
		// ctx.Error(fmt.Sprintf("User with nickname '%s' not found", requestBody.Nickname), fasthttp.StatusNotFound)
		return
	} else if result.Error != nil {
		ctx.Error("Internal Server Error", fasthttp.StatusInternalServerError)
		return
	}

	// Once the user is found, assign the task by creating an entry in the UserTasks table.
	userTask := UserTasks{
		UserID: user.ID,
		TaskID: uint(taskID),
	}

	// Upsert userTask using GORM's Clauses. This ensures it will insert or update the UserTasks entry.
	result = db.Create(&userTask)

	if result.Error != nil {
		ctx.SetStatusCode(fasthttp.StatusOK)
		ctx.SetContentType("application/json")
		ctx.Write([]byte(`{"success": false, "message": "Failed to assign task (already assigned?)"}`))
		return
	}

	// Send a JSON response back to the client if successful.
	ctx.SetStatusCode(fasthttp.StatusOK)
	ctx.SetContentType("application/json")
	ctx.Write([]byte(`{"success": true, "message": "Task assigned successfully"}`))
}

func CompleteTask(ctx *fasthttp.RequestCtx) {
	taskID := ctx.UserValue("id").(string)

	// Update task status in the database to 'completed'
	var task Task
	db.First(&task, "id = ?", taskID)
	if task.ID == 0 {
		ctx.Error("Task not found", fasthttp.StatusNotFound)
		return
	}

	if task.Status != "completed" {
		task.Status = "completed"
		db.Save(&task)

		ctx.SetStatusCode(fasthttp.StatusOK)
		ctx.Write([]byte("Job completed successfully"))
	} else {
		ctx.SetStatusCode(fasthttp.StatusBadRequest)
		ctx.Write([]byte("Already completed"))
	}
}

func fetchAndShowTaskDetailed(ctx *fasthttp.RequestCtx) {
	// Extract task ID from the URL parameters
	id := ctx.UserValue("id").(string)
	var task Task
	result := db.First(&task, id)
	if errors.Is(result.Error, gorm.ErrRecordNotFound) {
		ctx.Error("Record not found", fasthttp.StatusNotFound)
		return
	} else if result.Error != nil {
		ctx.Error("Internal Server Error", fasthttp.StatusInternalServerError)
		return
	}

	// Extract user ID from JWT claims stored previously by JWTMiddleware in the context.
	claims, ok := ctx.UserValue("claims").(jwt.MapClaims)
	if !ok {
		ctx.Error("Unauthorized", fasthttp.StatusUnauthorized)
		return
	}
	userID, ok := claims["id"].(float64)
	if !ok {
		ctx.Error("Unauthorized", fasthttp.StatusUnauthorized)
		return
	}

	// Retrieve the username from the database based on the userID
	var user User
	err := db.First(&user, uint(userID)).Error
	if err != nil {
		ctx.Error("Internal Server Error", fasthttp.StatusInternalServerError)
		return
	}

	// Retrieve the task's comments from the database
	var comments []*CommentWithContentString
	comments, err = GetTaskComments(strconv.Itoa(int(task.ID)))

	// Create a map to store usernames keyed by UserID
	userNames := make(map[uint64]string)

	// Iterate over each comment to fetch the username using the UserID
	for _, comment := range comments {
		if _, exists := userNames[comment.UserID]; !exists {
			var user User
			err := db.First(&user, comment.UserID).Error
			if err != nil {
				ctx.Error("Failed to retrieve user information", fasthttp.StatusInternalServerError)
				return
			}
			// Store the username in the map
			userNames[comment.UserID] = user.Username
		}
	}

	// Parse the HTML template
	t, err := template.New("task_detailed.html").ParseFS(templates, "templates/task_detailed.html")
	if err != nil {
		ctx.Error("Internal Server Error", fasthttp.StatusInternalServerError)
		return
	}
	ctx.Response.Header.Set("Content-Type", "text/html")

	// Struct for passing data to the template, including comments with usernames.
	data := struct {
		Task      Task
		Username  string
		Comments  []*CommentWithContentString
		Usernames map[uint64]string
	}{
		Task:      task,
		Username:  user.Username,
		Comments:  comments,
		Usernames: userNames,
	}

	err = t.Execute(ctx, data)
	if err != nil {
		ctx.Error("Failed to render template", fasthttp.StatusInternalServerError)
	}
}

func fetchAndShowTasks(ctx *fasthttp.RequestCtx) {
	// Extract user ID from JWT claims stored previously by JWTMiddleware in the context.
	claims, ok := ctx.UserValue("claims").(jwt.MapClaims)
	if !ok {
		ctx.Error("Unauthorized", fasthttp.StatusUnauthorized)
		return
	}
	userID, ok := claims["id"].(float64)
	if !ok {
		ctx.Error("Unauthorized", fasthttp.StatusUnauthorized)
		return
	}

	// Fetch the current User based on the userID retrieved from JWT claims.
	var user User
	err := db.First(&user, uint(userID)).Error
	if err != nil {
		ctx.Error("Failed to retrieve user information", fasthttp.StatusInternalServerError)
		return
	}

	// Query for UserTasks associations related to the current user.
	var userTasks []UserTasks
	err = db.Where("user_id = ?", uint(userID)).Find(&userTasks).Error
	if err != nil {
		// Handle potential errors during the database operation.
		ctx.Error("Internal Server Error", fasthttp.StatusInternalServerError)
		return
	}

	// Collect task IDs from the UserTasks
	taskIDs := make([]uint, len(userTasks))
	for i, ut := range userTasks {
		taskIDs[i] = ut.TaskID
	}

	// Fetch tasks associated with the user.
	var tasks []Task
	if len(taskIDs) > 0 {
		err = db.Where("id IN ?", taskIDs).Find(&tasks).Error
	} else {
		// If there are no task IDs, this means the user has no tasks associated with them.
		tasks = []Task{}
	}
	if err != nil {
		ctx.Error("Internal Server Error", fasthttp.StatusInternalServerError)
		return
	}

	// Rendering the template with retrieved tasks and the current user's username.
	t, err := template.New("tasks.html").ParseFS(templates, "templates/tasks.html")
	if err != nil {
		ctx.Error("Internal Server Error", fasthttp.StatusInternalServerError)
		return
	}
	ctx.Response.Header.Set("Content-Type", "text/html")

	// Struct for passing data to the template.
	data := struct {
		Tasks    []Task
		Username string
	}{
		Tasks:    tasks,
		Username: user.Username,
	}

	err = t.Execute(ctx, data)
	if err != nil {
		ctx.Error("Failed to render template", fasthttp.StatusInternalServerError)
	}
}
