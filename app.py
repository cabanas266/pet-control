import sqlite3
import streamlit as st
from PIL import Image
import io

st.set_page_config(page_title="Gestão e Diário do Pet", page_icon="🐾", layout="centered")

# Conexão com o banco e criação limpa das tabelas
def init_db():
    conn = sqlite3.connect("pet_control.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            breed TEXT,
            birth_date TEXT,
            gender TEXT,
            photo BLOB
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect("pet_control.db")

def resize_image(image_file):
    """Comprime e redimensiona a foto para um tamanho leve ideal para nuvem"""
    try:
        img = Image.open(image_file)
        img.thumbnail((500, 500))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        byte_arr = io.BytesIO()
        img.save(byte_arr, format="JPEG", quality=80)
        return byte_arr.getvalue()
    except Exception:
        return None

# Funções básicas
def get_pets():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, breed, birth_date, photo FROM pets")
        pets = cursor.fetchall()
        conn.close()
        return pets
    except Exception:
        return []

st.title("🐾 Controle do Pet")

pets = get_pets()
pet_dict = {p[1]: p for p in pets}
selected_name = st.selectbox("Selecione o Pet", ["Nenhum / Novo Pet..."] + list(pet_dict.keys()))

if selected_name == "Nenhum / Novo Pet...":
    st.subheader("Cadastrar Novo Pet")
    with st.form("cadastro_pet"):
        nome = st.text_input("Nome do Pet")
        raca = st.text_input("Raça")
        nasc = st.date_input("Data de Nascimento")
        sexo = st.selectbox("Sexo", ["Macho", "Fêmea"])
        foto = st.file_uploader("Foto do Pet", type=["jpg", "png", "jpeg"])
        
        salvar = st.form_submit_button("Cadastrar Pet")
        if salvar and nome:
            foto_bytes = resize_image(foto) if foto else None
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO pets (name, breed, birth_date, gender, photo) VALUES (?, ?, ?, ?, ?)",
                (nome, raca, str(nasc), sexo, foto_bytes)
            )
            conn.commit()
            conn.close()
            st.success("Pet cadastrado com sucesso!")
            st.rerun()
else:
    pet_data = pet_dict[selected_name]
    pet_id, name, breed, birth_date, photo_blob = pet_data
    
    st.markdown(f"### Perfil de {name}")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if photo_blob:
            st.image(photo_blob, width=180)
        else:
            st.info("Sem foto.")
    with col2:
        st.write(f"**Raça:** {breed}")
        st.write(f"**Nascimento:** {birth_date}")
        
    st.markdown("---")
    if st.button("🗑️ Excluir este Pet", type="primary"):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
        conn.commit()
        conn.close()
        st.success("Pet excluído!")
        st.rerun()
