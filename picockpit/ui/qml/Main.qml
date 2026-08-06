// Raiz da aplicacao: duas janelas, uma por display.
//
// A separacao nao e cosmetica. A tela do motorista mostra instrumentos e nao
// recebe comando; a da multimidia concentra navegacao, ajustes e a projecao.
// Sao papeis diferentes, com requisitos de seguranca diferentes, e por isso
// vivem em janelas diferentes em vez de abas da mesma tela.
import QtQuick

QtObject {
    property ClusterWindow cluster: ClusterWindow {}
    property ConsoleWindow multimedia: ConsoleWindow {}
}
