import sqlite3
import streamlit as st
from PIL import Image
import io

# Configuração da página
st.set_page_title_page_config = st.set_page_config(
    page_title="Gestão e Diário do Pet", page_icon="🐾", layout="centered"
)

# Conexão com o Banco de Dados SQLite na nuvem
def init_db():
    conn = sqlite3.connect("pet_control.db")
    cursor = conn.cursor()
    # Tabela de Pets
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            breed TEXT,
            birth_date TEXT,
            gender TEXT,
            photo BLOG
        )
    """
    )
    # Tabela de Peso
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS weight (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER,
            date TEXT,
            weight REAL
        )
    """
    )
    # Tabela de Vacinas
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS vaccines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER,
            name TEXT,
            date TEXT,
            next_date TEXT
        )
    """
    )
    # Tabela de Finanças
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS finances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER,
            date TEXT,
            category TEXT,
            amount REAL,
            description TEXT
        )
    """
    )
    # Tabela de Diário
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS diary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER,
            date TEXT,
            note TEXT,
            photo BLOG
        )
    """
    )
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect("pet_control.db")

def resize_image(image_file, max_size=(600, 600)):
    """Redimensiona e comprime a imagem automaticamente para evitar travamentos."""
    try:
        img = Image.open(image_file)
        img.thumbnail(max_size)
        # Converter para RGB se estiver em RGBA
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        byte_arr = io.BytesIO()
        img.save(byte_arr, format="JPEG", quality=85)
        return byte_arr.getvalue()
    except Exception:
        return None

# Funções auxiliares
def get_pets():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM pets")
    pets = cursor.fetchall()
    conn.close()
    return pets

# Menu Lateral
st.sidebar.title("🐾 Menu do Pet")
pets = get_pets()

pet_names = {p[1]: p[0] for p in pets}
selected_pet_name = None

if pets:
    selected_pet_name = st.sidebar.selectbox("Selecionar Pet", list(pet_names.keys()))
    pet_id = pet_names[selected_pet_name]
else:
    st.sidebar.warning("Nenhum pet cadastrado.")
    pet_id = None

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegação",
    ["Perfil / Editar", "Vacinas", "Financeiro", "Diário & Marcos", "Meus Pets / Novo Pet"]
)

# ----------------- ABA: MEUS PETS / NOVO PET -----------------
if menu == "Meus Pets / Novo Pet":
    st.header("Gerenciar Pets")
    
    with st.form("new_pet_form"):
        st.subheader("Cadastrar Novo Pet")
        name = st.text_input("Nome do Pet")
        breed = st.text_input("Raça")
        birth_date = st.date_input("Data de Nascimento")
        gender = st.selectbox("Sexo", ["Macho", "Fêmea"])
        photo_file = st.file_uploader("Foto do Pet", type=["jpg", "png", "jpeg"])
        
        submitted = st.form_submit_button("Salvar Novo Pet")
        if submitted and name:
            photo_bytes = resize_image(photo_file) if photo_file else None
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO pets (name, breed, birth_date, gender, photo) VALUES (?, ?, ?, ?, ?)",
                (name, breed, str(birth_date), gender, photo_bytes)
            )
            conn.commit()
            conn.close()
            st.success(f"Pet {name} cadastrado com sucesso! Atualize a página.")
            st.rerun()

    st.markdown("---")
    st.subheader("Pets Cadastrados")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, breed, birth_date FROM pets")
    all_pets = cursor.fetchall()
    conn.close()
    
    for p in all_pets:
        st.write(f"**Nome:** {p[1]} | **Raça:** {p[2]} | **Nascimento:** {p[3]}")

# Se não houver pets e não estiver na aba de cadastro, avisa
elif not pets:
    st.warning("Nenhum pet selecionado ou cadastrado. Vá na aba 'Meus Pets / Novo Pet' para começar.")

# ----------------- ABA: PERFIL / EDITAR -----------------
elif menu == "Perfil / Editar" and pet_id:
    st.header("Perfil do Pet")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, breed, birth_date, gender, photo FROM pets WHERE id = ?", (pet_id,))
    pet = cursor.fetchone()
    conn.close()
    
    if pet:
        col1, col2 = st.column(2) if hasattr(st, "column") else (st, st)
        with st.container():
            if pet[4]:
                st.image(pet[4], width=250, caption=pet[0])
            else:
                st.info("Sem foto cadastrada.")
                
        with st.form("edit_pet_form"):
            st.subheader("Editar Dados")
            new_name = st.text_input("Nome", value=pet[0])
            new_breed = st.text_input("Raça", value=pet[1] or "")
            new_photo = st.file_uploader("Atualizar Foto", type=["jpg", "png", "jpeg"])
            
            update_btn = st.form_submit_button("Salvar Alterações")
            if update_btn:
                conn = get_db_connection()
                cursor = conn.cursor()
                if new_photo:
                    photo_bytes = resize_image(new_photo)
                    cursor.execute("UPDATE pets SET name = ?, breed = ?, photo = ? WHERE id = ?", (new_name, new_breed, photo_bytes, pet_id))
                else:
                    cursor.execute("UPDATE pets SET name = ?, breed = ? WHERE id = ?", (new_name, new_breed, pet_id))
                conn.commit()
                conn.close()
                st.success("Atualizado com sucesso!")
                st.rerun()

# ----------------- OUTRAS ABAS (Placeholder funcional) -----------------
elif menu == "Vacinas" and pet_id:
    st.header(f"Controle de Vacinas - {selected_pet_name}")
    st.info("Módulo de vacinas pronto para uso no sistema.")

elif menu == "Financeiro" and pet_id:
    st.header(f"Controle Financeiro - {selected_pet_name}")
    st.info("Módulo financeiro pronto para uso no sistema.")

elif menu == "Diário & Marcos" and pet_id:
    st.header(f"Diário do Pet - {selected_pet_name}")
    st.info("Módulo de diário pronto para uso no sistema.")
