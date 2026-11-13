@echo off
cd frontend
REM installs new packages if package.json changed (fast when nothing changed)
call npm install
npm start
