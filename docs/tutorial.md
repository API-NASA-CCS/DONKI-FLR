# Tutorial de replicação — DONKI-FLR

Este guia descreve como montar o pipeline de erupções solares deste repositório. A solução consulta a API DONKI da NASA, salva os eventos no PostgreSQL do Supabase e publica o painel com GitHub Pages.

## 1. Componentes do projeto

```text
NASA DONKI/FLR → GitHub Actions → Supabase (PostgreSQL + REST) → GitHub Pages
```

- **API:** `https://api.nasa.gov/DONKI/FLR`
- **Coletor:** `scripts/fetch_nasa.py`
- **Modelo do banco:** `sql/setup.sql`
- **Agendamento e execução manual:** `.github/workflows/update-data.yml`
- **Painel:** `index.html`
- **Repositório do grupo:** https://github.com/API-NASA-CCS/DONKI-FLR
- **Painel publicado:** https://api-nasa-ccs.github.io/DONKI-FLR/
- **Projeto Supabase:** https://supabase.com/dashboard/project/zrovqrglnouisspmnzot

## 2. Contas e nomenclatura

O enunciado define a organização como `SN-2026-GRUPO-05-NASA`, o repositório como `DONKI-FLR` e o projeto Supabase como `DONKI-FLR-DB`. O repositório público está na organização com URL `https://github.com/API-NASA-CCS/DONKI-FLR`; o nome de exibição da organização foi ajustado para o padrão do grupo.

O projeto Supabase deve usar a região South America (São Paulo). Conforme o enunciado, convide o usuário `GilFerques` para a organização GitHub e `rafael.ferques@ifpr.edu.br` para o projeto Supabase com a permissão Developer. Confirme que os convites foram aceitos antes de encerrar a entrega.

## 3. Pré-requisitos

- Uma conta GitHub com acesso de escrita à organização e ao repositório.
- Um projeto Supabase na região São Paulo.
- Uma chave gratuita da NASA criada em https://api.nasa.gov/.
- Python 3.11 ou superior para executar o coletor localmente.
- A URL do projeto e uma chave secreta de servidor do Supabase.

O grupo tem três integrantes: Cristofer, Saulo e Cauã. Distribua entre eles as tarefas de pipeline, banco, painel e documentação; registre os responsáveis no README. O histórico desta conversa não confirma essa divisão.

## 4. Criar as tabelas e políticas

No projeto Supabase, abra o **SQL Editor** e execute o conteúdo completo de [`../sql/setup.sql`](../sql/setup.sql). O script cria:

- `public.flares`, com os campos normalizados do evento e o JSON original da NASA;
- `public.execucoes`, com horário, quantidade de registros, lotes, erros e status de cada coleta;
- uma restrição `UNIQUE` em `flr_id`, usada como chave natural do evento;
- índices para início do evento, classe e data de execução;
- RLS nas duas tabelas, política de leitura pública e permissões de leitura para `anon` e `authenticated`;
- permissões de escrita para `service_role`.

Depois da execução, confira no **Table Editor** se as duas tabelas existem e se o RLS aparece ativo. O painel só deve usar a chave pública. A chave `service_role` não pode ser colocada no HTML.

## 5. Como funciona a coleta

O arquivo `scripts/fetch_nasa.py` consulta os últimos 30 dias da API. Ele normaliza as datas para UTC, conserva campos úteis e a resposta original em `raw_payload`, descarta eventos sem identificador e elimina duplicatas por `flr_id` antes do upsert.

O script envia os eventos ao endpoint REST do Supabase em lotes de 100. A operação usa `on_conflict=flr_id` para inserir novos eventos e atualizar os já existentes sem duplicação. No fim, grava uma linha em `execucoes`. Se um lote falhar, o script registra o erro e encerra com código diferente de zero para que o Actions mostre a falha.

## 6. Configurar os secrets do GitHub

No repositório, abra **Settings → Secrets and variables → Actions → New repository secret**. Cadastre exatamente estes nomes:

| Nome | Valor |
|---|---|
| `NASA_API_KEY` | Chave pessoal criada em api.nasa.gov |
| `SUPABASE_URL` | URL do projeto, por exemplo `https://<project-ref>.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Chave Secret de servidor (`sb_secret_...`) ou chave legada `service_role` |

Digite as chaves diretamente na tela protegida do GitHub. Não as envie em chat, não as coloque no arquivo `.env` versionado e não tire capturas que mostrem os valores. Uma chave Secret moderna não é um JWT e o coletor a envia somente no cabeçalho `apikey`; para a chave legada `service_role`, ele também envia `Authorization: Bearer`. A chave pública do painel é diferente da chave secreta usada pelo coletor.

## 7. Testar o coletor localmente

No PowerShell, abra a raiz do repositório. Defina as variáveis apenas na sessão local e execute o script:

```powershell
$env:NASA_API_KEY = "sua-chave-da-nasa"
$env:SUPABASE_URL = "https://seu-projeto.supabase.co"
$env:SUPABASE_SERVICE_KEY = "sua-chave-secreta-do-supabase"
python scripts/fetch_nasa.py
```

Não salve os valores no histórico do Git. Um encerramento com código `0` indica coleta sem erros. Consulte a saída do terminal e depois confira as tabelas `flares` e `execucoes` no Supabase.

## 8. Configurar o GitHub Actions

O workflow `.github/workflows/update-data.yml` roda todos os dias às 09:17 UTC e também pode ser iniciado manualmente. Ele limita as permissões a `contents: read`, impede execuções concorrentes e encerra após dez minutos.

Depois de criar os três secrets:

1. Abra a aba **Actions** no repositório.
2. Selecione **Atualizar dados DONKI FLR**.
3. Clique em **Run workflow**, escolha `main` e confirme.
4. Abra a execução e confira se todas as etapas terminaram com ícone verde.
5. Abra os logs e anote o status e a quantidade de registros coletados.
6. No Supabase, confirme que há eventos em `flares` e uma execução em `execucoes`.

O enunciado exige pelo menos uma execução bem-sucedida com dados reais antes da entrega. Execuções agendadas que falham não atendem a esse requisito.

## 9. Configurar e verificar o painel

No início do `index.html`, confira `SUPABASE_URL` e `SUPABASE_ANON_KEY`. Use uma chave publishable (`sb_publishable_...`) ou a chave legada `anon`. O painel envia chaves publishable somente no cabeçalho `apikey`; para a chave legada `anon`, também usa `Authorization: Bearer`. Nunca substitua pela chave Secret ou `service_role`.

O painel consulta `flares` e `execucoes` pela API REST. Ele exibe classe, início, pico, localização, região ativa e um link para o evento. O seletor de classe e a busca por local/identificador são filtros interativos. `escapeHtml()` protege valores de texto externos; `safeExternalUrl()` aceita links HTTPS. A última execução vem da tabela `execucoes`.

Para testar no site publicado:

1. Abra https://api-nasa-ccs.github.io/DONKI-FLR/.
2. Confirme que a página informa registros carregados e mostra eventos.
3. Selecione uma classe e depois pesquise um identificador ou localização.
4. Confirme que o horário/status da última execução aparece.
5. Verifique no console do navegador se não há erro de rede ou acesso negado.

O site publicado pode continuar mostrando uma tabela vazia quando ainda não houve coleta bem-sucedida.

## 10. Publicar o GitHub Pages

No repositório GitHub, abra **Settings → Pages** e escolha **Deploy from a branch**, branch `main` e pasta `/(root)`. Salve. O workflow de Pages deve terminar com sucesso. O endereço público é https://api-nasa-ccs.github.io/DONKI-FLR/.

## 11. Evidências e entrega

Antes do prazo, produza capturas legíveis e sem chaves privadas:

- execução do workflow com status verde e resultado da coleta;
- Table Editor do Supabase mostrando registros em `flares` e uma execução em `execucoes`;
- painel publicado com dados, filtros e última atualização visíveis;
- endpoint REST retornando JSON com a chave pública, nunca com a chave secreta;
- links da organização e do repositório preenchidos nas colunas G e H da planilha de reserva.

O Classroom pede um único PDF de entrega com os links, a captura verde do workflow, a captura do Supabase, a URL REST e a confirmação dos links na planilha. O tutorial e os slides também devem estar versionados na pasta `docs/`.

## 12. Problemas comuns

| Sintoma | Verificação |
|---|---|
| Actions informa `Configuração ausente` | Confira se os três secrets existem e se os nomes estão exatamente iguais aos do workflow. |
| Actions falha ao conectar ao Supabase | Confira URL, chave secreta e status ativo do projeto Supabase. |
| Tabelas não aparecem no painel | Confirme a execução de `sql/setup.sql`, RLS, políticas de leitura e grants. |
| A tabela do painel fica vazia | Verifique a tabela `flares`, a última linha de `execucoes` e o console/rede do navegador. |
| GitHub Pages não atualiza | Confira branch `main`, pasta root e o resultado da implantação em **Actions**. |
| Projeto Supabase está pausado | Restaure o projeto no painel do Supabase e espere o banco ficar disponível antes de executar o pipeline. |

## 13. Preparação para o seminário

Organize a apresentação em até 20 minutos: API e motivação (6 min), arquitetura e modelagem (4 min), demonstração (8 min) e uso crítico da IA (2 min). Reserve até 10 minutos para perguntas. Todos os integrantes devem participar. Faça uma cópia local das capturas e grave um vídeo curto da demonstração para o caso de indisponibilidade da API ou da hospedagem.

## Referências

- Documentação e chave da NASA: https://api.nasa.gov/.
- Endpoint DONKI/FLR: https://api.nasa.gov/DONKI/FLR.
- Repositório do projeto: https://github.com/API-NASA-CCS/DONKI-FLR.
- Painel: https://api-nasa-ccs.github.io/DONKI-FLR/.
- Supabase: https://supabase.com/dashboard/project/zrovqrglnouisspmnzot.
- Tipos de chave e uso seguro: https://supabase.com/docs/guides/getting-started/api-keys.
- Requisitos da atividade: `Atividade Avaliativa 3 Trim (1).pdf` fornecido pelo grupo.
