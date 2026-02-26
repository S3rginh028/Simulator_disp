import streamlit as st
import docx
import random
import re

# Configurare pagină pentru mobil
st.set_page_config(page_title="Simulator Dispecer", layout="centered")

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
            if "Punctaj:" in linie or "Bibliografie:" in linie or re.match(r'^[a-e]\)', linie):
                break
            intrebare_curata.insert(0, linie)
        
        text_final_q = " ".join(intrebare_curata).strip()
        linii_corp = continut.split('\n')
        variante = []
        punctaj = 3
        current_v_text = ""
        current_v_correct = False

        for linie in linii_corp:
            if "Punctaj:" in linie:
                try: punctaj = int(re.search(r'\d+', linie).group())
                except: pass
            match_v = re.match(r'^([Xx]\s+)?([a-e]\)\s*)(.*)', linie)
            if match_v:
                if current_v_text:
                    variante.append({'text': current_v_text.strip(), 'correct': current_v_correct})
                current_v_correct = bool(match_v.group(1))
                current_v_text = match_v.group(2) + match_v.group(3)
            else:
                if "Bibliografie:" not in linie and "Categorie:" not in linie:
                    current_v_text += " " + linie
        if current_v_text:
            variante.append({'text': current_v_text.strip(), 'correct': current_v_correct})
        
        if variante:
            baza_date.append({'id': id_tag, 'q': text_final_q, 'v': variante, 'p': punctaj})
    return baza_date

# --- LOGICĂ APLICAȚIE ---
if 'test' not in st.session_state:
    st.session_state.test = []
    st.session_state.index = 0
    st.session_state.scor = 0
    st.session_state.verificat = False

st.title("🚀 Simulator Examen Dispecer")

uploaded_file = st.file_uploader("Încarcă fișierul Word cu întrebări", type="docx")

if uploaded_file and not st.session_state.test:
    if st.button("START TEST (40 Întrebări)"):
        with st.spinner('Se încarcă întrebările...'):
            date = proceseaza_word(uploaded_file)
            if len(date) >= 40:
                random.shuffle(date)
                st.session_state.test = date[:40]
            else:
                st.session_state.test = date
            st.rerun()

if st.session_state.test:
    q = st.session_state.test[st.session_state.index]
    st.write(f"**Întrebarea {st.session_state.index + 1} / {len(st.session_state.test)}** | Punctaj: {q['p']} pct")
    st.info(q['q'])

    with st.form(key=f"q_{st.session_state.index}"):
        optiuni = [v['text'] for v in q['v']]
        alese = []
        for i, opt in enumerate(optiuni):
            alese.append(st.checkbox(opt, key=f"opt_{st.session_state.index}_{i}"))
        
        submit = st.form_submit_button("Verifică Răspunsul")
        
        if submit:
            st.session_state.verificat = True
            corecte_text = [v['text'] for v in q['v'] if v['correct']]
            alese_text = [optiuni[i] for i, b in enumerate(alese) if b]
            
            if set(corecte_text) == set(alese_text):
                st.success("✅ CORECT!")
                st.session_state.scor += q['p']
            else:
                st.error(f"❌ GREȘIT!")
                st.write(f"Răspunsul corect era: **{', '.join(corecte_text)}**")

    if st.session_state.verificat:
        if st.button("Următoarea Întrebare ➡️"):
            st.session_state.index += 1
            st.session_state.verificat = False
            if st.session_state.index >= len(st.session_state.test):
                st.balloons()
                st.write(f"### 🎉 Test Finalizat!")
                st.write(f"Scorul tău total este: **{st.session_state.scor} puncte**")
                if st.button("Reîncepe Testul"):
                    st.session_state.test = []
                    st.session_state.index = 0
                    st.session_state.scor = 0
                    st.rerun()
            else:
                st.rerun()
