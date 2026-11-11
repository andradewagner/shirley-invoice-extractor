# Shirley Invoice Extractor

**API independente para identificação e extração de dados de documentos fiscais brasileiros.**

> 🚧 **Em desenvolvimento ativo.** Este projeto ainda não cobre todos os modelos fiscais, não realiza validação de autenticidade ou situação fiscal junto aos órgãos emissores e não deve ser exposto diretamente à internet sem controles adicionais de segurança.

## Sobre o projeto

O **Shirley Invoice Extractor** nasceu de uma necessidade de outro projeto: processar documentos fiscais sem incorporar a lógica de extração diretamente à aplicação principal. Em vez de criar uma funcionalidade fortemente acoplada à solução de origem, optei por desenvolver um **serviço autônomo, modular e reutilizável**, com API HTTP e distribuição por Docker.

A proposta é ampliar gradualmente o suporte aos **diferentes modelos de documentos fiscais utilizados no Brasil**, preservando um contrato de resposta consistente e mantendo cada parser isolado dos demais. O serviço poderá ser consumido por diferentes aplicações, independentemente do projeto que motivou sua criação.

### Por que “Shirley”?

**Shirley** é uma homenagem a ela e à nossa história. Depois de tudo o que passamos, escolhi dar seu nome a algo que estou construindo com dedicação — uma forma simples e pessoal de marcar essa trajetória.
https://drive.google.com/file/d/18zPABUPEfFBv8j0oVdUg14j-Xk0Ac2DF

## Estado atual

|                    Documento              |         PDF           |         XML           |
|                       ---                 |         ---           |         ---           |
| NF-e — Nota Fiscal Eletrônica (modelo 55) | Extração implementada | Extração implementada |
| NFS-e — Nota Fiscal de Serviços Eletrônica| Parser de PDF em evolução |     Planejado     |
| NFC-e — Nota Fiscal de Consumidor Eletrônica (modelo 65) | Planejado  |     Planejado     |
| CT-e — Conhecimento de Transporte Eletrônico (modelo 57) | Planejado  |     Planejado     |
|     Outros modelos fiscais brasileiros                   | Planejado  |     Planejado     |

A cobertura de layouts, principalmente para PDFs de NFS-e, ainda está sendo ampliada. **Extrair dados não significa validar a autenticidade fiscal do documento.**

### Funcionalidades existentes

- API HTTP com **FastAPI**.
- Detecção inicial de formato **PDF/XML**.
- Extração de texto de PDFs com **PyMuPDF** e `pdftotext`.
- Parser de **NF-e XML (modelo 55)** com tratamento seguro de XML por `defusedxml`.
- Respostas estruturadas em JSON, com indicação de situações que exigem revisão.
- Imagens Docker com estágios separados de execução e testes.
- Testes automatizados de parsers, detecção e endpoints HTTP.

## Executar com Docker

**Pré-requisito:** Docker instalado. Os comandos abaixo foram pensados para um terminal Linux e para execução local.

### 1. Obter o código

```bash
git clone https://github.com/andradewagner/shirley-invoice-extractor.git
cd shirley-invoice-extractor
```

> Durante o desenvolvimento, utilize a branch `feature/modular-extraction-engine` caso as alterações ainda não tenham sido integradas à `main`:
>
> ```bash
> git switch feature/modular-extraction-engine
> ```

### 2. Construir a imagem de execução

```bash
docker build \
  -f Dockerfile.slim \
  --target runtime \
  -t shirley-invoice-extractor:dev \
  .
```

O alvo `runtime` evita incluir dependências específicas de testes.

### 3. Iniciar a API

```bash
docker run --rm \
  --name shirley-invoice-extractor \
  --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m,mode=1777 \
  --cap-drop ALL \
  --memory 1g \
  --pids-limit 128 \
  -p 127.0.0.1:8000:8000 \
  shirley-invoice-extractor:dev
```

A API estará disponível **somente na própria máquina**, em `http://127.0.0.1:8000`. Para encerrar, pressione **Ctrl+C** no terminal do container.

### 4. Verificar a saúde do serviço

Em outro terminal:

```bash
curl --fail-with-body -sS http://127.0.0.1:8000/health
```

### 5. Extrair dados de um documento

Envie uma NF-e em PDF:

```bash
curl --fail-with-body -sS \
  -F "file=@/caminho/para/nota.pdf" \
  http://127.0.0.1:8000/v1/extract
```

Ou uma NF-e em XML (modelo 55):

```bash
curl --fail-with-body -sS \
  -F "file=@/caminho/para/nota.xml" \
  http://127.0.0.1:8000/v1/extract
```

O endpoint retorna um **JSON com os campos identificados**, por exemplo tipo do documento, número, emitente, data, valor e avisos de revisão, conforme o formato e os dados disponíveis. Documentos não suportados ou inválidos retornam erros HTTP apropriados.

## Executar os testes

Construa a imagem com as dependências de teste:

```bash
docker build \
  -f Dockerfile.slim \
  --target test \
  -t shirley-invoice-extractor:test \
  .
```

Execute a suíte usando o código-fonte local:

```bash
docker run --rm \
  --cap-drop ALL \
  --mount "type=bind,src=$PWD,dst=/workspace,readonly" \
  --workdir /workspace \
  --entrypoint python \
  shirley-invoice-extractor:test \
  -m unittest discover -s tests -p 'test_*.py' -v
```

## Arquitetura resumida

```text
Aplicação cliente
      |
      v
API HTTP /v1/extract
      |
      v
Detector de formato (PDF ou XML)
      |
      +--> Leitores e parsers PDF
      |
      +--> Parsers XML por modelo fiscal
      |
      v
Resposta estruturada em JSON
```

O processamento é **desacoplado dos sistemas consumidores**. Integrações com filas e outros serviços pertencem à camada de integração de cada aplicação e não são necessárias para executar esta API.

## Próximos passos

- Ampliar o reconhecimento dos **modelos fiscais**, além da distinção PDF/XML.
- Adicionar suporte a **NFC-e**, **NFS-e XML**, **CT-e** e outros documentos fiscais brasileiros.
- Expandir a cobertura de layouts e os testes com documentos sintéticos.
- Avaliar OCR para documentos digitalizados.
- Evoluir autenticação, limites de uso, observabilidade e verificações fiscais específicas antes de qualquer exposição pública.

## Segurança e limitações

- **Não exponha a API diretamente à internet:** a versão atual não possui autenticação entre serviços.
- Execute em rede confiável e aplique controles de acesso no ambiente de implantação.
- Os resultados extraídos podem exigir **revisão humana**.
- **Não há consulta oficial à SEFAZ ou a prefeituras** para confirmar autenticidade ou situação fiscal nesta etapa.
- Evite utilizar documentos reais com dados pessoais ou empresariais em exemplos públicos, issues e testes versionados.

---

**Status:** desenvolvimento ativo · **Escopo:** extração desacoplada de documentos fiscais brasileiros.
