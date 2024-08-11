# API de Download de Vídeos

Esta é uma API baseada em FastAPI para baixar vídeos, rastrear seu progresso e gerenciar arquivos baixados. Ela utiliza SQLite para persistência de dados e yt-dlp para download de vídeos.

## Funcionalidades

- **Baixar Vídeos:** Inicie downloads de vídeos a partir de URLs fornecidas.
- **Rastrear Progresso:** Monitore o progresso do download.
- **Listar Arquivos Baixados:** Recupere informações sobre downloads concluídos.
- **Baixar Arquivos:** Baixe arquivos de vídeo completos.
- **Excluir Arquivos:** Exclua arquivos baixados do servidor.
- **Limpar Downloads:** Exclua todos os arquivos baixados e registros do banco de dados.

## Instalação

1. **Clone o repositório:**

```bash
git clone https://github.com/jefersonapps/youtube-downloader.git
```

2. **Navegue até o diretório do projeto:**

```bash
cd youtube-downloader
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Executando a API

Inicie o servidor de desenvolvimento FastAPI:

```bash
uvicorn main:app --reload
```

Isso iniciará o servidor em `http://127.0.0.1:8000`. A flag `--reload` ativa o recarregamento automático em alterações de código.

## Endpoints da API

Observação: Substitua `{id_do_download}` pelo ID real do download.

**Baixar um vídeo**

`POST /download/`

Corpo da Solicitação:

```json
{
  "url": "https://www.youtube.com/watch?v=id_do_video"
}
```

Resposta:

```json
{
  "message": "Download iniciado",
  "download_id": "uuid"
}
```

**Obter progresso do download**

`GET /progress/{id_do_download}`

Resposta:

```json
{
  "url": "url_do_video",
  "status": "Baixando/Concluído",
  "percent": 90.5,
  "title": "Título do Vídeo"
}
```

**Listar arquivos baixados**

`GET /list-files/`

Resposta:

```json
{
  "files": [
    {
      "file_name_encoded": "nome_do_arquivo_codificado_em_base64",
      "original_file_name": "nome_do_arquivo_original.mp4",
      "id": "id_do_download",
      "title": "Título do Vídeo",
      "url": "url_do_video"
    }
    // ... mais arquivos
  ]
}
```

**Baixar um arquivo**

`GET /download/{id_do_download}`

Resposta: _Arquivo baixado_

**Excluir um arquivo**

`DELETE /delete/{id_do_download}`

Resposta:

```json
{
  "message": "Arquivo excluído com sucesso"
}
```

**Limpar todos os downloads**

`DELETE /clear_downloads/`

Resposta:

```json
{
  "message": "Todos os downloads foram limpos com sucesso"
}
```

# Contribuindo

Pull requests são bem-vindos. Para mudanças maiores, por favor, abra um issue primeiro para discutir o que você gostaria de mudar.

## Licença

MIT
