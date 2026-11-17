from fastapi import apirouter

router = apirouter

@router.get("/")
def health():
    return {"status": "okay"}