from fastapi import FastAPI,Body,Request, File, UploadFile, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import aiofiles
from dotenv import load_dotenv
import hashlib
import re

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# MongoDB connection
MONGO_DETAILS = "mongodb+srv://Gritfordcenter:2wambLSatzA5ukVe@gritford.7r15mug.mongodb.net/"
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.dstep_album
collection = database.get_collection("user")

# Pydantic model for user data
class User(BaseModel):
    profilePicture: Optional[str]
    ninImage: Optional[str]
    fingerprintPicture: Optional[str]
    nin: str
    firstName: str
    middleName: Optional[str]
    lastName: str
    dstepRegNo: Optional[str]
    admittedCourse: Optional[str]
    personalEmail: EmailStr
    officialEmail: Optional[EmailStr]
    gender: str
    phoneNumber: str
    whatsappNo: Optional[int]
    dateOfBirth: Optional[str]
    age: Optional[int]
    physicalChallenge: Optional[str]
    employmentStatus: Optional[str]
    stateOfResidence: Optional[str]
    stateOfOrigin: Optional[str]
    highestQualification: Optional[str]
    lastInstitutionAttended: Optional[str]
    tertiaryCourseOfStudy: Optional[str]
    occupation: Optional[str]

    # Validators
    @field_validator("profilePicture")
    def profile_picture_must_be_image(cls, v):
        if v and not v.endswith((".jpg", ".jpeg", ".png")):
            raise ValueError("Profile picture must be an image")
        return v

    @field_validator("gender")
    def gender_must_be_valid(cls, v):
        allowed_genders = ["male", "female"]
        if v.lower() not in allowed_genders:
            raise ValueError("Invalid gender")
        return v

    @field_validator("ninImage")
    def nin_image_must_be_image(cls, v):
        if v and not v.endswith((".jpg", ".jpeg", ".png")):
            raise ValueError("NIN image must be an image")
        return v

    @field_validator("fingerprintPicture")
    def fingerprint_picture_must_be_image(cls, v):
        if v and not v.endswith((".jpg", ".jpeg", ".png")):
            raise ValueError("Fingerprint picture must be an image")
        return v

# encrypt phone number
# def hash_string(input_string: str) -> str:
#     """ Hash a string using SHA-256 """
#     return hashlib.sha256(input_string.encode()).hexdigest()    

# # Regular expression pattern for valid phone numbers
# PHONE_NUMBER_PATTERN = re.compile(r"^\+?\d+$")

# home page route
@app.get('/')
def index(request:Request):
    return templates.TemplateResponse("index.html", {"request":request})

# create user
@app.post("/users/")
async def create_user(
    profilePicture: UploadFile = File(None),
    ninImage: UploadFile = File(None),
    fingerprintPicture: UploadFile = File(None),
    nin: str = Form(...),
    firstName: str = Form(...),
    middleName: Optional[str] = Form(None),
    lastName: str = Form(...),
    dstepRegNo: Optional[str] = Form(None),
    admittedCourse: Optional[str] = Form(None),
    personalEmail: str = Form(...),
    officialEmail: Optional[str] = Form(None),
    gender: str = Form(...),
    phoneNumber: str = Form(...),
    whatsappNo: Optional[int] = Form(None),
    dateOfBirth: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    physicalChallenge: Optional[str] = Form(None),
    employmentStatus: Optional[str] = Form(None),
    stateOfResidence: Optional[str] = Form(None),
    stateOfOrigin: Optional[str] = Form(None),
    highestQualification: Optional[str] = Form(None),
    lastInstitutionAttended: Optional[str] = Form(None),
    tertiaryCourseOfStudy: Optional[str] = Form(None),
    occupation: Optional[str] = Form(None),
):
    # Validate 'nin' length
    if not (nin.isdigit() and 11 <= len(nin) <= 11):
        raise HTTPException(status_code=400, detail="NIN must be between 11 digits")

    # Validate phoneNumber
    # if not PHONE_NUMBER_PATTERN.match(phoneNumber):
    #     raise HTTPException(status_code=400, detail="Phone number must contain only digits and an optional leading '+' sign")

    # Validate phoneNumber length
    if not (phoneNumber.isdigit() and 11 <= len(phoneNumber) <= 15):
        raise HTTPException(status_code=400, detail="Phone number must be between 11 and 15 digits")

    # Hash phoneNumber
    # hashed_phone_number = hash_string(phoneNumber)

    # Check if email is unique
    existing_user = await collection.find_one({"personalEmail": personalEmail})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Save files to disk
    if profilePicture:
        async with aiofiles.open(f"uploads/{profilePicture.filename}", mode="wb") as f:
            await f.write(profilePicture.file.read())
    if ninImage:
        async with aiofiles.open(f"uploads/{ninImage.filename}", mode="wb") as f:
            await f.write(ninImage.file.read())
    if fingerprintPicture:
        async with aiofiles.open(f"uploads/{fingerprintPicture.filename}", mode="wb") as f:
            await f.write(fingerprintPicture.file.read())

    user_data = User(
        profilePicture=profilePicture.filename if profilePicture else None,
        ninImage=ninImage.filename if ninImage else None,
        fingerprintPicture=fingerprintPicture.filename if fingerprintPicture else None,
        nin=nin,
        firstName=firstName,
        middleName=middleName,
        lastName=lastName,
        dstepRegNo=dstepRegNo,
        admittedCourse=admittedCourse,
        personalEmail=personalEmail,
        officialEmail=officialEmail,
        gender=gender,
        phoneNumber=phoneNumber,
        whatsappNo=whatsappNo,
        dateOfBirth=dateOfBirth,
        age=age,
        physicalChallenge=physicalChallenge,
        employmentStatus=employmentStatus,
        stateOfResidence=stateOfResidence,
        stateOfOrigin=stateOfOrigin,
        highestQualification=highestQualification,
        lastInstitutionAttended=lastInstitutionAttended,
        tertiaryCourseOfStudy=tertiaryCourseOfStudy,
        occupation=occupation,
    )

    # Save user data to MongoDB
    try:
        result = await collection.insert_one(jsonable_encoder(user_data))
        return JSONResponse(status_code=201, content={"message": "User created successfully"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": str(e)})

@app.get("/validate_number/")
async def validate_number(
    phoneNumber: str = Query(..., description="Phone number to validate"),
    nin: str = Query(..., description="NIN to validate")
):
    if not (phoneNumber.isdigit() and 11 <= len(phoneNumber) <= 15):
        raise HTTPException(status_code=400, detail="Phone number must be between 11 and 15 digits")

    if not (nin.isdigit() and 11 <= len(nin) <= 15):
        raise HTTPException(status_code=400, detail="NIN must be between 11 and 15 digits")

    return {"phoneNumber": phoneNumber, "nin": nin, "valid_length": True}