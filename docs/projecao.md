# Projecao: Android Auto

Documento de operacao da Etapa 5. A projecao nao e desenhada pelo PiCockpit: ela
roda em outro processo, o [LIVI](https://github.com/f-io/LIVI), com janela
propria ao lado da multimidia.

**Escopo: Android Auto apenas.** O CarPlay foi avaliado e descartado - ver
[Por que sem CarPlay](#por-que-sem-carplay). A decisao nao custa nada em codigo:
se um dia entrar, entra como mais uma origem de sessao do LIVI, sem tocar na
nossa camada.

## Por que outro processo

Duas razoes independentes, e qualquer uma delas ja bastaria.

**Tecnica.** Nenhuma solucao de projecao entrega o video como item Qt que a
gente possa ancorar dentro da cena. O LIVI decodifica no decodificador de
hardware do SoC e mantem o quadro na GPU de ponta a ponta, por um pipeline
GStreamer sem copia. Trazer isso para dentro do nosso QML significaria
exatamente a copia que ele existe para evitar - em 1080p, no Pi 5, com o painel
disputando a mesma GPU.

**Licenca.** O LIVI e GPL-3.0-or-later; o PiCockpit e proprietario. Dois
programas separados, que se falam por systemd e por socket, ficam em lados
corretos dessa fronteira. Linkar ou embutir codigo dele, nao. E a mesma
preocupacao que levou o projeto ao PySide6 em vez do PyQt6.

## Pre-requisito: Trixie

O LIVI exige **OpenGL ES 3.x**. No Pi 4, Pi 5, CM4 e CM5 isso so existe a partir
do **Raspberry Pi OS Trixie (Debian 13)** - o Bookworm nao alcanca, e nao e
questao de compilar diferente. Ver [migracao-trixie.md](migracao-trixie.md).

Pi 3 e anteriores usam a VideoCore IV, que para em OpenGL ES 2.0: nao ha
caminho.

## Hardware

**Nenhum.** Um cabo USB e o telefone.

| Uso | O que precisa |
| --- | --- |
| Android Auto com fio | so o cabo |
| Android Auto sem fio | nada - o LIVI levanta o proprio ponto de acesso Wi-Fi |

O modo sem fio nao depende de roteador: o LIVI sobe o proprio ponto de acesso e
o Bluetooth carrega o pareamento e a transferencia da sessao. Um telefone ja
pareado e reconhecido sozinho depois.

Vale comecar pelo cabo mesmo assim - com fio ha menos variavel entre o telefone
e a tela, e o objetivo do primeiro teste e validar a nossa integracao, nao a
qualidade do Wi-Fi.

## Por que sem CarPlay

O CarPlay exige que o acessorio se autentique contra o iPhone com um
**coprocessador MFi** da Apple. E um chip fisico, licenciado; nao existe
software que contorne, e o LIVI nao embute nem burla. Restariam dois caminhos,
os dois pagos:

| Caminho | Custo | Por que nao |
| --- | --- | --- |
| Dongle **Carlinkit CPC200-CCPA** (com e sem fio) | ~US$ 50-60 fora, mais imposto | preco desproporcional ao uso pretendido |
| Dongle **CPC200-CCPW** (so com fio) | menor que o CCPA | mesmo motivo, em escala menor |
| Chip **MFi** avulso | baixo em tese | exige soldar no barramento I2C e achar a peca |

Decisao de agosto de 2026: **fora de escopo**. O Android Auto entrega o que se
espera da projecao sem gasto nenhum, e o bloqueio que sobra para a Etapa 5 passa
a ser apenas a migracao para o Trixie.

Se um dia mudar: comprar o dongle, pluga-lo, e pronto - o LIVI trata o
adaptador como mais uma origem de sessao. **Nenhuma linha do PiCockpit muda.**
Este documento existe para que a pesquisa nao precise ser refeita.

## Instalacao, na ordem

### 1. LIVI

Software de terceiros, com instalador proprio. Nosso repositorio nao o baixa.

O caminho abaixo mudou depois que a pesquisa original foi feita - o projeto
separou o instalador em variantes desktop/headless. `scripts/install/pi/install.sh`
(a versao antiga, documentada por um tempo no README deles) nao existe mais;
quem serve uma maquina com sessao grafica - o nosso caso - e
`scripts/install/desktop/install.sh`. Se o `curl` abaixo devolver 404 de novo,
vale conferir a arvore atual do repositorio antes de supor que e falha de rede -
foi exatamente isso que aconteceu aqui.

```bash
curl -fL -o install.sh https://raw.githubusercontent.com/f-io/LIVI/main/scripts/install/desktop/install.sh
chmod +x install.sh
LIVI_CHANNEL=release LIVI_MFI=no LIVI_SPLASH=no LIVI_HDMI_PR=no ./install.sh
```

As quatro variaveis evitam os prompts interativos do instalador e travam nas
escolhas que ja fizemos: `release` (nao nightly), sem I2C para coprocessador
MFi (sem CarPlay, ver [Por que sem CarPlay](#por-que-sem-carplay)), sem splash
de boot (cosmetico, fora de escopo) e sem a reconstrucao do driver `vc4` para
pixel-repetition (isso e para paineis RGB/VGA abaixo do piso de clock do HDMI -
as nossas duas telas sao HDMI padrao, entrar nesse fluxo so arriscaria a
configuracao de video que o `apply_display_modes.sh` ja cuida). Sem essas
variaveis o instalador pergunta cada uma interativamente, com esses mesmos
valores como padrao seguro caso a entrada nao seja um terminal.

O instalador baixa o AppImage, cria atalho, **cria uma entrada de autostart** e
instala pacotes de sistema (GStreamer, ponto de acesso Wi-Fi, Bluetooth). O
patch do GStreamer roda por conta propria dentro dele - ver nota abaixo.

### 2. Patch do GStreamer

O GStreamer que o Raspberry Pi OS distribui (1.26.x anterior a 1.26.11) tem um
bug de *SAND-crop* que quebra o zero-copy em 1080p e **deixa a camada de video
preta**. O instalador detecta e recompila o plugin corrigido. Se algum dia a
projecao subir com audio e sem imagem, comece por aqui.

### 3. Nosso lado

```bash
~/picockpit/scripts/install_projection.sh
```

O script instala a unidade `livi.service`, coloca a regra de janela do
compositor e **avisa** sobre a entrada de autostart - sem remove-la, porque e
arquivo de outro programa.

### 4. Desligar o autostart

Com autostart, a projecao sobe sozinha no boot, por fora da interface, e aparece
**por cima do painel do motorista**. Remova ou renomeie a entrada que o script
apontou em `~/.config/autostart/`.

Quem sobe a projecao passa a ser a pagina Media da multimidia.

### 5. Conferir o app_id

A regra do LIVI casa pelo `app_id` do xdg-shell. Com o LIVI aberto:

```bash
lswt -v
```

A regra em `deployment/labwc-rc.xml` ja assume `dev.f-io.livi` - e o
`StartupWMClass` que o proprio instalador escreve nos atalhos que ele cria
(`~/.local/share/applications/dev.f-io.livi.desktop` e no `.desktop` da area de
trabalho), entao e o valor mais provavel. Mas continua sendo dado de terceiro:
se `lswt -v` mostrar outra coisa, ajuste o `identifier` em
`~/.config/labwc/rc.xml`. **App_id errado nao gera erro nenhum**: a regra
simplesmente nunca casa e a janela aparece onde o compositor quiser. E o modo
de falha silencioso desta configuracao. A regra da nossa propria janela de
multimidia casa por `title`, que nos mesmos definimos e nunca muda - nao
precisa desta conferencia.

## Geometria

Tres numeros precisam concordar, em arquivos diferentes:

| Onde | O que | Padrao |
| --- | --- | --- |
| drop-in do `picockpit.service` | `PICOCKPIT_CONSOLE_FRACTION` | `0.3` |
| `~/.config/labwc/rc.xml` | largura da regra do `livi` | `1344` px |
| `~/.config/labwc/rc.xml` | largura da regra da multimidia (`title`) | `576` px |

Num display de 1920 px, 30% para a multimidia deixam 1344 px para a projecao;
as duas larguras da regra do labwc precisam somar o total do display. Mudar um
sem os outros produz sobreposicao ou faixa preta - o `install_projection.sh`
imprime os tres lado a lado por isso.

## Wayland, de novo

A aplicacao nao escolhe onde a propria janela aparece - isso vale tanto para o
LIVI quanto para a nossa. Enquanto cluster e multimidia vao a tela cheia
(`Window.FullScreen`, um pedido de protocolo de verdade), o Qt resolve sozinho
via `screen:` e nao ha ambiguidade de posicao. Mas com a projecao ocupando
parte da tela da multimidia, a nossa janela deixa de ser tela cheia - vira uma
janela flutuante, e posicao de janela flutuante e decisao do compositor, nao
do cliente. Foi por isso que a faixa reservada para o LIVI estava sumindo na
pratica mesmo com `DisplayController.consoleGeometry` calculando o numero
certo: a visibilidade `FullScreen` ignorava a geometria pedida e cobria a
saida inteira. `DisplayController.consoleFullscreenAllowed` agora so autoriza
tela cheia quando a multimidia e a unica coisa no display; dividindo a tela
com a projecao, ela fica `Windowed` do tamanho de `consoleGeometry` e depende
da regra do compositor abaixo para a posicao.

Vale registrar o limite de fundo: no Wayland o `app_id` pertence a
**aplicacao**, nao a janela. As nossas duas janelas compartilham o mesmo
app_id, entao uma regra por `identifier` nunca conseguiria distinguir cluster
de multimidia. Por isso a nossa regra de compositor - a segunda em
`labwc-rc.xml`, a que prende a multimidia na faixa direita - casa por `title`,
que e por janela.

## Cluster stream

O LIVI suporta o fluxo de video de cluster do Android Auto, com area de
seguranca configuravel, e tem roteamento multi-display. Ou seja: e possivel
mandar o mapa para a tela do motorista.

Fica registrado como possibilidade, nao como plano. Hoje a tela do motorista e
nossa e mostra instrumentos; dividir esse espaco com navegacao e decisao de
produto, nao de implementacao, e depende de dirigir com o conjunto montado para
saber o que faz sentido.

## Estados na interface

A pagina Media mostra o estado real, consultado no systemd a cada dois segundos:

| Estado | O que significa |
| --- | --- |
| nao instalada | a unidade `livi.service` nao existe nesta maquina |
| pronta | instalada e parada; conecte o telefone pelo cabo |
| iniciando | subindo |
| projetando | ocupando a regiao reservada |
| tentando de novo | caiu e o systemd esta repetindo - em ambar, com o PARAR liberado |
| falhou | desistiu - conferir cabo e `journalctl --user -u livi` |

A unidade nao tem `Restart=always`, ao contrario do painel. O painel e essencial
e volta sozinho; a projecao depende de cabo e telefone, e um laco de reinicio
com o cabo solto so encheria o log e esquentaria a CPU.

O limite de tentativas vive na secao `[Unit]`, e nao em `[Service]` - e onde o
systemd le. Declarado na secao errada ele e silenciosamente ignorado, e vale o
padrao de 10 s: medimos 52 reinicios seguidos assim. Com o limite no lugar
certo, sao tres tentativas e o servico desiste.
