from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "georush-seo-api",
        "version": "0.1.0",
    }
