"""
Textos da demonstração (sem lógica).

Cada etapa em ETAPAS pode ter:
  quem    -> personagem em destaque: "alice", "meio" (canal/Mallory) ou "bob"
  status  -> (texto, cor) ou (texto, cor, cor da linha) mostrado no topo do desenho
  titulo  -> título da explicação
  texto   -> explicação; quando o app mostra várias etapas juntas, os textos são emendados
  painel  -> linhas (painel, estilo, texto) escritas nos painéis de Alice, canal e Bob

Estilos das linhas: titulo, info, hex, ok, erro, alerta, msg.
Os campos entre chaves, como {fp_bob}, são preenchidos pelo app com os valores da execução.
"""

INICIO = (
    "Como usar",
    "Escolha o cenário no topo e clique em Conectar. Cada etapa é explicada aqui, e a "
    "demonstração só segue quando você clica em Próximo (ou aperta → / Page Down).",
)

STATUS = {
    "inicio": "Clique em Conectar para iniciar a troca de chaves",
    "gerando": "Gerando chaves…",
    "config": "Configuração alterada: clique em Conectar de novo",
}

# Rótulos dos pacotes que voam entre os personagens
PACOTES = {
    "chave": "chave pública RSA",
    "chave_assinada": "chave pública RSA + assinatura",
    "sessao": "chave AES cifrada com RSA",
    "mensagem": "mensagem cifrada (AES)",
}

ETAPAS = {
    # ------------------------------------------------------------ 1) troca de chaves
    "bob_gera": {
        "quem": "bob",
        "status": ("1) Troca de chaves (assimétrica)", "texto"),
        "titulo": "Bob gera o par de chaves RSA e publica a chave pública",
        "texto": "A chave pública pode ser entregue a qualquer um; a privada nunca sai do computador "
                 "do Bob. O que for cifrado com a pública só pode ser aberto com a privada.",
        "painel": [
            ("bob", "titulo", "Troca de chaves"),
            ("bob", "info", "Gerei meu par de chaves RSA-2048."),
            ("bob", "hex", "Fingerprint: {fp_bob}"),
        ],
    },
    "bob_assina": {
        "texto": "Ele também assina a chave pública com sua chave Ed25519, como um selo de autenticidade.",
        "painel": [
            ("bob", "info", "Assinei minha chave pública com minha chave Ed25519:"),
            ("bob", "hex", "{assinatura}"),
            ("alice", "titulo", "Chave de assinatura do Bob (já confio nela)"),
            ("alice", "hex", "{fp_assin_bob}"),
            ("alice", "info", "Na vida real: garantida por uma autoridade certificadora."),
        ],
    },
    "bob_envia": {
        "painel": [("bob", "info", "Enviando minha chave pública para a Alice…")],
    },
    "canal_chave": {
        "quem": "meio",
        "titulo": "A chave pública atravessa a rede",
        "texto": "Qualquer um no caminho pode ver essa chave, e não tem problema: ela só serve para "
                 "cifrar, não para decifrar.",
        "painel": [
            ("meio", "titulo", "Chave pública passando"),
            ("meio", "info", "É pública: qualquer um pode ver, e tudo bem."),
            ("meio", "hex", "{fp_bob}"),
        ],
    },
    "mallory_troca_chave": {
        "quem": "meio",
        "titulo": "Mallory troca a chave do Bob pela dele",
        "texto": "Ele está no caminho: guarda a chave do Bob e entrega a própria chave pública à Alice "
                 "como se fosse do Bob. Compare os fingerprints: o que a Alice receber vai ser igual "
                 "ao do Mallory.",
        "painel": [
            ("meio", "erro", "Interceptei a chave do Bob!"),
            ("meio", "info", "Guardei a dele e mandei a MINHA no lugar:"),
            ("meio", "hex", "{fp_mallory}"),
        ],
    },
    "mallory_sem_assinatura": {
        "texto": "Mas ele não tem a chave privada de assinatura do Bob, então não consegue assinar a "
                 "chave falsa.",
        "painel": [
            ("meio", "info", "Não consigo assinar como o Bob… vou repassar a assinatura dele e torcer."),
        ],
    },
    "alice_recebe": {
        "painel": [
            ("alice", "titulo", "Chave recebida"),
            ("alice", "hex", "Fingerprint: {fp_recebida}"),
        ],
    },
    "alice_sem_verificacao": {
        "quem": "alice",
        "titulo": "Alice recebe a chave, mas não sabe de quem ela é",
        "texto": "Nada prova que essa chave é do Bob, então ela simplesmente confia. É exatamente "
                 "essa brecha que o ataque man-in-the-middle explora.",
        "painel": [("alice", "alerta", "Não tenho como verificar de quem é… vou confiar.")],
    },
    "alice_assinatura_ok": {
        "quem": "alice",
        "titulo": "Alice verifica a assinatura",
        "texto": "Ela usa a chave Ed25519 do Bob, que já conhecia antes (na vida real, garantida por "
                 "uma autoridade certificadora). A assinatura confere: a chave veio mesmo do Bob e não "
                 "foi trocada no caminho.",
        "painel": [("alice", "ok", "✔ Assinatura válida: a chave é mesmo do Bob.")],
    },
    "alice_assinatura_invalida": {
        "quem": "alice",
        "status": ("✖ Conexão recusada: a assinatura não confere (ataque detectado)", "vermelho", "vermelho"),
        "titulo": "Alice verifica a assinatura… e ela não confere",
        "texto": "A assinatura foi feita pelo Bob sobre a chave DELE, não sobre a chave do Mallory. "
                 "A Alice recusa a conexão: o ataque foi detectado antes de qualquer segredo ser enviado.",
        "painel": [
            ("alice", "erro", "✖ ASSINATURA INVÁLIDA! Essa chave não é do Bob."),
            ("alice", "erro", "Conexão recusada."),
            ("meio", "alerta", "✖ A Alice detectou a troca. Ataque falhou."),
        ],
    },

    # ------------------------------------------------------------ 2) chave de sessão
    "alice_cria_sessao": {
        "quem": "alice",
        "status": ("2) Envio da chave de sessão AES", "texto"),
        "titulo": "Alice cria a chave de sessão AES e a cifra com RSA",
        "texto": "Por que não cifrar tudo com RSA? Porque ele é lento e só cifra poucos bytes. A Alice "
                 "gera uma chave AES aleatória (simétrica e rápida) e usa o RSA só para entregá-la. "
                 "Isso é criptografia híbrida, a mesma ideia do HTTPS.",
        "painel": [
            ("alice", "titulo", "Chave de sessão"),
            ("alice", "info", "Gerei uma chave AES-256 aleatória:"),
            ("alice", "hex", "{chave}"),
            ("alice", "info", "Cifrei com a chave RSA recebida (OAEP):"),
            ("alice", "hex", "{chave_cifrada}"),
        ],
    },
    "canal_sessao": {
        "quem": "meio",
        "titulo": "A chave de sessão atravessa a rede",
        "texto": "Quem olha a rede vê só bytes embaralhados. Para abrir, seria preciso a chave privada "
                 "RSA do Bob, que nunca saiu do computador dele.",
        "painel": [
            ("meio", "titulo", "Chave de sessão passando"),
            ("meio", "info", "Só dá para abrir com a chave privada do Bob:"),
            ("meio", "hex", "{chave_cifrada}"),
        ],
    },
    "mallory_abre_sessao": {
        "quem": "meio",
        "titulo": "Mallory abre a chave de sessão",
        "texto": "A Alice cifrou a chave AES com a chave pública do Mallory, então ele abre com a privada "
                 "dele. Depois cifra de novo com a chave verdadeira do Bob, para ninguém desconfiar.",
        "painel": [
            ("meio", "titulo", "Chave de sessão"),
            ("meio", "erro", "Foi cifrada com a MINHA chave, então eu abro:"),
            ("meio", "hex", "{chave}"),
            ("meio", "info", "Recifrei com a chave real do Bob e repassei."),
        ],
    },
    "bob_abre_sessao": {
        "painel": [
            ("bob", "titulo", "Chave de sessão"),
            ("bob", "info", "Abri com minha chave privada RSA:"),
            ("bob", "hex", "{chave}"),
            ("bob", "ok", "✔ Sessão estabelecida."),
            ("alice", "ok", "✔ Sessão estabelecida. Pode escrever!"),
        ],
    },
    "sessao_ok": {
        "quem": "bob",
        "status": ("● Sessão cifrada estabelecida (AES-256-GCM)", "verde", "verde"),
        "titulo": "Bob abre a chave de sessão com a chave privada dele",
        "texto": "Agora só Alice e Bob têm a chave de sessão. Daqui em diante toda mensagem é cifrada "
                 "com AES. Escreva uma mensagem no painel da Alice.",
    },
    "sessao_espionada": {
        "quem": "bob",
        "status": ("● Conectado… mas o Mallory tem a chave da sessão", "amarelo", "verde"),
        "titulo": "Bob abre a chave de sessão… e tudo parece normal",
        "texto": "Para o Bob nada mudou. Mas agora três pessoas têm a mesma chave de sessão: Alice, Bob "
                 "e Mallory. Escreva uma mensagem para ver o que acontece.",
    },

    # ------------------------------------------------------------ 3) mensagens
    "alice_cifra": {
        "quem": "alice",
        "titulo": "Alice cifra a mensagem com AES-256-GCM",
        "texto": "Ela usa a chave de sessão. O modo GCM também gera uma tag de autenticação: se um único "
                 "bit for alterado no caminho, o Bob vai perceber.",
        "painel": [
            ("alice", "titulo", "Mensagem"),
            ("alice", "msg", "“{texto}”"),
            ("alice", "info", "Cifrada com AES-256-GCM:"),
            ("alice", "hex", "{cifrada}"),
        ],
    },
    "canal_msg": {
        "quem": "meio",
        "titulo": "A mensagem cifrada atravessa a rede",
        "texto": "Sem a chave de sessão, só aparecem bytes sem sentido. É impossível ler o conteúdo.",
        "painel": [
            ("meio", "titulo", "Mensagem passando"),
            ("meio", "info", "Sem a chave, só dá para ver isto:"),
            ("meio", "hex", "{cifrada}"),
        ],
    },
    "canal_corrompe": {
        "titulo": "Alguém altera 1 bit da mensagem no caminho",
        "texto": "Mas quem não tem a chave ainda pode tentar estragar o conteúdo: aqui um único bit do "
                 "texto cifrado foi invertido.",
        "painel": [
            ("meio", "alerta", "Alguém inverteu 1 bit no caminho!"),
            ("meio", "hex", "{cifrada_alterada}"),
        ],
    },
    "mallory_le": {
        "painel": [
            ("meio", "titulo", "Mensagem interceptada"),
            ("meio", "erro", "Eu li:"),
            ("meio", "msg", "“{lida}”"),
        ],
    },
    "mallory_repassa": {
        "quem": "meio",
        "titulo": "Mallory lê a mensagem",
        "texto": "Ele tem a chave de sessão, então lê tudo e repassa sem alterar. Ninguém percebe que a "
                 "conversa foi espionada.",
        "painel": [("meio", "info", "Repassei sem alterar.")],
    },
    "mallory_troca_msg": {
        "quem": "meio",
        "titulo": "Mallory lê e troca a mensagem",
        "texto": "Ele tem a chave de sessão: decifra, troca o texto e cifra de novo. A tag do GCM fica "
                 "válida porque ele a gerou com a chave certa. Cifrar não basta se a chave pública não "
                 "for autenticada.",
        "painel": [
            ("meio", "erro", "Troquei por:"),
            ("meio", "msg", "“{nova}”"),
            ("meio", "info", "Recifrei com a chave de sessão. O GCM não percebe: eu tenho a chave."),
        ],
    },
    "bob_decifra": {
        "painel": [
            ("bob", "titulo", "Mensagem"),
            ("bob", "info", "Decifrei com AES-256-GCM:"),
            ("bob", "msg", "“{recebida}”"),
        ],
    },
    "bob_msg_ok": {
        "quem": "bob",
        "titulo": "Bob decifra a mensagem",
        "texto": "Com a mesma chave de sessão ele decifra, e a tag confere: a mensagem é da Alice e "
                 "chegou sem nenhuma alteração.",
    },
    "bob_msg_espionada": {
        "quem": "bob",
        "titulo": "Bob decifra a mensagem",
        "texto": "Ela chegou intacta e o Bob não desconfia de nada, mas o Mallory leu tudo. Ligue a "
                 "assinatura digital e conecte de novo.",
    },
    "bob_msg_do_mallory": {
        "quem": "bob",
        "titulo": "Bob decifra… a mensagem do Mallory",
        "texto": "A tag confere, então o Bob acredita no conteúdo. Mas quem escreveu foi o Mallory, não "
                 "a Alice. Ligue a assinatura digital e conecte de novo.",
    },
    "bob_msg_adulterada": {
        "quem": "bob",
        "titulo": "O GCM detecta a adulteração",
        "texto": "Ao decifrar, o GCM recalcula a tag e ela não bate com a recebida. A mensagem é "
                 "descartada: a alteração foi percebida mesmo sem o atacante saber o conteúdo.",
        "painel": [
            ("bob", "titulo", "Mensagem"),
            ("bob", "erro", "✖ O GCM detectou adulteração!"),
            ("bob", "info", "A tag de autenticação não confere. Mensagem descartada."),
        ],
    },
}
