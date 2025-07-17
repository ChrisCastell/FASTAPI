from fastapi import FastAPI, Body, Path, Query, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional, List
from pydantic import BaseModel, Field
from jwt_manager import create_token, validate_token
from fastapi.security import HTTPBearer
from config.database import Session, engine, Base
from models.product import Product as ProductModel
from fastapi.encoders import jsonable_encoder

app = FastAPI()

app.title = "Chris Castell Store"
app.version = '0.1.1'

Base.metadata.create_all(bind=engine)

class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request):
        auth = await super().__call__(request)
        data = validate_token(auth.credentials)
        if data['email'] != "admin@gmail.com":
            raise HTTPException(status_code=401, detail="Invalid user")

class User(BaseModel):
    email:str
    password: str

class Product(BaseModel):
    id: Optional[int] = None
    title: str = Field(default="Product name" ,min_length=2, max_length=50)
    overview: str = Field(default="Product description" ,min_length=10, max_length=300)
    year: int = Field(default=2023, le=2023)
    rating: float = Field(default=10, ge=0, le=10)
    category: str = Field(default="Beauty" ,min_length=4, max_length=15)

@app.get("/", tags=['home'])
def message():
    return HTMLResponse(content="<h1> Chris Castell Store </h1>")

@app.get("/products", tags=['products'], response_model=List[Product], status_code=200, dependencies=[Depends(JWTBearer())])
def get_products() -> List[Product]:
    db = Session()
    result = db.query(ProductModel).all() # SELECT * FROM products
    return JSONResponse(status_code=200, content=jsonable_encoder(result))

@app.get("/products/{id}", tags=['products'], status_code=200, response_model=Product)
def get_product(id: int) -> Product:
    db = Session()
    result = db.query(ProductModel).filter(ProductModel.id == id).first()
    if result:
        return JSONResponse(content=jsonable_encoder(result), status_code=200)
    else:
        return JSONResponse(content={"message": "Product not found"}, status_code=404)

@app.get("/products/", tags=['products'], response_model=List[Product])
def get_product_by_category(category: str) -> List[Product]:
    db = Session()
    result = db.query(ProductModel).filter(ProductModel.category == category).all()
    if result:
        return JSONResponse(content=jsonable_encoder(result), status_code=200)
    else:
        return JSONResponse(content={"message": "Product not found"}, status_code=404)

@app.post("/products", tags=['products'], response_model=dict, status_code=201)
def create_product(product: Product) -> dict:
    db = Session()
    new_product = ProductModel(**product.model_dump())
    db.add(new_product)
    db.commit()
    return JSONResponse(content={"message": "Product created successfully"},
                        status_code=201)

@app.put("/products/{id}", tags=['products'], response_model=dict, status_code=200)
def update_product(id: int, product: Product) -> dict:
    db = Session()
    result = db.query(ProductModel).filter(ProductModel.id == id).first()
    if not result:
        return JSONResponse(content={"message": "Products not found"}, status_code=404)
    result.title = product.title
    result.overview = product.overview
    result.year = product.year
    result.rating = product.rating
    result.category = product.category
    db.commit()
    return JSONResponse(content={"message": "Product updated successfully"}, status_code=200)

@app.delete("/products/{id}", tags=['products'], response_model=dict)
def delete_product(id: int) -> dict:
    db = Session()
    result = db.query(ProductModel).filter(ProductModel.id == id).first()
    if not result:
        return JSONResponse(content={"message": "Products not found"}, status_code=404)
    db.delete(result)
    db.commit()
    return JSONResponse(content={"message": "Product deleted successfully"})

@app.post("/login", tags=['auth'], response_model=dict, status_code=200)
def login(user: User):
    if user.email == "admin@gmail.com" and user.password == "admin":
        token = create_token(data=user.model_dump())
        return JSONResponse(content={"token": token}, status_code=200)
    else:
        return JSONResponse(content={"message": "Invalid credentials"}, status_code=401)