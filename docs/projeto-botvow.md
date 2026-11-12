# BotVow («a promessa do bot»): a caixa negra dos Bots

*Documento de projeto (versão pública), 12/11/2026. Código MIT; documentação CC BY 4.0.*

> **Nome: BotVow** («a promessa do bot»). Substitui o nome de trabalho «Selo», abandonado por conflito (ver secção 1). **Antes de um lançamento mais amplo, falta a verificação de marcas (EUIPO, INPI e USPTO) e uma opinião jurídica.**

---

## Visão (em 2 frases)

O BotVow é a caixa negra dos Bots: um registo Bot 2 Bot, inalterável e verificável, de tudo o que dois Bots combinam (quem combinou o quê, quem autorizou e quando), assinado pelos dois. Os Bots são o núcleo; agentes de outras IA (OpenAI, Google, Anthropic, modelos abertos, etc.) que também queiram registar acordos na caixa negra dos Bots podem fazê-lo por uma porta aberta complementar, mas **têm de seguir as regras da caixa negra dos Bots**, sem regras próprias nem exceções.

---

## 1. O nome: BotVow, e porque deixámos o «Selo»

### 1.1 Porque mudámos

O nome de trabalho era «Selo». A pesquisa de 12/11/2026 (por volta das 22:30, hora de Lisboa) mostrou que estava ocupado precisamente no nosso nicho:

| O quê | Pormenores | Fonte |
|---|---|---|
| Proposta na IETF chamada «Selo» | *draft-hamlett-selo-architecture-00*, de James Bradley Hamlett, de 31/10/2026: acordos de acesso negociados e assinados pelas duas partes entre agentes de organizações. O autor declara um **pedido de patente pendente** relacionado com o documento. | https://datatracker.ietf.org/doc/draft-hamlett-selo-architecture/ |
| Pedido de marca «SELO» nos EUA | USPTO n.º 50193265, de 31/10/2026, do mesmo autor, classes 9 e 42 (software para negociar e gerir acordos entre empresas e os seus agentes). | https://getcopymark.com/trademark/50193265 |
| Selo (C1) | Recibos assinados com Ed25519 para agentes de programação. | https://selo.c1.run/ |
| Selo AI, SELO+ | Empresa de marketing com IA; token cripto. | https://www.seloai.com/ · https://www.coincarp.com/currencies/selo/ |

Por isso, escolhemos um nome novo: **BotVow**, «a promessa do bot». Uma *vow* é uma promessa solene, e é isso que a caixa negra guarda: o que cada Bot prometeu ao outro.

### 1.2 Disponibilidade do nome BotVow

Verificação de 12/11/2026, às 22:40 (hora de Lisboa), por RDAP (o registo oficial de domínios), DNS público e as APIs do GitHub, npm e PyPI.

| Nome | Estado | Evidência |
|---|---|---|
| **botvow.org** | **Livre (a usar)** | RDAP 404 e DNS sem registo |
| botvow.dev, botvow.ai, botvow.bot | Livres | RDAP 404 e DNS sem registo |
| botvow.com | **Ocupado** | RDAP: registado a 26/03/2026, expira a 26/03/2027; sem site |
| **github.com/botvow** | **Livre (a usar)** | API do GitHub: 404 |
| **npm `botvow`** | **Livre (a usar)** | Registo npm: 404 |
| **PyPI `botvow`** | **Livre (a usar)** | PyPI: 404 |

Um domínio livre só fica garantido no momento da compra.

**Conflitos encontrados:** não encontrei nenhum produto chamado BotVow. Na mesma área há projetos com a palavra «vow», mas com outros nomes: o */vow Protocol*, de compromissos verificáveis de agentes (https://thecolony.ai/c/vow-protocol), e o Keptvow, de confiança antes de pagamentos de bots (https://keptvow.com/). Convém distinguir-nos deles na comunicação.

### 1.3 Verificação de marcas antes do lançamento

Não consegui pesquisar marcas de forma automática. **Antes de qualquer lançamento público, é preciso verificar o nome BotVow nas bases da EUIPO (UE), do INPI (Portugal) e do USPTO (EUA)**, e pedir uma opinião jurídica. Isto não é aconselhamento legal.

### 1.4 Alternativas consideradas (plano B)

BotSeal (risco de confusão com o AgentSeal e com um projeto GitHub chamado «botseal»), VowBox e BotPact (botpact.ai ocupado; existe a proposta IETF PACT). 

---

## 2. O problema

Os agentes de IA começam a negociar e a comprometer-se em nome de pessoas e empresas: encomendas, reservas, acessos a dados, pagamentos. Quando algo corre mal, a primeira pergunta vai ser: *o que é que o teu agente aceitou, exatamente, e quem o autorizou?*

Hoje, quando dois Bots combinam alguma coisa, cada lado guarda o seu próprio registo, que pode editar, e o outro lado pode negá-lo. Uma proposta da IETF descreve bem isto como «o meu registo contra o teu» (https://datatracker.ietf.org/doc/html/draft-mih-agent-bilateral-attestation-03). Os Bots precisam de uma caixa negra própria, como os aviões: um sítio onde o acordo fica selado pelos dois e que nenhum dos lados consegue alterar depois. E, como nem todos os agentes com quem um Bot fala são Bots (há agentes de outras IA), a caixa negra deve aceitar também esses registos, sem deixar de ser feita a pensar nos Bots.

**Contexto europeu.** O Regulamento da IA (UE 2024/1689), no **artigo 12.º**, obriga os sistemas de IA de risco elevado a «permitir tecnicamente o registo automático de eventos (logs) ao longo da vida do sistema», para identificar riscos, apoiar o acompanhamento pós-comercialização e monitorizar o funcionamento. O **artigo 19.º** obriga a guardar esses registos durante pelo menos seis meses. Fontes: https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-12 · https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-19 · texto consolidado em https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng

*Atenção:* o artigo 12.º aplica-se apenas a sistemas de **risco elevado**, e o BotVow sozinho **não** torna ninguém conforme. Pode, isso sim, ser uma peça de prova inalterável dentro desses registos.

---

## 3. Como funciona (explicado de forma simples)

1. **Apresentação.** Os dois Bots (ou um Bot e um agente de outra IA) abrem um «caderno» comum. Cada um diz quem é e mostra a sua chave pública, que pode estar ligada ao seu *Agent Card* do A2A. Os dois assinam esta abertura.
2. **Negociação.** Propostas e contrapropostas ficam registadas apenas como uma «impressão digital» (hash). O texto em si não é guardado, por privacidade.
3. **Acordo.** O acordo final é **assinado pelos dois**. Pode incluir quem autorizou do lado humano, a referência ao mandato e o prazo.
4. **Fecho.** Um «selo» final, também assinado pelos dois, fecha o caderno e indica quantas entradas tem.
5. **Verificação.** Qualquer pessoa, com uma ferramenta gratuita e só com as chaves públicas, confirma que nada foi alterado, apagado ou reordenado. O resultado é «VERIFY OK» ou «TAMPER DETECTED».

**Os Bots no núcleo, com uma porta aberta e regras iguais para todos:**
- **Núcleo: Bot 2 Bot.** O formato, os exemplos e as ferramentas são pensados primeiro para os Bots registarem os acordos entre si (por exemplo, um Bot de um cliente e o Bot de um fornecedor).
- **Porta aberta complementar.** Um agente de outra IA (OpenAI, Google, Anthropic, open source) pode registar acordos na caixa negra dos Bots. Não é o centro do projeto, mas também não fica de fora.
- **As regras são as da caixa negra dos Bots, e mais nenhumas.** Quem entra pela porta aberta segue exatamente a especificação do BotVow: mesmo formato JSON, mesma assinatura Ed25519, co-assinatura obrigatória do acordo e do fecho, cadeia de hashes, privacidade (só hashes) e mesmo verificador. Não há regras próprias, extensões que mudem as regras, nem exceções. Um registo que não cumpra as regras é recusado pelo verificador («TAMPER DETECTED» ou inválido).
- É **só um formato JSON e um verificador**. Não exige conta, servidor central, blockchain nem SDK de um fornecedor.
- Entra pelos protocolos que já existem: como extensão ou metadado de uma tarefa A2A, como ferramenta MCP (registar, verificar) ou por HTTPS simples.
- Usa padrões abertos: Ed25519, SHA-256, JSON canónico (RFC 8785, https://www.rfc-editor.org/rfc/rfc8785) e, mais tarde, carimbos de tempo RFC 3161 (https://www.rfc-editor.org/rfc/rfc3161) e registos de transparência (RFC 9162, https://www.rfc-editor.org/rfc/rfc9162; Sigstore Rekor, https://docs.sigstore.dev/logging/overview/).

---

## 4. Casos de negócio reais (8)

*(Em todos os casos, o cenário principal é Bot 2 Bot; o outro lado pode também ser um agente de outra IA, pela porta aberta e com as mesmas regras.)*

1. **Compras entre empresas.** O Bot de compras de um restaurante e o Bot de um fornecedor combinam preço, quantidade e prazo de entrega. Se a entrega falhar, ambos têm a mesma prova do que foi acordado.
2. **Reservas e cancelamentos.** O Bot de um cliente reserva um alojamento junto do Bot do alojamento. As condições de cancelamento aceites ficam seladas, o que evita discussões do tipo «não foi isso que o vosso bot disse».
3. **Licenças de acesso a dados entre empresas.** Fica registado para que finalidade os dados são usados, quanto tempo são guardados e se podem servir para treinar IA. É o tipo de acordo que a proposta IETF «Selo» também trata.
4. **Seguros e sinistros.** O Bot do segurado e o Bot da seguradora acordam a participação, a data da peritagem e os documentos entregues. O registo ajuda a resolver disputas sem acusações cruzadas.
5. **Logística e transportes.** O Bot do expedidor e o do transportador combinam a janela de entrega, as condições e a responsabilidade por danos. Cada alteração fica numa entrada «amendment» assinada.
6. **Apoio ao cliente.** O Bot de uma operadora promete um reembolso ou desconto ao Bot do cliente. A promessa fica assinada pelo bot da empresa e pode ser verificada mais tarde.
7. **Alteração de dados de pagamento (proteção contra fraude).** A mudança de IBAN de um fornecedor exige um registo selado e a referência à aprovação humana. A própria proposta IETF «Selo» dá destaque a este caso (https://btw.media/en/selo-agents-bank-details-human-approval).
8. **Auditoria e conformidade.** Uma empresa que usa agentes em processos de risco elevado junta os recibos selados aos registos exigidos pelos artigos 12.º e 19.º do Regulamento da IA, como prova que não pode ser alterada.

*(Estes casos são cenários ilustrativos. Ainda não temos nenhum cliente ou piloto real.)*

---

## 5. Concorrência e o que nos distingue

Partimos do princípio de que a concorrência já tem, ou vai ter, algo parecido, e a pesquisa confirma-o. Esta área está a encher depressa:

| Projeto | O que faz | Ligação |
|---|---|---|
| **Google AP2** (Agent Payments Protocol) | Pagamentos por agentes com «mandatos» assinados (SD-JWT e credenciais verificáveis): *Checkout Mandate* e *Payment Mandate*, mais um recibo de pagamento assinado. Só cobre **pagamentos** | https://ap2-protocol.org/ap2/specification/ · https://github.com/google-agentic-commerce/AP2 · https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol |
| **A2A** (Agent2Agent, Linux Foundation) | Comunicação entre agentes; os *Agent Cards* podem ser assinados (JWS + RFC 8785). Não define o acordo final | https://a2a-protocol.org/latest/specification/ · https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents |
| **MCP** (Model Context Protocol) | Liga modelos a ferramentas e dados. Não regista acordos | https://modelcontextprotocol.io/specification |
| **W3C Verifiable Credentials 2.0** | Credenciais assinadas e verificáveis (identidade, autorizações) | https://www.w3.org/TR/vc-data-model-2.0/ |
| **Proposta IETF «Selo»** (Hamlett) | Arquitetura completa: entidades verificadas, negociação tipada, acordo assinado pelos dois, gateway, tokens. Patente pendente | https://datatracker.ietf.org/doc/draft-hamlett-selo-architecture/ |
| **PACT** (IETF) | Contratos de tarefa co-assinados, entregas, veredictos e resultados | https://www.ietf.org/archive/id/draft-laxsharma-pact-03.html |
| **Bilateral attestation** (IETF) | Atestações assinadas pelos dois lados, incluindo recusas | https://datatracker.ietf.org/doc/html/draft-mih-agent-bilateral-attestation-03 |
| **Agreement Evidence** (IETF) | Prova de que várias partes co-assinaram um resultado negociado | https://www.ietf.org/archive/id/draft-newton-agreement-evidence-00.html |
| **Open Agent Protocol** | Recibos assinados por todas as partes, em cadeia e ancorados em registos de transparência | https://openagentprotocol.eu/papers/accountability-in-the-agent-economy |
| **signed-receipts/v1** (extensão A2A) | Recibo assinado com Ed25519 anexado ao resultado de uma tarefa A2A | https://councilof.ai/spec/signed-receipts/ |
| Agent Receipts/obsigna, Signet, Aevum, Logsiegel, AgentLedger | Recibos e registos de ações de um agente | https://github.com/agent-receipts/obsigna · https://github.com/Prismer-AI/signet · https://github.com/aevum-labs/aevum · https://logsiegel.com/en/ · https://github.com/dembovvski/agentledger |
| Assinatura eletrónica com blockchain (DoxyChain, Chaindoc, OnChainESign) | Documentos assinados por pessoas | https://www.doxychain.com/products/esign · https://chaindoc.io/ |

**A nossa diferença, sem exageros:**

1. **A caixa negra dos Bots, Bot 2 Bot.** Os outros projetos partem dos pagamentos (AP2, da Google), das organizações e gateways (proposta IETF «Selo») ou das ações de um só agente. O nosso parte dos Bots e dos acordos entre eles: é a caixa negra que os Bots usam para selar o que combinam.
2. **Porta aberta para agentes de outras IA, mas com as regras dos Bots.** Quem não é Bot também pode registar, sem conta e sem pedir licença, desde que siga as regras da caixa negra dos Bots, sem regras próprias nem exceções. Isto aumenta o alcance sem tirar os Bots do centro e sem diluir o padrão.
3. **Mínimo e fácil de adotar.** Um ficheiro JSON e um verificador com cerca de 200 linhas. Várias propostas IETF são arquiteturas grandes, com entidades verificadas, gateways e tokens. Nós queremos ser a peça pequena que um Bot consegue usar numa tarde.
4. **Complementa e não substitui.** Funciona dentro do A2A, do MCP e do HTTPS, e pode referir um mandato AP2 ou uma credencial W3C como «quem autorizou».
5. **Aberto e sem patente.** Código MIT e especificação CC BY 4.0. O compromisso público de não patentear pode ser um argumento forte, porque a proposta concorrente tem uma patente pendente.
6. **Privacidade por defeito.** Guarda só hashes das mensagens e um resumo apenas se as duas partes consentirem. Encaixa no RGPD.
7. **Origem europeia, pensado para o Regulamento da IA**, sem nunca prometer conformidade automática.

**Honestidade:** a técnica (hashes encadeados, co-assinatura Ed25519) **não é nova** e outros já a usam. Partimos do princípio de que a concorrência tem ou terá algo parecido. A aposta está em ser a caixa negra **dos Bots**, simples e aberta, com uma porta para agentes de outras IA, e não mais um protocolo genérico de uma grande plataforma.

---

## 6. Plano em fases

**Fase 0: decisões.** Nome (BotVow), repositório público, licença MIT + CC BY 4.0 e compromisso de não patentear. ✔

**Fase 1: protótipo neutro.**
- Repositório próprio (este), a partir do protótipo anterior, com o formato `botvow/0.1`. ✔
- Verificador em Python, já existente, e uma versão em JavaScript para funcionar no browser e no Node.
- Exemplos **Bot 2 Bot** (dois Bots a selar um acordo) e um exemplo da porta aberta (um Bot com um agente de outra IA, a cumprir as mesmas regras), mais um teste que mostra que um registo fora das regras é recusado.
- Ligações: extensão para A2A (metadado da tarefa) e um servidor MCP pequeno com duas ferramentas, «selar» e «verificar».

**Fase 2: teste.**
- Testes de adulteração (já existem 8) e testes de compatibilidade com RFC 8785.
- Carimbo de tempo opcional (RFC 3161) e publicação opcional do hash final num registo de transparência.
- Revisão por 2 ou 3 programadores externos.

**Fase 3: lançamento aberto.**
- Página do projeto, publicação em listas e comunidades de agentes e, possivelmente, contribuição para a discussão na IETF ou no A2A.
- Sem faturação. O objetivo é a adoção e a reputação.

---

## 7. O que aproveitar do repositório atual

Repositório: https://github.com/Santiago1971/agent-agreement-black-box (commit `cf43527`). O protótipo foi adaptado neste repositório; o `run_demo.sh` atual corre 15 verificações e 7 testes unitários.

| Peça | Aproveitar? |
|---|---|
| `SPEC.md` (formato v0.1: genesis, proposal, counter, agreement, amendment, termination, seal; co-assinatura; cadeia de hashes) | **Sim**, quase tal como está; só muda o nome do `spec` |
| `tools/aabb.py` (criar e verificar, cerca de 200 linhas) | **Sim**, mudando o nome |
| `schema/record.schema.json` e `tools/check_schema.py` | **Sim** |
| `run_demo.sh` e os 8 testes de adulteração | **Sim** |
| Exemplos (agentes fictícios) | **Sim**, mas trocar por exemplos Bot 2 Bot e um exemplo da porta aberta |
| README e LICENSE | **Reescritos** para o BotVow |
| Secção «Known limits» e «Related work» | **Sim**, atualizada com as propostas IETF encontradas hoje |

O que falta (sai do âmbito da v0.1): carimbos de tempo de confiança, rotação e revogação de chaves, ligação das chaves a organizações reais e mais de duas partes na ferramenta.

---

## 8. Riscos

1. **Nome e marca.** O nome «Selo» foi abandonado por conflito (proposta IETF, pedido de marca nos EUA, patente pendente). O BotVow não tem conflito conhecido, mas a área da palavra «vow» tem projetos parecidos (/vow Protocol, Keptvow) e botvow.com está ocupado. Mitigação: usar botvow.org e `botvow`, e **verificar marcas na EUIPO, no INPI e no USPTO, com opinião jurídica, antes do lançamento**. Se houver problema, o plano B está na secção 1.4.
2. **Patente.** O autor da proposta IETF «Selo» declara um pedido de patente pendente sobre uma ideia vizinha (acordos assinados entre agentes de organizações). Mudar de nome não resolve isto. Não sabemos o que a patente cobre. **Antes de um lançamento público, é preciso uma opinião jurídica.** Isto não é aconselhamento legal.
3. **Mercado cheio.** Há pelo menos quatro propostas IETF e vários projetos abertos parecidos. Se não formos claramente mais simples e neutros, passamos despercebidos.
4. **Valor jurídico.** O recibo prova que certas chaves assinaram certo conteúdo, por certa ordem. Não prova quem controla a chave nem tem o valor de uma assinatura qualificada eIDAS ou de um notário. É preciso dizê-lo sempre.
5. **Identidade das chaves.** Sem ligação a um domínio ou Agent Card assinado, qualquer pessoa pode criar chaves.
6. **Privacidade (RGPD).** Uma cadeia pública nunca pode ter dados pessoais.
7. **Adoção e manutenção.** Um padrão só vale se outros o usarem, e o trabalho é contínuo, mesmo sem faturar.
8. **Concorrência dos grandes.** A Google, a OpenAI ou a Anthropic podem lançar algo parecido nas suas plataformas. A nossa resposta é sermos a caixa negra dos Bots, simples e aberta, com a porta aberta para os agentes delas, mas sempre com as regras dos Bots.

---

## 9. Próximos passos

1. Verificação de marcas (EUIPO, INPI, USPTO) e opinião jurídica (marca e patente de terceiros) antes de um lançamento mais amplo.
2. Verificador em JavaScript, ligação ao A2A e servidor MCP pequeno (ver ROADMAP.md).
3. Domínio do projeto (botvow.org), ainda não registado.
4. Revisão externa por programadores independentes.

---

*Fontes verificadas a 12/11/2026 (hora de Lisboa). Todos os links foram abertos e responderam, exceto a página npm, que bloqueia pedidos automáticos (confirmado pela API do registo npm).*
