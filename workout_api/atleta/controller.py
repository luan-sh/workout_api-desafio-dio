from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Body, HTTPException, status
from fastapi_pagination import Page, paginate
from pydantic import UUID4
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from workout_api.categorias.models import CategoriaModel
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.contrib.dependencies import DatabaseDependency
from workout_api.atleta.schemas import AtletaIn, AtletaOut, AtletaUpdate
from workout_api.atleta.models import AtletaModel

router = APIRouter()

@router.post(
    "/",
    summary = "Criar novo atleta",
    status_code = status.HTTP_201_CREATED,
    response_model = AtletaOut
)

async def post(
    db_session: DatabaseDependency,
    atleta_in: AtletaIn = Body(...)
):
    
    categoria_nome = atleta_in.categoria.nome
    centro_treinamento_nome = atleta_in.centro_treinamento.nome

    categoria = (
        await db_session.execute(select(CategoriaModel).filter_by(nome=categoria_nome))
    ).scalars().first()

    if not categoria:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = f"A categoria {categoria_nome} não foi encontrada"
        )
    
    centro_treinamento = (
        await db_session.execute(select(CentroTreinamentoModel).filter_by(nome=centro_treinamento_nome))
    ).scalars().first()

    if not centro_treinamento:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = f"O centro de treinamento {centro_treinamento_nome} não foi encontrado"
        )

    try:
        atleta_out = AtletaOut(id=uuid4(), created_at=datetime.utcnow(), **atleta_in.model_dump())
        atleta_model = AtletaModel(**atleta_out.model_dump(exclude={"categoria", "centro_treinamento"}))

        atleta_model.categoria_id = categoria.pk_id
        atleta_model.centro_treinamento_id = centro_treinamento.pk_id
        
        db_session.add(atleta_model)
        await db_session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code = status.HTTP_303_SEE_OTHER,
            detail = f"Já existe um atleta cadastrado com o cpf: {atleta_in.cpf}"
        )

    return atleta_out

@router.get(
    "/",
    summary = "Consultar todos os atletas",
    status_code = status.HTTP_200_OK,
    response_model=Page[AtletaOut],
)

async def query(db_session: DatabaseDependency) -> Page[AtletaOut]:

    atletas: list[AtletaOut] = (await db_session.execute(select(AtletaModel))).scalars().all()
    
    atletas_out = [AtletaOut.model_validate(atleta) for atleta in atletas]

    return paginate(atletas_out)

@router.get(
    "/consultar-atleta",
    summary = "Consultar um atleta por id, nome ou cpf",
    status_code = status.HTTP_200_OK,
    response_model = AtletaOut,
)

async def get(
            db_session: DatabaseDependency,
            id: Optional[UUID4] = None,
            nome: Optional[str] = None,
            cpf: Optional[str] = None,
    ) -> AtletaOut:

    if not id and not nome and not cpf:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, 
            detail = "Pelo menos um dos parâmetros (id, nome ou cpf) deve ser fornecido."
        )
    
    query = select(AtletaModel)
    
    if id:
        query = query.filter_by(id=id)
    if nome:
        query = query.filter_by(nome=nome)
    if cpf:
        query = query.filter_by(cpf=cpf)
    

    atletas: AtletaOut = (
        await db_session.execute(query)
    ).scalars().first()

    if not atletas:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = "Atleta não encontrado"
        )
    
    return atletas

@router.patch(
    "/{id}",
    summary = "Editar um atleta pelo id",
    status_code = status.HTTP_200_OK,
    response_model = AtletaOut,
)

async def patch(id: UUID4, db_session: DatabaseDependency, atleta_up: AtletaUpdate = Body(...)) -> AtletaOut:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
    ).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = f'Atleta não encontrado para o id: {id}'
        )
    
    atleta_update = atleta_up.model_dump(exclude_unset=True)
    for key, value in atleta_update.items():
        setattr(atleta, key, value)

    await db_session.commit()
    await db_session.refresh(atleta)

    return atleta

@router.delete(
    "/{id}",
    summary = "Deletar um atleta pelo id",
    status_code = status.HTTP_204_NO_CONTENT,
)

async def delete(id: UUID4, db_session: DatabaseDependency) -> None:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
    ).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = f'Atleta não encontrado para o id: {id}'
        )
    
    await db_session.delete(atleta)
    await db_session.commit()