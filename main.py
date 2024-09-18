from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session


app = FastAPI()
models.Base.metadata.create_all(bind=engine)

class ChoiceBase(BaseModel):
    choice_text: str
    is_correct: bool

class QuestionBase(BaseModel):
    question_text: str
    choices: List[ChoiceBase] = []

class QuizBase(BaseModel):
    quiz_title: str
    questions: List[QuestionBase] = []

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

## Quizes main routes
@app.get("/quizes/")
async def read_quizes(db: db_dependency):
    result = db.query(models.Quizes).all()
    if not result:
        raise HTTPException(status_code=404, detail='No quizes')
    return result

@app.post("/quizes/")
async def create_quiz(quiz: QuizBase, db: db_dependency):
    db_quiz = models.Quizes(quiz_title=quiz.quiz_title)
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    
    if not quiz.questions:
        return {"message": "Quiz created successfully"}
    
    for question in quiz.questions:
        db_question = models.Questions(
            question_text=question.question_text,
            quiz_id=db_quiz.id)
        
        db.add(db_question)
    db.commit()
    
    return {"message": "Quiz created successfully"}

@app.delete("/quizes/{quiz_id}/")
async def delete_quiz(quiz_id: int, db: db_dependency):
    db_quiz = db.query(models.Quizes).filter(models.Quizes.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(status_code=404, detail='Quiz not found')
    db.delete(db_quiz)
    db.commit()
    return {"message": "Quiz deleted successfully"}


## Questions routes
@app.get("/quizes/{quiz_id}/questions/")
async def read_questions(quiz_id: int, db: db_dependency):
    result = db.query(models.Questions).filter(models.Questions.quiz_id == quiz_id).all()
    if not result:
        raise HTTPException(status_code=404, detail='Quiz not found')
    for question in result:
        question.choices = db.query(models.Choices).filter(models.Choices.question_id == question.id).all()
    return result

@app.post("/quizes/{quiz_id}/questions/")
async def create_question(quiz_id: int, question: QuestionBase, db: db_dependency):
    db_question = models.Questions(
        question_text=question.question_text,
        quiz_id=quiz_id)
    
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    
    for choice in question.choices:
        db_choice = models.Choices(
            choice_text=choice.choice_text,
            is_correct=choice.is_correct,
            question_id=db_question.id)
        
        db.add(db_choice)
    db.commit()
    return {"message": "Question created successfully"}

@app.delete("/quizes/{quiz_id}/questions/{question_id}")
async def delete_question(quiz_id: int, question_id: int, db: db_dependency):
    db_quiz = db.query(models.Quizes).filter(models.Quizes.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(status_code=404, detail='Quiz not found')
    db_questions = db.query(models.Questions).filter(models.Questions.id == question_id).first()
    if not db_questions:
        raise HTTPException(status_code=404, detail='Questions not found')
    for question in db_questions:
        db.delete(question)
    db.commit()
    return {"message": "Questions deleted successfully"}

## Choices routes
@app.post("/quizes/{quiz_id}/questions/{question_id}")
async def create_choices(quiz_id: int, question_id: int, choice: ChoiceBase, db: db_dependency):
    db_choice = models.Choices(
        choice_text=choice.choice_text,
        is_correct=choice.is_correct,
        question_id=question_id)
    
    db.add(db_choice)
    db.commit()
    return {"message": "Choice created successfully"}

@app.get("/quizes/{quiz_id}/questions/{question_id}")
async def read_choices(quiz_id: int, question_id: int, db: db_dependency):
    result = db.query(models.Choices).filter(models.Choices.question_id == question_id).all()
    if not result:
        raise HTTPException(status_code=404, detail='Choices not found')
    return result
