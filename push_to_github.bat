@echo off
echo ==================================
echo  Pushing updates to GitHub...
echo ==================================

:: Prompt for a commit message
set /p commit_message="Enter your commit message: "

:: Add all changes to be tracked by Git
echo.
echo --> Adding all files...
git add .

:: Commit the changes with the message you provided
echo.
echo --> Committing changes...
git commit -m "%commit_message%"

:: Push the committed changes to your GitHub repository's main branch
echo.
echo --> Pushing to GitHub...
git push origin main

echo.
echo ==================================
echo  Push complete!
echo ==================================
pause
