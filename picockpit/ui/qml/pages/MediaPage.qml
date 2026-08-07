// Projecao de CarPlay e Android Auto.
//
// Esta pagina nao desenha o video. A projecao roda em outro processo, com
// janela propria posicionada pelo compositor na regiao reservada ao lado da
// multimidia - decidido assim por duas razoes independentes: nenhuma solucao
// de projecao entrega o quadro como item Qt sem uma copia que anula a
// decodificacao por hardware, e a licenca do LIVI (GPL) nao se mistura com um
// produto proprietario quando os dois sao processos separados.
//
// O que a pagina faz e o que sobra, e nao e pouco: dizer em que estado a
// projecao esta e dar o comando de ligar e desligar. Sem isso o motorista
// ficaria diante de uma tela preta sem saber se falta cabo, adaptador ou
// software.
import QtQuick
import ".."
import PiCockpit 1.0

Item {
    id: page

    readonly property bool narrow: width < 520

    Rectangle {
        anchors { fill: parent; margins: 24 }
        radius: 14
        color: Theme.colors.surface
        border.width: 1
        border.color: Projection.running ? Theme.colors.success : Theme.colors.surface_alt

        Column {
            anchors {
                left: parent.left
                right: parent.right
                verticalCenter: parent.verticalCenter
                margins: 24
            }
            spacing: 14

            Text {
                text: qsTr("PROJECAO")
                color: Theme.colors.text_muted
                font { pixelSize: 11; weight: Font.DemiBold; letterSpacing: 1.6 }
            }

            Text {
                width: parent.width
                text: Projection.running
                    ? qsTr("Em exibicao")
                    : qsTr("CarPlay e Android Auto")
                color: Theme.colors.text
                font { pixelSize: page.narrow ? 22 : 28; weight: Font.Light }
                wrapMode: Text.WordWrap
            }

            Text {
                width: parent.width
                text: Projection.summary
                color: Projection.state === "failed"
                    ? Theme.colors.danger
                    : Projection.state === "retrying"
                        ? Theme.colors.warning
                        : Theme.colors.text_muted
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }

            // Flow e nao Row: esta pagina tambem aparece na coluna estreita.
            Flow {
                width: parent.width
                spacing: 10

                ActionButton {
                    // O rotulo distingue subida de retentativa: "INICIANDO..."
                    // parado na tela por dois minutos, quando na verdade ja
                    // falhou tres vezes, e informacao errada.
                    text: Projection.state === "retrying"
                        ? qsTr("TENTANDO...")
                        : Projection.busy ? qsTr("INICIANDO...") : qsTr("INICIAR")
                    enabled: Projection.installed && !Projection.running && !Projection.busy
                    onActivated: Projection.start()
                }

                ActionButton {
                    // Habilitado tambem na retentativa: sem isso, sair de um
                    // laco de reinicio exigiria um terminal, que ninguem tem
                    // dentro do carro.
                    text: qsTr("PARAR")
                    enabled: Projection.stoppable
                    onActivated: Projection.stop()
                }
            }

            Text {
                width: parent.width
                visible: !Projection.installed
                text: qsTr("Instale o LIVI conforme docs/projecao.md. Ele exige Raspberry Pi OS Trixie: o Pi 5 so alcanca OpenGL ES 3.x a partir dele.")
                color: Theme.colors.warning
                font.pixelSize: 12
                wrapMode: Text.WordWrap
            }
        }
    }
}
