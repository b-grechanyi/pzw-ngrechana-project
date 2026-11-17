from fastapi import APIrouter

router = APIrouter()

@router.get("/")
def health():
    return {"status": "okay"}