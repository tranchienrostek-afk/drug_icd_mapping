# Use official Playwright image which includes Python and all browser dependencies
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Install specific browser if needed (the image has them, but verifying versions)
RUN playwright install --with-deps chromium

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]