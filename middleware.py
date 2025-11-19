# middleware.py
from starlette.middleware.sessions import SessionMiddleware

def add_session(app):
    app.add_middleware(
        SessionMiddleware,
        secret_key="supersecretkey123"  # change for production
    )
