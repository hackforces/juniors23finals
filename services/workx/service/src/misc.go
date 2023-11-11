package main

import (
	"bytes"
	"fmt"
	"os/exec"
)

// RunCommand executes a program with given input and returns its output.
func RunCommand(name string, input []byte) (output string, err error) {
	// Set up the command
	cmd := exec.Command(name)

	// Set up buffers to capture the output and any errors
	var out bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &stderr

	// Create a buffer to hold the input
	in := bytes.NewReader(input)
	cmd.Stdin = in

	// Run the command
	if err := cmd.Run(); err != nil {
		fmt.Println(err.Error())
		// Return both the output and stderr in case of error
		return out.String(), fmt.Errorf("%v: %s", err, stderr.String())
	}

	// Return the output as a string
	return out.String(), nil
}
