from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from boutique.application.dataset.interfaces import ImportKaggleOlistDatasetUseCase
from boutique.domain.common.cache import CacheInvalidationError
from boutique.domain.dataset.exceptions import (
    DatasetAlreadySeededError,
    KaggleCredentialsMissingError,
    KaggleDatasetDownloadError,
)
from boutique.presentation.http.schemas.dataset import (
    DatasetImportResponseSchema,
    KaggleOlistImportRequestSchema,
)
from boutique.presentation.http.security import get_authenticated_user

router = APIRouter(
    prefix="/dataset",
    tags=["dataset"],
    dependencies=[Depends(get_authenticated_user)],
)


@router.post("/import/kaggle", response_model=DatasetImportResponseSchema)
@inject
async def import_kaggle_olist_dataset(
    payload: KaggleOlistImportRequestSchema,
    use_case: Annotated[
        ImportKaggleOlistDatasetUseCase,
        Depends(Provide["import_kaggle_olist_dataset"]),
    ],
) -> DatasetImportResponseSchema:
    try:
        result = await use_case(replace_existing=payload.replace_existing)
    except DatasetAlreadySeededError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Data already exists. Confirm replacement to import it again.",
        ) from error
    except KaggleCredentialsMissingError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except (KaggleDatasetDownloadError, CacheInvalidationError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    return DatasetImportResponseSchema.from_seed_result(result=result)
