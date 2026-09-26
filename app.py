"""
Interface gráfica: Alice conversa com Bob usando criptografia híbrida,
com Mallory (MITM) e assinatura digital ligáveis ao vivo.

Executar:  python app.py
Atalhos:   Ctrl + / Ctrl -  aumentam/diminuem a fonte
           → ou Page Down   avançam para a próxima etapa
"""

import math
import tkinter as tk
from tkinter import ttk

import cenarios as cen
import estilo
import textos as tx
from estilo import (AMARELO, APAGADO, AZUL, BG, BORDA, CINZA, CORES, NOMES_COR, PAINEL,
                    ROXO, TEXTO, VERDE, VERMELHO)

# Velocidade da animacao do voo de pacotes
VOO_MS = 1500

class App:
    def __init__(self, root: tk.Tk):

        self.root = root
        root.title("TP1 — Criptografia Híbrida: AES + RSA + Ed25519")
        root.configure(bg=BG)
        root.geometry("1320x820")
        root.minsize(1100, 700)

        self.var_mitm = tk.BooleanVar(value=False)
        self.var_assinar = tk.BooleanVar(value=False)
        self.var_corromper = tk.BooleanVar(value=False)

        self.sessao = None      # cenarios.Sessao da conexão atual
        self.ocupado = False
        self.ativo = None       # personagem em destaque na etapa atual
        self.aguardando = None  # etapa seguinte, esperando o clique em Próximo
        self.ultimo = False
        self.painel = {}
        self.status_txt = tx.STATUS["inicio"]
        self.status_cor = CINZA
        self.linha_cor = BORDA

        self.f = estilo.criar_fontes()
        estilo.aplicar(self.f)
        self._topo()
        self._canvas()
        self._explicacao()
        self._paineis()

        self.var_mitm.trace_add("write", lambda *_: self._config_mudou())
        self.var_assinar.trace_add("write", lambda *_: self._config_mudou())
        root.bind("<Control-plus>", lambda e: self._zoom(1))
        root.bind("<Control-equal>", lambda e: self._zoom(1))
        root.bind("<Control-minus>", lambda e: self._zoom(-1))
        root.bind("<Right>", self._avancar)
        root.bind("<Next>", self._avancar)  # Page Down (passadores de slide)

        self._atualizar_modo()
        self._habilitar()

    # ------------------------------------------------------------------ visual

    def _zoom(self, passo):
        for fonte in self.f.values():
            fonte.configure(size=max(7, fonte.cget("size") + passo))
        self._redesenhar()

    def _topo(self):
        topo = tk.Frame(self.root, bg=BG)
        topo.pack(fill="x", padx=16, pady=(12, 4))
        tk.Label(topo, text="Criptografia Híbrida", font=self.f["titulo"], bg=BG, fg=TEXTO).pack(side="left")

        self.btn_reiniciar = ttk.Button(topo, text="Limpar", style="Sec.TButton", command=self._limpar)
        self.btn_reiniciar.pack(side="right", padx=(8, 0))
        self.btn_conectar = ttk.Button(topo, text="Conectar", style="Acao.TButton", command=self.conectar)
        self.btn_conectar.pack(side="right", padx=(8, 0))
        self.chk_assinar = ttk.Checkbutton(topo, text="Assinatura digital (Ed25519)", variable=self.var_assinar)
        self.chk_assinar.pack(side="right", padx=12)
        self.chk_mitm = ttk.Checkbutton(topo, text="Mallory no meio (MITM)", variable=self.var_mitm)
        self.chk_mitm.pack(side="right", padx=12)

    def _canvas(self):
        self.cv = tk.Canvas(self.root, height=220, bg=BG, highlightthickness=0)
        self.cv.pack(fill="x", padx=16)
        self.cv.bind("<Configure>", lambda e: self._redesenhar())

    def _pos(self):
        w = max(self.cv.winfo_width(), 600)
        return {"alice": w * 0.12, "meio": w * 0.5, "bob": w * 0.88, "y": 115}

    def _redesenhar(self):
        cv, p = self.cv, self._pos()
        cv.delete("fixo")
        y, r = p["y"], 46
        cv.create_text(p["meio"], 24, text=self.status_txt, fill=self.status_cor,
                       font=self.f["status"], tags="fixo")
        cv.create_line(p["alice"], y, p["bob"], y, fill=self.linha_cor, width=4, tags="fixo")

        fp = self.sessao.fp if self.sessao else {}

        def no(chave, nome, cor, papel):
            x = p[chave]
            if self.ativo == chave:
                h = r + 9
                cv.create_oval(x - h, y - h, x + h, y + h, outline=cor, width=2, dash=(5, 3), tags="fixo")
            cv.create_oval(x - r, y - r, x + r, y + r, fill=PAINEL, outline=cor,
                           width=6 if self.ativo == chave else 3, tags="fixo")
            cv.create_text(x, y, text=nome, fill=cor, font=self.f["no"], tags="fixo")
            cv.create_text(x, y + r + 16, text=papel, fill=CINZA, font=self.f["normal"], tags="fixo")
            if fp.get(chave):
                cv.create_text(x, y + r + 36, text=fp[chave], fill=AMARELO,
                               font=self.f["mono"], tags="fixo")

        no("alice", "ALICE", AZUL, "chave RSA que recebi:")
        no("bob", "BOB", VERDE, "minha chave RSA:")
        if self.var_mitm.get():
            no("meio", "MALLORY", VERMELHO, "chave RSA dele:")
        else:
            x = p["meio"]
            ativo = self.ativo == "meio"
            cv.create_rectangle(x - 60, y - 20, x + 60, y + 20, fill=BG, outline=CINZA if ativo else BORDA,
                                width=4 if ativo else 2, dash=(4, 3), tags="fixo")
            cv.create_text(x, y, text="Internet", fill=CINZA, font=self.f["negrito"], tags="fixo")
        cv.tag_raise("pacote")

    def _status(self, texto, cor, linha=None):
        self.status_txt, self.status_cor = texto, cor
        self.linha_cor = linha or BORDA
        self._redesenhar()

    def _explicacao(self):
        """Faixa entre o desenho e os painéis: explica a etapa atual e tem o botão Próximo."""
        barra = tk.Frame(self.root, bg=PAINEL, highlightbackground=BORDA, highlightthickness=1)
        barra.pack(fill="x", padx=22, pady=(0, 6))
        self.barra_cor = tk.Frame(barra, bg=CINZA, width=6)
        self.barra_cor.pack(side="left", fill="y")

        self.btn_proximo = ttk.Button(barra, text="Próximo  ▶", style="Acao.TButton", command=self._avancar)
        self.btn_proximo.pack(side="right", padx=12, pady=10)
        self.btn_proximo.state(["disabled"])

        texto = tk.Frame(barra, bg=PAINEL)
        texto.pack(side="left", fill="both", expand=True, padx=14, pady=8)
        self.lbl_titulo = tk.Label(texto, font=self.f["negrito"], bg=PAINEL, anchor="w")
        self.lbl_titulo.pack(fill="x")
        self.lbl_exp = tk.Label(texto, font=self.f["exp"], bg=PAINEL, fg=TEXTO, justify="left",
                                anchor="nw", height=4)
        self.lbl_exp.pack(fill="x")
        texto.bind("<Configure>", lambda e: self.lbl_exp.configure(wraplength=max(200, e.width - 8)))
        self._explicar(None, *tx.INICIO)

    def _cor(self, chave):
        if chave == "meio" and not self.var_mitm.get():
            return CINZA
        return CORES.get(chave, CINZA)

    def _explicar(self, quem, titulo, texto):
        """Mostra a explicação da etapa e destaca quem está agindo."""
        cor = self._cor(quem)
        self.barra_cor.configure(bg=cor)
        self.lbl_titulo.configure(text=titulo, fg=cor if quem else TEXTO)
        self.lbl_exp.configure(text=texto)
        self._foco(quem)

    def _foco(self, quem):
        self.ativo = quem
        for chave, f in self.painel.items():
            f.configure(highlightbackground=self._cor(chave) if chave == quem else BORDA)
        self._redesenhar()

    def _paineis(self):
        grade = tk.Frame(self.root, bg=BG)
        grade.pack(fill="both", expand=True, padx=16, pady=(4, 14))
        for i in range(3):
            grade.columnconfigure(i, weight=1, uniform="col")
        grade.rowconfigure(0, weight=1)

        self.txt = {}
        self.cab = {}
        self.sub = {}
        rodapes = {}
        for i, (chave, nome, sub) in enumerate([
            ("alice", "ALICE", "remetente"),
            ("meio", "CANAL", "o que trafega na rede"),
            ("bob", "BOB", "destinatário"),
        ]):
            f = tk.Frame(grade, bg=PAINEL, highlightbackground=BORDA, highlightthickness=2)
            f.grid(row=0, column=i, sticky="nsew", padx=6)
            self.painel[chave] = f
            cab = tk.Frame(f, bg=PAINEL)
            cab.pack(fill="x", padx=12, pady=(10, 4))
            self.cab[chave] = tk.Label(cab, text=nome, font=self.f["titulo"], bg=PAINEL, fg=CORES[chave])
            self.cab[chave].pack(side="left")
            self.sub[chave] = tk.Label(cab, text="  " + sub, font=self.f["normal"], bg=PAINEL, fg=CINZA)
            self.sub[chave].pack(side="left")

            rodape = tk.Frame(f, bg=PAINEL)
            rodape.pack(fill="x", side="bottom", padx=12, pady=10)
            rodapes[chave] = rodape

            corpo = tk.Frame(f, bg=PAINEL)
            corpo.pack(fill="both", expand=True, padx=(12, 4))
            t = tk.Text(corpo, bg=PAINEL, fg=TEXTO, font=self.f["normal"], wrap="word",
                        relief="flat", highlightthickness=0, padx=4, pady=4, cursor="arrow")
            sb = ttk.Scrollbar(corpo, orient="vertical", command=t.yview)
            t.configure(yscrollcommand=sb.set, state="disabled")
            sb.pack(side="right", fill="y")
            t.pack(side="left", fill="both", expand=True)
            t.tag_configure("titulo", font=self.f["negrito"], foreground=TEXTO, spacing1=10)
            t.tag_configure("info", foreground=CINZA)
            t.tag_configure("hex", font=self.f["mono"], foreground=ROXO, lmargin1=14, lmargin2=14)
            t.tag_configure("ok", font=self.f["negrito"], foreground=VERDE, spacing1=4)
            t.tag_configure("erro", font=self.f["negrito"], foreground=VERMELHO, spacing1=4)
            t.tag_configure("alerta", font=self.f["negrito"], foreground=AMARELO, spacing1=4)
            t.tag_configure("msg", font=self.f["msg"], foreground=TEXTO, spacing1=6, spacing3=4)
            self.txt[chave] = t

        # Rodapé da Alice: campo de mensagem
        r = rodapes["alice"]
        self.ent_msg = ttk.Entry(r, font=self.f["normal"])
        self.ent_msg.insert(0, "Transfira R$ 100 para a conta 1234")
        self.ent_msg.pack(side="left", fill="x", expand=True)
        self.ent_msg.bind("<Return>", lambda e: self.enviar())
        self.btn_enviar = ttk.Button(r, text="Enviar", style="Acao.TButton", command=self.enviar)
        self.btn_enviar.pack(side="left", padx=(8, 0))

        # Rodapé do meio: muda conforme o modo
        r = rodapes["meio"]
        self.rod_mallory = tk.Frame(r, bg=PAINEL)
        tk.Label(self.rod_mallory, text="Trocar a próxima mensagem por (opcional):",
                 font=self.f["normal"], bg=PAINEL, fg=CINZA).pack(anchor="w")
        self.ent_mallory = ttk.Entry(self.rod_mallory, font=self.f["normal"])
        self.ent_mallory.pack(fill="x", pady=(4, 0))
        self.rod_canal = tk.Frame(r, bg=PAINEL)
        self.chk_corromper = ttk.Checkbutton(
            self.rod_canal, style="Painel.TCheckbutton", variable=self.var_corromper,
            text="Corromper 1 bit da próxima mensagem\n(atacante SEM a chave)")
        self.chk_corromper.pack(anchor="w")

        # Rodapé do Bob: só informativo
        tk.Label(rodapes["bob"], text="Mensagens decifradas aparecem acima.",
                 font=self.f["normal"], bg=PAINEL, fg=APAGADO).pack(anchor="w", pady=6)

    # ------------------------------------------------------------------ utilidades

    def log(self, painel, texto, tag="info"):
        t = self.txt[painel]
        t.configure(state="normal")
        t.insert("end", texto + "\n", tag)
        t.configure(state="disabled")
        t.see("end")

    def _limpar_logs(self):
        for t in self.txt.values():
            t.configure(state="normal")
            t.delete("1.0", "end")
            t.configure(state="disabled")

    def _limpar(self):
        self.sessao = None
        self._limpar_logs()
        self._status(tx.STATUS["inicio"], CINZA)
        self._explicar(None, *tx.INICIO)
        self._habilitar()

    def _habilitar(self):
        livre = not self.ocupado
        for w in (self.chk_mitm, self.chk_assinar, self.btn_conectar, self.btn_reiniciar):
            w.state(["!disabled"] if livre else ["disabled"])
        pode_enviar = livre and self._conectado()
        for w in (self.ent_msg, self.btn_enviar):
            w.state(["!disabled"] if pode_enviar else ["disabled"])

    def _conectado(self):
        return self.sessao is not None and self.sessao.conectada

    def _atualizar_modo(self):
        if self.var_mitm.get():
            self.cab["meio"].configure(text="MALLORY", fg=VERMELHO)
            self.sub["meio"].configure(text="  atacante no meio")
            self.rod_canal.pack_forget()
            self.rod_mallory.pack(fill="x")
        else:
            self.cab["meio"].configure(text="CANAL", fg=CINZA)
            self.sub["meio"].configure(text="  o que qualquer um vê na rede")
            self.rod_mallory.pack_forget()
            self.rod_canal.pack(fill="x")
        self._redesenhar()

    def _config_mudou(self):
        self._atualizar_modo()
        if self._conectado():
            self.sessao.conectada = False
            self._status(tx.STATUS["config"], AMARELO)
            self._habilitar()

    # ------------------------------------------------------------------ animação

    def _executar(self, roteiro):
        """Toca um roteiro de cenarios.py: cada Voo anima um pacote e cada Etapa
        mostra seus textos e espera o Próximo."""
        passos = [self._voo(p) if isinstance(p, cen.Voo) else self._etapa(p.fazer) for p in roteiro]
        self.ocupado = True
        self._habilitar()

        def fim():
            self.ocupado = False
            self.aguardando = None
            self.btn_proximo.state(["disabled"])
            self._foco(None)
            self._habilitar()

        def rodar(i):
            self.ultimo = i == len(passos) - 1
            if i < len(passos):
                passos[i](lambda: rodar(i + 1), fim)
            else:
                fim()
        rodar(0)

    def _etapa(self, fn):
        """Etapa parada: fn faz a parte criptográfica e devolve quais etapas de
        textos.ETAPAS mostrar. Se a lista terminar em PARAR, a sequência acaba ali."""
        def passo(prox, fim):
            chaves = fn()
            parar = chaves[-1] is cen.PARAR
            self._mostrar([c for c in chaves if c is not cen.PARAR])
            if parar:
                fim()
            else:
                self._pausa(prox)
        return passo

    def _mostrar(self, chaves):
        """Escreve nos painéis e explica. Várias etapas juntas viram uma só:
        as linhas e os textos se somam, e vale o último quem/título/status."""
        quem = titulo = status = None
        partes = []
        for chave in chaves:
            e = tx.ETAPAS[chave]
            for painel, tag, modelo in e.get("painel", []):
                self.log(painel, modelo.format(**self.sessao.valores), tag)
            quem, titulo, status = e.get("quem", quem), e.get("titulo", titulo), e.get("status", status)
            if "texto" in e:
                partes.append(e["texto"])
        if status:
            texto, cor, *linha = status
            self._status(texto, NOMES_COR[cor], NOMES_COR[linha[0]] if linha else None)
        if titulo:
            self._explicar(quem, titulo, " ".join(partes))

    def _pausa(self, prox):
        """Espera o clique em Próximo para seguir para a etapa seguinte."""
        if self.ultimo:
            prox()
        else:
            self.aguardando = prox
            self.btn_proximo.state(["!disabled"])

    def _avancar(self, *_):
        if self.aguardando:
            prox, self.aguardando = self.aguardando, None
            self.btn_proximo.state(["disabled"])
            prox()

    def _voo(self, voo):
        """Anima o pacote atravessando o canal. Vermelho quando sai do Mallory."""
        rotulo = tx.PACOTES[voo.pacote]
        cor = VERMELHO if self.sessao.mitm and voo.de == "meio" else AMARELO

        def passo(prox, fim):
            p = self._pos()
            x0, x1, y = p[voo.de], p[voo.para], p["y"]
            larg = self.f["negrito"].measure(rotulo) + 24
            alt = self.f["negrito"].metrics("linespace") + 12
            caixa = self.cv.create_rectangle(0, 0, 0, 0, fill=BG, outline=cor, width=2, tags="pacote")
            texto = self.cv.create_text(0, 0, text=rotulo, fill=cor, font=self.f["negrito"], tags="pacote")
            n = VOO_MS // 18

            def quadro(i):
                t = i / n
                t = t * t * (3 - 2 * t)  # suavização
                x = x0 + (x1 - x0) * t
                yy = y - 58 - 10 * math.sin(math.pi * t)
                self.cv.coords(caixa, x - larg / 2, yy - alt / 2, x + larg / 2, yy + alt / 2)
                self.cv.coords(texto, x, yy)
                if i < n:
                    self.root.after(18, quadro, i + 1)
                else:
                    self.cv.delete(caixa, texto)
                    prox()
            quadro(0)
        return passo

    # ------------------------------------------------------------------ ações

    def conectar(self):
        self._limpar_logs()
        self.sessao = None
        self._status(tx.STATUS["gerando"], CINZA)
        self.root.update_idletasks()
        self.sessao = cen.Sessao(self.var_mitm.get(), self.var_assinar.get())
        self._executar(self.sessao.conectar())

    def enviar(self):
        if self.ocupado or not self._conectado():
            return
        texto = self.ent_msg.get().strip()
        if texto:
            self._executar(self.sessao.enviar(texto, self._troca_do_mallory, self._corromper))

    def _troca_do_mallory(self):
        """Texto digitado no painel do Mallory; o campo é esvaziado depois de usado."""
        nova = self.ent_mallory.get().strip()
        self.ent_mallory.delete(0, "end")
        return nova

    def _corromper(self):
        """Se a caixa Corromper 1 bit está marcada; ela vale só para uma mensagem."""
        marcado = self.var_corromper.get()
        self.var_corromper.set(False)
        return marcado


def main():
    try:  # nitidez em telas de alta resolução no Windows
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
