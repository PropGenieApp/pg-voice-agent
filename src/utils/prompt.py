#####################################################################################################
import json
from typing import Mapping

from configs.constants import BASE_DIR

#####################################################################################################

class PromptTemplateBuilder:

    _PROMPT_STORAGE_PATH = BASE_DIR / "src" / "prompts" / "instructions_blueprint.json"

    def __init__(self) -> None:
        pass

    def load(self) -> Mapping:
        with open(self._PROMPT_STORAGE_PATH, 'r') as f:
            return json.load(f)

    def build_instructions(self, tasks: list[str]) -> str:
        data = self.load()
        parts = [data["role"]]

        # Add task description
        for task in tasks:
            if task in data['tasks']:
                parts.append(data['tasks'][task]['description'])

        # Add task instructions
        for task in tasks:
            if task in data["tasks"]:
                parts.append(data["tasks"][task]["instructions"])

        parts.append(data["important_notes"])

        return "\n".join(parts)

#####################################################################################################

# FOR TESTING
# if __name__ == '__main__':
#     builder = PromptTemplateBuilder()
#     print(builder.build_instructions(tasks=['valuation', 'viewing']))
