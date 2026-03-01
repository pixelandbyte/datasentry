from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI

from modules.ecg.router import router as ecg_router

app = FastAPI(title="DataSentry", version="0.1.0")
app.include_router(ecg_router, prefix="/ecg")
