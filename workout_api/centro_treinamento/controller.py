from uuid import uuid4

from fastapi import APIRouter, HTTPException, Body, status
from fastapi_pagination import Page, paginate
from pydantic import UUID4
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from workout_api.centro_treinamento.schemas import CentroTreinamentoIn, CentroTreinamentoOut
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.contrib.dependencies import DatabaseDependency

router = APIRouter()

@router.post(
    "/",
    summary = "Criar novo Centro de treinamento",
    status_code = status.HTTP_201_CREATED,
    response_model = CentroTreinamentoOut,
)

async def post(
    db_session: DatabaseDependency,
    centro_treinamento_in: CentroTreinamentoIn = Body(...)
) -> CentroTreinamentoOut:

    try:
        centro_treinamento_out = CentroTreinamentoOut(id=uuid4(), **centro_treinamento_in.model_dump())
        centro_treinamento_model = CentroTreinamentoModel(**centro_treinamento_out.model_dump())
        
        db_session.add(centro_treinamento_model)
        await db_session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code = status.HTTP_303_SEE_OTHER,
            detail = f"Já existe um centro de treinamento cadastrado com o nome: {centro_treinamento_in.nome}"
        )

    return centro_treinamento_out

@router.get(
    "/",
    summary = "Consultar todos os centros de treinamento",
    status_code = status.HTTP_200_OK,
    response_model = Page[CentroTreinamentoOut],
)

async def query(db_session: DatabaseDependency) -> Page[CentroTreinamentoOut]:
    centros_treinamento: list[CentroTreinamentoOut] = (
        await db_session.execute(select(CentroTreinamentoModel))
    ).scalars().all()

    centros_treinamento_out = [CentroTreinamentoOut.model_validate(centro_treinamento) for centro_treinamento in centros_treinamento]
    
    return paginate(centros_treinamento_out)

@router.get(
    "/{id}",
    summary = "Consultar centro de treinamento por id",
    status_code = status.HTTP_200_OK,
    response_model = CentroTreinamentoOut,
)

async def get(id: UUID4, db_session: DatabaseDependency) -> CentroTreinamentoOut:
    centro_treinamento_out: CentroTreinamentoOut = (
        await db_session.execute(select(CentroTreinamentoModel).filter_by(id=id))
    ).scalars().first()

    if not centro_treinamento_out:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = f'Centro de treinamento não encontrado para o id: {id}'
        )
    
    return centro_treinamento_out