import flet as ft
import os
import requests
import json
from datetime import datetime
import zipfile

def main(page: ft.Page):
    page.title = "Backup Automatizado (GitHub + Supabase)"
    page.window_width = 450
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK

    github_token_input = ft.TextField(label="GitHub Personal Access Token", password=True, width=400)
    supa_url_input = ft.TextField(label="Supabase URL", value="https://kpzhyyvyyrblsmwzuelg.supabase.co", width=400)
    supa_key_input = ft.TextField(label="Supabase Key (Service Role ou Anon)", password=True, width=400)
    tables_input = ft.TextField(label="Tabelas do BD (separadas por vírgula)", value="categorias, erros, perfis", width=400)
    
    status_text = ft.Text("Aguardando...", color=ft.colors.YELLOW)
    progress_ring = ft.ProgressRing(visible=False)

    def log_status(msg, color=ft.colors.WHITE):
        status_text.value = msg
        status_text.color = color
        page.update()

    def realizar_backup(e):
        gh_token = github_token_input.value.strip()
        supa_url = supa_url_input.value.strip().rstrip('/')
        supa_key = supa_key_input.value.strip()
        tabelas_str = tables_input.value.strip()

        if not gh_token or not supa_url or not supa_key:
            log_status("Por favor, preencha todas as chaves!", ft.colors.RED)
            return

        progress_ring.visible = True
        log_status("Iniciando processo de backup...", ft.colors.BLUE)
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = f"Backup_Projeto_{timestamp}"
            os.makedirs(backup_folder, exist_ok=True)

            # 1. Backup do GitHub
            log_status("Baixando código do GitHub...")
            repo_owner = "vaz-gabriel"
            repo_name = "saas-essenza"
            
            gh_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/zipball/main"
            gh_headers = {"Authorization": f"token {gh_token}"}
            
            gh_response = requests.get(gh_url, headers=gh_headers)
            if gh_response.status_code == 200:
                with open(os.path.join(backup_folder, "codigo_github.zip"), "wb") as f:
                    f.write(gh_response.content)
            else:
                log_status(f"Aviso GitHub ({gh_response.status_code}), baixando banco...", ft.colors.ORANGE)

            # 2. Backup do Supabase via REST API (Robusto e sem erros)
            log_status("Conectando ao Supabase via API REST...")
            supa_headers = {
                "apikey": supa_key,
                "Authorization": f"Bearer {supa_key}"
            }
            
            tabelas = [t.strip() for t in tabelas_str.split(",") if t.strip()]
            
            for tabela in tabelas:
                log_status(f"Fazendo backup da tabela: {tabela}...")
                endpoint = f"{supa_url}/rest/v1/{tabela}?select=*"
                res = requests.get(endpoint, headers=supa_headers)
                
                if res.status_code == 200:
                    dados = res.json()
                    caminho_json = os.path.join(backup_folder, f"bd_{tabela}.json")
                    with open(caminho_json, "w", encoding="utf-8") as f:
                        json.dump(dados, f, ensure_ascii=False, indent=4)
                else:
                    raise Exception(f"Erro na tabela '{tabela}': Status {res.status_code}")

            # 3. Compactação Final
            log_status("Compactando backup final...")
            zip_final = f"{backup_folder}.zip"
            with zipfile.ZipFile(zip_final, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(backup_folder):
                    for file in files:
                        caminho_completo = os.path.join(root, file)
                        caminho_relativo = os.path.relpath(caminho_completo, backup_folder)
                        zipf.write(caminho_completo, caminho_relativo)

            log_status(f"✅ Sucesso! Backup salvo em: {zip_final}", ft.colors.GREEN)

        except Exception as ex:
            log_status(f"❌ Erro: {str(ex)}", ft.colors.RED)
        
        finally:
            progress_ring.visible = False
            page.update()

    btn_backup = ft.ElevatedButton("Iniciar Backup", on_click=realizar_backup, icon=ft.icons.BACKUP)

    page.add(
        ft.Text("Ferramenta de Backup Automatizado", size=20, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        github_token_input, supa_url_input, supa_key_input, tables_input,
        ft.Divider(),
        btn_backup,
        ft.Row([progress_ring, status_text])
    )

ft.app(target=main)
