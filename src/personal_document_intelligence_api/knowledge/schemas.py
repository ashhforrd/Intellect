from pydantic import BaseModel, Field


class ExtractedConcept(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    description: str = Field(min_length=1)
    source_numbers: list[int]


class ExtractedRelation(BaseModel):
    source_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    source_numbers: list[int]


class KnowledgeGraphExtraction(BaseModel):
    concepts: list[ExtractedConcept]
    relations: list[ExtractedRelation]
