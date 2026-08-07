# Projecao: CarPlay e Android Auto

Documento de operacao da Etapa 5. A projecao nao e desenhada pelo PiCockpit: ela
roda em outro processo, o [LIVI](https://github.com/f-io/LIVI), com janela
propria ao lado da multimidia.

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

| Uso | O que precisa |
| --- | --- |
| Android Auto com fio | so o cabo |
| Android Auto sem fio | nada - o LIVI levanta o proprio ponto de acesso Wi-Fi |
| CarPlay nativo | coprocessador de autenticacao **MFi** da Apple, no barramento I2C |
| CarPlay via adaptador | dongle **Carlinkit CPC200-CCPA** (com e sem fio) ou **CCPW** (com fio) |

O coprocessador MFi e um chip fisico. Nao pode ser emulado, e o LIVI nao o
embute nem contorna. **Para atender iPhone e Android com uma peca so, o caminho
e o dongle Carlinkit CPC200-CCPA**: ele cobre CarPlay e Android Auto, com e sem
fio, e dispensa soldar o chip.

## Instalacao, na ordem

### 1. LIVI

Software de terceiros, com instalador proprio. Nosso repositorio nao o baixa.

```bash
curl -fL -o install.sh https://raw.githubusercontent.com/f-io/LIVI/main/scripts/install/pi/install.sh
chmod +x install.sh
./install.sh
```

O instalador baixa o AppImage, cria atalho, **cria uma entrada de autostart** e
aplica o patch do GStreamer descrito abaixo.

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

A regra do compositor casa pelo `app_id` do xdg-shell. Com o LIVI aberto:

```bash
lswt -v
```

Se nao for `livi`, ajuste o `identifier` em `~/.config/labwc/rc.xml`. **App_id
errado nao gera erro nenhum**: a regra simplesmente nunca casa e a janela
aparece onde o compositor quiser. E o modo de falha silencioso desta
configuracao.

## Geometria

Dois numeros precisam concordar, em arquivos diferentes:

| Onde | O que | Padrao |
| --- | --- | --- |
| drop-in do `picockpit.service` | `PICOCKPIT_CONSOLE_FRACTION` | `0.3` |
| `~/.config/labwc/rc.xml` | largura da regra do `livi` | `1344` px |

Num display de 1920 px, 30% para a multimidia deixam 1344 px para a projecao.
Mudar um sem o outro produz sobreposicao ou faixa preta - o
`install_projection.sh` imprime os dois lado a lado por isso.

## Wayland, de novo

A aplicacao nao escolhe onde a propria janela aparece. Nossas janelas se
resolvem atribuindo a tela pelo Qt; a do LIVI, nao - e processo de terceiros e a
unica alavanca e a regra do compositor.

Vale registrar o limite: no Wayland o `app_id` pertence a **aplicacao**, nao a
janela. As nossas duas janelas compartilham o mesmo app_id, entao regra de
compositor nunca conseguiria distinguir cluster de multimidia. Por isso a
distribuicao delas vive no `DisplayController`, e nao aqui.

## Cluster stream

O LIVI suporta o fluxo de video de cluster do Android Auto e do CarPlay, com
area de seguranca configuravel, e tem roteamento multi-display. Ou seja: e
possivel mandar o mapa para a tela do motorista.

Fica registrado como possibilidade, nao como plano. Hoje a tela do motorista e
nossa e mostra instrumentos; dividir esse espaco com navegacao e decisao de
produto, nao de implementacao, e depende de dirigir com o conjunto montado para
saber o que faz sentido.

## Estados na interface

A pagina Media mostra o estado real, consultado no systemd a cada dois segundos:

| Estado | O que significa |
| --- | --- |
| nao instalada | a unidade `livi.service` nao existe nesta maquina |
| pronta | instalada e parada; conecte o telefone ou o adaptador |
| iniciando | subindo |
| projetando | ocupando a regiao reservada |
| falhou | terminou em erro - conferir cabo, adaptador e `journalctl --user -u livi` |

A unidade nao tem `Restart=always`, ao contrario do painel. O painel e essencial
e volta sozinho; a projecao depende de cabo, adaptador e telefone, e um laco de
reinicio com o cabo solto so encheria o log e esquentaria a CPU.
