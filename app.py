import os
import io
import zipfile
from datetime import datetime

import cv2
import numpy as np
import pandas as pd
import qrcode
import barcode
import streamlit as st
from PIL import Image
from barcode.writer import ImageWriter

import cloudinary
import cloudinary.uploader

# =========================
# APP SETUP
# =========================
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

st.set_page_config(
    page_title="Elegant QR Link Generator",
    page_icon="👑",
    layout="wide"
)

if "history" not in st.session_state:
    st.session_state.history = []

# =========================
# CLOUDINARY CONFIG
# =========================
# Replace these with your own values
CLOUD_NAME = "dewhqilca"
API_KEY = "616245617475274"
API_SECRET = "TgvjxQk_3zrCL6v3G-yszCzQ6lw"

cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET,
    secure=True
)

# =========================
# HELPER FUNCTIONS
# =========================
def add_history(input_value, code_type, output_file, notes=""):
    st.session_state.history.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input": input_value,
        "type": code_type,
        "output_file": output_file,
        "notes": notes
    })


def file_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in str(name)).strip("_")


def detect_type(value):
    value = str(value).strip()
    if not value:
        return "invalid"
    if value.startswith("http://") or value.startswith("https://"):
        return "qr"
    if value.isdigit() and len(value) >= 8:
        return "barcode"
    return "qr"


def generate_qr(data, filename, box_size=10, border=4, fill_color="black", back_color="white"):
    qr = qrcode.QRCode(
        version=1,
        box_size=box_size,
        border=border
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    path = os.path.join(OUTPUT_DIR, f"{sanitize_filename(filename)}.png")
    img.save(path)
    return path


def generate_barcode(data, filename, barcode_format="code128"):
    barcode_format = barcode_format.lower()

    if barcode_format == "ean13":
        if not data.isdigit() or len(data) != 12:
            raise ValueError("EAN13 needs exactly 12 digits")
    elif barcode_format == "ean8":
        if not data.isdigit() or len(data) != 7:
            raise ValueError("EAN8 needs exactly 7 digits")
    elif barcode_format == "upca":
        if not data.isdigit() or len(data) != 11:
            raise ValueError("UPCA needs exactly 11 digits")
    elif barcode_format == "code128":
        pass
    else:
        raise ValueError("Unsupported barcode format")

    barcode_class = barcode.get_barcode_class(barcode_format)
    code = barcode_class(data, writer=ImageWriter())
    full_path_no_ext = os.path.join(OUTPUT_DIR, sanitize_filename(filename))
    saved_path = code.save(full_path_no_ext)
    return saved_path


def create_zip_from_files(file_paths):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in file_paths:
            if os.path.exists(file_path):
                zip_file.write(file_path, arcname=os.path.basename(file_path))
    zip_buffer.seek(0)
    return zip_buffer


def decode_qr_from_uploaded_image(uploaded_file):
    file_bytes_data = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes_data, cv2.IMREAD_COLOR)

    detector = cv2.QRCodeDetector()
    decoded_text, points, _ = detector.detectAndDecode(image)

    return decoded_text, image


def looks_like_image_url(text):
    text = str(text).strip().lower()
    image_extensions = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
    return text.startswith(("http://", "https://")) and any(ext in text for ext in image_extensions)


def upload_image_to_cloudinary(uploaded_file):
    uploaded_file.seek(0)
    result = cloudinary.uploader.upload(uploaded_file)
    return result["secure_url"]

# =========================
# STYLING
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(212,175,55,0.18), transparent 25%),
        radial-gradient(circle at top right, rgba(106,27,154,0.18), transparent 25%),
        linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    color: #f5f1e8;
}

.main-title {
    text-align: center;
    font-family: 'Cinzel', serif;
    font-size: 44px;
    font-weight: 700;
    color: #f4d06f;
    margin-top: 10px;
    margin-bottom: 6px;
    letter-spacing: 1px;
}

.sub-title {
    text-align: center;
    font-size: 18px;
    color: #f3e9d2;
    margin-bottom: 22px;
}

.box {
    background: rgba(255,255,255,0.10);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    padding: 22px;
    border-radius: 20px;
    border: 1px solid rgba(244,208,111,0.25);
    box-shadow: 0 10px 30px rgba(0,0,0,0.25);
    margin-bottom: 20px;
}

.small-text, .stCaption, label, p, li, div, h1, h2, h3 {
    color: #f7f2e8 !important;
}

.stButton > button {
    background: linear-gradient(135deg, #d4af37, #f4d06f);
    color: #1c1630;
    border: none;
    border-radius: 12px;
    font-weight: 700;
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #6a1b9a, #8e44ad);
    color: white;
    border: none;
    border-radius: 12px;
    font-weight: 700;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1633, #241b4d);
    color: #f5f1e8;
}

.stTextInput input, .stTextArea textarea {
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">👑 Elegant QR Image Link Generator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Upload image → create public link → convert link into QR code</div>',
    unsafe_allow_html=True
)

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.title("🧭 Navigation")
    page = st.radio(
        "Open Page",
        [
            "🏠 Home",
            "🖼️ Upload Image to Link",
            "🔳 Manual QR / Barcode",
            "📂 Batch CSV Upload",
            "👤 Contact QR",
            "🎫 Ticket QR",
            "📍 Location QR",
            "🔍 QR Decoder",
            "📜 History",
            "ℹ️ About"
        ]
    )

    st.markdown("---")
    st.subheader("🎨 QR Settings")
    qr_box_size = st.slider("Enter QR Size", 4, 20, 10)
    qr_border = st.slider("Enter QR Border", 1, 10, 4)
    qr_fill = st.color_picker("Enter QR Color", "#000000")
    qr_back = st.color_picker("Enter Background Color", "#FFFFFF")

    st.markdown("---")
    st.subheader("🏷️ Barcode Settings")
    barcode_format = st.selectbox("Select Barcode Type", ["code128", "ean13", "ean8", "upca"])

# =========================
# PAGES
# =========================
if page == "🏠 Home":
    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.subheader("Welcome")
    st.write("This app helps you upload an image, turn it into a public link, and create a QR code from that link.")
    st.info(
        "Easy steps:\n"
        "1. Open Upload Image to Link\n"
        "2. Upload your image\n"
        "3. Get public image link\n"
        "4. Generate QR code\n"
        "5. Scan QR and open image"
    )
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "🖼️ Upload Image to Link":
    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.subheader("Upload Image to Link")
    st.write("Upload your image here. The app will create a public image link, then make a QR code from that link.")

    image_name = st.text_input("Enter Image Name", placeholder="Example: Product Photo")
    uploaded_image = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg", "webp"])

    if uploaded_image is not None:
        preview = Image.open(uploaded_image)
        st.image(preview, caption="Uploaded Image Preview", width=320)

        if st.button("🌐 Upload Image and Create Link"):
            try:
                with st.spinner("Uploading image and creating public link..."):
                    public_url = upload_image_to_cloudinary(uploaded_image)

                    qr_file = generate_qr(
                        public_url,
                        image_name or "image_link_qr",
                        box_size=qr_box_size,
                        border=qr_border,
                        fill_color=qr_fill,
                        back_color=qr_back
                    )

                    st.success("Image uploaded successfully.")
                    st.text_input("Public Image Link", value=public_url)
                    st.markdown(f"[Open Image Link]({public_url})")

                    st.markdown("### QR Code")
                    st.image(qr_file, caption="QR Code for Image Link", width=260)

                    st.download_button(
                        "Download QR Code",
                        data=file_bytes(qr_file),
                        file_name="image_link_qr.png",
                        mime="image/png"
                    )

                    add_history(public_url, "Image Link QR", qr_file, notes=image_name)

                    st.info("Now if anyone scans this QR code, they can open the image link.")
            except Exception as e:
                st.error(f"Upload failed: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

elif page == "🔳 Manual QR / Barcode":
    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.subheader("Manual QR / Barcode")
    user_input = st.text_input("Enter Website, Text, or Number")

    if st.button("Generate Code"):
        with st.spinner("Generating code..."):
            code_type = detect_type(user_input)

            if code_type == "invalid":
                st.error("Please enter a value.")
            elif code_type == "qr":
                path = generate_qr(
                    user_input,
                    "generated_qr",
                    box_size=qr_box_size,
                    border=qr_border,
                    fill_color=qr_fill,
                    back_color=qr_back
                )
                st.success("QR code generated successfully.")
                st.image(path, caption="Generated QR Code", width=280)
                st.download_button("Download QR Code", data=file_bytes(path), file_name="generated_qr.png", mime="image/png")
                add_history(user_input, "QR", path)
            elif code_type == "barcode":
                try:
                    path = generate_barcode(user_input, "generated_barcode", barcode_format=barcode_format)
                    st.success("Barcode generated successfully.")
                    st.image(path, caption="Generated Barcode", width=420)
                    st.download_button("Download Barcode", data=file_bytes(path), file_name=os.path.basename(path), mime="image/png")
                    add_history(user_input, f"Barcode ({barcode_format})", path)
                except Exception as e:
                    st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "📂 Batch CSV Upload":
    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.subheader("Batch CSV Upload")
    st.write("Upload CSV with columns: name, value")
    csv_file = st.file_uploader("Upload CSV File", type=["csv"])

    if csv_file is not None:
        df = pd.read_csv(csv_file)
        st.dataframe(df)

        if st.button("Generate Batch Codes"):
            generated_files = []
            results = []

            with st.spinner("Processing CSV..."):
                for idx, row in df.iterrows():
                    name = str(row.get("name", f"item_{idx+1}"))
                    value = str(row.get("value", "")).strip()
                    safe_name = sanitize_filename(name)

                    try:
                        code_type = detect_type(value)
                        if code_type == "invalid":
                            raise ValueError("Empty value")

                        if code_type == "qr":
                            path = generate_qr(value, safe_name, qr_box_size, qr_border, qr_fill, qr_back)
                        else:
                            path = generate_barcode(value, safe_name, barcode_format=barcode_format)

                        generated_files.append(path)
                        results.append({"name": name, "value": value, "type": code_type, "status": "success", "file": path})
                        add_history(value, f"Batch {code_type.upper()}", path, notes=name)

                    except Exception as e:
                        results.append({"name": name, "value": value, "type": "unknown", "status": "failed", "file": "", "error": str(e)})

            results_df = pd.DataFrame(results)
            results_csv_path = os.path.join(OUTPUT_DIR, "batch_results.csv")
            results_df.to_csv(results_csv_path, index=False)
            generated_files.append(results_csv_path)

            st.success("Batch generation completed.")
            st.dataframe(results_df)

            zip_data = create_zip_from_files(generated_files)
            st.download_button(
                label="Download All as ZIP",
                data=zip_data,
                file_name="batch_outputs.zip",
                mime="application/zip"
            )
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "👤 Contact QR":
    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.subheader("Contact QR")

    name = st.text_input("Enter Name")
    phone = st.text_input("Enter Phone")
    email = st.text_input("Enter Email")
    company = st.text_input("Enter Company")

    if st.button("Generate Contact QR"):
        vcard = (
            "BEGIN:VCARD\n"
            "VERSION:3.0\n"
            f"FN:{name}\n"
            f"TEL:{phone}\n"
            f"EMAIL:{email}\n"
            f"ORG:{company}\n"
            "END:VCARD"
        )
        path = generate_qr(vcard, "contact_qr", qr_box_size, qr_border, qr_fill, qr_back)
        st.success("Contact QR generated.")
        st.image(path, width=280)
        st.download_button("Download Contact QR", data=file_bytes(path), file_name="contact_qr.png", mime="image/png")
        add_history(name, "Contact QR", path)
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "🎫 Ticket QR":
    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.subheader("Ticket QR")

    event_name = st.text_input("Enter Event Name")
    attendee_name = st.text_input("Enter Attendee Name")
    ticket_id = st.text_input("Enter Ticket ID")

    if st.button("Generate Ticket QR"):
        ticket_data = (
            f"Event: {event_name}\n"
            f"Attendee: {attendee_name}\n"
            f"Ticket ID: {ticket_id}\n"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        path = generate_qr(ticket_data, "ticket_qr", qr_box_size, qr_border, qr_fill, qr_back)
        st.success("Ticket QR generated.")
        st.image(path, width=280)
        st.download_button("Download Ticket QR", data=file_bytes(path), file_name="ticket_qr.png", mime="image/png")
        add_history(ticket_id, "Ticket QR", path)
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "📍 Location QR":
    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.subheader("Location QR")

    location_name = st.text_input("Enter Location Name")
    latitude = st.text_input("Enter Latitude")
    longitude = st.text_input("Enter Longitude")
    google_maps_link = st.text_input("Enter Google Maps Link")

    if st.button("Generate Location QR"):
        if google_maps_link.strip():
            location_data = google_maps_link.strip()
        elif latitude.strip() and longitude.strip():
            location_data = f"https://www.google.com/maps?q={latitude.strip()},{longitude.strip()}"
        else:
            st.error("Please enter Google Maps link or latitude and longitude.")
            st.stop()

        path = generate_qr(location_data, "location_qr", qr_box_size, qr_border, qr_fill, qr_back)
        st.success("Location QR generated.")
        st.write(f"Stored Link: {location_data}")
        st.image(path, width=280)
        st.download_button("Download Location QR", data=file_bytes(path), file_name="location_qr.png", mime="image/png")
        add_history(location_name or location_data, "Location QR", path)
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "🔍 QR Decoder":
    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.subheader("QR Decoder")

    qr_upload = st.file_uploader("Upload QR Code Image", type=["png", "jpg", "jpeg"], key="qr_decoder_upload")
    camera_qr = st.camera_input("Or Take Photo of QR Code")

    qr_source = qr_upload if qr_upload is not None else camera_qr

    if qr_source is not None:
        st.info("Image ready to decode.")

        if st.button("Decode QR"):
            with st.spinner("Reading QR code..."):
                decoded_text, _ = decode_qr_from_uploaded_image(qr_source)

                if decoded_text:
                    st.success("QR decoded successfully.")
                    st.text_area("Decoded Result", decoded_text, height=140)
                    add_history(decoded_text, "QR Decoded", "N/A")

                    if looks_like_image_url(decoded_text):
                        st.markdown("### Image Preview")
                        st.image(decoded_text, caption="Image from decoded link")
                    elif decoded_text.startswith("http://") or decoded_text.startswith("https://"):
                        st.markdown("### Open Link")
                        st.markdown(f"[Click Here to Open]({decoded_text})")
                    else:
                        st.markdown("### Text Result")
                        st.write(decoded_text)
                else:
                    st.error("No readable QR code found.")
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "📜 History":
    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.subheader("History")

    if st.session_state.history:
        history_df = pd.DataFrame(st.session_state.history)
        search_term = st.text_input("Enter Search Word")
        if search_term.strip():
            mask = history_df.astype(str).apply(lambda col: col.str.contains(search_term, case=False, na=False))
            history_df = history_df[mask.any(axis=1)]
        st.dataframe(history_df)
    else:
        st.info("No history yet.")
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "ℹ️ About":
    st.markdown('<div class="box">', unsafe_allow_html=True)
    st.subheader("About")
    st.write("""
This app is made for:

- Upload image to public link
- Convert link to QR code
- Generate manual QR and barcode
- Create contact QR
- Create ticket QR
- Create location QR
- Decode QR
- Save history
""")
    st.warning("Important: add your Cloudinary cloud name, API key, and API secret before using Upload Image to Link.")
    st.markdown('</div>', unsafe_allow_html=True)
