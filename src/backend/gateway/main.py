from app.infrastructure.api.middlewares.request_logging import RequestLoggingMiddleware
from app.infrastructure.api.routes import health
from fastapi import FastAPI

app = FastAPI(
    title="Ticketera Virtual - API Gateway",
    version="1.0.0",
    description="Punto único de entrada y orquestador BFF de la plataforma de venta de tickets."
)

# Registro de middlewares
app.add_middleware(RequestLoggingMiddleware)

# Registro de routers
app.include_router(health.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
