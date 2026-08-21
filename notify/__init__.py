from .pushplus import send_pushplus


def notify(event: str, title: str, content: str) -> dict:
    return send_pushplus(title, content)
