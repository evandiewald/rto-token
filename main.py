from fastapi import Depends, FastAPI, HTTPException, Form, File, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm, OAuth2, HTTPBasic
from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.openapi.utils import get_openapi
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from starlette.status import HTTP_403_FORBIDDEN
from starlette.responses import RedirectResponse, Response, JSONResponse, HTMLResponse, FileResponse
from starlette.requests import Request
from pydantic.decorator import Optional

import transactions
import config
from database import *
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import inspect

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Postgres
db = create_engine(config.DB_STRING)
conn = db.connect()
session = Session(db)
table = listings_table(db)

# create table if it does not already exist
if not inspect(db).has_table('listings'):
    print('\'listings\' table does not yet exist. Creating it now...')
    table.create()


@app.route("/", methods=["GET", "POST"])
async def homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/balance")
async def check_balance(request: Request, address: str = Form(...)):
    balance = transactions.balanceOf(address) / 1e18
    return templates.TemplateResponse("balance.html", {"request": request, "address": address, "balance": balance})


@app.get("/wallet", response_class=HTMLResponse)
async def connect_wallet(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/rent", response_class=HTMLResponse)
async def pay_rent_page(request: Request):
    return templates.TemplateResponse("pay_rent.html", {"request": request})


@app.post("/rent/pay")
async def pay_rent_confirm(request: Request, amount_eth: str = Form(...), landlord: str = Form(...)):
    txn_dict = transactions.payRent(landlord, amount_eth)
    return templates.TemplateResponse("confirm_transaction.html", {"request": request, "txn_data": txn_dict['data'],
                                                                   "contract_address": config.CONTRACT_ADDRESS,
                                                                   "amount_eth": amount_eth, "value": hex(txn_dict['value']),
                                                                   "landlord": landlord})


@app.route("/listings", methods=["GET", "POST"])
async def view_listings(request: Request):
    listings = get_listings(table)
    return templates.TemplateResponse("listings.html", {"request": request, "listings": listings})


@app.get("/listings/new", response_class=HTMLResponse)
async def new_listing(request: Request):
    return templates.TemplateResponse("new_listing.html", {"request": request})


@app.post("/listings/new/post")
async def new_listing_post(request: Request, renter: str = Form(...), streetAddress: str = Form(...), description: str = Form(...),
                           imageUrl: str = Form(...), listPrice: str = Form(...), earningsPercent: str = Form(...)):
    txn_dict = transactions.addHome(int(listPrice)*1e18, renter, int(earningsPercent))
    add_listing(table, renter, streetAddress, description, imageUrl, None)
    return templates.TemplateResponse("confirm_new_home.html", {"request": request, "txn_data": txn_dict['data'],
                                                                "contract_address": config.CONTRACT_ADDRESS,
                                                                "renter": renter, "listPrice": listPrice,
                                                                "earningsPercent": earningsPercent
                                                                })


@app.post("/listings/{renter}/post")
async def view_listing_post(renter, txn_hash: str = Form(...)):
    if txn_hash:
        transactionUrl = 'https://ropsten.etherscan.io/tx/' + txn_hash
        update_transaction_url(table, renter, transactionUrl)
    listing = get_listing(table, renter)
    blockchain_data = transactions.getHome(renter)
    return templates.TemplateResponse("view_listing.html", {"request": request, "listing": listing, "blockchain_data": blockchain_data})


@app.get("/listings/{renter}", response_class=HTMLResponse)
async def view_listing(request: Request, renter):
    listing = get_listing(table, renter)
    blockchain_data = transactions.getHome(renter)
    blockchain_data[2] /= 1e18
    blockchain_data[3] /= 1e18
    print(blockchain_data)
    return templates.TemplateResponse("view_listing.html", {"request": request, "listing": listing, "blockchain_data": blockchain_data})
