# Sleep Disorder Detection

A Django-based web application for predicting sleep disorders and analyzing sleep health using ML models.

## Features
- User accounts and patient dashboard
- Sleep disorder prediction using trained ML models (in `sleep_predictor/ml`)
- Data visualization and analytics in `sleepdetect` templates
- SHAP explanation files stored in `static/images/shap` and `static/shap`

## Prerequisites
- Python 3.10+ (virtualenv recommended)
- pip

## Environment
Create a `.env` file in the project root (or set environment variables) and include:

- `OPENAI_API_KEY` (optional; used by parts of the app that integrate with OpenAI)

## Quick setup (Windows)

1. Create and activate a virtual environment

```powershell
python -m venv venv
.
venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Apply migrations and create a superuser

```powershell
python manage.py migrate
python manage.py createsuperuser
```

4. Run the dev server

```powershell
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

## Project layout (key files/folders)
- `accounts/` — authentication, registration, login views and templates
- `patient/` — patient profiles and dashboard
- `sleepdetect/` — analytics, prediction views and templates
- `sleep_predictor/` — ML training and SHAP code (`ml/` contains training and dataset)
- `templates/` — HTML templates used by the app
- `static/` — static assets (including SHAP images)
- `check_accuracy.py` — helper script for evaluating model accuracy

## ML / Data
Datasets live under `sleep_predictor/ml/dataset`. Trained-model artifacts and SHAP images are expected in `static/shap` or `static/images/shap`.

To retrain the model or generate SHAP explanations, see:

- `sleep_predictor/ml/train_model.py`
- `sleep_predictor/ml/create_shap.py`

## Notes
- `MEDIA_ROOT` in settings currently uses `os.path.join(BASE_DIR, '/media/')` — that leading slash will create an absolute path component on some platforms; consider `os.path.join(BASE_DIR, 'media')` if you plan to store uploaded files locally.
- Make sure to set `DEBUG=False` and configure `ALLOWED_HOSTS` before deploying to production.

## Contributing
Feel free to open issues or PRs. Add tests under each app's `tests.py`.

## License
This project does not include a license file. Add one if you intend to open-source it.
