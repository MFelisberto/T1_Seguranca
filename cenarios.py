"""
Roteiro da demonstração (sem interface).

Uma Sessao representa uma conexão entre Alice e Bob, com ou sem Mallory no meio
e com ou sem assinatura digital. conectar() e enviar() devolvem a sequência de
passos que a interface "toca" em ordem:

  Voo(de, para, pacote)  -> um pacote atravessa o canal (só animação)
  Etapa(fazer)           -> fazer() executa a criptografia daquele momento e devolve
                            os nomes das etapas de textos.ETAPAS a mostrar

Os valores exibidos nos textos (fingerprints, hex, mensagens) ficam em sessao.valores.
"""

from collections import namedtuple

import crypto_core as cc

Voo = namedtuple("Voo", "de para pacote")
Etapa = namedtuple("Etapa", "fazer")

PARAR = object()  # no fim da lista de uma Etapa: a sequência acaba ali


class Sessao:
    def __init__(self, mitm: bool, assinar: bool):
        self.mitm, self.assinar = mitm, assinar
        self.bob = cc.Bob()
        self.alice = cc.Alice(self.bob.assin_publica)
        self.mallory = cc.Mallory() if mitm else None
        self.conectada = False
        self.fp = {"alice": "", "bob": "", "meio": ""}  # fingerprints mostrados no desenho
        self.valores = {}                               # campos {…} dos textos

    def conectar(self):
        """Troca de chaves (RSA, opcionalmente assinada) e envio da chave de sessão AES."""
        estado = {}  # bytes que trafegam no canal
        v = self.valores = {}

        def bob_publica():
            estado["pem"], estado["assinatura"] = self.bob.publicar_chave(self.assinar)
            self.fp["bob"] = v["fp_bob"] = cc.fingerprint(self.bob.pem)
            if not self.assinar:
                return ["bob_gera", "bob_envia"]
            v["assinatura"] = cc.hexcurto(estado["assinatura"])
            v["fp_assin_bob"] = cc.fingerprint(cc.para_pem(self.bob.assin_publica))
            return ["bob_gera", "bob_assina", "bob_envia"]

        def meio_chave():
            if not self.mallory:
                return ["canal_chave"]
            estado["pem"], estado["assinatura"] = self.mallory.trocar_chave(estado["pem"], estado["assinatura"])
            self.fp["meio"] = v["fp_mallory"] = cc.fingerprint(self.mallory.pem)
            return ["mallory_troca_chave"] + (["mallory_sem_assinatura"] if self.assinar else [])

        def alice_recebe():
            self.fp["alice"] = v["fp_recebida"] = cc.fingerprint(estado["pem"])
            if not self.assinar:
                resultado = "alice_sem_verificacao"
            elif self.alice.verificar_chave(estado["pem"], estado["assinatura"]):
                resultado = "alice_assinatura_ok"
            else:
                return ["alice_recebe", "alice_assinatura_invalida", PARAR]
            self.alice.aceitar_chave(estado["pem"])
            return ["alice_recebe", resultado]

        def alice_sessao():
            chave, estado["cifrada"] = self.alice.criar_sessao()
            v["chave"], v["chave_cifrada"] = cc.hexcurto(chave), cc.hexcurto(estado["cifrada"])
            return ["alice_cria_sessao"]

        def meio_sessao():
            if not self.mallory:
                return ["canal_sessao"]
            chave, estado["cifrada"] = self.mallory.interceptar_chave_sessao(estado["cifrada"])
            v["chave"] = cc.hexcurto(chave)
            return ["mallory_abre_sessao"]

        def bob_sessao():
            v["chave"] = cc.hexcurto(self.bob.receber_chave_sessao(estado["cifrada"]))
            self.conectada = True
            return ["bob_abre_sessao", "sessao_espionada" if self.mallory else "sessao_ok"]

        pacote = "chave_assinada" if self.assinar else "chave"
        return [
            Etapa(bob_publica),
            Voo("bob", "meio", pacote),
            Etapa(meio_chave),
            Voo("meio", "alice", pacote),
            Etapa(alice_recebe),
            Etapa(alice_sessao),
            Voo("alice", "meio", "sessao"),
            Etapa(meio_sessao),
            Voo("meio", "bob", "sessao"),
            Etapa(bob_sessao),
        ]

    def enviar(self, texto: str, troca_do_mallory, corromper):
        """Alice manda uma mensagem cifrada com AES-GCM.

        troca_do_mallory() e corromper() são perguntados na hora em que a mensagem
        passa pelo meio: o texto que o Mallory quer pôr no lugar (ou "") e se um
        bit deve ser invertido no caminho."""
        estado = {}
        v = self.valores = {"texto": texto}

        def alice_cifra():
            estado["nonce"], estado["cifrada"] = self.alice.cifrar(texto)
            v["cifrada"] = cc.hexcurto(estado["cifrada"], 20)
            return ["alice_cifra"]

        def meio_msg():
            if self.mallory:
                nova = troca_do_mallory()
                v["lida"], estado["nonce"], estado["cifrada"] = self.mallory.interceptar_mensagem(
                    estado["nonce"], estado["cifrada"], nova)
                if not nova:
                    return ["mallory_le", "mallory_repassa"]
                v["nova"] = nova
                return ["mallory_le", "mallory_troca_msg"]
            if not corromper():
                return ["canal_msg"]
            estado["cifrada"] = cc.adulterar_as_cegas(estado["cifrada"])
            v["cifrada_alterada"] = cc.hexcurto(estado["cifrada"], 20)
            return ["canal_msg", "canal_corrompe"]

        def bob_msg():
            try:
                v["recebida"] = self.bob.receber_mensagem(estado["nonce"], estado["cifrada"])
            except cc.InvalidTag:
                return ["bob_msg_adulterada"]
            if not self.mallory:
                return ["bob_decifra", "bob_msg_ok"]
            return ["bob_decifra", "bob_msg_do_mallory" if v["recebida"] != texto else "bob_msg_espionada"]

        return [
            Etapa(alice_cifra),
            Voo("alice", "meio", "mensagem"),
            Etapa(meio_msg),
            Voo("meio", "bob", "mensagem"),
            Etapa(bob_msg),
        ]
