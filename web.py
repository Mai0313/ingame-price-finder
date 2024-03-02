from index import demo
import gradio as gr
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_main():
    return {"message": "This is your main app"}


app = gr.mount_gradio_app(app, demo, path="/seller")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)
