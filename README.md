# TP1 — Criptografia Simétrica e Assimétrica

Trabalho da disciplina de Segurança de Sistemas (Escola Politécnica / PUCRS).

Demonstração de **criptografia híbrida** (o mesmo princípio usado pelo HTTPS), de um ataque
**man-in-the-middle (MITM)** e da correção desse ataque com **assinatura digital**.

## Primitivas utilizadas

| Primitiva | Tipo | Papel na demo |
|---|---|---|
| AES-256-GCM | Simétrica (cifra de bloco + modo de operação) | Cifra a mensagem |
| RSA-2048 com OAEP | Assimétrica | Cifra a chave AES (distribuição de chaves) |
| Ed25519 | Assimétrica (curvas elípticas) | Assina a chave pública do Bob |

## Arquivos

| Arquivo | O que é |
|---|---|
| `app.py` | Interface gráfica (Tkinter): desenho, painéis e botão Próximo |
| `cenarios.py` | Roteiro do protocolo: o que Alice, Bob e Mallory fazem em cada etapa |
| `crypto_core.py` | Toda a lógica criptográfica de Alice, Bob e Mallory |
| `textos.py` | Explicações de cada etapa e mensagens dos painéis (para revisar sem mexer no código) |
| `estilo.py` | Cores, fontes e estilos dos botões |

## Requisitos

- Python 3.9 ou superior, com Tkinter (já vem no Windows e no macOS; no Ubuntu/Debian: `sudo apt install python3-tk`)
- Biblioteca `cryptography`

## Instalação

```bash
git clone https://github.com/MFelisberto/T1_Seguranca.git
cd T1_Seguranca
pip install -r requirements.txt
```

## Execução

```bash
python app.py
```

1. Marque ou desmarque **Mallory no meio (MITM)** e **Assinatura digital (Ed25519)**.
2. Clique em **Conectar**: a troca de chaves é animada entre Alice, canal/Mallory e Bob.
3. Escreva uma mensagem no painel da Alice e clique em **Enviar**.
4. Com Mallory ativo, digite no painel dele um texto para trocar a próxima mensagem.
5. Sem Mallory, marque **Corromper 1 bit** para ver o AES-GCM detectando a adulteração.

Os fingerprints (resumos SHA-256 das chaves) aparecem embaixo de cada personagem: quando o
Mallory está no meio, a chave que a Alice recebeu é igual à dele, e não à do Bob.

A faixa abaixo do desenho explica cada etapa e destaca o personagem que está agindo. A demonstração
para depois de cada etapa e só continua quando você clica em **Próximo** ou aperta `→` / `Page Down`
(funciona com passador de slides). Na pausa antes do Mallory agir, dá tempo de digitar a mensagem
falsa no painel dele.

`Ctrl +` e `Ctrl -` aumentam e diminuem a fonte, útil no projetor.

## Como funciona

1. **Troca de chaves:** Bob envia sua chave pública RSA para a Alice.
2. **Envio:** Alice gera uma chave AES aleatória, cifra a mensagem com AES-GCM e cifra a chave AES
   com a chave pública RSA do Bob.
3. **Recebimento:** Bob decifra a chave AES com sua chave privada RSA e, com ela, decifra a mensagem.

**Ataque (MITM):** Mallory troca a chave pública do Bob pela dele. Alice cifra a chave AES para o
Mallory sem saber. Ele lê a mensagem, altera, recifra com a chave real do Bob e repassa.
Nenhum dos dois percebe.

**Correção (assinatura digital):** Bob assina a chave pública RSA com sua chave Ed25519. Alice já conhece
a chave de assinatura do Bob (na vida real isso é garantido por uma autoridade certificadora) e
verifica a assinatura. Como Mallory não tem a chave privada de assinatura do Bob, não consegue
forjar uma assinatura válida para a chave dele, e o ataque é detectado.

**Atacante sem a chave:** se alguém só altera bits do texto cifrado no caminho, o AES-GCM detecta,
porque a tag de autenticação deixa de conferir. Por isso o Mallory precisa ter a chave de sessão,
o que ele consegue justamente trocando a chave pública RSA.
