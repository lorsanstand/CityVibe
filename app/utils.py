from typing import Type, Union, List, Sequence
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

def convert_from_pydantic(
    schema: Type[BaseModel],
    models
):

    if models is None:
        return None

    if not isinstance(models, (list, tuple)):
        return schema.model_validate(models, from_attributes=True)

    answer = [schema.model_validate(row, from_attributes=True) for row in models]
    return answer[0] if len(answer) == 1 else answer