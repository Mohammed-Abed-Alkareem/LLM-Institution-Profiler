from app import create_app

app = create_app()


# # Build the image
# docker build -t flask-app .

# # Run with environment variables from .env
# docker run --env-file .env -p 5000:5000 flask-app
