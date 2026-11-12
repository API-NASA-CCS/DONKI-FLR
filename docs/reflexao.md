# Reflexão sobre o uso de IA

> Rascunho baseado no histórico disponível da conversa. O grupo deve ler, corrigir e aprovar este texto antes da entrega, pois a avaliação final precisa representar a experiência de todos os integrantes.

## Onde a IA ajudou

A IA ajudou a transformar o enunciado em tarefas menores e a preparar a estrutura do projeto: coletor em Python, workflow do GitHub Actions, tabelas do Supabase e painel publicado no GitHub Pages. Também explicou opções de configuração, organizou uma lista de pendências até o seminário e preparou um rascunho do histórico de prompts. Os primeiros logs mostraram secrets ausentes; depois que foram cadastrados, outra execução revelou HTTP 404 porque o endpoint DONKI antigo tinha sido migrado.

## Onde a IA errou ou precisou de correção

Durante a configuração do GitHub, a IA seguiu inicialmente um fluxo ligado à conta errada. Saulo esclareceu que a conta correta era **Sauloopf** e fez o login manualmente. A conexão exigiu várias tentativas e gerou frustração. O grupo também precisou distinguir um commit no GitHub das configurações e dados armazenados no Supabase. A publicação do Pages confirmou que o site estava hospedado, mas isso não comprovava que o pipeline havia coletado e gravado dados. As execuções agendadas falharam por ausência dos secrets. O projeto Supabase estava inativo quando foi verificado e foi reativado durante a finalização; ainda não há dados coletados.

## O que o grupo aprendeu

O grupo precisa validar cada parte do fluxo com evidência própria. Um workflow só está comprovado quando o Actions termina em verde e a tabela do Supabase recebe registros. O painel usa a chave pública de leitura; o coletor usa a chave secreta `service_role`, que deve ficar somente nos secrets do GitHub. Chaves privadas não devem aparecer em mensagens, código, commits ou capturas de tela. Também aprendemos a conferir os logs do Actions e os avisos oficiais do provedor: a DONKI migrou os endpoints em setembro de 2026 e a URL antiga passou a retornar 404. O código agora aponta para o endereço novo; ainda falta uma execução bem-sucedida com dados reais para validar o fluxo completo.

## Revisão do grupo antes da entrega

- Confirmar se todos os integrantes concordam com esta avaliação e acrescentar exemplos das contribuições individuais.
- Registrar qualquer uso de IA feito em outras conversas ou por outros integrantes.
- Atualizar este texto depois que o pipeline executar com sucesso e os dados aparecerem no painel.
