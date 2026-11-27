"""Render matching SVG views of the baseline and delivered architecture; stdlib only."""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def render(final):
    good, bad, neutral = '#287c45', '#b42328', '#526174'
    accent = good if final else bad
    fill = '#edf8ef' if final else '#fff0ef'
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="990" viewBox="0 0 1100 990">',
           '<defs><marker id="arrow" markerWidth="9" markerHeight="8" refX="8" refY="4" orient="auto-start-reverse"><path d="M0,0 L8,4 L0,8 Z" fill="#526174"/></marker></defs>',
           '<rect width="1100" height="990" fill="white"/>']

    def text(x, y, lines, size=18, bold=False, color='#17212f'):
        for i, line in enumerate(lines):
            svg.append(f'<text x="{x}" y="{y + i * (size + 6)}" text-anchor="middle" font-family="DejaVu Sans, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{escape(line)}</text>')

    def box(x, y, w, h, title, lines, changed=False):
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{fill if changed else "#f3f5f8"}" stroke="{accent if changed else neutral}" stroke-width="2"/>')
        text(x + w / 2, y + 29, [title], 17 if len(title) > 24 else 20, True)
        text(x + w / 2, y + 57, lines, 17)

    def arrow(d, label=None, x=None, y=None, both=False, dashed=False):
        svg.append(f'<path d="{d}" fill="none" stroke="#526174" stroke-width="2" marker-end="url(#arrow)"' + (' marker-start="url(#arrow)"' if both else '') + (' stroke-dasharray="7 5"' if dashed else '') + '/>')
        if label:
            # Opaque label backgrounds keep crossing edges readable.
            for i, line in enumerate(label):
                width = max(30, len(line) * 8.4 + 14)
                svg.append(f'<rect x="{x - width/2}" y="{y + i*23 - 16}" width="{width}" height="22" fill="white"/>')
            text(x, y, label, 16)

    box(400, 15, 300, 75, 'Browser', ['Projetos, pipeline e media'])
    box(400, 150, 300, 95, 'nginx :8080', ['Única porta publicada', 'PUT/POST em fluxo'] if final else ['Entrada pública nominal', 'Pode guardar corpo em disco'], True)
    box(400, 320, 300, 110, 'api_gateway', ['JWT antes de receber o corpo', 'Identidade interna RS256'] if final else ['Corpo integral antes do JWT', 'Confia em identidade por header'], True)
    box(400, 510, 300, 120, 'projects', ['Autoriza objeto e operação', 'Motor comum; commit condicional', 'Tentativas e 3 vagas globais'] if final else ['Buffer integral; hash síncrono', 'ffprobe em ficheiro temporário', 'Orquestra imagens e vídeos'], True)
    box(790, 510, 280, 120, 'img_storage', ['Só projects por mTLS', 'Candidato com chave única', 'Adaptador em fluxo'] if final else ['Buffer integral do ficheiro', 'Sem autenticação própria', 'Fachada S3'], True)
    box(790, 715, 280, 100, 'SeaweedFS / S3', ['TLS; credencial por principal', 'Serviços internos em loopback'] if final else ['HTTP; credenciais da base', 'Originais e derivados'], True)
    box(400, 715, 300, 100, 'users / subscriptions', ['Perfis, presets e faturação', 'Quota cobrada no Apply'])
    box(20, 320, 280, 110, 'ws_gateway', ['JWT e autorização por sala', 'Revalida / suspende / corta'] if final else ['JWT opcional; join livre', 'Sem corte por revogação'], True)
    box(20, 715, 280, 100, 'RabbitMQ', ['AMQPS; exchange topic', 'Permissões por routing key'] if final else ['AMQP; exchange direct', 'Filas de trabalho e eventos'], True)
    box(20, 890, 280, 85, 'Workers de imagem/vídeo', ['Etapa / pipeline por mensagem'])

    arrow('M550 90 V150', ['HTTPS / WSS'], 550, 125, both=True)
    arrow('M550 245 V320', ['mTLS' if final else 'HTTP'], 550, 289)
    arrow('M550 430 V510', ['mTLS + RS256' if final else 'HTTPS não validado'], 550, 477)
    arrow('M700 570 H790', ['mTLS' if final else 'HTTP'], 745, 555)
    arrow('M930 630 V715', ['TLS + credencial' if final else 'HTTP S3'], 930, 680)
    arrow('M550 630 V715', ['mTLS; quota no Apply' if final else 'HTTPS não validado'], 550, 680)
    arrow('M700 375 H745 V765 H700', ['mTLS' if final else 'HTTPS'], 745, 460)
    arrow('M400 195 H160 V320', ['mTLS / Socket.IO' if final else 'HTTP / Socket.IO'], 160, 250, both=True)
    arrow('M160 715 V430', ['ws_queue', 'com projectId' if final else 'eventos'], 160, 581)
    arrow('M400 592 L300 745', ['pedidos /', 'resultados'], 350, 657, both=True)
    arrow('M160 815 V890', ['filas de trabalho / respostas'], 160, 861, both=True)
    arrow('M700 195 H1090 V765 H1070', ['PUT direto' if final else 'GET de URL', 'autorizado' if final else 'assinada', 'em fluxo' if final else 'por /s3/'], 980, 310)
    if final:
        arrow('M300 375 H345 V545 H400', ['join /', 'revalidar', 'mTLS'], 345, 472, dashed=True)
        arrow('M700 610 H765 V845 H930 V815', ['Leitura TLS em janelas de 4 MiB: ffprobe e hash'], 795, 880)
        text(700, 935, ['Verde: alterado por DA-1 / DA-2.', 'Tracejado: consulta de autorização WS.', 'Vista parcial; MongoDB e frontend omitidos.'], 17)
    else:
        text(700, 885, ['Vermelho: fragilidade diagnosticada.', '12 portas internas também publicadas no host.', 'Vista parcial; MongoDB e frontend omitidos.'], 17)
    svg.append('</svg>')
    return '\n'.join(svg) + '\n'


if __name__ == '__main__':
    for final, name in ((False, 'vista-antes-final.svg'), (True, 'vista-depois-final.svg')):
        (ROOT / name).write_text(render(final), encoding='utf-8')
