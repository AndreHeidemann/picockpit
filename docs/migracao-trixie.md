# Migracao para Raspberry Pi OS Trixie

Documento de operacao. Ler inteiro antes de comecar: a instalacao limpa apaga o
cartao, e ha dados no Pi que nao existem em nenhum outro lugar.

## Por que migrar

Duas travas do Bookworm caem de uma vez:

| Trava | Bookworm | Trixie |
| --- | --- | --- |
| PySide6 | 6.8.0.2 (ultima `manylinux_2_31`, glibc 2.36) | 6.11, wheels `manylinux_2_39` |
| OpenGL ES | 3.1 sem suporte pleno no driver do Pi 5 | 3.x completo, exigido pelo LIVI |
| Python | 3.11 | 3.13 |

O LIVI - central de Android Auto - so roda no Pi 5 com Trixie. Sem a
migracao, a projecao fica fora do projeto.

## Antes de reinstalar

Estes itens vivem apenas no Pi e somem com a formatacao:

- [ ] **Codigo**: `git push origin main` (GitHub) e conferir que o commit apareceu
- [ ] **Repositorio bare** `~/picockpit.git`: e o remote de deploy; sera recriado
- [ ] **Banco de viagens, configuracoes e drop-ins**: `scripts/backup.sh`

```bash
# no Pi
cd ~/picockpit
./scripts/backup.sh
ls -lt ~/picockpit-backups | head -3

# no PC (WSL) - tirar a copia de dentro do cartao que sera apagado
scp <usuario>@<ip-do-pi>:~/picockpit-backups/picockpit-*.tar.gz ~/
```

O arquivo carrega tambem `sistema.txt`, com os modos de video forcados e as
versoes de origem. Vale abrir e ler antes de comecar - e a unica anotacao de
como esta maquina estava configurada.

- [ ] Anotar a configuracao de rede (Wi-Fi, IP fixo se houver)
- [ ] Lembrar que o Raspberry Pi Connect precisara ser vinculado de novo

## Instalacao

1. Gravar o **Raspberry Pi OS 13 (Trixie), 64 bits, com desktop** pelo Raspberry
   Pi Imager, em outro cartao se possivel - o cartao antigo vira backup fisico
2. No Imager, pre-configurar - os valores da maquina atual:

   | Campo | Valor |
   | --- | --- |
   | Hostname | `raspberrypi5-heidemann` |
   | Usuario | `andreheidemann` |
   | Wi-Fi | `CAHEIDE_2.4G`, pais `BR` |
   | Rede | DHCP, sem IP fixo (eth0 caiu em `.54`, wlan0 em `.183`) |
   | SSH | habilitado, **colando a chave publica do PC** |

   Colar a chave publica no Imager evita repetir a dança de `authorized_keys`
   com permissoes `700`/`600` que ja custou uma sessao inteira - e e o que faz
   o `git push pi` funcionar logo no primeiro boot.
3. Primeiro boot **com monitor conectado** - o passo seguinte e o que devolve o
   acesso sem monitor, e ate ele existir nao ha o que compartilhar

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y git rpi-connect
rpi-connect on
rpi-connect signin      # vincula o dispositivo de novo
```

## Devolver o acesso remoto antes de tudo

Sem monitor, o Pi desliga a saida HDMI, a sessao grafica fica sem output e o
Connect nao tem tela para compartilhar. Numa instalacao limpa nao ha nem os
modos forcados nem o `disable_fw_kms_setup=1` que os torna efetivos - o script
cuida dos dois.

O repositorio e publico, entao o Pi clona direto do GitHub - sem credencial,
sem chave, sem depender do PC estar ligado. O repositorio bare de deploy vem
depois, quando o ciclo de desenvolvimento recomecar.

```bash
git clone https://github.com/AndreHeidemann/picockpit.git ~/picockpit
git -C ~/picockpit config core.fileMode false
sudo bash ~/picockpit/scripts/setup_displays.sh
sudo reboot
```

Depois do reboot, ainda com monitor, conferir:

```bash
wlr-randr        # devem aparecer HDMI-A-1 e HDMI-A-2 nos modos pedidos
```

So entao desconectar o monitor e seguir pelo Connect.

## Restaurar o PiCockpit

O codigo ja esta no lugar, do passo anterior.

```bash
# 0. Repositorio bare de deploy, para voltar a empurrar codigo do PC
git init --bare ~/picockpit.git

# 1. Ambiente - escolhe sozinho o constraint pela glibc do sistema
~/picockpit/scripts/setup_pi.sh

# 2. Banco, configuracoes e drop-ins de systemd
#    (copiar antes o .tar.gz do PC:  scp ~/picockpit-*.tar.gz <pi>:~/ )
~/picockpit/scripts/restore.sh ~/picockpit-<data>.tar.gz

# 3. Servico
~/picockpit/scripts/install_service.sh
systemctl --user start picockpit
```

Docker nao volta. Ele existia no cartao antigo por outros projetos e ocupava
dezenas de gigabytes; o backend headless roda no PC, nunca no Pi.

## Verificar depois

```bash
grep PRETTY /etc/os-release          # Debian 13 (trixie)
ldd --version | head -1              # glibc 2.41 ou superior
python3 -V                           # 3.13
~/picockpit-venv/bin/python -c "import PySide6; print(PySide6.__version__)"
QT_QPA_PLATFORM=offscreen ~/picockpit-venv/bin/python -m pytest -q
~/picockpit/scripts/lint_qml.sh
```

- [ ] Copiar a versao instalada do PySide6 para `constraints/trixie.txt` como
      pin exato e fazer commit. Ate aqui o arquivo carrega uma faixa, porque a
      versao so se conhece depois da primeira instalacao real.

## O que provavelmente vai quebrar

**PySide6 6.11 nao e 6.8.** A API de `QtQuick.Shapes` mudou entre as versoes -
os mostradores sao o ponto a conferir primeiro. O teste de fumaca da interface
existe justamente para isso: ele transforma qualquer aviso do QML em falha.

**O compositor pode nao ser mais o labwc.** Conferir com
`echo $XDG_CURRENT_DESKTOP`; as regras de posicionamento de janela para a
projecao dependem disso.

**Python 3.13 no lugar do 3.11.** O container de desenvolvimento precisa passar
para `python:3.13-trixie` para as duas trilhas voltarem a espelhar uma a outra.
Fica para depois da migracao de proposito: enquanto o Pi roda Bookworm, o
container tem de espelhar o Bookworm.
