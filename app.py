import sqlite3
import streamlit as st
from PIL import Image
import io

st.set_page_config(page_title="Gestão e Diário do Pet", page_icon="🐾", layout="centered")

def init_db():
    conn = sqlite3.connect("pet_control.db")
    cursor = conn.cursor()
    
    # Recria todas as tabelas e força a limpeza da tabela de vacinas antiga para atualizar colunas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            breed TEXT,
            birth_date TEXT,
            gender TEXT,
            owner TEXT,
            microchip TEXT,
            photo BLOB
        )
    """)
    # Drop temporário para garantir que a tabela de vacinas nasça com a estrutura correta na nuvem
    cursor.execute("DROP TABLE IF EXISTS vaccines")
    cursor.execute("""
        CREATE TABLE vaccines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER,
            name TEXT,
            date TEXT,
            next_date TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER,
            date TEXT,
            category TEXT,
            amount REAL,
            description TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER,
            date TEXT,
            note TEXT,
            photo BLOB
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
        cursor.execute("SELECT id, name, breed, birth_date, gender, owner, microchip, photo FROM pets")
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
    pet_id, pet_name, pet_breed, pet_birth, pet_gender, pet_owner, pet_microchip, pet_photo = pet_data
else:
    st.sidebar.warning("Nenhum pet cadastrado.")
    pet_id = None

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegação",
    ["Perfil / Editar", "Vacinas", "Financeiro", "Diário & Marcos", "Meus Pets / Novo Pet"]
)

# ----------------- ABA: PERFIL / EDITAR -----------------
if menu == "Perfil / Editar" and pet_id:
    st.header(f"Perfil de {pet_name}")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if pet_photo:
            st.image(io.BytesIO(pet_photo), width=200, caption=pet_name)
        else:
            st.info("Sem foto cadastrada.")
            
    with col2:
        st.write(f"**Raça:** {pet_breed}")
        st.write(f"**Nascimento:** {pet_birth}")
        st.write(f"**Sexo:** {pet_gender}")
        st.write(f"**Tutor:** {pet_owner or 'Não informado'}")
        st.write(f"**Microchip:** {pet_microchip or 'Não cadastrado'}")

    st.markdown("---")
    with st.form("update_form"):
        st.subheader("Atualizar Dados ou Foto")
        new_name = st.text_input("Nome", value=pet_name)
        new_breed = st.text_input("Raça", value=pet_breed or "")
        new_owner = st.text_input("Tutor", value=pet_owner or "")
        new_microchip = st.text_input("Microchip", value=pet_microchip or "")
        new_photo = st.file_uploader("Atualizar Foto", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("Salvar Alterações"):
            conn = get_db_connection()
            cursor = conn.cursor()
            if new_photo:
                photo_bytes = resize_image(new_photo)
                cursor.execute("UPDATE pets SET name = ?, breed = ?, owner = ?, microchip = ?, photo = ? WHERE id = ?", (new_name, new_breed, new_owner, new_microchip, photo_bytes, pet_id))
            else:
                cursor.execute("UPDATE pets SET name = ?, breed = ?, owner = ?, microchip = ? WHERE id = ?", (new_name, new_breed, new_owner, new_microchip, pet_id))
            conn.commit()
            conn.close()
            st.success("Atualizado com sucesso!")
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ Excluir este Pet", type="primary"):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
        cursor.execute("DELETE FROM vaccines WHERE pet_id = ?", (pet_id,))
        cursor.execute("DELETE FROM finances WHERE pet_id = ?", (pet_id,))
        cursor.execute("DELETE FROM diary WHERE pet_id = ?", (pet_id,))
        conn.commit()
        conn.close()
        st.success("Pet excluído com sucesso!")
        st.rerun()

# ----------------- ABA: VACINAS -----------------
elif menu == "Vacinas" and pet_id:
    st.header(f"💉 Controle de Vacinas - {pet_name}")
    
    with st.form("vac_form"):
        v_name = st.text_input("Nome da Vacina")
        v_date = st.date_input("Data da Aplicação")
        v_next = st.date_input("Próxima Dose (Previsão)")
        if st.form_submit_button("Adicionar Vacina"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO vaccines (pet_id, name, date, next_date) VALUES (?, ?, ?, ?)", (pet_id, v_name, str(v_date), str(v_next)))
            conn.commit()
            conn.close()
            st.success("Vacina registrada!")
            st.rerun()
            
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, date, next_date FROM vaccines WHERE pet_id = ?", (pet_id,))
    vacs = cursor.fetchall()
    conn.close()
    
    if vacs:
        st.markdown("### Vacinas Registradas")
        for v in vacs:
            col_v1, col_v2 = st.columns([4, 1])
            col_v1.write(f"✔️ **{v[1]}** | Aplicada: {v[2]} | Próxima: {v[3]}")
            if col_v2.button("Apagar", key=f"del_vac_{v[0]}"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM vaccines WHERE id = ?", (v[0],))
                conn.commit()
                conn.close()
                st.success("Vacina removida!")
                st.rerun()
    else:
        st.info("Nenhuma vacina registrada ainda.")

# ----------------- ABA: FINANCEIRO -----------------
elif menu == "Financeiro" and pet_id:
    st.header(f"💰 Controle Financeiro - {pet_name}")
    
    with st.form("fin_form"):
        f_cat = st.selectbox("Categoria", ["Ração", "Veterinário", "Petshop / Banho", "Brinquedos", "Outros"])
        f_val = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        f_date = st.date_input("Data do Gasto")
        f_desc = st.text_input("Descrição / Observação")
        if st.form_submit_button("Adicionar Despesa"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO finances (pet_id, date, category, amount, description) VALUES (?, ?, ?, ?, ?)", (pet_id, str(f_date), f_cat, f_val, f_desc))
            conn.commit()
            conn.close()
            st.success("Despesa salva!")
            st.rerun()
            
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, category, amount, date, description FROM finances WHERE pet_id = ?", (pet_id,))
    fins = cursor.fetchall()
    conn.close()
    
    if fins:
        total = sum([f[2] for f in fins])
        st.metric("Gasto Total com o Pet", f"R$ {total:.2f}")
        st.markdown("### Histórico de Despesas")
        for f in fins:
            col_f1, col_f2 = st.columns([4, 1])
            col_f1.write(f"📌 **{f[1]}** - R$ {f[2]:.2f} ({f[3]}) - *{f[4]}*")
            if col_f2.button("Apagar", key=f"del_fin_{f[0]}"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM finances WHERE id = ?", (f[0],))
                conn.commit()
                conn.close()
                st.success("Despesa removida!")
                st.rerun()
    else:
        st.info("Nenhuma despesa registrada ainda.")

# ----------------- ABA: DIÁRIO & MARCOS -----------------
elif menu == "Diário & Marcos" and pet_id:
    st.header(f"📖 Diário & Marcos - {pet_name}")
    
    with st.form("diary_form"):
        d_date = st.date_input("Data do Acontecimento")
        d_note = st.text_area("O que aconteceu hoje?")
        if st.form_submit_button("Salvar no Diário"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO diary (pet_id, date, note) VALUES (?, ?, ?)", (pet_id, str(d_date), d_note))
            conn.commit()
            conn.close()
            st.success("Momento salvo no diário!")
            st.rerun()
            
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, note FROM diary WHERE pet_id = ?", (pet_id,))
    diaries = cursor.fetchall()
    conn.close()
    
    if diaries:
        for d in diaries:
            col_d1, col_d2 = st.columns([4, 1])
            col_d1.write(f"📅 **{d[1]}**: {d[2]}")
            if col_d2.button("Apagar", key=f"del_dia_{d[0]}"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM diary WHERE id = ?", (d[0],))
                conn.commit()
                conn.close()
                st.success("Registro removido!")
                st.rerun()
            st.markdown("---")
    else:
        st.info("Nenhum registro no diário ainda.")

# ----------------- ABA: MEUS PETS / NOVO PET -----------------
elif menu == "Meus Pets / Novo Pet":
    st.header("🐾 Gerenciar Meus Pets")
    
    with st.form("new_pet"):
        st.subheader("Cadastrar Novo Pet")
        name = st.text_input("Nome do Pet")
        breed = st.text_input("Raça")
        birth_date = st.date_input("Data de Nascimento")
        gender = st.selectbox("Sexo", ["Macho", "Fêmea"])
        owner = st.text_input("Nome do Tutor")
        microchip = st.text_input("Número do Microchip")
        photo_file = st.file_uploader("Foto do Pet", type=["jpg", "png", "jpeg"])
        
        submitted = st.form_submit_button("Salvar Novo Pet")
        if submitted and name:
            photo_bytes = resize_image(photo_file) if photo_file else None
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO pets (name, breed, birth_date, gender, owner, microchip, photo) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, breed, str(birth_date), gender, owner, microchip, photo_bytes)
            )
            conn.commit()
            conn.close()
            st.success(f"Pet {name} cadastrado com sucesso!")
            st.rerun()

    if pets:
        st.markdown("---")
        st.subheader("Pets Cadastrados / Excluir")
        for p in pets:
            col_a, col_b = st.columns([3, 1])
            col_a.write(f"**{p[1]}** (Raça: {p[2] or 'Non informada'})")
            if col_b.button("Excluir", key=f"del_{p[0]}"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM pets WHERE id = ?", (p[0],))
                cursor.execute("DELETE FROM vaccines WHERE pet_id = ?", (p[0],))
                cursor.execute("DELETE FROM finances WHERE pet_id = ?", (p[0],))
                cursor.execute("DELETE FROM diary WHERE pet_id = ?", (p[0],))
                conn.commit()
                conn.close()
                st.success(f"Pet {p[1]} excluído com sucesso!")
                st.rerun()

elif not pets:
    st.info("👈 Nenhum pet cadastrado. Use a aba 'Meus Pets / Novo Pet' no menu lateral para cadastrar o Pudim!")
