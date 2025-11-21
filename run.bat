@echo off
start cmd /k "textual console -x SYSTEM -x EVENT -x DEBUG -x INFO"
textual run application.py --dev
pause