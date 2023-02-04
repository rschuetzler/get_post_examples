from fastapi import FastAPI, Body
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from fastapi.responses import HTMLResponse

app = FastAPI()

Base = declarative_base()


class Message(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True)
    text = Column(String)
    section_number = Column(Integer)


engine = create_engine("sqlite:///uppercase.db")
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.create_all(engine)


@app.post("/shout")
async def shout(
    input: str = Body(..., example="example text"),
    section_number: int = Body(..., example=1),
):
    upper_text = input.upper()
    upper_case = Message(text=upper_text, section_number=section_number)
    session.add(upper_case)
    session.commit()
    return {"shout": upper_text}


@app.post("/madlib")
async def generate_madlib(
    section_number: int = Body(..., example=1),
    animal: str = Body(..., example="horse"),
    verb1: str = Body(..., example="eat"),
    verb2: str = Body(..., example="run"),
    movement_verb: str = Body(..., example="dance"),
    food: str = Body(..., example="banana"),
    noun: str = Body(..., example="desk chair"),
    place: str = Body(..., example="Tanner Building"),
):
    vals = locals()
    madlib = (
        f"If you give a {animal} a {food}, it is going to ask for a {noun}. "
        f"When you give it the {noun}, it will want to {verb1}. When it is finished, "
        f"it will {verb2}. Then it will {movement_verb} to the {place}."
    )

    message = Message(text=madlib, section_number=section_number)
    session.add(message)
    session.commit()
    return {"madlib": madlib}


@app.get("/{section}")
@app.get("/")
def show_messages(section: int = None):
    if section:
        results = (
            session.query(Message)
            .filter(Message.section_number == section)
            .order_by(Message.id.desc())
            .limit(50)
        )
    else:
        results = session.query(Message).order_by(Message.id.desc()).limit()
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
