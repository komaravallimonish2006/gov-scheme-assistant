import os
import sys
from pathlib import Path

# Add backend directory to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings, RAW_PDFS_DIR
from app.core.pdf_processor import pdf_processor
from app.core.vector_store import vector_store


def create_sample_policy_pdf_if_empty():
    """
    Creates verified sample government scheme PDFs if raw_pdfs is empty,
    so the assistant can be immediately tested and demonstrated.
    """
    sample_files = list(RAW_PDFS_DIR.glob("*.pdf"))
    if sample_files:
        return

    print("📄 No PDF files found in data/raw_pdfs/. Generating sample government scheme PDFs for testing...")

    # We can write sample policy text using reportlab or pypdf or a clean text-based PDF writer
    try:
        # Generate 2 official sample scheme PDFs
        sample_schemes = [
            {
                "filename": "PM_KISAN_Guidelines.pdf",
                "title": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
                "pages": [
                    (
                        "GOVERNMENT OF INDIA - MINISTRY OF AGRICULTURE AND FARMERS WELFARE\n"
                        "OPERATIONAL GUIDELINES: PRADHAN MANTRI KISAN SAMMAN NIDHI (PM-KISAN)\n\n"
                        "1. OBJECTIVE & SCHEME OVERVIEW\n"
                        "The Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) is a Central Sector Scheme to provide income support "
                        "to all landholding farmer families in the country to supplement their financial needs for procuring "
                        "various inputs related to agriculture and allied activities as well as domestic needs.\n\n"
                        "2. FINANCIAL BENEFITS\n"
                        "Under the Scheme, an income support of Rs. 6,000/- per year is provided to all eligible farmer families "
                        "across the country in three equal installments of Rs. 2,000/- each, every four months. "
                        "The amount is transferred directly into the bank accounts of the beneficiaries through Direct Benefit Transfer (DBT)."
                    ),
                    (
                        "3. ELIGIBILITY CRITERIA\n"
                        "All landholding farmer families, who have cultivable landholding in their names, are eligible to get benefits "
                        "under the scheme.\n\n"
                        "4. EXCLUSION CATEGORIES\n"
                        "The following categories of beneficiaries of higher economic status shall not be eligible:\n"
                        "a) All Institutional Landholders.\n"
                        "b) Former and present holders of constitutional posts.\n"
                        "c) Former and present Ministers, MPs, MLAs, MLCs, Mayors, and Chairpersons of District Panchayats.\n"
                        "d) All serving or retired officers and employees of Central/State Government Ministries and Departments.\n"
                        "e) All Persons who paid Income Tax in last assessment year.\n"
                        "f) Professionals like Doctors, Engineers, Lawyers, Chartered Accountants registered with professional bodies.\n\n"
                        "5. REQUIRED DOCUMENTS\n"
                        "Citizens applying require: 1. Aadhaar Card (mandatory), 2. Proof of citizenship, 3. Land ownership papers (Khatauni/Pattadar passbook), "
                        "4. Bank account details linked with Aadhaar, and 5. Active mobile number."
                    ),
                    (
                        "6. APPLICATION PROCEDURE\n"
                        "Farmers can apply through:\n"
                        "a) Official Portal: www.pmkisan.gov.in via 'New Farmer Registration'.\n"
                        "b) Common Service Centres (CSC) or Village Level MeeSeva / Grama Sachivalayam.\n"
                        "c) State Nodal Agriculture Officers designated by State Governments.\n\n"
                        "7. e-KYC MANDATORY REQUIREMENT\n"
                        "Aadhaar-based OTP verification on PM-KISAN portal or biometric e-KYC at CSC centers is compulsory "
                        "for the release of subsequent installments."
                    )
                ]
            },
            {
                "filename": "Ayushman_Bharat_PMJAY_Guidelines.pdf",
                "title": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)",
                "pages": [
                    (
                        "NATIONAL HEALTH AUTHORITY - GOVERNMENT OF INDIA\n"
                        "AYUSHMAN BHARAT - PRADHAN MANTRI JAN AROGYA YOJANA (AB PM-JAY)\n\n"
                        "1. SCHEME OVERVIEW\n"
                        "Ayushman Bharat PM-JAY is the world's largest health assurance scheme fully financed by the government. "
                        "It aims to provide health cover of Rs. 5 lakhs per family per year for secondary and tertiary care hospitalization.\n\n"
                        "2. BENEFITS & FINANCIAL COVERAGE\n"
                        "A defined benefit cover of Rs. 5,00,000 per family per year on a family floater basis. "
                        "It covers up to 3 days of pre-hospitalization and 15 days post-hospitalization expenses such as diagnostics and medicines. "
                        "There is no restriction on family size, age or gender. All pre-existing conditions are covered from day one."
                    ),
                    (
                        "3. ELIGIBILITY CRITERIA\n"
                        "Beneficiary households are identified from the Socio-Economic Caste Census (SECC 2011) database based on deprivation criteria:\n"
                        "- Rural: Families living in only one room with kucha walls/roof, female-headed households with no adult male member aged 16-59, "
                        "disabled members, SC/ST households, landless households deriving major income from manual casual labor.\n"
                        "- Urban: 11 defined occupational categories (ragpickers, domestic workers, street vendors, construction workers, transport workers, etc.).\n"
                        "- Senior Citizens (70+ years): Comprehensive health coverage expanded for all citizens aged 70 years and above irrespective of income.\n\n"
                        "4. REQUIRED DOCUMENTS & AYUSHMAN CARD\n"
                        "Aadhaar Card or Ration Card is required to verify identity. Once verified, the citizen receives the PVC Ayushman Card free of charge."
                    ),
                    (
                        "5. HOW TO AVAIL TREATMENT\n"
                        "Treatment is completely cashless and paperless at all empaneled public and private hospitals across India.\n"
                        "Citizens can check their eligibility at:\n"
                        "a) Official Portal: beneficiary.nha.gov.in or pmjay.gov.in\n"
                        "b) National Helpline: 14555\n"
                        "c) Ayushman Mitra kiosk at any empaneled hospital."
                    )
                ]
            }
        ]

        # Function to write standard minimal PDF
        for scheme in sample_schemes:
            pdf_path = RAW_PDFS_DIR / scheme["filename"]
            _write_text_pdf(pdf_path, scheme["pages"])
            print(f"  ✓ Created sample PDF: {scheme['filename']}")

    except Exception as e:
        print(f"Error generating sample PDFs: {e}")


def _write_text_pdf(file_path: Path, pages_text: list[str]):
    """Creates a valid, standard PDF file with text pages."""
    # Build standard minimal PDF syntax with Helvetica font
    pdf_objects = []
    page_obj_ids = []

    # Object 1: Catalog
    # Object 2: Outlines
    # Object 3: Pages
    
    # We will build pages
    pages_count = len(pages_text)
    # Font object ID = 4 + pages_count * 2
    font_id = 4 + pages_count * 2

    # Catalog & Outlines
    obj_catalog = "1 0 obj\n<< /Type /Catalog /Pages 3 0 R >>\nendobj\n"
    obj_outlines = "2 0 obj\n<< /Type /Outlines /Count 0 >>\nendobj\n"
    pdf_objects.extend([obj_catalog, obj_outlines])

    # We will populate Pages object after creating page objects
    page_objs = []
    content_objs = []

    for idx, page_content in enumerate(pages_text):
        page_id = 4 + idx * 2
        content_id = page_id + 1
        page_obj_ids.append(page_id)

        # Escape parenthesis and format text lines
        lines = page_content.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").split("\n")
        
        # Build text stream
        stream_parts = ["BT", "/F1 10 Tf", "50 780 Td", "14 TL"]
        for line in lines:
            if not line.strip():
                stream_parts.append("T*")
            else:
                stream_parts.append(f"({line}) Tj T*")
        stream_parts.append("ET")
        stream_str = "\n".join(stream_parts)

        c_obj = f"{content_id} 0 obj\n<< /Length {len(stream_str.encode('latin-1', 'replace'))} >>\nstream\n{stream_str}\nendstream\nendobj\n"
        content_objs.append(c_obj)

        p_obj = (
            f"{page_id} 0 obj\n<< /Type /Page /Parent 3 0 R /MediaBox [0 0 595 842] "
            f"/Contents {content_id} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>\nendobj\n"
        )
        page_objs.append(p_obj)

    # Pages object (ID 3)
    kids_str = " ".join([f"{pid} 0 R" for pid in page_obj_ids])
    obj_pages = f"3 0 obj\n<< /Type /Pages /Kids [{kids_str}] /Count {pages_count} >>\nendobj\n"

    # Font object
    obj_font = f"{font_id} 0 obj\n<< /Type /Font /Subtype /Type1 /Name /F1 /BaseFont /Helvetica >>\nendobj\n"

    all_objs = [obj_catalog, obj_outlines, obj_pages]
    for p, c in zip(page_objs, content_objs):
        all_objs.extend([p, c])
    all_objs.append(obj_font)

    # Build PDF with xref table
    with open(file_path, "wb") as f:
        f.write(b"%PDF-1.4\n")
        offsets = [0]
        cur_offset = 9  # len("%PDF-1.4\n")
        for obj in all_objs:
            offsets.append(cur_offset)
            encoded = obj.encode("latin-1", "replace")
            f.write(encoded)
            cur_offset += len(encoded)

        xref_pos = cur_offset
        f.write(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode("latin-1"))
        for off in offsets[1:]:
            f.write(f"{off:010d} 00000 n \n".encode("latin-1"))

        f.write(
            f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("latin-1")
        )


def ingest_all_pdfs():
    """
    Scans data/raw_pdfs/ and indexes all PDF files into ChromaDB.
    """
    create_sample_policy_pdf_if_empty()

    pdf_files = list(RAW_PDFS_DIR.glob("*.pdf"))
    if not pdf_files:
        print("⚠️  No PDF files to ingest.")
        return

    print(f"🔍 Found {len(pdf_files)} PDF file(s) in {RAW_PDFS_DIR}:")
    total_ingested_chunks = 0

    for pdf_file in pdf_files:
        print(f"\n📂 Processing '{pdf_file.name}'...")
        try:
            chunks = pdf_processor.chunk_document(pdf_file)
            print(f"   Extracted {len(chunks)} chunks across pages.")
            count = vector_store.add_chunks(chunks)
            total_ingested_chunks += count
            print(f"   ✓ Successfully indexed {count} chunks in ChromaDB.")
        except Exception as e:
            print(f"   ✗ Error indexing {pdf_file.name}: {e}")

    print("\n" + "=" * 50)
    print(f"🎉 Ingestion Complete! Total indexed chunks: {total_ingested_chunks}")
    stats = vector_store.get_stats()
    print(f"📊 Vector Store Summary: {stats}")
    print("=" * 50)


if __name__ == "__main__":
    ingest_all_pdfs()
