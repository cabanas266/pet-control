from datetime import datetime
import os
import sqlite3
import base64
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão e Diário do Pet", page_icon="🐶", layout="centered")

# --- BANCO DE DADOS ---
conn = sqlite3.connect("pet_control.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS pet (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT, raca TEXT, nascimento TEXT, microchip TEXT, tutor TEXT, foto BLOB
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS pesos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pet_id INTEGER,
        data TEXT, peso REAL
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS vacinas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pet_id INTEGER,
        nome TEXT, data_aplicacao TEXT, proxima_dose TEXT, veterinario TEXT, lote TEXT, notas TEXT, foto_etiqueta BLOB
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS despesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pet_id INTEGER,
        data TEXT, categoria TEXT, descricao TEXT, valor REAL
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS marcos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pet_id INTEGER,
        data TEXT, titulo TEXT, descricao TEXT, foto_marco BLOB
    )
""")
conn.commit()

def migrar_banco():
    tabelas = ["pesos", "vacinas", "despesas", "marcos"]
    for tabela in tabelas:
        cursor.execute(f"PRAGMA table_info({tabela})")
        colunas = [col[1] for col in cursor.fetchall()]
        if "pet_id" not in colunas:
            try:
                cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN pet_id INTEGER")
                conn.commit()
            except Exception as ex:
                print(f"Erro ao migrar tabela {tabela}: {ex}")

migrar_banco()

# --- CONTROLE DE ESTADO DA SESSÃO ---
if "aba" not in st.session_state:
    st.session_state["aba"] = "Perfil"
if "pet_id" not in st.session_state:
    st.session_state["pet_id"] = None

# Buscar primeiro pet se não houver selecionado
if not st.session_state["pet_id"]:
    cursor.execute("SELECT id FROM pet LIMIT 1")
    p_res = cursor.fetchone()
    if p_res:
        st.session_state["pet_id"] = p_res[0]

# --- MENU LATERAL ---
st.sidebar.title("🐾 Menu do Pet")
menu_opcao = st.sidebar.radio("Navegação", ["Perfil / Editar", "💉 Vacinas", "💰 Financeiro", "📸 Diário & Marcos", "🔄 Meus Pets / Novo Pet"], index=0)

# Mapeamento do rádio para abas lógicas
if "Perfil" in menu_opcao:
    st.session_state["aba"] = "Perfil"
elif "Vacinas" in menu_opcao:
    st.session_state["aba"] = "Vacinas"
elif "Financeiro" in menu_opcao:
    st.session_state["aba"] = "Financeiro"
elif "Diário" in menu_opcao:
    st.session_state["aba"] = "Diario"
elif "Meus Pets" in menu_opcao:
    st.session_state["aba"] = "Pets"

# ================= TELA: MEUS PETS / CADASTRAR =================
if st.session_state["aba"] == "Pets":
    st.header("🔄 Gerenciar Pets")
    
    with st.expander("➕ Cadastrar Novo Pet", expanded=False):
        novo_nome = st.text_input("Nome do Pet")
        nova_raca = st.text_input("Raça")
        novo_tutor = st.text_input("Nome do Tutor")
        novo_nasc = st.text_input("Nascimento (AAAA-MM-DD)")
        novo_micro = st.text_input("Microchip")
        foto_cad_file = st.file_uploader("Foto do Pet", type=["png", "jpg", "jpeg"], key="foto_cad")
        
        if st.button("Salvar Novo Pet", type="primary"):
            if not novo_nome:
                st.error("O nome do pet é obrigatório!")
            else:
                foto_bytes = foto_cad_file.read() if foto_cad_file else None
                cursor.execute(
                    "INSERT INTO pet (nome, raca, nascimento, microchip, tutor, foto) VALUES (?, ?, ?, ?, ?, ?)",
                    (novo_nome, nova_raca, novo_nasc, novo_micro, novo_tutor, foto_bytes)
                )
                conn.commit()
                cursor.execute("SELECT last_insert_rowid()")
                st.session_state["pet_id"] = cursor.fetchone()[0]
                st.success("Novo pet cadastrado com sucesso!")
                st.rerun()

    st.divider()
    st.subheader("Selecione o Pet Ativo")
    cursor.execute("SELECT id, nome, raca, foto FROM pet")
    pets = cursor.fetchall()
    
    if not pets:
        st.info("Nenhum pet cadastrado. Utilize o formulário acima para cadastrar.")
    else:
        for pid, pnome, praca, pfoto in pets:
            col1, col2, col3 = st.columns([1, 3, 2])
            with col1:
                if pfoto:
                    st.image(pfoto, width=60)
                else:
                    st.write("🐶")
            with col2:
                st.write(f"**{pnome}**")
                st.caption(f"Raça: {praca or 'Não informada'}")
            with col3:
                if st.button("Selecionar", key=f"sel_{pid}"):
                    st.session_state["pet_id"] = pid
                    st.success(f"Pet {pnome} selecionado!")
                    st.rerun()

# Validação se existe pet selecionado para as outras abas
elif not st.session_state["pet_id"]:
    st.warning("Nenhum pet selecionado ou cadastrado. Vá na aba 'Meus Pets / Novo Pet' para começar.")
else:
    cursor.execute("SELECT nome, raca, nascimento, microchip, tutor, foto FROM pet WHERE id = ?", (st.session_state["pet_id"],))
    pet_info = cursor.fetchone()
    
    if not pet_info:
        st.session_state["pet_id"] = None
        st.rerun()
        
    p_nome, p_raca, p_nasc, p_micro, p_tutor, p_foto = pet_info

    # ================= TELA: PERFIL =================
    if st.session_state["aba"] == "Perfil":
        st.header(f"🐶 Perfil: {p_nome}")
        
        col_img, col_form = st.columns([1, 2])
        with col_img:
            if p_foto:
                st.image(p_foto, width=120)
            else:
                st.info("Sem foto")
                
        with col_form:
            nova_foto_file = st.file_uploader("Alterar Foto", type=["png", "jpg", "jpeg"], key="foto_perfil")

        with st.form("form_perfil"):
            n_nome = st.text_input("Nome do Pet", value=p_nome or "")
            n_raca = st.text_input("Raça", value=p_raca or "")
            n_tutor = st.text_input("Nome do Tutor", value=p_tutor or "")
            n_nasc = st.text_input("Nascimento (AAAA-MM-DD)", value=p_nasc or "")
            n_micro = st.text_input("Microchip", value=p_micro or "")
            
            btn_salvar = st.form_submit_button("Salvar Alterações")
            if btn_salvar:
                foto_a_salvar = nova_foto_file.read() if nova_foto_file else p_foto
                cursor.execute(
                    "UPDATE pet SET nome=?, raca=?, nascimento=?, microchip=?, tutor=?, foto=? WHERE id=?",
                    (n_nome, n_raca, n_nasc, n_micro, n_tutor, foto_a_salvar, st.session_state["pet_id"])
                )
                conn.commit()
                st.success("Alterações salvas com sucesso!")
                st.rerun()

        if st.button("🗑️ Excluir Pet", type="secondary"):
            pid = st.session_state["pet_id"]
            cursor.execute("DELETE FROM pesos WHERE pet_id = ?", (pid,))
            cursor.execute("DELETE FROM vacinas WHERE pet_id = ?", (pid,))
            cursor.execute("DELETE FROM despesas WHERE pet_id = ?", (pid,))
            cursor.execute("DELETE FROM marcos WHERE pet_id = ?", (pid,))
            cursor.execute("DELETE FROM pet WHERE id = ?", (pid,))
            conn.commit()
            st.session_state["pet_id"] = None
            st.success("Pet excluído!")
            st.rerun()

        st.divider()
        st.subheader("⚖️ Evolução de Peso")
        
        with st.form("form_peso", clear_on_submit=True):
            col_d, col_v, col_b = st.columns(3)
            with col_d:
                p_data = st.text_input("Data", value=datetime.today().strftime("%Y-%m-%d"))
            with col_v:
                p_valor = st.text_input("Peso (kg)")
            with col_b:
                st.write("")
                st.write("")
                sub_peso = st.form_submit_button("Adicionar Peso")
            
            if sub_peso:
                try:
                    val_f = float(p_valor.replace(",", "."))
                    cursor.execute("INSERT INTO pesos (pet_id, data, peso) VALUES (?, ?, ?)", (st.session_state["pet_id"], p_data, val_f))
                    conn.commit()
                    st.success("Peso registrado!")
                    st.rerun()
                except ValueError:
                    st.error("Digite um valor de peso válido!")

        st.write("**Histórico de Pesos:**")
        cursor.execute("SELECT id, data, peso FROM pesos WHERE pet_id = ? ORDER BY data DESC", (st.session_state["pet_id"],))
        pesos_list = cursor.fetchall()
        for pidx, pdata, ppeso in pesos_list:
            c1, c2 = st.columns([5, 1])
            with c1:
                st.text(f"📅 Data: {pdata} | ⚖️ Peso: {ppeso} kg")
            with c2:
                if st.button("🗑️", key=f"del_p_{pidx}"):
                    cursor.execute("DELETE FROM pesos WHERE id = ?", (pidx,))
                    conn.commit()
                    st.rerun()

    # ================= TELA: VACINAS =================
    elif st.session_state["aba"] == "Vacinas":
        st.header("💉 Controle de Vacinas")
        
        with st.form("form_vacina", clear_on_submit=True):
            v_nome = st.text_input("Nome da Vacina / Antipulgas")
            c1, c2 = st.columns(2)
            with c1:
                v_app = st.text_input("Data Aplicação", value=datetime.today().strftime("%Y-%m-%d"))
            with c2:
                v_prox = st.text_input("Próxima Dose", value=datetime.today().strftime("%Y-%m-%d"))
            v_vet = st.text_input("Veterinário / Clínica")
            v_lote = st.text_input("Lote / Fabricante")
            v_file = st.file_uploader("Foto da Etiqueta", type=["png", "jpg", "jpeg"])
            
            if st.form_submit_button("Cadastrar Vacina"):
                v_bytes = v_file.read() if v_file else None
                cursor.execute(
                    "INSERT INTO vacinas (pet_id, nome, data_aplicacao, proxima_dose, veterinario, lote, foto_etiqueta) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (st.session_state["pet_id"], v_nome, v_app, v_prox, v_vet, v_lote, v_bytes)
                )
                conn.commit()
                st.success("Vacina cadastrada!")
                st.rerun()

        st.divider()
        st.subheader("Histórico de Vacinas")
        cursor.execute("SELECT id, nome, data_aplicacao, proxima_dose, veterinario, foto_etiqueta FROM vacinas WHERE pet_id = ? ORDER BY data_aplicacao DESC", (st.session_state["pet_id"],))
        for vid, vnome, vapp, vprox, vvet, vfoto in cursor.fetchall():
            with st.container(border=True):
                col_txt, col_btn = st.columns([5, 1])
                with col_txt:
                    tem_foto = " 📷 [Com Foto]" if vfoto else ""
                    st.markdown(f"**💉 {vnome}**{tem_foto}")
                    st.caption(f"Aplicada em: {vapp} | Próxima: {vprox}\n\nVet: {vvet}")
                with col_btn:
                    if st.button("🗑️", key=f"del_v_{vid}"):
                        cursor.execute("DELETE FROM vacinas WHERE id = ?", (vid,))
                        conn.commit()
                        st.rerun()

    # ================= TELA: FINANCEIRO =================
    elif st.session_state["aba"] == "Financeiro":
        st.header("💰 Controle Financeiro")
        
        with st.form("form_gasto", clear_on_submit=True):
            g_cat = st.selectbox("Categoria", ["Ração / Alimentação", "Veterinário / Vacinas", "Banho / Tosa", "Acessórios"])
            g_desc = st.text_input("Descrição do Gasto")
            g_val = st.text_input("Valor (R$)")
            
            if st.form_submit_button("Adicionar Gasto"):
                try:
                    val_g = float(g_val.replace(",", "."))
                    cursor.execute(
                        "INSERT INTO despesas (pet_id, data, categoria, descricao, valor) VALUES (?, ?, ?, ?, ?)",
                        (st.session_state["pet_id"], datetime.today().strftime("%Y-%m-%d"), g_cat, g_desc, val_g)
                    )
                    conn.commit()
                    st.success("Despesa registrada!")
                    st.rerun()
                except ValueError:
                    st.error("Informe um valor válido!")

        st.divider()
        cursor.execute("SELECT id, data, categoria, descricao, valor FROM despesas WHERE pet_id = ?", (st.session_state["pet_id"],))
        gastos = cursor.fetchall()
        total = sum(g[4] for g in gastos)
        
        st.metric("Total Gasto", f"R$ {total:.2f}")
        st.subheader("Extrato de Gastos")
        
        for did, ddata, dcat, ddesc, dval in gastos:
            c1, c2 = st.columns([5, 1])
            with c1:
                st.text(f"📅 {ddata} | {dcat} - {ddesc}: R$ {dval:.2f}")
            with c2:
                if st.button("🗑️", key=f"del_g_{did}"):
                    cursor.execute("DELETE FROM despesas WHERE id = ?", (did,))
                    conn.commit()
                    st.rerun()

    # ================= TELA: DIÁRIO =================
    elif st.session_state["aba"] == "Diario":
        st.header("📸 Diário & Marcos")
        
        with st.form("form_marco", clear_on_submit=True):
            m_tit = st.text_input("Título do Marco")
            m_desc = st.text_area("Como foi?")
            m_file = st.file_uploader("Foto do Marco", type=["png", "jpg", "jpeg"])
            
            if st.form_submit_button("Salvar Marco"):
                m_bytes = m_file.read() if m_file else None
                cursor.execute(
                    "INSERT INTO marcos (pet_id, data, titulo, descricao, foto_marco) VALUES (?, ?, ?, ?, ?)",
                    (st.session_state["pet_id"], datetime.today().strftime("%Y-%m-%d"), m_tit, m_desc, m_bytes)
                )
                conn.commit()
                st.success("Marco salvo com sucesso!")
                st.rerun()

        st.divider()
        st.subheader("Linha do Tempo")
        cursor.execute("SELECT id, data, titulo, descricao, foto_marco FROM marcos WHERE pet_id = ? ORDER BY id DESC", (st.session_state["pet_id"],))
        for mid, mdata, mtitulo, mdesc, mfoto in cursor.fetchall():
            with st.container(border=True):
                col_txt, col_btn = st.columns([5, 1])
                with col_txt:
                    tem_foto = " 📷 [Com Foto]" if mfoto else ""
                    st.markdown(f"**📌 {mdata} - {mtitulo}**{tem_foto}")
                    st.write(mdesc)
                with col_btn:
                    if st.button("🗑️", key=f"del_m_{mid}"):
                        cursor.execute("DELETE FROM marcos WHERE id = ?", (mid,))
                        conn.commit()
                        st.rerun()