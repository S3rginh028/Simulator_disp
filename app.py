import docx
import random
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from datetime import datetime
import json
import os

class SimulatorExamenV8:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulator Examen Dispecer")
        self.root.state("zoomed")
        self.root.configure(bg="#f4f6f9")

        self.baza_date = []
        self.test_curent = []
        self.index = 0
        self.scor_total = 0
        self.istoric = self.incarca_istoric()
        self.selectii_utilizator = []

        # Container scrollabil
        self.container = tk.Frame(root, bg="#f4f6f9")
        self.container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.container, bg="#f4f6f9", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f4f6f9")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.main_frame = self.scrollable_frame
        self.ecran_start()

    # --------------------- ECRAN START ---------------------

    def ecran_start(self):
        self.curata_ecran()

        tk.Label(self.main_frame, text="SIMULATOR EXAMEN DISPECER",
                 font=("Segoe UI", 26, "bold"),
                 bg="#f4f6f9", fg="#1a73e8").pack(pady=50)

        btn_style = {"font": ("Segoe UI", 12, "bold"),
                     "padx": 30, "pady": 15, "cursor": "hand2"}

        tk.Button(self.main_frame,
                  text="ÎNCARCĂ WORD ȘI START TEST (40 Întrebări)",
                  command=self.incarca_datele,
                  bg="#27ae60", fg="white",
                  **btn_style).pack(pady=10)

        tk.Button(self.main_frame,
                  text="VEZI ISTORIC REZULTATE",
                  command=self.arata_statistici,
                  bg="#2c3e50", fg="white",
                  **btn_style).pack(pady=10)

    # --------------------- ÎNCĂRCARE DATE ---------------------

    def incarca_datele(self):
        cale = filedialog.askopenfilename(filetypes=[("Word", "*.docx")])
        if not cale:
            return

        try:
            doc = docx.Document(cale)
            paragrafe = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            full_text = "\n".join(paragrafe)

            parti = re.split(r'(ID:\d+)', full_text)
            self.baza_date = []

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
                        try:
                            punctaj = int(re.search(r'\d+', linie).group())
                        except:
                            pass

                    match_v = re.match(r'^([Xx]\s+)?([a-e]\)\s*)(.*)', linie)
                    if match_v:
                        if current_v_text:
                            variante.append({'text': current_v_text.strip(),
                                             'correct': current_v_correct})

                        current_v_correct = bool(match_v.group(1))
                        current_v_text = match_v.group(2) + match_v.group(3)
                    else:
                        if "Bibliografie:" not in linie and "Categorie:" not in linie:
                            current_v_text += " " + linie

                if current_v_text:
                    variante.append({'text': current_v_text.strip(),
                                     'correct': current_v_correct})

                if variante:
                    self.baza_date.append({
                        'id': id_tag,
                        'q': text_final_q,
                        'v': variante,
                        'p': punctaj
                    })

            if len(self.baza_date) < 40:
                messagebox.showwarning("Atenție",
                                       f"Am găsit doar {len(self.baza_date)} întrebări.")

            self.porneste_test()

        except Exception as e:
            messagebox.showerror("Eroare", f"Eroare la procesare: {e}")

    # --------------------- TEST ---------------------

    def porneste_test(self):
        random.shuffle(self.baza_date)
        self.test_curent = self.baza_date[:40]
        self.index = 0
        self.scor_total = 0
        self.afiseaza_intrebare()

    def afiseaza_intrebare(self):
        self.curata_ecran()
        q = self.test_curent[self.index]
        self.selectii_utilizator = []

        tk.Label(self.main_frame,
                 text=f"Întrebarea {self.index+1} / 40 | {q['id']} | {q['p']} pct",
                 bg="#dfe6e9",
                 font=("Segoe UI", 10)).pack(fill="x", pady=5)

        tk.Label(self.main_frame,
                 text=q['q'],
                 font=("Segoe UI", 15, "bold"),
                 wraplength=1200,
                 justify="left",
                 bg="#f4f6f9").pack(pady=20)

        self.v_frame = tk.Frame(self.main_frame, bg="#f4f6f9")
        self.v_frame.pack(fill="x", padx=50)

        self.butoane_variante = []

        for v in q['v']:
            btn = tk.Button(self.v_frame,
                            text=v['text'],
                            font=("Segoe UI", 12),
                            bg="white",
                            anchor="w",
                            justify="left",
                            wraplength=1100,
                            padx=20,
                            pady=12,
                            relief="solid",
                            bd=1)

            btn.config(command=lambda b=btn, val=v: self.toggle_select(b, val))
            btn.pack(fill="x", pady=5)
            self.butoane_variante.append((btn, v))

        self.btn_check = tk.Button(self.main_frame,
                                   text="VERIFICĂ RĂSPUNSUL",
                                   command=self.check_answer,
                                   bg="#e67e22",
                                   fg="white",
                                   font=("Segoe UI", 12, "bold"),
                                   padx=40,
                                   pady=10)

        self.btn_check.pack(pady=30)

    # --------------------- LOGICĂ ---------------------

    def toggle_select(self, btn, val):
        if btn in self.selectii_utilizator:
            self.selectii_utilizator.remove(btn)
            btn.config(bg="white")
        else:
            self.selectii_utilizator.append(btn)
            btn.config(bg="#d0e6ff")

    def check_answer(self):
        q = self.test_curent[self.index]
        self.btn_check.config(state='disabled')

        set_corecte = set(v['text'] for v in q['v'] if v['correct'])
        set_alese = set(b['text'] for b in self.selectii_utilizator)

        for btn, v in self.butoane_variante:
            btn.config(state='disabled')
            if v['correct']:
                btn.config(bg="#2ecc71", fg="white")
            elif btn in self.selectii_utilizator:
                btn.config(bg="#e74c3c", fg="white")

        if set_corecte == set_alese:
            self.scor_total += q['p']

        tk.Button(self.main_frame,
                  text="URMĂTOAREA >>",
                  command=self.next_q,
                  bg="#2c3e50",
                  fg="white",
                  font=("Segoe UI", 11, "bold"),
                  padx=30,
                  pady=8).pack(pady=20)

    def next_q(self):
        self.index += 1
        if self.index < len(self.test_curent):
            self.afiseaza_intrebare()
        else:
            self.ecran_final()

    # --------------------- FINAL + ISTORIC ---------------------

    def ecran_final(self):
        self.curata_ecran()

        scor_max = sum(q['p'] for q in self.test_curent)
        data_s = datetime.now().strftime("%d-%m-%Y %H:%M")

        rezultat = {
            "data": data_s,
            "scor": self.scor_total,
            "maxim": scor_max
        }

        self.istoric.append(rezultat)
        self.salveaza_istoric()

        tk.Label(self.main_frame,
                 text="REZULTAT FINAL",
                 font=("Segoe UI", 24, "bold"),
                 bg="#f4f6f9").pack(pady=40)

        tk.Label(self.main_frame,
                 text=f"{self.scor_total} / {scor_max} puncte",
                 font=("Segoe UI", 20),
                 bg="#f4f6f9").pack(pady=20)

        tk.Button(self.main_frame,
                  text="REVENIRE LA MENIU",
                  command=self.ecran_start,
                  bg="#1a73e8",
                  fg="white",
                  padx=30,
                  pady=12).pack(pady=40)

    def arata_statistici(self):
        self.curata_ecran()

        tk.Label(self.main_frame,
                 text="ISTORIC TESTE",
                 font=("Segoe UI", 20, "bold"),
                 bg="#f4f6f9").pack(pady=20)

        txt = scrolledtext.ScrolledText(self.main_frame,
                                        width=80,
                                        height=20,
                                        font=("Consolas", 11))
        txt.pack(pady=10)

        for r in self.istoric:
            txt.insert(tk.END,
                       f"{r['data']} | {r['scor']} / {r['maxim']} pct\n")

        tk.Button(self.main_frame,
                  text="ÎNAPOI",
                  command=self.ecran_start).pack(pady=20)

    # --------------------- ISTORIC PERSISTENT ---------------------

    def salveaza_istoric(self):
        with open("istoric_rezultate.json", "w") as f:
            json.dump(self.istoric, f)

    def incarca_istoric(self):
        if os.path.exists("istoric_rezultate.json"):
            with open("istoric_rezultate.json", "r") as f:
                return json.load(f)
        return []

    # ---------------------

    def curata_ecran(self):
        for w in self.main_frame.winfo_children():
            w.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SimulatorExamenV8(root)
    root.mainloop()
