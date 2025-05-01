#####################################################################################################

from typing import Final

from fastapi import APIRouter, Request, HTTPException, Response, status
from fastapi.responses import HTMLResponse

from configs.constants import BASE_DIR


#####################################################################################################

router: Final = APIRouter(tags=['Demo'], prefix='/api/demo')

#####################################################################################################

@router.get('')
async def dg_voice_demo(request: Request) -> HTMLResponse:
    app = request.app
    instructions_filepath = BASE_DIR / 'src' / 'prompts' / 'dev_instructions.txt'
    assistant_instructions = instructions_filepath.read_text()
    response = app.templates.TemplateResponse(
        request=request,
        name='demo.html',
        context={'instructions': assistant_instructions}
    )
    return response

#####################################################################################################

@router.get("/get-demo-instructions")
async def get_instructions() -> dict[str, str]:
    instructions_filepath = BASE_DIR / 'src' / 'prompts' / 'dev_instructions.txt'
    assistant_instructions = instructions_filepath.read_text()
    return {'instructions': assistant_instructions}

#####################################################################################################

@router.post("/update-prompt")
async def update_prompt(prompt_data: dict):
    try:
        instructions_filepath = BASE_DIR / 'src' / 'prompts' / 'dev_instructions.txt'
        with open(instructions_filepath, 'w') as f:
            f.write(prompt_data["prompt"])
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
