import streamlit as st
import docx
import random
import re
from datetime import datetime

st.set_page_config(page_title="Simulator Dispecer", layout="centered")

# Inițializare variabile de sesiune
if 'test' not in st.session_state:
    st.session_state.test = []
    st.session_state.index = 0
    st.session_state.scor = 0
    st.session_state.gresite = 0
    st.session_state.verificat = False
    st.session_state.istoric = []

def proceseaza_word(file):
    doc = docx.Document(file)
    paragrafe = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    full_text = "\n".join(paragrafe)
    parti = re.split(r'(ID:\d+)', full_text)
    baza_date = []

    for i in range(1, len(parti), 2):
        id_tag = parti[i]
        continut = parti[i+1] if i+1 < len(parti) else ""
        text_precedent = parti[i-1].split('\n')
        intrebare_curata = []
        for linie in reversed(text_precedent):
            if any(x in linie for x in ["Punctaj:", "Bibliografie:", "ID:"]) or re.match(r'^[a-e]\)', linie):
                break
            intrebare_curata.insert(0, linie)
        
        text_final_q = " ".join(intrebare_curata).strip()
        linii_corp = continut.split('\n')
        variante = []
        punctaj = 3
        current_v_text = ""
        current_v_correct = False

        for linie in linii_corp:
            linie = linie.strip()
            if not linie: continue
            match_v = re.match(r'^([Xx]\s+)?([a-e]\)\s*)(.*)', linie)
            if match_v:
                if current_v_text:
                    variante.append({'text': current_v_text.strip(), 'correct': current_v_correct})
                current_v_correct = bool(match_v.group(1))
                current_v_text = match_v.group(2) + match_v.group(3)
            else:
                if "ID:" not in linie:
                    current_v_text += " " + linie
        
        if current_v_text:
            variante.append({'text': current_v_text.strip(), 'correct': current_v_correct})
        
        if variante and text_final_q:
            baza_date.append({'id': id_tag, 'q': text_final_q, 'v': variante, 'p': punctaj})
    return baza_date

st.title("🚀 Simulator Examen Dispecer")

# Sidebar pentru Istoric
with st.sidebar:
    st.header("📊 Istoric Teste")
    if not st.session_state.istoric:
        st.write("Nu ai teste efectuate încă.")
    for res in reversed(st.session_state.istoric):
        st.info(f"📅 {res['data']}\n🏆 Scor: {res['scor']} pct ({res['procent']}%)")

uploaded_file = st.file_uploader("Încarcă fișierul Word", type="docx")

if uploaded_file and not st.session_state.test:
    if st.button("START TEST NOU (40 Întrebări)"):
        date = proceseaza_word(uploaded_file)
        if date:
            random.shuffle(date)
            st.session_state.test = date[:40]
            st.session_state.index = 0
            st.session_state.scor = 0
            st.session_state.gresite = 0
            st.rerun()

# Logica de desfășurare a testului
if st.session_state.test and st.session_state.index < len(st.session_state.test):
    q = st.session_state.test[st.session_state.index]
    st.subheader(f"Întrebarea {st.session_state.index + 1} / {len(st.session_state.test)}")
    st.info(f"**{q['id']}**: {q['q']}")

    with st.form(key=f"form_{st.session_state.index}"):
        optiuni = [v['text'] for v in q['v']]
        raspunsuri_utilizator = []
        for i, opt in enumerate(optiuni):
            raspunsuri_utilizator.append(st.checkbox(opt, key=f"c_{st.session_state.index}_{i}"))
        
        if st.form_submit_button("Verifică Răspunsul"):
            st.session_state.verificat = True
            corecte = [v['text'] for v in q['v'] if v['correct']]
            selectate = [optiuni[idx] for idx, val in enumerate(raspunsuri_utilizator) if val]
            
            if set(corecte) == set(selectate):
                st.success("✅ CORECT!")
                st.session_state.scor += 1
            else:
                st.error(f"❌ GREȘIT!")
                st.write(f"Răspunsul corect era: **{', '.join(corecte)}**")
                st.session_state.gresite += 1

    if st.session_state.verificat:
        if st.button("Următoarea Întrebare ➡️"):
            st.session_state.index += 1
            st.session_state.verificat = False
            st.rerun()

# Ecran Final Rezumat
elif st.session_state.test and st.session_state.index >= len(st.session_state.test):
    st.balloons()
    st.header("🎉 Rezumat Final")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Corecte", st.session_state.scor)
    col2.metric("Greșite", st.session_state.gresite)
    procent = int((st.session_state.scor / len(st.session_state.test)) * 100)
    col3.metric("Procentaj", f"{procent}%")

    # Salvare în istoric (doar o dată la final)
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    if not any(d['data'] == now for d in st.session_state.istoric):
        st.session_state.istoric.append({
            "data": now,
            "scor": st.session_state.scor,
            "procent": procent
        })

    if st.button("Începe un test nou"):
        st.session_state.test = []
        st.rerun()
