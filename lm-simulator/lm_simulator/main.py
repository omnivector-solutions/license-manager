from typing import List

from fastapi import Body, Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from lm_simulator import crud, models, schemas
from lm_simulator.database import engine, session

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()


subapp = FastAPI(title="License Manager Simulator API")
subapp.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@subapp.get(
    "/health",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={204: {"description": "API is healthy"}},
)
def health():
    """
    Provide a health-check endpoint for the app.
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@subapp.post(
    "/licenses/",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.LicenseRow,
)
def create_license(license: schemas.LicenseCreate, db: Session = Depends(get_db)):
    try:
        created_license = crud.create_license(db, license)
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"License already exists\n{e}")
    return created_license


@subapp.get(
    "/licenses/",
    status_code=status.HTTP_200_OK,
    response_model=List[schemas.LicenseRow],
)
def list_licenses(db: Session = Depends(get_db)):
    return crud.get_licenses(db)


@subapp.delete(
    "/licenses/{license_name}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_license(
    license_name: str,
    db: Session = Depends(get_db),
):
    try:
        crud.delete_license(db, license_name)
    except crud.LicenseNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@subapp.post(
    "/licenses-in-use/",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.LicenseInUseRow,
)
def create_license_in_use(license_in_use: schemas.LicenseInUseCreate, db: Session = Depends(get_db)):
    try:
        created_license_in_use = crud.create_license_in_use(db, license_in_use)
    except crud.LicenseNotFound:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The license {license_in_use.license_name} doesn't exist.",
        )
    except crud.NotEnoughLicenses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough licenses available.")
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"LicenseInUse already exists\n{e}")
    return created_license_in_use


@subapp.get(
    "/licenses-in-use/",
    status_code=status.HTTP_200_OK,
    response_model=List[schemas.LicenseInUseRow],
)
def list_licenses_in_use(db: Session = Depends(get_db)):
    return crud.get_licenses_in_use(db)


@subapp.get(
    "/licenses-in-use/{license_name}",
    status_code=status.HTTP_200_OK,
    response_model=List[schemas.LicenseInUseRow],
)
def list_licenses_in_use_from_name(license_name: str, db: Session = Depends(get_db)):
    return crud.get_licenses_in_use_from_name(db, license_name)


@subapp.delete(
    "/licenses-in-use/",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_license_in_use(
    lead_host: str = Body(...),
    user_name: str = Body(...),
    quantity: int = Body(...),
    license_name: str = Body(...),
    db: Session = Depends(get_db),
):
    try:
        crud.delete_license_in_use(db, lead_host, user_name, quantity, license_name)
    except crud.LicenseNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


app = FastAPI()
app.mount("/lm-sim", subapp)
