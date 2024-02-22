from reactpy import component, html
from reactpy.backend.fastapi import configure
from fastapi import FastAPI

@component
def HelloWorld():
    return html.h1("Hello, world!")


app = FastAPI()
configure(app, HelloWorld)