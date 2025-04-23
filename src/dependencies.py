from fastapi import Request

from app import App


def get_app(request: Request) -> App:
    return request.app

