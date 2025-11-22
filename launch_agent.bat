@echo off
cd /d "%~dp0"
start "Claude Plays Zelda - Agent Log" cmd /k "py -m claude_plays_zelda.cli play"
