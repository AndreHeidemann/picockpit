# PiCockpit OS

Plataforma automotiva modular para Raspberry Pi 5: painel digital, Android Auto,
OBD-II/CAN e sistema de widgets, construida como produto de longa vida.

O desenvolvimento tem duas trilhas complementares:

| Trilha | Onde roda | O que cobre |
| --- | --- | --- |
| Backend / dominio | Docker no PC (`python:3.11-bookworm`) | `core`, `services`, `simulation`, `data`, testes, lint |
| UI e hardware | Raspberry Pi 5 real | Qt/QML, FPS, GPU, OBD/CAN/serial, camera |

A UI **nunca** roda em container. Arquitetura x86 e ausencia de aceleracao de GPU
tornariam qualquer medicao de performance enganosa, e validar performance no
hardware final e um objetivo do projeto.

---

## Etapa 0 - Ambiente remoto validado

Levantamento feito via shell remoto do Raspberry Pi Connect em 2026-08-05.

| Item | Valor |
| --- | --- |
| Dispositivo | `raspberry5andreheidemann` (`raspberrypi5-heidemann`) |
| Modelo | Raspberry Pi 5 rev 1.1, 8 GB |
| Sistema | Raspberry Pi OS 12 (Bookworm), Debian 12, `aarch64` |
| glibc | 2.36 |
| Python do sistema | 3.11.2 |
| Sessao grafica | Wayland, compositor `labwc` (`WAYLAND_DISPLAY=wayland-0`, Xwayland em `:0`) |
| GPU | `/dev/dri/card0`, `card1`, `renderD128` (V3D) |
| Display | HDMI-A-1, 1920x1080 @ 60 Hz (preferido e ativo) |
| Armazenamento | Cartao SD 59,5 GB, 79% ocupado |
| Connect client | 2.12.2, screen sharing e remote shell habilitados |

### Como abrir a sessao de visualizacao

1. Acesse <https://connect.raspberrypi.com/devices>.
2. Em `raspberry5andreheidemann`, use **Connect via > Screen sharing**.
3. Para o shell remoto, o mesmo menu oferece **Remote shell** (util quando o SSH
   local nao estiver a mao).

O SSH continua sendo o canal principal para comandos e transferencia de
arquivos; o Connect e o canal de visualizacao.

### Como trocar a resolucao do display

A sessao e Wayland com `labwc`, entao `xrandr` nao se aplica. Use `wlr-randr`:

```bash
wlr-randr                                    # lista saidas e modos
wlr-randr --output HDMI-A-1 --mode 1920x1080@60
wlr-randr --output HDMI-A-1 --mode 1280x800@60    # ensaio de tela automotiva
```

Telas automotivas costumam ser widescreen (1280x480, 1920x720) ou quadradas.
Para fixar um modo entre reboots, use `~/.config/labwc/autostart` ou os
parametros `video=HDMI-A-1:<modo>` em `/boot/firmware/cmdline.txt`.

---

## Etapa 0.5 - Ambiente Docker local (backend)

Pre-requisito: Docker Desktop com backend WSL2.

```bash
cd ~/picockpit
make build      # constroi a imagem
make up         # sobe o container em background
make test       # pytest dentro do container
make lint       # ruff + black --check
make fmt        # aplica correcoes
make sh         # shell no container
```

O codigo e montado por bind mount: editar no host reflete imediatamente no
container, sem rebuild.

Este ambiente cobre **apenas** logica de dominio. Nada aqui mede FPS, valida
QML ou toca hardware; isso e sempre no Pi.

---

## Etapa 1 - Infraestrutura e UI base

### Preparar o Pi (uma vez)

```bash
# no Pi
git clone ~/picockpit.git ~/picockpit
~/picockpit/scripts/setup_pi.sh
```

### Enviar codigo do PC para o Pi

O Pi hospeda um repositorio bare em `~/picockpit.git`, que funciona como remote.

```bash
# no WSL, uma vez
git remote add pi ssh://andreheidemann@192.168.1.54/home/andreheidemann/picockpit.git

# a cada ciclo
git push pi HEAD:refs/heads/main
ssh andreheidemann@192.168.1.54 'cd ~/picockpit && git pull'
```

### Executar

```bash
# no Pi, por SSH ou pelo shell remoto do Connect
~/picockpit/scripts/run_pi.sh
```

O script exporta `XDG_RUNTIME_DIR`, `WAYLAND_DISPLAY` e `DISPLAY` porque uma
conexao SSH nao herda a sessao grafica do usuario, e escolhe
`QT_QPA_PLATFORM="wayland;xcb"` - Wayland nativo quando o socket existe, com
Xwayland como fallback automatico.

Atalhos: `F11` alterna tela cheia (ensaio de kiosk sem systemd), `Ctrl+Q` encerra.

### Medicao de FPS

O medidor da barra superior reporta ao Python, que agrega e grava no log. Fica
em nivel DEBUG porque uma linha a cada 5 s significaria escrita continua no
cartao SD.

```bash
PICOCKPIT_LOG_LEVEL=DEBUG ~/picockpit/scripts/run_pi.sh
grep 'FPS janela' ~/picockpit/logs/picockpit.log
```

Medido em 2026-08-05, painel da Etapa 3 animado, janela de 65 s:
**60,0 fps de media, minimo 59** - identico com e sem a sessao de screen
sharing aberta. A codificacao de video do Raspberry Pi Connect nao custou FPS
mensuravel nesta carga.

### Analise estatica do QML

```bash
# no Pi
~/picockpit/scripts/lint_qml.sh
```

O QML degrada em silencio: propriedade inexistente vira aviso em tempo de
execucao, as vezes apontando para a linha errada. O `qmllint` pega isso antes.

A janela abre em 1280x480, proporcao comum de tela automotiva widescreen.
O contador de FPS na barra superior mede frames realmente renderizados e serve
de referencia desde ja para as Etapas 3 e 4.

---

## Etapa 2 - Simulador

Veiculo de referencia: **Ford Ka 1.0 Ti-VCT flex**, cambio manual de cinco
marchas, tanque de 42 L. Os parametros sao aproximacoes de catalogo e serao
calibrados contra o carro real na Etapa 8.

Telemetria sintetica com coerencia fisica entre os sinais: o acelerador move o
motor, a transmissao impoe a rotacao a partir da velocidade, a carga aquece o
liquido de arrefecimento e o fluxo de ar consome combustivel.

Numeros que o modelo produz, conferidos contra o que se espera do carro:

| Grandeza | Modelo | Referencia |
| --- | --- | --- |
| 0-100 km/h, gasolina | 14,8 s | ~14,5 s |
| 0-100 km/h, etanol | 13,7 s | ~13,5 s |
| Marcha lenta | 0,83 L/h | 0,7 a 1,0 L/h |
| Cruzeiro leve, 62 km/h | 19,7 km/L | 18 a 20 km/L |
| 107 km/h | 14,1 km/L | 13 a 15 km/L |
| Autonomia, tanque cheio | ~600 km | ~550 km |

Etanol rende cerca de 30% menos por litro (estequiometria 9,0 contra 14,7) e
entrega 7% mais torque - as duas coisas saem do mesmo `FuelProperties`.

```
DriverProfile  -> acelerador e freio ao longo de um ciclo de conducao
VehicleModel   -> step(dt) puro: dinamica, cambio, termica e consumo
SimulationProvider -> implementa TelemetryProvider
TelemetryService   -> valida, consolida VehicleState e publica no EventBus
```

Para ver os numeros correndo, sem interface:

```bash
# no container (WSL)
docker compose exec backend python scripts/simulate.py 20 3

# ou no Pi
cd ~/picockpit && PYTHONPATH=. ~/picockpit-venv/bin/python scripts/simulate.py 20 3
```

O segundo argumento e a escala de tempo: `3` faz o ciclo de conducao correr
tres vezes mais rapido que o relogio, util para exercitar todas as fases sem
esperar.

---

## Decisoes tecnicas relevantes

### PySide6 fixado em 6.8.0.2

As wheels `aarch64` do PySide6 a partir da 6.8.1 sao publicadas como
`manylinux_2_39`, exigindo glibc >= 2.39. O Raspberry Pi OS 12 traz glibc 2.36,
e o Debian 12 nao empacota PySide6 no apt. A 6.8.0.2 e a ultima wheel
`manylinux_2_31` e coincide com o ciclo LTS do Qt 6.8 - base estavel para um
projeto de anos.

Migrar para Raspberry Pi OS Trixie (glibc 2.41, Python 3.13, PySide6 6.11)
destravaria versoes novas, mas exige reinstalacao limpa do sistema.

PySide6 foi preferido a PyQt6 por licenca: LGPL permite produto proprietario
sem contrapartida comercial.

### Python 3.11, nao 3.12

O sistema do Pi entrega 3.11.2 e o PySide6 do projeto e instalado por pip
contra esse interpretador. Compilar um 3.12 paralelo criaria divergencia entre
as duas trilhas sem beneficio pratico. O container espelha exatamente esse
ambiente com `python:3.11-bookworm`.

### Estado imutavel e barramento de eventos

`VehicleState` e `Reading` sao imutaveis. A UI sempre recebe um objeto novo, o
que elimina bugs de mutacao concorrente entre a thread do Qt e as tarefas
asyncio dos providers. O `EventBus` isola falhas por handler: um widget que
levanta excecao e registrado no log e ignorado naquele ciclo, sem derrubar o
velocimetro.

### Cartao SD com 79% de ocupacao

Restam cerca de 12 GB. Persistencia (Etapa 10) e logging em arquivo desgastam
cartao SD. A recomendacao e migrar o sistema para SSD via USB3 antes da Etapa 10,
ou ao menos manter o banco e os logs fora do cartao.

---

## Estrutura

```
picockpit/
  app/          composicao da aplicacao (wiring)
  core/         modelos, event bus, config, logging
  services/     contratos e orquestracao de providers
  ui/           Qt/QML - nunca importado pelo backend
  simulation/   telemetria sintetica
  data/         persistencia SQLite
  plugins/      pontos de extensao
  assets/ themes/
configs/        configuracao TOML
docker/         Dockerfile da trilha backend
tests/unit/     testes de dominio (Docker)
tests/integration/  testes com UI e hardware (somente no Pi)
scripts/ deployment/ docs/
```

Testes marcados com `@pytest.mark.hardware` ou `@pytest.mark.ui` so rodam no Pi.
