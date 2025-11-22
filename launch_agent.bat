@echo off
title Claude Plays Zelda
echo Starting Claude Plays Zelda...
echo.
cd /d "%~dp0"
py -m claude_plays_zelda.cli play
pause
