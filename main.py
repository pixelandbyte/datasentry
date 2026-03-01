from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI

from modules.ecg.router import router as ecg_router
from modules.dv.router import router as dv_router
from modules.dcloak.router import router as dcloak_router

app = FastAPI(title="DataSentry", version="0.1.0")
app.include_router(ecg_router, prefix="/ecg")
app.include_router(dv_router, prefix="/dv")
app.include_router(dcloak_router, prefix="/dcloak")
