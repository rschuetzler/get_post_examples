import base64
import codecs
import hashlib

from fastapi import Body, FastAPI, Response, status
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SECRET = base64.urlsafe_b64encode("404isbest".encode("utf-8"))

API_KEY = "404isthebestclass"
API_KEY_NAME = "access_token"

tags_metadata = [
    {"name": "skillcheck", "description": "APIs to be used in Skill Check 2"},
    {
        "name": "shoutcast",
        "description": "A simple API-driven shouting social network.",
    },
]

app = FastAPI(
    title="IS404.net APIs",
    description="A bunch of APIs for use in IS 404",
    version="0.2",
    redoc_url="/docs",
    docs_url=None,
    openapi_tags=tags_metadata,
)

Base = declarative_base()


class ShortMessage(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True)
    text = Column(String)
    section_number = Column(Integer)


engine = create_engine("sqlite:///uppercase.db")
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.create_all(engine)


@app.post("/shout", tags=["shoutcast"])
async def shout(
    input: str = Body(..., example="example text"),
    section_number: int = Body(..., example=1),
):
    upper_text = input.upper()
    upper_case = ShortMessage(text=upper_text, section_number=section_number)
    session.add(upper_case)
    session.commit()
    return {"shout": upper_text}


@app.post("/madlib", tags=["shoutcast"])
async def generate_madlib(
    section_number: int = Body(..., example=1),
    noun: str = Body(..., example="desk chair"),
    food: str = Body(..., example="banana"),
    place: str = Body(..., example="Tanner Building"),
    animal: str = Body(..., example="horse"),
    movement_verb: str = Body(..., example="dance"),
    verb1: str = Body(..., example="eat"),
    verb2: str = Body(..., example="run"),
):
    vals = locals()
    madlib = (
        f"If you give a {animal} a {food}, it is going to ask for a {noun}. "
        f"When you give it the {noun}, it will want to {verb1}. When it is finished, "
        f"it will {verb2}. Then it will {movement_verb} to the {place}."
    )

    message = ShortMessage(text=madlib, section_number=section_number)
    session.add(message)
    session.commit()
    return {"madlib": madlib}


@app.get("/")
def index():
    html = """
    <html>
      <head>
        <title>Skill Check 2</title>
      </head>
      <body>I don't think this is what you want. Maybe try going to the <a href="/docs">API docs</a>.</body>
    </html>
    """  # noqa
    return HTMLResponse(status_code=200, content=html)


@app.get("/apikey", status_code=201, tags=["skillcheck"])
async def get_api_key(netid: str, response: Response):
    secret = SECRET
    hashed = hashlib.sha1(f"{netid}+salt".encode("utf-8"))
    apikey = hashed.hexdigest()[:8]
    print(apikey)
    response.headers["X-this-is-a-secret"] = secret.decode("utf-8")
    return {"api_key": apikey}


class Message(BaseModel):
    netid: str = Field(..., example="netid123")
    api_key: str = Field(..., example="abc123")
    secret_code: str = Field(..., example="ASDF1234")
    message: str = Field(..., example="Put your message here")


@app.post("/encode_message", status_code=200, tags=["skillcheck"])
async def encode_message(message: Message, response: Response):
    hashed = hashlib.sha1(f"{message.netid}+salt".encode("utf-8")).hexdigest()[:8]
    if not hashed == message.api_key:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"message": "Invalid API key. Please try again."}
    if not message.secret_code.encode("utf-8") == SECRET:
        print(message.secret_code.encode("utf-8"))
        print(SECRET)
        response.status_code = status.HTTP_403_FORBIDDEN
        return {"message": "Invalid secret. Please try again"}
    rotted = codecs.encode(message.message, "rot_13")
    return {"encoded_message": rotted}


@app.get("/teapot", response_class=HTMLResponse, tags=["skillcheck"])
async def im_a_teapot(response: Response):
    response.status_code = 418
    return """
    <html>
      <head>
        <title>I'm a Teapot</title>
      </head>
      <body><h1>I'm a Teapot</h1><p>A little teapot.</p></body>
    </html>
    """


@app.get("/favicon.ico", response_class=FileResponse, include_in_schema=False)
async def favicon(response: Response):
    return "favicon.ico"


@app.get("/{section}", tags=["shoutcast"])
def show_messages(section: int = None):
    if section:
        results = (
            session.query(ShortMessage)
            .filter(ShortMessage.section_number == section)
            .order_by(ShortMessage.id.desc())
            .limit(25)
        )
    else:
        results = session.query(ShortMessage).order_by(ShortMessage.id.desc()).limit(25)
    messages = [result.text for result in results]
    if len(messages) > 0:
        html = (
            "<html><body><h1>Most recent messages</h1><ul>"
            + "\n".join([f"<li>{message}</li>" for message in messages])
            + "</ul></body></html>"
        )
    else:
        html = "<html><body><h1>No messages yet</h1></body></html>"
    return HTMLResponse(content=html, status_code=200)
