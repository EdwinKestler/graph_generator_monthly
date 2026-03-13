@echo off
cd /d e:\github_projects\graph_generator_monthly

echo activating conda env... >> dev\test_output.txt

call C:\Users\kestl\anaconda3\Scripts\activate.bat graph_generator

echo activated, python is: >> dev\test_output.txt
where python >> dev\test_output.txt

python dev\test_suite.py >> dev\test_output.txt 2>&1
exit /b %ERRORLEVEL%
