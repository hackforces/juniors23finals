package main

import (
	"gorm.io/gorm"
)

var db *gorm.DB

type User struct {
	gorm.Model
	Username string `gorm:"unique"`
	Password string
	Role     string // 'freelancer' or 'job-giver'
}

type Task struct {
	gorm.Model
	Title       string
	Description string
	Status      string // 'open', 'in-progress', 'completed'
}

type Comment struct {
	gorm.Model
	TaskID  uint64 `json:"task_id"`
	UserID  uint64
	Content []byte
}

type UserTasks struct {
	gorm.Model
	UserID uint `gorm:"index:idx_user_task,unique"`
	TaskID uint `gorm:"index:idx_user_task,unique"`
}
