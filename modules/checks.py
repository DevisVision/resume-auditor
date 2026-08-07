from __future__ import annotations
import io
import re
import fitz

from pypdf import PdfReader
from PIL import Image as PILImage

# Computer Vision components for deep profile photo analysis
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

REQUIRED_CERTS = [
    "DP-900", "DP900", "DP-700", "DP700",
    "Databricks Associate", "Databricks Fundamentals",
    "Databricks GenAI", "Databricks Generative AI",
]
KEY_SKILLS = ["Azure", "ADF", "SQL", "Python", "PySpark", "Databricks"]

# Added GitHub verification rules to standard mapping filters
CONTACT_PATTERNS = {
    "email":    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "phone":    r"(\+?\d[\d\s\-().]{7,}\d)",
    "linkedin": r"linkedin\.com/in/[A-Za-z0-9\-_/]+",
    "github":   r"github\.com/[A-Za-z0-9\-_]+",
}


def get_page_count(file_name: str, file_bytes: bytes) -> int:
    """Return PDF page count, or 0 for non-PDF."""
    if not file_name.lower().endswith(".pdf"):
        return 0
    try:
        return len(PdfReader(io.BytesIO(file_bytes)).pages)
    except Exception:
        return 0


def _is_actual_face(pil_img: PILImage) -> bool:
    """
    Applies Computer Vision (Haar Cascades) to detect actual human faces and eyes.
    Instantly filters out badges, logos, abstracts, and shapes.
    """
    if not OPENCV_AVAILABLE:
        if pil_img.mode in ("P", "1", "L"):
            return False
        unique_colors = pil_img.convert("RGB").getcolors(maxcolors=4000)
        return unique_colors is None

    try:
        img_rgb = pil_img.convert("RGB")
        img_np = np.array(img_rgb)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        face_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        eye_path = cv2.data.haarcascades + "haarcascade_eye.xml"
        
        face_cascade = cv2.CascadeClassifier(face_path)
        eye_cascade = cv2.CascadeClassifier(eye_path)

        if face_cascade.empty() or eye_cascade.empty():
            unique_colors = pil_img.convert("RGB").getcolors(maxcolors=4000)
            return unique_colors is None

        # Detect clear facial landscapes
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=4, minSize=(40, 40))

        # Confirm eye features match parameters inside the face target box
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.05, minNeighbors=2)
            if len(eyes) >= 1:
                return True
                
        return False
    except Exception:
        return False


def has_profile_photo(file_name: str, file_bytes: bytes) -> bool:
    """
    Detect whether the first page of a PDF/DOCX contains a profile photo.
    """

    name = file_name.lower().strip()

    # ---------------- PDF ----------------
    if name.endswith(".pdf"):
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")

            if len(doc) == 0:
                return False

            page = doc.load_page(0)

            image_list = page.get_images(full=True)

            for image in image_list:
                try:
                    xref = image[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]

                    with PILImage.open(io.BytesIO(image_bytes)) as img:

                        width, height = img.size
                        aspect_ratio = width / max(height, 1)

                        # Ignore tiny icons/logos
                        if width < 80 or height < 80:
                            continue

                        # Accept common resume photo shapes
                        if not (0.20 <= aspect_ratio <= 2.20):
                            continue

                        # Try actual face detection first
                        if _is_actual_face(img):
                            return True

                        # Fallback for compressed resume photos
                        if width >= 150 and height >= 150:
                            return True

                except Exception:
                    continue

        except Exception:
            return False

    # ---------------- DOCX ----------------
    elif name.endswith(".docx"):
        try:
            import zipfile

            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:

                media_files = [
                    n for n in z.namelist()
                    if n.startswith("word/media/")
                ]

                for media_file in media_files:
                    with z.open(media_file) as img_file:
                        with PILImage.open(img_file) as img:

                            width, height = img.size
                            aspect_ratio = width / max(height, 1)

                            # Ignore tiny icons/logos
                            if width < 80 or height < 80:
                                continue

                            # Accept common resume photo shapes
                            if not (0.20 <= aspect_ratio <= 2.20):
                                continue

                            # Try OpenCV face detection
                            if _is_actual_face(img):
                                return True

                            # Fallback
                            if width >= 150 and height >= 150:
                                return True

        except Exception:
            return False

    return False

def check_filename(file_name: str) -> bool:
    """Expected: 'RESUME AZURE DATA ENGINEER_<NAME>.pdf' (case-insensitive)."""
    base = file_name.rsplit(".", 1)[0].upper().strip()
    return bool(re.match(r"^RESUME[\s_]+AZURE[\s_]+DATA[\s_]+ENGINEER[_\s].+", base))


def check_pdf_format(file_name: str) -> bool:
    return file_name.lower().endswith(".pdf")


def page_count_ok(pages: int, years_experience: float) -> tuple[bool, str]:
    """Org policy: 1pg (0-5y), 2pg (5-10y), 3pg (10+y)."""
    if pages == 0:
        return False, "Not a PDF (page count unknown)"
    if years_experience < 5 and pages == 1:
        return True, "1 page · matches 0-5 yr policy"
    if 5 <= years_experience < 10 and pages == 2:
        return True, "2 pages · matches 5-10 yr policy"
    if years_experience >= 10 and pages == 3:
        return True, "3 pages · matches 10+ yr policy"
    expected = "1" if years_experience < 5 else "2" if years_experience < 10 else "3"
    return False, f"{pages} page(s) · expected {expected} for {years_experience:.0f} yrs exp"


def contact_completeness(text: str) -> dict:
    return {
        "email":    bool(re.search(CONTACT_PATTERNS["email"], text)),
        "phone":    bool(re.search(CONTACT_PATTERNS["phone"], text)),
        "linkedin": bool(re.search(CONTACT_PATTERNS["linkedin"], text, re.I)),
        "github":   bool(re.search(CONTACT_PATTERNS["github"], text, re.I)),
    }


def keywords_found(text: str) -> list:
    t = text.lower()
    return [k for k in KEY_SKILLS if k.lower() in t]


def certifications_found(text: str) -> dict:
    """
    Detect mandatory certifications.

    Required:
    - DP-900
    - DP-700
    - Databricks Associate
    """

    t = text.lower()

    found = {
        "DP-900": False,
        "DP-700": False,
        "Databricks Associate": False,
    }

    # ---------------- DP-900 ----------------
    if (
        "dp-900" in t
        or "dp900" in t
        or "azure data fundamentals" in t
    ):
        found["DP-900"] = True

    # ---------------- DP-700 ----------------
    if (
        "dp-700" in t
        or "dp700" in t
        or "fabric data engineer" in t
    ):
        found["DP-700"] = True

    # ---------------- Databricks Associate ----------------
    if (
        "databricks associate" in t
        or "databricks certified associate" in t
        or "associate developer for apache spark" in t
        or "data engineer associate" in t
    ):
        found["Databricks Associate"] = True

    return found
def ade_project_has_minimum_rr(text: str) -> tuple[bool, int]:
    """
    Check whether the Azure Data Engineer project/work experience
    contains at least 10 responsibility bullet points.
    """

    import re

    lines = text.splitlines()

    bullet_count = 0
    inside_project = False

    ade_keywords = [
        "azure data engineer",
        "data engineer",
        "project",
        "roles and responsibilities",
        "responsibilities",
        "experience",
    ]

    for line in lines:

        l = line.strip().lower()

        if any(k in l for k in ade_keywords):
            inside_project = True
            continue

        if inside_project:

            if re.match(r"^[-•*]", l):
                bullet_count += 1

            elif re.match(r"^\d+\.", l):
                bullet_count += 1

            # Stop after a long blank section
            elif l == "" and bullet_count > 0:
                break

    return bullet_count >= 10, bullet_count
#----------------------------------CGPA CHECK ----------------------------------
def highest_education_has_cgpa(text: str) -> tuple[bool, str]:
    """
    Check whether the highest education section contains CGPA.
    """

    import re

    lines = text.splitlines()

    education_keywords = [
        "education",
        "academic",
        "qualification",
        "b.tech",
        "b.e",
        "bachelor",
        "m.tech",
        "m.e",
        "master",
        "degree",
        "university",
        "college",
    ]

    cgpa_pattern = re.compile(
        r"(cgpa|gpa)\s*[:\-]?\s*\d+(\.\d+)?",
        re.IGNORECASE,
    )

    inside_education = False

    for line in lines:

        l = line.strip()

        if any(k in l.lower() for k in education_keywords):
            inside_education = True

        if inside_education:

            #if cgpa_pattern.search(l):
            #    return True, l.strip()
            if cgpa_pattern.search(l):
                match = cgpa_pattern.search(l)
                return True, f"CGPA detected: {match.group(0)}"
    return False, "CGPA not mentioned"

def build_format_checklist(file_name: str, file_bytes: bytes, text: str, years_exp: float) -> dict:
    """Returns a dict with score (0-100) and a list of pass/fail items."""
    photo = has_profile_photo(file_name, file_bytes)
    fname_ok = check_filename(file_name)
    pdf_ok = check_pdf_format(file_name)
    pages = get_page_count(file_name, file_bytes)
    pages_ok, pages_note = page_count_ok(pages, years_exp)
    contact = contact_completeness(text)
    kw = keywords_found(text)
    certs = certifications_found(text)
    cert_count = sum(certs.values())
    ade_rr_ok, ade_rr_count = ade_project_has_minimum_rr(text)
    cgpa_ok, cgpa_note = highest_education_has_cgpa(text)
    missing = [
        cert
        for cert, present in certs.items()
        if not present
    ]

    # Added GitHub to compliance engine layout matrix tracking 
    items = [
        {"item": "Profile photo embedded",     "passed": photo,                  "note": ""},
        {"item": "Email present",              "passed": contact["email"],       "note": ""},
        {"item": "Phone present",              "passed": contact["phone"],       "note": ""},
        {"item": "LinkedIn profile link",      "passed": contact["linkedin"],    "note": ""},
        {"item": "GitHub portfolio link",      "passed": contact["github"],      "note": ""},
        {"item": "PDF format",                 "passed": pdf_ok,                 "note": "" if pdf_ok else "Convert to PDF"},
        {"item": "Filename format",            "passed": fname_ok,
         "note": "Expected: RESUME AZURE DATA ENGINEER_<NAME>.pdf"},
        {"item": "Page count matches policy",  "passed": pages_ok,               "note": pages_note},
        {"item": "Key skills present (Azure/ADF/SQL/Python/PySpark/Databricks)",
         "passed": len(kw) >= 4, "note": f"Found {len(kw)}/6: {', '.join(kw) or '—'}"},
        {"item": "ADE Project has minimum 10 Roles & Responsibilities","passed": ade_rr_ok,
            "note": f"Found {ade_rr_count} responsibility points (Minimum required: 10)"},
        {"item": "Highest Qualification includes CGPA","passed": cgpa_ok,"note": cgpa_note,},
        {"item": "Mandatory Certifications (DP-900, DP-700, Databricks Associate)",
          "passed": cert_count == 3,"note": ("All mandatory certifications found."
            if cert_count == 3
                else f"Missing: {', '.join(missing)}"),},
            ]
    passed = sum(1 for it in items if it["passed"])
    score = round(100 * passed / len(items))
    return {"score": score, "passed": passed, "total": len(items), "items": items, "page_count": pages}