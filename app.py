# !pip install --upgrade google-api-python-client google-auth gspread streamlit qrcode[pil] -q

import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from datetime import datetime
import qrcode
from io import BytesIO
import base64
import json

# === 🔐 Load Google API credentials securely from Streamlit secrets ===
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/forms.body',
    'https://www.googleapis.com/auth/forms.responses.readonly'
]

service_account_info = json.loads(st.secrets["gcp_service_account"])
credentials = service_account.Credentials.from_service_account_info(
    service_account_info, scopes=SCOPES)

form_service = build('forms', 'v1', credentials=credentials)
drive_service = build('drive', 'v3', credentials=credentials)
gc = gspread.authorize(credentials)

sheet = gc.open("Pre-Post Test").sheet1
DESTINATION_FOLDER_ID = '1moTA94vOTorwpnUpGQZnKz5-5S9jYeBw'

# === 🎨 Styling ===
st.markdown("""
    <style>
    .main {
        background-color: #f4f6f9;
    }
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
        color: #1f2e4d;
    }
    h1, h2, h3 {
        color: #0a1930;
        margin-bottom: 10px;
    }
    .title-container {
        background-color: #001f3f;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
        text-align: center;
        color: white;
    }
    .stTextInput > div > div > input,
    .stNumberInput > div,
    .stSelectbox > div {
        background-color: #ffffff;
        border: 1px solid #dcdde1;
        padding: 10px;
        border-radius: 6px;
    }
    .stButton > button {
        background-color: #1f2e4d;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 12px 20px;
        font-weight: 600;
        display: block;
        margin: 0 auto;
    }
    .stButton > button:hover {
        background-color: #0a1930;
    }
    .centered-title {
        text-align: center;
        font-size: 26px;
        font-weight: 700;
        color: #0a1930;
        margin-top: 40px;
        margin-bottom: 20px;
    }
    a {
        color: #1f77b4 !important;
        font-weight: 500;
    }
    .stAlert {
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# === 🖼️ Logo ===
st.markdown("""
    <div style="background-color: #001f3f; padding: 20px; border-radius: 10px; margin-bottom: 30px; text-align: center;">
        <img src="https://res.cloudinary.com/dcjmaapvi/image/upload/v1740489025/ga-hori_ylcnm3.png" width="300">
    </div>
""", unsafe_allow_html=True)

# === 📘 Title Box ===
st.markdown("""
    <div class='title-container'>
        <h1 style="font-size: 28px; margin-bottom: 10px;">Trainer Assessment Form Creator</h1>
        <p style="font-size: 16px;">Create Pre & Post assessment forms for Aptitude, Technical, and Soft Skills training sessions.</p>
    </div>
""", unsafe_allow_html=True)

# === 👤 Trainer Details ===
st.markdown("<div class='centered-title'>Trainer Information</div>", unsafe_allow_html=True)
trainer_name = st.text_input("Trainer Name")
college_name = st.text_input("College Name")

# === 🧾 Test Configuration ===
st.markdown("<div class='centered-title'>Test Details</div>", unsafe_allow_html=True)
test_title = st.text_input("Test Title")
num_questions = st.number_input("Number of Questions", min_value=1, max_value=50, step=1)

# === ❓ Questions ===
st.markdown("<div class='centered-title'>Questionnaire</div>", unsafe_allow_html=True)
questions = []
for i in range(num_questions):
    st.markdown(f"#### Question {i+1}")
    q = st.text_input("Question", key=f"q{i}")
    opt1 = st.text_input("Option 1", key=f"q{i}opt1")
    opt2 = st.text_input("Option 2", key=f"q{i}opt2")
    opt3 = st.text_input("Option 3", key=f"q{i}opt3")
    opt4 = st.text_input("Option 4", key=f"q{i}opt4")
    ans = st.selectbox("Correct Answer", [opt1, opt2, opt3, opt4], key=f"q{i}ans")
    questions.append({
        "question": q,
        "options": [opt1, opt2, opt3, opt4],
        "answer": ans
    })

# === 🚀 Generate Google Form ===
st.markdown("<br>", unsafe_allow_html=True)
if st.button("Generate Google Form"):
    form_title = f"{test_title} - {college_name}"
    new_form = {
        "info": {
            "title": form_title,
            "documentTitle": form_title
        }
    }
    created_form = form_service.forms().create(body=new_form).execute()
    form_id = created_form["formId"]

    info_questions = [
        {
            "title": "Student Full Name",
            "description": "Enter your full name as per Aadhar.",
            "questionItem": {
                "question": {
                    "required": True,
                    "textQuestion": {}
                }
            }
        },
        {
            "title": "Batch & Specialization",
            "questionItem": {
                "question": {
                    "required": True,
                    "textQuestion": {}
                }
            }
        }
    ]

    requests = []
    for i, item in enumerate(info_questions):
        requests.append({
            "createItem": {
                "item": item,
                "location": {"index": i}
            }
        })

    for q in questions:
        requests.append({
            "createItem": {
                "item": {
                    "title": q["question"],
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [{"value": opt} for opt in q["options"]],
                                "shuffle": False
                            }
                        }
                    }
                },
                "location": {"index": len(requests)}
            }
        })

    form_service.forms().batchUpdate(formId=form_id, body={"requests": requests}).execute()
    form_link = f"https://docs.google.com/forms/d/{form_id}/viewform"

    try:
        drive_service.files().update(
            fileId=form_id,
            addParents=DESTINATION_FOLDER_ID
        ).execute()
        st.info("Form has been moved to your specified Google Drive folder.")
    except Exception as e:
        st.warning(f"Could not move form to the folder: {e}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, trainer_name, college_name, test_title, form_link])

    st.success("✅ Google Form created successfully!")
    st.markdown(f"🔗 [Click here to open your form]({form_link})")

    # === 📱 QR Code Section ===
    st.markdown("<div class='centered-title'>📱 Scan to Open Form</div>", unsafe_allow_html=True)
    qr = qrcode.make(form_link)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()
    qr_html = f"""
    <div style="text-align: center;">
        <img src="data:image/png;base64,{img_b64}" width="250" alt="QR Code" />
        <div style="margin-top: 8px; font-weight: 600; color: #0a1930;">Scan to open the form</div>
    </div>
    """
    st.markdown(qr_html, unsafe_allow_html=True)
