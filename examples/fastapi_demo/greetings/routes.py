"""FastAPI router — resolves ports from the container via ``Depends(Provide(...))``."""

from fastapi import APIRouter, Depends

from django_autowired.integrations.fastapi import Provide
from greetings.domain.ports.services.greeter import IGreeter

router = APIRouter()


@router.get("/greet/{name}")
def greet(name: str, greeter: IGreeter = Depends(Provide(IGreeter))):
    return {"message": greeter.greet(name)}
