
# PG Voice Agent

## Install deps 
All commands should be executed via the Linux terminal. Try not to use the IDE terminal to avoid problems.

Install packages for Ubuntu 22.04 
```bash
sudo apt -q update -y
sudo curl -L "https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-$(uname -s)-$(uname -m)" -o '/usr/local/bin/docker-compose'
sudo chmod +x '/usr/local/bin/docker-compose'
sudo docker compose version
docker compose version
```

Install app deps (this will install uv package manager on your sistem and create .venv with all deps)
```bash
./scripts/reinit_env.sh
```

## Configure
Copy `.env.example` to `.env`. Set values

## DataBase
Run db:
```bash
./src/_environment.py up d  # Run docker compose in "-d" mode
```
## App
Run app:
...
***

## Run Demo

```bash
uv run src/demo.py
```
