from fastapi import FastAPI

app = FastAPI(
    title='RepoPilot',
    description='AI engineering assistant for GitHub repositories',
    version='0.1.0'
)

@app.get('/')
def root():
    return {'msg' : 'RepoPilot is running'}