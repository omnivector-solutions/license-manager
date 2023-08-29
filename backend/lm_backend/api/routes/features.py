from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from lm_backend.api.cruds.feature import FeatureCRUD
from lm_backend.api.models.feature import Feature
from lm_backend.api.schemas.feature import (
    FeatureCreateSchema,
    FeatureSchema,
    FeatureUpdateByNameSchema,
    FeatureUpdateSchema,
)
from lm_backend.database import SecureSession, secure_session
from lm_backend.permissions import Permissions

router = APIRouter()

crud_feature = FeatureCRUD(Feature, FeatureCreateSchema, FeatureUpdateSchema)


@router.post(
    "",
    response_model=FeatureSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_feature(
    feature: FeatureCreateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.FEATURE_EDIT)),
):
    """Create a new feature"""
    return await crud_feature.create(db_session=secure_session.session, obj=feature)


@router.get(
    "",
    response_model=List[FeatureSchema],
    status_code=status.HTTP_200_OK,
)
async def read_all_features(
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
    secure_session: SecureSession = Depends(secure_session(Permissions.FEATURE_VIEW)),
):
    """Return all features with associated bookings."""
    return await crud_feature.read_all(
        db_session=secure_session.session,
        search=search,
        sort_field=sort_field,
        sort_ascending=sort_ascending,
        force_refresh=True,  # To lazy load relationships and hybrid properties
    )


@router.get(
    "/{feature_id}",
    response_model=FeatureSchema,
    status_code=status.HTTP_200_OK,
)
async def read_feature(
    feature_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.FEATURE_VIEW)),
):
    """Return a feature with associated bookings with the given id."""
    return await crud_feature.read(db_session=secure_session.session, id=feature_id, force_refresh=True)


@router.put(
    "/bulk",
    status_code=status.HTTP_200_OK,
)
async def bulk_update_feature(
    features: List[FeatureUpdateByNameSchema],
    secure_session: SecureSession = Depends(secure_session(Permissions.FEATURE_EDIT)),
):
    """
    Update a list of features in the database using the name of each feature.
    Since the name is not unique across clusters, the client_id
    in the token is used to identify the cluster.
    """
    client_id = secure_session.identity_payload.client_id

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("Couldn't find a valid client_id in the access token."),
        )

    await crud_feature.bulk_update(
        db_session=secure_session.session,
        features=features,
        cluster_client_id=client_id,
    )

    return {"message": "Features updated successfully."}


@router.put(
    "/{feature_id}",
    response_model=FeatureSchema,
    status_code=status.HTTP_200_OK,
)
async def update_feature(
    feature_id: int,
    feature_update: FeatureUpdateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.FEATURE_EDIT)),
):
    """Update a feature in the database."""
    return await crud_feature.update(
        db_session=secure_session.session,
        id=feature_id,
        obj=feature_update,
    )


@router.delete(
    "/{feature_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_feature(
    feature_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.FEATURE_EDIT)),
):
    """
    Delete a feature from the database.
    """
    return await crud_feature.delete(db_session=secure_session.session, id=feature_id)
