"""
Núcleo criptográfico do TP1 (sem interface).

Primitivas:
  - AES-256-GCM   (simétrica, cifra de bloco + modo autenticado) -> cifra as mensagens
  - RSA-2048 OAEP (assimétrica)                                -> cifra a chave de sessão AES
  - Ed25519       (assimétrica, curvas elípticas)              -> assina a chave pública RSA do Bob

Tudo que passa pelo "canal" são bytes, como numa rede de verdade.
"""

import os

from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

OAEP = padding.OAEP(
    mgf=padding.MGF1(algorithm=hashes.SHA256()),
    algorithm=hashes.SHA256(),
    label=None,
)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def para_pem(chave_publica) -> bytes:
    return chave_publica.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def de_pem(dados: bytes):
    return serialization.load_pem_public_key(dados)


def fingerprint(pem: bytes) -> str:
    """Resumo SHA-256 da chave pública, formatado para comparação visual."""
    d = hashes.Hash(hashes.SHA256())
    d.update(pem)
    h = d.finalize().hex()[:16].upper()
    return ":".join(h[i:i + 4] for i in range(0, 16, 4))


def hexcurto(dados: bytes, n: int = 12) -> str:
    h = dados.hex()
    return h[: n * 2] + ("…" if len(h) > n * 2 else "")


def gerar_rsa():
    privada = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return privada, privada.public_key()


# ---------------------------------------------------------------------------
# Personagens
# ---------------------------------------------------------------------------

class Bob:
    def __init__(self):
        self.rsa_privada, self.rsa_publica = gerar_rsa()
        self.pem = para_pem(self.rsa_publica)
        # Identidade de longo prazo do Bob (curvas elípticas)
        self.assin_privada = ed25519.Ed25519PrivateKey.generate()
        self.assin_publica = self.assin_privada.public_key()
        self.chave_sessao = None

    def publicar_chave(self, assinar: bool):
        """Retorna (pem da chave RSA, assinatura Ed25519 ou None)."""
        assinatura = self.assin_privada.sign(self.pem) if assinar else None
        return self.pem, assinatura

    def receber_chave_sessao(self, chave_cifrada: bytes) -> bytes:
        self.chave_sessao = self.rsa_privada.decrypt(chave_cifrada, OAEP)
        return self.chave_sessao

    def receber_mensagem(self, nonce: bytes, cifrada: bytes) -> str:
        return AESGCM(self.chave_sessao).decrypt(nonce, cifrada, None).decode()


class Alice:
    def __init__(self, assin_publica_do_bob):
        # Suposição: Alice já conhece a chave de assinatura do Bob
        # (na vida real, garantida por uma autoridade certificadora).
        self.assin_publica_do_bob = assin_publica_do_bob
        self.rsa_do_bob = None
        self.chave_sessao = None

    def verificar_chave(self, pem: bytes, assinatura) -> bool:
        try:
            self.assin_publica_do_bob.verify(assinatura or b"", pem)
            return True
        except InvalidSignature:
            return False

    def aceitar_chave(self, pem: bytes) -> None:
        self.rsa_do_bob = de_pem(pem)

    def criar_sessao(self):
        """Gera a chave AES da sessão e a cifra com a chave RSA recebida."""
        self.chave_sessao = AESGCM.generate_key(bit_length=256)
        return self.chave_sessao, self.rsa_do_bob.encrypt(self.chave_sessao, OAEP)

    def cifrar(self, mensagem: str):
        nonce = os.urandom(12)
        return nonce, AESGCM(self.chave_sessao).encrypt(nonce, mensagem.encode(), None)


class Mallory:
    def __init__(self):
        self.rsa_privada, self.rsa_publica = gerar_rsa()
        self.pem = para_pem(self.rsa_publica)
        self.rsa_do_bob = None
        self.chave_sessao = None

    def trocar_chave(self, pem_do_bob: bytes, assinatura):
        """Guarda a chave do Bob e entrega a própria no lugar.
        Não tem como assinar pelo Bob, então só repassa a assinatura original."""
        self.rsa_do_bob = de_pem(pem_do_bob)
        return self.pem, assinatura

    def interceptar_chave_sessao(self, chave_cifrada: bytes):
        """Abre a chave de sessão (foi cifrada para ele) e recifra para o Bob."""
        self.chave_sessao = self.rsa_privada.decrypt(chave_cifrada, OAEP)
        return self.chave_sessao, self.rsa_do_bob.encrypt(self.chave_sessao, OAEP)

    def interceptar_mensagem(self, nonce: bytes, cifrada: bytes, nova: str = ""):
        """Lê a mensagem e, se 'nova' for informada, troca o conteúdo."""
        lida = AESGCM(self.chave_sessao).decrypt(nonce, cifrada, None).decode()
        if not nova:
            return lida, nonce, cifrada
        nonce2 = os.urandom(12)
        return lida, nonce2, AESGCM(self.chave_sessao).encrypt(nonce2, nova.encode(), None)


def adulterar_as_cegas(cifrada: bytes) -> bytes:
    """Inverte um bit do texto cifrado, como faria um atacante SEM a chave."""
    b = bytearray(cifrada)
    b[0] ^= 0x01
    return bytes(b)


__all__ = [
    "Alice", "Bob", "Mallory", "fingerprint", "hexcurto",
    "adulterar_as_cegas", "InvalidTag",
]
