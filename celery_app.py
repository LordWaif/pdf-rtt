from celery import Celery
import os,json

# Importação condicional do módulo utils
try:
    from utils import process_soup
except ImportError:
    process_soup = None

# Configuração do Celery com Redis existente
celery_app = Celery(
    'tasks',
    broker='redis://10.2.50.49:5009/0',  # O Redis já existente
    backend='redis://10.2.50.49:5009/0',  # Também pode usar o Redis como backend de resultados
    include=['celery_app']  # Inclui os módulos de tarefas
)

# Especifica uma fila exclusiva para esta aplicação
celery_app.conf.task_routes = {'process_file_task': {'queue': 'rtt_queue'}}

@celery_app.task(name="process_file_task")
def process_file_task(filepath, config, task_id):
    config_process = {
        "input_file": filepath,
        "generate_bbox": config['output']["bbox"],
        "header": config["header"]["process"],
        "footer": config["footer"]["process"],
        "tables": config["output"]["csv"],
        "sections": False,
        "min_sequence_header": config["header"]["min_sequence_header"],
        "min_sequence_footer": config["footer"]["min_sequence_footer"],
        "preprocess_soup": config["preprocess_soup"],
        "delimit_margin": config["delimit_margin"],
        "reach_search": config["header-footer"]["reach_search"],
        "min_chain": config["header-footer"]["min_chain"],
        "out_file_bbox": config.get("out_file_bbox", None),
        "out_file_txt": config.get("out_file_txt", None),
        "out_file_html": config.get("out_file_html", None),
        "out_path_csv": config.get("out_path_csv", None),
    }
    result = process_soup(**config_process)   
    return {"status": "Processado com sucesso", "output": result, "task_id": task_id}