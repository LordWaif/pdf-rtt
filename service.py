import uuid
import os
import shutil
from fastapi import FastAPI, UploadFile, BackgroundTasks
from celery.result import AsyncResult
from celery_app import celery_app
import json
import time

app = FastAPI()

# Caminho parametrizável para salvar os arquivos temporários
SAVE_PATH = "./shared"
FILE_RETENTION_DAYS = 10

def cleanup_old_files(path, retention_days):
    """
    Remove arquivos mais antigos que retention_days do diretório especificado.
    """
    now = time.time()
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        if os.stat(file_path).st_mtime < now - retention_days * 86400:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

@app.post("/api/v1/document/")
async def process_document(
        file: UploadFile, 
        config: UploadFile, 
        background_tasks: BackgroundTasks
    ):
    # Limpeza de arquivos antigos
    background_tasks.add_task(cleanup_old_files, SAVE_PATH, FILE_RETENTION_DAYS)

    # Gera um UUID para identificar o trabalho
    task_id = str(uuid.uuid4())

    os.makedirs(f"{SAVE_PATH}/{task_id}", exist_ok=True)
    # Salva o documento temporariamente
    temp_doc_filename = f"{SAVE_PATH}/{task_id}/{file.filename}"
    with open(temp_doc_filename, "wb") as f:
        f.write(await file.read())

    # Salva o config.json temporariamente
    temp_config_filename = f"{SAVE_PATH}/{task_id}/config.json"
    with open(temp_config_filename, "wb") as f:
        f.write(await config.read())

    # Carrega o config.json
    with open(temp_config_filename) as f:
        config = json.load(f)

    if config['output'].get("bbox",False):
        config["out_file_bbox"] = f"{SAVE_PATH}/{task_id}/{task_id}_bbox.pdf"

    if config['output'].get("txt",False):
        config["out_file_txt"] = f"{SAVE_PATH}/{task_id}/{task_id}_txt.txt"
    
    if config['output'].get("html",False):
        config["out_file_html"] = f"{SAVE_PATH}/{task_id}/{task_id}_html.html"

    if config['output'].get("csv",False):
        os.makedirs(f"{SAVE_PATH}/{task_id}/csv", exist_ok=True)
        config["out_path_csv"] = f"{SAVE_PATH}/{task_id}/csv"


    # Envia a tarefa para o Celery
    task = celery_app.send_task("process_file_task", args=[temp_doc_filename, config, task_id], task_id= task_id)
    return PlainTextResponse(
        status_code=202,
        content=task.id
    )

# Rota para verificar o status do processamento
@app.get("/api/v1/queue/{task_id}")
async def check_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.state == 'PENDING':
        return JSONResponse(content={"status": "Aguardando", "task_id": task_id},status_code=200)
    elif task_result.state == 'SUCCESS':
        return JSONResponse(content={
            "id": task_id,
            "text": f"/api/v1/text/{task_id}",
            "html": f"/api/v1/html/{task_id}",
            "bbox": f"/api/v1/bbox/{task_id}",
            "csv": f"/api/v1/csv/{task_id}",
        },status_code=201)
    elif task_result.state == 'FAILURE':
        return JSONResponse(content={"status": "Falhou", "task_id": task_id, "error": str(task_result.info)},status_code=500)
    else:
        return JSONResponse(content={"status": task_result.state, "task_id": task_id},status_code=500)
    
from fastapi.responses import PlainTextResponse, JSONResponse,FileResponse,HTMLResponse
@app.get("/api/v1/text/{task_id}")
async def get_txt(task_id: str):
    txt_path = f"{SAVE_PATH}/{task_id}/{task_id}_txt.txt"
    
    if os.path.exists(txt_path):
        with open(txt_path) as f:
            txt = f.read()
        return PlainTextResponse(content=txt, status_code=200)
    else:
        return JSONResponse(content={"status": "Arquivo não encontrado", "task_id": task_id}, status_code=404)
    
@app.get("/api/v1/html/{task_id}")
async def get_html(task_id: str):
    html_path = f"{SAVE_PATH}/{task_id}/{task_id}_html.html"
    
    if os.path.exists(html_path):
        with open(html_path) as f:
            html = f.read()
        return PlainTextResponse(content=html, status_code=200)
    else:
        return JSONResponse(content={"status": "Arquivo não encontrado", "task_id": task_id}, status_code=404)
    
@app.get("/api/v1/bbox/{task_id}")
async def get_bbox(task_id: str):
    bbox_path = f"{SAVE_PATH}/{task_id}/{task_id}_bbox.pdf"
    
    if os.path.exists(bbox_path):
        return FileResponse(bbox_path)
    else:
        return JSONResponse(content={"status": "Arquivo não encontrado", "task_id": task_id}, status_code=404)
    
@app.get("/api/v1/csv/{task_id}")
async def get_csv(task_id: str):
    csv_path = f"{SAVE_PATH}/{task_id}/csv"
    routes = []
    if os.path.exists(csv_path):
        csv_files = [f for f in os.listdir(csv_path) if f.endswith('.csv')]
        for file in csv_files:
            import regex as re
            match = re.match(r'pg_(\d+)_n_(\d+).csv', file)
            if match:
                page = match.group(1)
                number = match.group(2)
                route = f"/api/v1/csv/{task_id}/{page}/{number}"
                routes.append(route)
        routes = sorted(routes)
        return routes
    else:
        return JSONResponse(content={"status": "Arquivo não encontrado", "task_id": task_id}, status_code=404)
    
@app.get("/api/v1/csv/{task_id}/{page}/{number}")
async def get_csv(task_id: str, page: int, number: int):
    csv_path = f"{SAVE_PATH}/{task_id}/csv"
    if os.path.exists(csv_path):
        file_csv = f"{csv_path}/pg_{page}_n_{number}.csv"
        with open(file_csv,'r') as f:
            csv = f.read()
        return PlainTextResponse(content=csv, status_code=200)
    else:
        return JSONResponse(content={}, status_code=404)