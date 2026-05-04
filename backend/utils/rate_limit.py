from slowapi import Limiter

limiter = Limiter(key_func=lambda request: request.client.host or "unknown")
auth_limiter = Limiter(key_func=lambda request: request.client.host, default_limits=["5/minute"])
