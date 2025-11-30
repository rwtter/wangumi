# build.ps1
$ErrorActionPreference = "Stop"

Push-Location frontend
npm install
npm run build
Pop-Location

pip install -r requirements.txt
python backend/manage.py collectstatic --noinput
python backend/manage.py migrate
