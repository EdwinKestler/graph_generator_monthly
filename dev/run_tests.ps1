Set-Location 'e:\github_projects\graph_generator_monthly'
$python = 'C:\Users\kestl\anaconda3\envs\graph_generator\python.exe'
$result = & $python 'dev\test_suite.py' 2>&1
$result | Set-Content 'dev\test_output.txt' -Encoding UTF8
$result | ForEach-Object { Write-Host $_ }
exit $LASTEXITCODE
