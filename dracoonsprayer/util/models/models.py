from pydantic import BaseModel
from typing import List
from datetime import datetime


# models based on response model of /GET branding/api/v1/public/branding

class BrandingColorDetail(BaseModel):
    type: str
    rgba: str

class BrandingColor(BaseModel):
    type: str
    colorDetails: List[BrandingColorDetail]

class BrandingFile(BaseModel):
    size: str
    url: str

class BrandingImage(BaseModel):
    type: str
    files: List[BrandingFile]

class BrandingLanguageText(BaseModel):
    languageTag: str
    content: str

class BrandingText(BaseModel):
    type: str
    languages: List[BrandingLanguageText]

# Branding as returned by API
class Branding(BaseModel):
    createdAt: datetime
    changedAt: datetime
    productName: str
    colors: List[BrandingColor]
    colorizeHeader: bool
    images: List[BrandingImage]
    texts: List[BrandingText]
    imprintUrl: str
    privacyUrl: str
    supportUrl: str
    emailContact: str
    emailSender: str
    positionLoginBox: int
    appearanceLoginBox: str

# Generic uploaded image response 

class BrandingImageUpload(BaseModel):
    type: str
    id: int
    
# Payload to update branding
class BrandingUpload(BaseModel):
    appearanceLoginBox: str
    colorizeHeader: bool
    colors: List[BrandingColor]
    emailContact: str
    emailSender: str
    images: List[BrandingImageUpload]
    imprintUrl: str
    positionLoginBox: int
    privacyUrl: str
    productName: str
    supportUrl: str
    texts: List[BrandingText]


class ImageResponse(BaseModel):
    id: int
    createdAt: datetime

    



