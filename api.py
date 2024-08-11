import os
import uuid
import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import yt_dlp
import base64

class VideoUrl(BaseModel):
    url: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


temp_folder = "temp_downloads"
if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)


DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Download(Base):
    __tablename__ = "downloads"
    id = Column(String, primary_key=True, index=True)
    url = Column(String, index=True)
    file_name = Column(String, index=True)  
    status = Column(String, index=True)
    percent = Column(Float, default=0)
    title = Column(String, index=True)  

Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)

def download_video(url: str, output_path: str, download_id: str, db):
    ydl_opts = {
        "outtmpl": os.path.join(output_path, f"{download_id}.%(ext)s"),
        "format": "bestvideo+bestaudio/best",
        "progress_hooks": [lambda d: progress_hook(d, url, download_id, db)],
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            file_name = f"{download_id}.{info.get('ext', 'mp4')}"
            file_path = os.path.join(output_path, file_name)

            
            video_title = info.get("title", "Unknown Title")
            db.query(Download).filter(Download.id == download_id).update({"file_name": file_name, "title": video_title})
            db.commit()

            logging.info(f"File downloaded and saved as: {file_path}")
            logging.info(f"Video title saved: {video_title}")

            
            if os.path.isfile(file_path):
                logging.info(f"File name updated in database: {file_name}")
            else:
                logging.error(f"File not found at path: {file_path}")

        except Exception as e:
            logging.error(f"Error downloading video: {e}")
        finally:
            db.query(Download).filter(Download.id == download_id).update({"status": "Completed"})
            db.commit()
            logging.info(f"Download completed: {download_id}")

def progress_hook(d, url, download_id: str, db):
    if d['status'] == 'finished':
        db.query(Download).filter(Download.id == download_id).update({"status": "Completed"})
        logging.info(f"Download finished: {download_id}")
    else:
        percent = d.get('downloaded_bytes') / d.get('total_bytes') * 100 if d.get('total_bytes') else 0
        db.query(Download).filter(Download.id == download_id).update({"status": d['status'], "percent": percent})
        logging.info(f"Download progress: {download_id}, {percent}%")
    db.commit()

@app.post("/download/")
async def download_video_endpoint(video_url: VideoUrl, background_tasks: BackgroundTasks):
    db = SessionLocal()
    download_id = str(uuid.uuid4())
    new_download = Download(id=download_id, url=video_url.url, file_name="", status="Downloading")
    db.add(new_download)
    db.commit()
    
    logging.info(f"Created new download: {new_download.id} with status {new_download.status}")
    
    background_tasks.add_task(download_video, video_url.url, temp_folder, download_id, db)
    return {"message": "Download started", "download_id": download_id}

@app.get("/progress/{download_id}")
def get_progress(download_id: str):
    db = SessionLocal()
    progress = db.query(Download).filter(Download.id == download_id).first()
    if progress:
        return {
            "url": progress.url,
            "status": progress.status,
            "percent": progress.percent,
            "title": progress.title  
        }
    return {"status": "No progress found"}

@app.get("/list-files/")
def list_files():
    db = SessionLocal()
    downloads = db.query(Download).filter(Download.status == "Completed").all()
    
    if downloads:
        file_info_list = []
        for download in downloads:
            file_name_encoded = base64.b64encode(download.id.encode()).decode()
            file_info_list.append({
                "file_name_encoded": file_name_encoded,
                "original_file_name": download.file_name,
                "id": download.id,
                "title": download.title,  
                "url": download.url
            })
        return {"files": file_info_list}
    return {"message": "No files available"}

@app.get("/download/{download_id}")
async def download_file(download_id: str):
    db = SessionLocal()
    try:
        logging.info(f"Downloading file with ID: {download_id}")
        
        download = db.query(Download).filter(Download.id == download_id).first()
        if not download:
            logging.error("Download record not found in database.")
            raise HTTPException(status_code=404, detail="File not found")
        
        file_name = download.file_name
        file_path = os.path.join(temp_folder, file_name)
        
        logging.info(f"File path: {file_path}")
        
        if not os.path.isfile(file_path):
            logging.error(f"File not found in the specified path: {file_path}")
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            file_path,
            media_type='application/octet-stream',
            headers={"Content-Disposition": f"attachment; filename=\"{download.file_name}\""}
        )
    except Exception as e:
        logging.error(f"Error serving file: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        db.close()

@app.delete("/delete/{download_id}")
async def delete_file(download_id: str):
    db = SessionLocal()
    try:
        download = db.query(Download).filter(Download.id == download_id).first()
        if not download:
            raise HTTPException(status_code=404, detail="File not found")

        file_path = os.path.join(temp_folder, download.file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)

        db.delete(download)
        db.commit()
        return {"message": "File deleted successfully"}
    except Exception as e:
        logging.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

@app.delete("/clear_downloads/")
async def clear_all_downloads():
    db = SessionLocal()
    try:
 
        for file_name in os.listdir(temp_folder):
            file_path = os.path.join(temp_folder, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        db.query(Download).delete()
        db.commit()

        return {"message": "All downloads and records cleared successfully"}
    except Exception as e:
        logging.error(f"Error clearing all downloads: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()
