"""
HSN/SAC seed data — inserts 25 common codes if the table is empty.
"""
from sqlalchemy.orm import Session

from app.models.models import HSNSACMaster

HSN_SEED_DATA = [
    # Manufacturing
    {"code": "7308", "description": "Structures of iron or steel", "type": "HSN", "cgst_rate": 9, "sgst_rate": 9, "igst_rate": 18},
    {"code": "8471", "description": "Computers and peripherals", "type": "HSN", "cgst_rate": 9, "sgst_rate": 9, "igst_rate": 18},
    {"code": "8517", "description": "Telephone sets, smartphones", "type": "HSN", "cgst_rate": 6, "sgst_rate": 6, "igst_rate": 12},
    {"code": "6109", "description": "T-shirts, singlets, other vests", "type": "HSN", "cgst_rate": 6, "sgst_rate": 6, "igst_rate": 12},
    {"code": "6203", "description": "Men's suits, jackets, trousers", "type": "HSN", "cgst_rate": 6, "sgst_rate": 6, "igst_rate": 12},
    {"code": "0901", "description": "Coffee", "type": "HSN", "cgst_rate": 2.5, "sgst_rate": 2.5, "igst_rate": 5},
    {"code": "0902", "description": "Tea", "type": "HSN", "cgst_rate": 2.5, "sgst_rate": 2.5, "igst_rate": 5},
    {"code": "1006", "description": "Rice", "type": "HSN", "cgst_rate": 0, "sgst_rate": 0, "igst_rate": 0},
    {"code": "1001", "description": "Wheat", "type": "HSN", "cgst_rate": 0, "sgst_rate": 0, "igst_rate": 0},
    {"code": "2710", "description": "Petroleum oils", "type": "HSN", "cgst_rate": 0, "sgst_rate": 0, "igst_rate": 0},
    {"code": "3004", "description": "Medicaments", "type": "HSN", "cgst_rate": 6, "sgst_rate": 6, "igst_rate": 12},
    {"code": "3923", "description": "Plastic articles for packing", "type": "HSN", "cgst_rate": 9, "sgst_rate": 9, "igst_rate": 18},
    {"code": "4901", "description": "Printed books", "type": "HSN", "cgst_rate": 0, "sgst_rate": 0, "igst_rate": 0},
    {"code": "7204", "description": "Ferrous waste and scrap", "type": "HSN", "cgst_rate": 9, "sgst_rate": 9, "igst_rate": 18},
    {"code": "8708", "description": "Parts for motor vehicles", "type": "HSN", "cgst_rate": 14, "sgst_rate": 14, "igst_rate": 28},
    # Services (SAC)
    {"code": "9983", "description": "Other professional, technical and business services", "type": "SAC", "cgst_rate": 9, "sgst_rate": 9, "igst_rate": 18},
    {"code": "9984", "description": "Telecommunications services", "type": "SAC", "cgst_rate": 9, "sgst_rate": 9, "igst_rate": 18},
    {"code": "9985", "description": "Support services", "type": "SAC", "cgst_rate": 9, "sgst_rate": 9, "igst_rate": 18},
    {"code": "9986", "description": "Agriculture, forestry and fishing services", "type": "SAC", "cgst_rate": 0, "sgst_rate": 0, "igst_rate": 0},
    {"code": "9987", "description": "Maintenance, repair and installation services", "type": "SAC", "cgst_rate": 9, "sgst_rate": 9, "igst_rate": 18},
    {"code": "9988", "description": "Manufacturing services on physical inputs", "type": "SAC", "cgst_rate": 9, "sgst_rate": 9, "igst_rate": 18},
    {"code": "9993", "description": "Human health and social care services", "type": "SAC", "cgst_rate": 0, "sgst_rate": 0, "igst_rate": 0},
    {"code": "9994", "description": "Sewage and waste collection services", "type": "SAC", "cgst_rate": 9, "sgst_rate": 9, "igst_rate": 18},
    {"code": "9996", "description": "Recreational, cultural and sporting services", "type": "SAC", "cgst_rate": 9, "sgst_rate": 9, "igst_rate": 18},
    {"code": "9997", "description": "Other services", "type": "SAC", "cgst_rate": 9, "sgst_rate": 9, "igst_rate": 18},
]


def seed_hsn_data(db: Session) -> None:
    """Insert HSN/SAC seed data if the table is empty."""
    existing_count = db.query(HSNSACMaster).count()
    if existing_count > 0:
        return

    for entry in HSN_SEED_DATA:
        record = HSNSACMaster(
            code=entry["code"],
            description=entry["description"],
            type=entry["type"],
            cgst_rate=entry["cgst_rate"],
            sgst_rate=entry["sgst_rate"],
            igst_rate=entry["igst_rate"],
            cess_rate=0,
            is_active=True,
        )
        db.add(record)

    db.commit()
