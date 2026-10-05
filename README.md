# DONKI-FLR — Grupo 05

Pipeline e painel de dados de erupções solares (Solar Flares) da API DONKI da NASA.

## Arquitetura

O GitHub Actions executa `scripts/fetch_nasa.py` diariamente ou sob demanda. O script consulta a API DONKI/FLR, normaliza e deduplica os eventos e envia lotes ao PostgreSQL do Supabase. O `index.html`, publicado pelo GitHub Pages, lê os eventos e o registro da última execução pela API REST do Supabase.

```text
NASA DONKI/FLR → GitHub Actions → Supabase (PostgreSQL + REST) → GitHub Pages
```

## API e dados

A DONKI registra eventos de clima espacial. Este projeto acompanha erupções solares e apresenta classe, horários de início/pico/fim, localização e região ativa quando esses dados estão disponíveis. O coletor consulta a janela dos últimos 30 dias e usa `flrID` como identificador único para que execuções repetidas atualizem registros sem criar duplicatas.

Endpoint definido no enunciado: `https://api.nasa.gov/DONKI/FLR`.

## Responsabilidades do grupo

Preencher os responsáveis antes da entrega:

| Área | Integrante(s) |
|---|---|
| Pipeline e GitHub Actions | A definir |
| Banco de dados e Supabase | A definir |
| Painel web | A definir |
| Documentação e apresentação | A definir |

Integrantes: Cristofer, Saulo e Cauã.

## Configuração local

1. Crie o projeto Supabase `DONKI-FLR-DB` na região South America (São Paulo).
2. No SQL Editor do Supabase, execute [`sql/setup.sql`](sql/setup.sql).
3. Gere uma chave gratuita em [api.nasa.gov](https://api.nasa.gov/) e defina as variáveis de ambiente abaixo no ambiente local.
4. Instale Python 3.11 ou superior e execute `python scripts/fetch_nasa.py`.

```powershell
$env:NASA_API_KEY = "sua-chave-nasa"
$env:SUPABASE_URL = "https://seu-projeto.supabase.co"
$env:SUPABASE_SERVICE_KEY = "sua-chave-secreta-do-supabase"
python scripts/fetch_nasa.py
```

No GitHub, cadastre `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` em **Settings → Secrets and variables → Actions**. Cadastre `NASA_API_KEY` como Secret. Nunca coloque a chave secreta do Supabase no código ou no painel. O painel usa somente `SUPABASE_URL` e a chave pública (publishable/anon), que podem ser incluídas no `index.html`.

## Executar o pipeline

O workflow [`.github/workflows/update-data.yml`](.github/workflows/update-data.yml) agenda a coleta diária e também permite execução manual em **Actions → Atualizar dados DONKI FLR → Run workflow**. Ele precisa de `contents: read`, concorrência limitada e timeout configurado. Falhas totais ou parciais retornam código diferente de zero para ficarem visíveis no Actions; cada tentativa registra status na tabela `execucoes` quando o Supabase está acessível.

## Publicar o painel

1. Preencha `SUPABASE_URL` e `SUPABASE_ANON_KEY` no início de `index.html`.
2. No repositório GitHub, habilite **Settings → Pages → Deploy from a branch → main → /(root)**.
3. Abra o link mostrado nas configurações do GitHub Pages.

O painel oferece filtro por classe, pesquisa e exibe a última execução. O acesso público é somente leitura e as tabelas mantêm RLS habilitado.

## Estrutura

```text
index.html
scripts/fetch_nasa.py
sql/setup.sql
.github/workflows/update-data.yml
docs/ai-interaction.md
docs/reflexao.md
docs/tutorial.pdf          (a preparar)
docs/apresentacao.pdf      (a preparar)
```

## Endereços do projeto

- Organização GitHub: https://github.com/API-NASA-CCS
- Repositório: https://github.com/API-NASA-CCS/DONKI-FLR
- Projeto Supabase: https://supabase.com/dashboard/project/zrovqrglnouisspmnzot
- GitHub Pages: https://api-nasa-ccs.github.io/DONKI-FLR/

**Nomenclatura da organização:** o nome exibido no GitHub já está como `SN-2026-GRUPO-05-NASA`. O identificador usado no endereço da organização e do repositório continua `API-NASA-CCS`, então os links acima permanecem válidos.

## Documentação da entrega

O grupo deve completar `docs/ai-interaction.md` com os prompts e ajustes feitos com IA, `docs/reflexao.md` com a análise crítica, além de produzir o tutorial replicável (até 15 páginas), os slides e os prints de evidência para envio no Classroom.
