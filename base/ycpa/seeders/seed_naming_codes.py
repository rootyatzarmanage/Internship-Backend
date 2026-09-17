# scripts/seed_naming_codes.py
NAMING_CODES = {
    "functional_breakdown": [("AR","Architectural"), ("EE","Electrical System"), ("FB","Fabrication System"), ("FP","Fire System"), ("IT","Network Systems"), ("ME","Mechanical System"), ("PL","Plumbing System")],
    "spatial_breakdown": [("00","Base / Ground Floor Level"), ("01","First Floor Level"), ("B1","Basement Level 1"), ("ZZ","All Levels / Locations")],
    "form": [("M3","Model-three-dimensional"), ("CM","Combined model"), ("DR","Drawing Rendition"), ("SH","Schedule")],
    "discipline": [("S","Structural Engineering"), ("A","Architecture"), ("E","Electrical Engineering"), ("M","Mechanical Engineer"), ("P","Public Health Engineering")],
    "status_code": [("S0","Initial status"), ("S1","Suitable for coordination"), ("S2","Suitable for information"), ("S3","Suitable for review and comment")],
    "revision": [("P01","Preliminary revision and version"), ("C01","Contractual revision"), ("XX","None Applicable")],
}

async def seed(session, owner_id: UUID, created_by: UUID):
    for category, items in NAMING_CODES.items():
        for order, (code, label) in enumerate(items):
            session.add(CdeNamingCode(
                owner_id=owner_id, category=category, code=code,
                label=label, order=order, created_by=created_by,
            ))
    await session.commit()