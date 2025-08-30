import argparse

import fire
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from toolcall_bridge.app import create_app
from toolcall_bridge.configs import LOG_DIR
# from prompt_agent.lifespan import lifespan
# from prompt_agent.middlewares.register_middlewares import register_middleware
# from prompt_agent.router import router

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="0.0.0.0", help="host")
parser.add_argument("--port", default=3648, help="port")
args = parser.parse_args()
logger.add(LOG_DIR / "log_file.log", rotation="1 week")  # 每周轮换一次文件

app = create_app()


def start_server(port=args.port, host=args.host):
    logger.info(f"Starting server at {host}:{port}")
    config = uvicorn.Config(app, host=host, port=port)
    server = uvicorn.Server(config=config)
    try:
        server.run()
    finally:
        logger.info("Server shutdown.")


if __name__ == "__main__":
    fire.Fire(start_server)
