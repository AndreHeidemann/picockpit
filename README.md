# PiCockpit OS

Painel digital automotivo para Raspberry Pi 5. Telemetria em tempo real,
histórico de viagens, cronômetros de desempenho e temas visuais — construído
para rodar a 60 fps no hardware final, não numa máquina de desenvolvimento.

Veículo de referência: **Ford Ka 1.0 Ti-VCT flex**.

---

## O que já funciona

| Recurso | Estado |
| --- | --- |
| Painel digital com mostradores segmentados | pronto, 60 fps no Pi 5 |
| Simulador com física coerente (Ford Ka 1.0) | pronto |
| Consumo instantâneo, autonomia, marcha, hodômetro | pronto |
| Cronômetro 0–100 km/h e de volta | pronto |
| Gráficos em tempo real (janela de 60 s) | pronto |
| Histórico de viagens em SQLite | pronto |
| 5 temas com geometria própria | pronto |
| Unidades métrico e imperial | pronto |
| Injeção de falhas OBD-II para testes | pronto |
| Serviço systemd com kiosk e watchdog | pronto |
| Tela dividida e widgets | pronto |
| CarPlay e Android Auto | integração pronta; exige Trixie e hardware |
| OBD-II real | planejado, depende do veículo |

---

## Instalação no Raspberry Pi

### Requisitos

- Raspberry Pi 5 com Raspberry Pi OS 12 (Bookworm), 64 bits
- Sessão gráfica ativa (Wayland/labwc, o padrão do sistema)
- Python 3.11, o que já vem no sistema
- Acesso por SSH ou pelo shell remoto do Raspberry Pi Connect

### Passo a passo

```bash
# 1. Clonar
git clone https://github.com/<seu-usuario>/picockpit.git ~/picockpit

# 2. Criar o ambiente virtual e instalar as dependencias
~/picockpit/scripts/setup_pi.sh

# 3. Rodar
~/picockpit/scripts/run_pi.sh
```

Deve abrir uma janela de 1280x480 com o painel funcionando sobre o simulador.
`F11` alterna tela cheia, `Ctrl+Q` encerra.

> **A versão do PySide6 é escolhida pela glibc do sistema.** O `setup_pi.sh` lê
> a glibc e aplica `constraints/bookworm.txt` (6.8.0.2) ou
> `constraints/trixie.txt` (série 6.11). Ver
> [Decisões técnicas](#decisões-técnicas).

### Instalar como serviço (opcional)

Para o painel subir sozinho com o sistema, em tela cheia, e voltar sozinho se
cair:

```bash
~/picockpit/scripts/install_service.sh
systemctl --user start picockpit
```

Comandos do dia a dia:

```bash
systemctl --user status picockpit    # estado
systemctl --user stop picockpit      # para, gravando a viagem em andamento
systemctl --user restart picockpit   # reinicia
tail -f "$XDG_RUNTIME_DIR"/picockpit/logs/picockpit.log
```

---

## Desenvolvimento

O projeto tem duas trilhas complementares:

| Trilha | Onde roda | O que cobre |
| --- | --- | --- |
| Backend e domínio | Docker no PC (`python:3.11-bookworm`) | `core`, `services`, `simulation`, `data`, testes, lint |
| Interface e hardware | Raspberry Pi 5 real | Qt/QML, FPS, GPU, OBD/CAN/serial, câmera |

A interface **nunca** roda em container. Arquitetura x86 e ausência de aceleração
de GPU tornariam qualquer medição de performance enganosa, e validar performance
no hardware final é um objetivo do projeto.

### Trilha rápida (Docker, sem Raspberry Pi)

Requer Docker Desktop com backend WSL2, ou Docker em Linux.

```bash
make build      # constroi a imagem
make up         # sobe o container
make test       # pytest dentro do container
make lint       # ruff + black --check
make fmt        # aplica as correcoes
make sh         # shell no container
```

O código é montado por bind mount: editar no host reflete no container sem
rebuild. Esta trilha cobre **apenas** lógica de domínio — nada aqui mede FPS,
valida QML ou toca hardware.

Para ver o simulador funcionando sem interface gráfica:

```bash
docker compose exec backend python scripts/simulate.py 20 3
```

```
      speed |   rpm | gear | throttle | consumption | fuel_rate | range
        0.0 |   850 |    0 |      0.0 |         0.0 |       0.8 | 546.0
       22.3 |  2964 |    1 |     58.8 |         3.2 |       6.9 | 531.2
       75.6 |  2597 |    4 |     55.2 |        18.4 |       3.5 | 514.3
```

### Enviar código do PC para o Pi

O Pi hospeda um repositório bare que funciona como remote de deploy:

```bash
# uma vez, no Pi
git init --bare ~/picockpit.git

# uma vez, no PC
git remote add pi ssh://<usuario>@<ip-do-pi>/home/<usuario>/picockpit.git

# a cada ciclo
git push pi HEAD:refs/heads/main
ssh <usuario>@<ip-do-pi> 'cd ~/picockpit && git pull'
```

### Qualidade

```bash
# no container ou no Pi
pytest
ruff check picockpit tests scripts
black --check picockpit tests scripts

# somente no Pi: analise estatica do QML
~/picockpit/scripts/lint_qml.sh
```

Testes marcados com `@pytest.mark.ui` exigem PySide6 e são pulados fora do Pi.
Os marcados com `@pytest.mark.hardware` exigem OBD, CAN ou serial reais.

O `qmllint` existe por um motivo específico: **QML degrada em silêncio**.
Propriedade inexistente vira aviso em tempo de execução, às vezes apontando para
a linha errada. Três bugs do projeto foram dessa família — por isso o teste de
fumaça da interface transforma qualquer aviso do QML em falha.

---

## Arquitetura

```
picockpit/
  app/          composicao da aplicacao (wiring, ponte asyncio x Qt)
  core/         modelos, event bus, series, temas, unidades, config, logging
  services/     contratos de provider, telemetria, cronometros, viagens
  ui/           controladores Qt e QML, nunca importado pelo backend
  simulation/   modelo fisico do veiculo, motorista sintetico, falhas
  data/         SQLite: migracoes, viagens, preferencias
  plugins/      pontos de extensao
configs/        configuracao de fabrica em TOML
deployment/     unidades systemd e regra de janela do compositor
scripts/        setup, execucao, lint, backup, atualizacao
tests/unit/     dominio, roda no Docker
tests/integration/  interface e hardware, somente no Pi
```

O fluxo de dados é sempre o mesmo, e é o que permite trocar a origem sem tocar na
interface:

```
Provider  ->  TelemetryService  ->  EventBus  ->  Controllers  ->  QML
(simulacao,   valida e              desacopla    convertem       exibe
 OBD, CAN)    consolida                          unidades
```

`TelemetryProvider` é o contrato único. Trocar simulação por OBD-II na Etapa 8 é
acrescentar um ramo em `create_provider` — nada acima disso muda.

---

## Decisões técnicas

**PySide6 fixado por arquivo de constraint, não no `pyproject.toml`.** Wheels
`aarch64` a partir da 6.8.1 são `manylinux_2_39` (glibc >= 2.39); o Raspberry Pi
OS 12 tem glibc 2.36, então lá a última utilizável é a 6.8.0.2 — que cai no
ciclo LTS do Qt 6.8. O Trixie tem glibc 2.41 e roda a série 6.11.

Fixar um número único no `pyproject.toml` obrigaria a editar o repositório no
meio da migração, com o Pi recém-formatado e sem monitor. Em vez disso o
`pyproject.toml` declara a faixa compatível e o `setup_pi.sh` escolhe o arquivo
de `constraints/` pela glibc — a decisão fica explícita e o mesmo commit instala
corretamente nos dois sistemas.

**PySide6 e não PyQt6**, por licença: LGPL permite produto proprietário sem
contrapartida comercial.

**Python 3.11.** É o que o sistema entrega e contra o que o PySide6 é instalado.
O container espelha exatamente, com `python:3.11-bookworm`.

**Mostradores em `QtQuick.Shapes` com `CurveRenderer`**, nunca `Canvas`. Canvas
rasteriza na CPU e repinta a textura inteira a cada atualização — no Pi 5 isso
derruba o FPS. O avanço é quantizado em segmentos inteiros: além de ser o
comportamento correto de um mostrador segmentado, prende a geometria e evita
re-tesselar o preenchimento a cada quadro.

**`qasync` para casar asyncio e Qt.** Um laço só — provider, serviços e interface
vivem na mesma thread, sem fronteira de concorrência para errar.

**Singletons QML registrados antes do engine.** Objetos registrados com
`qmlRegisterSingletonInstance` pertencem a um único engine, e o registro precisa
acontecer antes de instanciá-lo. Fora disso o Qt reporta erros que apontam para o
lugar errado. `build_engine` falha alto se for chamado duas vezes.

**Estado imutável.** `VehicleState` e `Reading` são congelados e a interface
sempre recebe objeto novo. Elimina uma classe inteira de bugs de mutação
concorrente entre a thread do Qt e as tarefas assíncronas.

**Unidades convertidas só na borda.** O domínio trabalha sempre em km/h, °C e
km/L. Guardar valor convertido tornaria o histórico incomparável no dia em que o
usuário trocasse de sistema. Limiares de alerta comparam sempre em unidade
canônica: superaquecimento é propriedade do motor, não da unidade exibida.

**Um registro por viagem, não por amostra.** SQLite em modo WAL com
`synchronous=NORMAL`. No pior caso perde-se a última viagem numa queda de
energia, o que é barato perto de gastar a vida do cartão SD.

**Log em tmpfs por padrão.** Sem SSD, escrita contínua no cartão é desgaste por
um dado que quase nunca é lido. Para guardar em disco, defina `PICOCKPIT_LOG_DIR`.

**`SIGTERM` tratado.** É por esse caminho que a viagem em andamento é gravada
antes do desligamento. Sem isso, `systemctl stop` perderia justamente a viagem que
acabou de acontecer.

---

## Configuração

Valores de fábrica em `configs/default.toml`. Qualquer um pode ser sobrescrito
por variável de ambiente com o prefixo `PICOCKPIT_`:

```bash
PICOCKPIT_LOG_LEVEL=DEBUG PICOCKPIT_KIOSK=true ~/picockpit/scripts/run_pi.sh
```

| Chave | Padrão | Descrição |
| --- | --- | --- |
| `env` | `development` | Ambiente lógico |
| `log_level` | `INFO` | Nível de log |
| `log_dir` | tmpfs | Diretório dos logs rotacionados |
| `provider` | `simulation` | Origem dos dados: `simulation`, `obd`, `can` |
| `target_fps` | `60` | Alvo de quadros |
| `sample_interval_ms` | `50` | Intervalo de amostragem |
| `database_path` | `data/picockpit.db` | Banco SQLite |
| `theme` | `normal` | Tema inicial |
| `kiosk` | `false` | Tela cheia sem decoração |

O que o usuário muda na tela de Ajustes é guardado no banco e **tem precedência**
sobre o arquivo.

### Medir FPS

O medidor da barra superior reporta ao Python, que agrega e grava em nível DEBUG:

```bash
PICOCKPIT_LOG_LEVEL=DEBUG ~/picockpit/scripts/run_pi.sh
grep 'FPS janela' "$XDG_RUNTIME_DIR"/picockpit/logs/picockpit.log
```

Medição de 2026-08-06, painel animado, janela de 65 s: **60,0 fps de média,
mínimo 59** — idêntico com e sem a sessão de screen sharing aberta.

---

## Backup e atualização

```bash
~/picockpit/scripts/backup.sh       # banco e configs, mantem os 10 mais recentes
~/picockpit/scripts/update.sh       # backup, pull, dependencias, testes, restart
~/picockpit/scripts/restore.sh <arquivo.tar.gz>
```

O banco é copiado pela API de backup do SQLite, não com `cp`: em modo WAL, copiar
o arquivo com a aplicação rodando pode capturar um estado sem as transações que
ainda vivem no journal.

---

## Displays sem monitor

Sem monitor conectado o Pi desabilita a saida HDMI, a sessao grafica fica sem
output e o Raspberry Pi Connect nao tem o que compartilhar - o desenvolvimento
passaria a exigir um monitor dedicado ao Pi.

O script forca as duas saidas a existirem, simulando o arranjo final: cluster
widescreen numa, multimidia na outra.

```bash
sudo ~/picockpit/scripts/setup_displays.sh
sudo reboot

# depois de reiniciar
wlr-randr
```

Para voltar atras: `sudo ~/picockpit/scripts/setup_displays.sh --remover`.
O `cmdline.txt` original fica em `cmdline.txt.picockpit-bak`.

Modos podem ser trocados por variavel:

```bash
sudo CLUSTER_MODE=1920x720@60 CONSOLE_MODE=1280x800@60 \
  ~/picockpit/scripts/setup_displays.sh
```

Com duas saidas, o compartilhamento de tela do Connect normalmente exibe apenas
uma delas. Por isso o cluster fica em `HDMI-A-1`, que costuma ser a primeira -
e a que aparece.

---

## Acesso remoto

O desenvolvimento acontece por SSH para comandos e **Raspberry Pi Connect** para
visualização.

1. Acesse <https://connect.raspberrypi.com/devices>
2. No dispositivo, use **Connect via → Screen sharing**, ou **Remote shell**

A sessão é Wayland com `labwc`, então `xrandr` não se aplica. Para trocar a
resolução:

```bash
wlr-randr                                       # lista saidas e modos
wlr-randr --output HDMI-A-1 --mode 1280x800@60  # ensaio de tela automotiva
```

---

## Roadmap

| Etapa | Situação |
| --- | --- |
| 0 — Validação do acesso remoto | concluída |
| 0.5 — Ambiente Docker local | concluída |
| 1 — Infraestrutura e UI base | concluída |
| 2 — Simulador | concluída |
| 3 — Painel digital | concluída |
| 3.5 — Cronômetros e gráficos | concluída |
| 4 — Temas | concluída |
| 10 — Persistência | concluída |
| 12 — Configurações | concluída |
| 13 — Produção e watchdog | concluída |
| 6 — Tela dividida | concluída |
| 7 — Widgets | concluída |
| 5 — CarPlay e Android Auto | integração pronta; falta o Trixie e o hardware ([docs/projecao.md](docs/projecao.md)) |
| 8 — OBD-II e CAN reais | planejada, depende do veículo |

---

## Licença

Projeto proprietário. PySide6 é usado sob LGPL, sem modificação da biblioteca.

A projeção de CarPlay e Android Auto é feita pelo [LIVI](https://github.com/f-io/LIVI), que é GPL-3.0-or-later. Ele roda como **processo separado**, sem compartilhar código nem processo com o PiCockpit — a fronteira entre os dois é a unidade de serviço em `deployment/livi.service`. Nada do LIVI é linkado ou embutido aqui.
