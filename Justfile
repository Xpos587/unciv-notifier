# Justfile for unciv-notifier project

# Aliases
alias b := build
alias p := push
alias l := login

# Variables
image_name := "docker.io/xpos587/unciv-notifier"
image_tag := "latest"
containerfile := "Containerfile"
registry := "docker.io"

# Login to Docker Hub
login:
    @echo "Logging into Docker Hub..."
    @podman login {{registry}}

# Command to build Docker image
build:
    podman build -t {{image_name}}:{{image_tag}} -f {{containerfile}} .

# Command to push image to repository (with prior authentication)
push: login
    podman push {{image_name}}:{{image_tag}}

# Command to build and push image
deploy: build push
    @echo "Image successfully built and pushed to repository"

# Display list of available commands
default:
    @just --list

