import sqlite3
import streamlit as st
from PIL import Image
import io

st.set_page_config(page_title="Gestão e Diário do Pet", page_icon="🐾", layout="centered")

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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vaccines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER,
            name TEXT,
            date TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER,
            category TEXT,
            amount REAL,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect("pet_control.db")

def resize_image(image_file):
    try:
        img = Image.open(image_file)
        img.thumbnail((400, 400))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        byte_arr = io.BytesIO()
        img.save(byte_arr, format="JPEG", quality=80)
        return byte_arr.getvalue()
    except Exception:
        return None

def get_pets():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, breed, birth_date, gender, photo FROM pets")
        pets = cursor.fetchall()
        conn.close()
        return pets
    except Exception:
        return []

# Menu Lateral
st.sidebar.title("🐾 Menu do Pet")
pets = get_pets()
pet_dict = {p[1]: p for p in pets}

selected_pet_name = None
if pets:
    selected_pet_name = st.sidebar.selectbox("Selecionar Pet", list(pet_dict.keys()))
    pet_data = pet_dict[selected_pet_name]
    pet_id, pet_name, pet_breed, pet_birth, pet_gender, pet_photo = pet_data
else:
    st.sidebar.warning("Nenhum pet cadastrado.")
    pet_id = None

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegação",
    ["Perfil / Editar", "Vacinas", "Financeiro", "Meus Pets / Novo Pet"]
)

# ----------------- ABA: NOVO PET / GERENCIAR -----------------
if menu == "Meus Pets / Novo Pet":
    st.header("🐾 Cadastrar Novo Pet")
    with st.form("new_pet"):
        name = st.text_input("Nome do Pet")
        breed = st.text_input("Raça")
        birth_date = st.date_input("Data de Nascimento")
        gender = st.selectbox("Sexo", ["Macho", "Fêmea"])
        photo_file = st.file_uploader("Foto do Pet", type=["jpg", "png", "jpeg"])
        
        submitted = st.form_submit_button("Salvar Pet")
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
            st.success(f"Pet {name} cadastrado com sucesso!")
            st.rerun()

    if pets:
        st.markdown("---")
        st.subheader("Gerenciar Pets Existentes")
        for p in pets:
            col_a, col_b = st.columns([3, 1])
            col_a.write(f"**{p[1]}** ({p[2]})")
            if col_b.button("Excluir", key=f"del_{p[0]}"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM pets WHERE id = ?", (p[0],))
                conn.commit()
                conn.close()
                st.success(f"Pet {p[1]} excluído!")
                st.rerun()

elif not pets:
    st.info("👈 Comece cadastrando o Pudim na aba 'Meus Pets / Novo Pet' no menu ao lado!")

# ----------------- ABA: PERFIL -----------------
elif menu == "Perfil / Editar" and pet_id:
    st.header(f"Perfil de {pet_name}")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if pet_photo:
            # Converte os bytes do banco em um fluxo legível pelo Streamlit
            st.image(io.BytesIO(pet_photo), width=200, caption=pet_name)
        else:
            st.info("Sem foto cadastrada.")
            
    with col2:
        st.write(f"**Raça:** {pet_breed}")
        st.write(f"**Nascimento:** {pet_birth}")
        st.write(f"**Sexo:** {pet_gender}")

    st.markdown("---")
    with st.form("update_form"):
        st.subheader("Atualizar Foto ou Dados")
        new_name = st.text_input("Nome", value=pet_name)
        new_breed = st.text_input("Raça", value=pet_breed or "")
        new_photo = st.file_uploader("Nova Foto", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("Salvar Alterações"):
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

# ----------------- ABA: VACINAS -----------------
elif menu == "Vacinas" and pet_id:
    st.header(f"💉 Controle de Vacinas - {pet_name}")
    
    with st.form("vac_form"):
        v_name = st.text_input("Nome da Vacina")
        v_date = st.date_input("Data da Aplicação")
        if st.form_submit_button("Adicionar Vacina"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO vaccines (pet_id, name, date) VALUES (?, ?, ?)", (pet_id, v_name, str(v_date)))
            conn.commit()
            conn.close()
            st.success("Vacina registrada!")
            st.rerun()
            
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, date FROM vaccines WHERE pet_id = ?", (pet_id,))
    vacs = cursor.fetchall()
    conn.close()
    
    if vacs:
        for v in vacs:
            st.write(f"✔️ **{v[0]}** - Aplicada em: {v[1]}")
    else:
        st.info("Nenhuma vacina registrada ainda.")

# ----------------- ABA: FINANCEIRO -----------------
elif menu == "Financeiro" and pet_id:
    st.header(f"💰 Controle Financeiro - {pet_name}")
    
    with st.form("fin_form"):
        f_cat = st.selectbox("Categoria", ["Ração", "Veterinário", "Petshop / Banho", "Brinquedos", "Outros"])
        f_val = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        f_date = st.date_input("Data do Gasto")
        if st.form_submit_button("Adicionar Despesa"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO finances (pet_id, category, amount, date) VALUES (?, ?, ?, ?)", (pet_id, f_cat, f_val, str(f_date)))
            conn.commit()
            conn.close()
            st.success("Despesa salva!")
            st.rerun()
            
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT category, amount, date FROM finances WHERE pet_id = ?", (pet_id,))
    fins = cursor.fetchall()
    conn.close()
    
    if fins:
        total = sum([f[1] for f in fins])
        st.metric("Gasto Total com o Pet", f"R$ {total:.2f}")
        for f in fins:
            st.write(f"📌 **{f[0]}** - R$ {f[1]:.2f} em {f[2]}")
    else:
        st.info("Nenhuma despesa registrada ainda.")
