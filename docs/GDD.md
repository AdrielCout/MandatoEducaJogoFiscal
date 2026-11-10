# GDD — Mandato: Contas da Cidade

**Documento de Game Design · EducaJogo Fiscal · NP2 · 2026.2**

**Equipe:** Adriel

---

## 1. Público-alvo

- **Prioritário:** estudantes do Ensino Médio, idade aproximada de 15 a 18 anos, com ou sem experiência prévia com jogos.
- **Adaptações de linguagem:** textos curtos (até 175 caracteres por carta), vocabulário explicado no Caderno de
  Cidadania e personagens do cotidiano (padeira, vendedor de feira, diretor de escola, estudante).
- **Adaptações de dificuldade:** o **Modo Mediador** (ligado por padrão) mostra o conceito fiscal logo após cada
  decisão, com a explicação do que aconteceu. Pode ser desligado para uma partida mais livre.
- **Uso esperado:** também pode ser usado por mediadores do NAF com um grupo de estudantes, em sala ou oficina.

## 2. Objetivo Educativo

Tributos, orçamento público e controle social costumam aparecer para jovens como um assunto distante, feito de siglas e
leis. Quando aparecem em texto, o aluno decora definições, mas raramente percebe por que um imposto existe, para onde
ele vai e quem fiscaliza.

O desafio central da NP2 é: *como usar um jogo digital para ajudar jovens a compreender situações relacionadas a
tributos, cidadania fiscal, utilização de recursos públicos e suas consequências para a sociedade?*

Nosso recorte: **quem paga, para onde vai e quem fiscaliza.** O jogo trata de quatro situações que aparecem no dia a
dia de uma cidade: arrecadação (IPTU, dívida ativa, nota fiscal), prioridades de gasto (saúde, escola, obras),
licitação e corrupção, e transparência com participação popular.

Por que um jogo e não um quiz: perguntas isoladas ensinam o nome das coisas. Um jogo em que cada decisão tem um
custo obriga o jogador a pensar nas consequências, que é o que um cidadão precisa entender sobre o orçamento público.

### 2.1 Objetivo de aprendizagem

Ao final de uma partida, o jogador deve ser capaz de:

1. **Explicar a função social dos tributos:** a arrecadação só tem sentido se virar serviço público.
2. **Reconhecer que o orçamento é limitado:** toda escolha de gasto deixa outra necessidade sem atendimento.
3. **Identificar que os dois extremos são erros:** dinheiro insuficiente quebra a cidade, e dinheiro parado também
   prejudica a população.
4. **Relacionar transparência e controle social:** confiança sem fiscalização não é controle, e controle excessivo
   pode travar a máquina pública.
5. **Reconhecer sinais de irregularidade** (vantagens em licitação, contratos sem transparência) e suas consequências
   adiadas.

**Como saberemos se funcionou:** a intenção é medir isso no teste com alunos (seção 13 do plano de entrega), com
perguntas antes e depois da partida sobre os conceitos 1 a 4. Os resultados ainda não foram coletados; esta seção
descreve o que queremos medir, não o que foi medido.

## 3. Conceito do jogo e Duração

**Título:** Mandato — Contas da Cidade.

**Premissa:** você é o(a) prefeito(a) de **Novaluz**, uma cidade fictícia de 80 mil habitantes. Você governa por 48
meses. A cada decisão, passam-se cerca de dois meses. Uma partida dura de 8 a 12 minutos.

**Como se joga:** a cada turno, uma carta apresenta uma situação com um personagem (uma vereadora, uma auditora, uma
dona de mercadinho, um estudante influenciador). A carta traz duas opções. Cada opção mexe em quatro forças da cidade:


| Força             | Representa                       | Em zero                                              | Em cem                                    |
| -------------------- | ---------------------------------- | ------------------------------------------------------ | ------------------------------------------- |
| **Povo**           | Confiança e participação      | A população deixa de colaborar e pede a cassação | Cheque em branco: ninguém fiscaliza      |
| **Serviços**      | Saúde, escola, ruas             | Colapso dos serviços                                | Promessas que a receita não sustenta     |
| **Cofre**          | Caixa da prefeitura              | Calote: salários e fornecedores param               | Dinheiro parado: "para que pago imposto?" |
| **Transparência** | Controle e prestação de contas | Escândalo: os desvios aparecem                      | Paralisia: burocracia trava obras         |

Se qualquer força chegar a zero ou a cem, o mandato termina. Um sucessor assume, e o jogo lembra o que aconteceu
(progressão entre mandatos, com selos, finais vistos e verbetes do Caderno).

**Diferencial:** não existe opção certa. Toda decisão melhora uma força e piora outra. A melhor escolha depende do
estado atual da cidade, e o conceito fiscal aparece como consequência da própria regra, não como pergunta de prova.

**Por que cada decisão mexe com o cofre de um jeito diferente:** algumas despesas são pontuais (um reparo), outras
são permanentes (um plantão médico que se repete todo mês). Uma receita também pode ser repetida (IPTU em dia) ou
única (venda de um terreno). O jogador precisa perceber essa diferença, que é um dos conceitos centrais da LRF.

## 4. Equipamentos necessários:

- Computador com Windows, Linux ou macOS.
- Teclado e mouse (o jogo também pode ser controlado só pelo teclado: ← → para decidir e Enter para continuar).
- Tela de pelo menos 1280x720 pixels; em telas menores, a janela se ajusta, mas o texto fica menor.
- Som opcional (o jogo funciona sem áudio).
- **Necessidade de conexão com a Internet:** não. Depois de instalado, o jogo roda offline. A instalação precisa de
  internet uma única vez, para baixar o Python e o pygame-ce.

## 5. Contas, licenças, instalações ou dependências necessárias:

- Python 3.10 ou mais novo (gratuito, python.org).
- Biblioteca pygame-ce, versão 2.5.8, instalada com `pip install -r requirements.txt`. Licença livre (LGPL).
- Nenhuma conta é necessária para jogar.
- Fontes DejaVu incluídas no projeto (licença livre).

## 6. Instruções básicas para o mediador:

1. Instale o projeto conforme o `README.md` e rode `python main.py` para confirmar que a janela abre.
2. Antes da aula, jogue uma partida inteira para se familiarizar com as telas.
3. Deixe o **Modo Mediador ligado** (padrão) para que o conceito fiscal apareça após cada decisão.
4. Apresente o objetivo: "você governa a cidade; cada decisão tem custo; nenhuma opção é a única certa".
5. Deixe os estudantes jogarem sozinhos ou em dupla. Não diga qual opção é melhor.
6. Ao final de cada mandato, leia com a turma a tela de prestação de contas.
7. Conduza a discussão com as perguntas da próxima seção.
8. Para recomeçar, use o menu. O progresso (selos, verbetes, finais) fica salvo no computador.

## 7. Questões para discussão após o uso (tiradas das próprias telas de fim de mandato do jogo):

- Que decisões deixaram o povo sem ver retorno dos impostos? Confiança se reconstrói como?
- Quais serviços você deixou cair primeiro? Por quê?
- Por que guardar dinheiro demais também é um problema? Qual a diferença entre reserva e dinheiro parado?
- Por que o excesso de popularidade pode ser perigoso? O que o cidadão faz quando concorda com o governo, mas quer conferir as contas?
- Em que momento a proposta parecia boa? O que ela escondia? Qual é o papel da licitação em evitar isso?
- Quais decisões mais ajudaram o equilíbrio? Quais prioridades você deixou para depois, e valeu a pena?

## 8. Limitações conhecidas e cuidados para aplicação:

- **Não aplicado com alunos ainda.** Os resultados de aprendizagem não foram medidos. Esta ficha descreve a
  intenção de uso, não um resultado.
- **Só funciona em computador.** A versão para navegador (pygbag) está prevista como melhoria, não entregue.
- **Não é acessível para leitores de tela.** O texto é desenhado na tela. A cobertura de daltonismo usa ícones e texto,
  não só cor. Cuidado com estudantes com deficiência visual.
- **Conteúdo fictício.** A cidade (Novaluz), os personagens e os valores são inventados para o jogo. As leis citadas
  devem ser conferidas com as fontes oficiais antes da aplicação.
- **Simplificação intencional.** O jogo não representa todo o orçamento público nem todas as regras da LRF. Deixe
  isso claro ao final da atividade.
- **Tempo de tela.** A atividade é curta, mas recomenda-se pausa ao final de cada mandato.
