import models.users as models
import bcrypt
import uuid
import geopy
from datetime import datetime
from config.main import AGENT
from starlette.exceptions import HTTPException


async def check_address(address):
    location = AGENT.geocode(address)
    if not location:
        raise HTTPException(status_code=422, detail="Address could not be verified")
    return (location.latitude, location.longitude)


async def register_user(form, db):
    column = db["carecart"]["users"]
    user = models.FullUserData(
        **form.dict(),
        points=0,
        trips=0,
        hours=0.0,
        active_order=None,
        orders_completed=[],
    )
    if user.age < 16:
        raise HTTPException(status_code=422, detail="Too young!")
    user.change_password(user.password)
    user_dict = user.dict()
    user_id = str(uuid.uuid4())
    user_dict["_id"] = user_id
    await check_address(user.address)
    column.insert_one(user_dict)
    return user_id


async def find_user(query, db):
    column = db["carecart"]["users"]
    try:
        document = column.find_one(query)
        return document
    except:
        raise Exception("Database exception")


async def login_user(form, db):
    query = {"email": form.email}
    document = await find_user(query, db)
    if not document:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    match = models.FullUserData(**document).check_password(form.password)
    if not match:
        raise HTTPException(
            status_code=403,
            detail="Incorrect password",
        )
    return form.email


async def create_ticket(form, db):
    column = db["carecart"]["tickets"]
    user_column = db["carecart"]["users"]
    ticket = models.FullTicketInfo(
        **form.dict(),
        created=datetime.now(),
        status=models.StatusEnum.CREATED,
        volunteer=None,
    )
    (lat, lng) = await check_address(ticket.destinationAddress)
    order_id = str(uuid.uuid4())
    order_dict = ticket.dict()
    order_dict["_id"] = order_id
    # set author's active order
    user = await find_user({"_id": ticket.author}, db)
    print(user)
    user["active_order"] = order_dict["_id"]
    #user_column.update(user)

    column.insert_one(order_dict)
    return models.ticket_form_output(lat=lat, lng=lng, order_id=order_dict["_id"])


async def cancel_ticket(form, db):
    return 0
