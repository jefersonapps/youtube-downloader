import os
import yt_dlp
from concurrent.futures import ThreadPoolExecutor


def download_video(url, output_path):
    ydl_opts = {
        "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
        "format": "bestvideo+bestaudio/best",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def download_videos_parallel(urls, output_path, max_workers=4):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_video, url, output_path) for url in urls]
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"Ocorreu um erro ao baixar o vídeo: {e}")


def main():
    downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")

    urls = input(
        "Digite as URLs dos vídeos para baixar, separadas por espaço: "
    ).split()

    print(f"Iniciando o download de {len(urls)} vídeos...")
    download_videos_parallel(urls, downloads_folder)
    print(f"Todos os vídeos foram baixados e salvos em {downloads_folder}")


if __name__ == "__main__":
    main()
