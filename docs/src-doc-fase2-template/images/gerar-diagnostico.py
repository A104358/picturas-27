"""Readable vector summaries of the baseline diagrams; Python standard library only."""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class Drawing:
    def __init__(self, width, height):
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                      '<defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto-start-reverse"><path d="M0,0 L8,4 L0,8 Z" fill="#506176"/></marker></defs>',
                      f'<rect width="{width}" height="{height}" fill="white"/>']

    def text(self, x, y, lines, size=18, bold=False, color='#17212f'):
        for i, line in enumerate(lines):
            self.parts.append(f'<text x="{x}" y="{y + i*(size+5)}" text-anchor="middle" font-family="DejaVu Sans, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{escape(line)}</text>')

    def box(self, x, y, w, h, title, lines, video=False, volume=False):
        color = '#c76c1b' if video else '#8056a5' if volume else '#526174'
        fill = '#fff2e4' if video else '#f5edfc' if volume else '#f3f5f8'
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{color}" stroke-width="2"/>')
        self.text(x+w/2, y+27, [title], 16 if len(title) > 21 else 19, True)
        self.text(x+w/2, y+51, lines, 13 if w < 150 else 16)

    def arrow(self, d, label=None, x=0, y=0, video=False, both=False, dashed=False):
        self.parts.append(f'<path d="{d}" fill="none" stroke="{"#c76c1b" if video else "#506176"}" stroke-width="2" marker-end="url(#a)"' + (' marker-start="url(#a)"' if both else '') + (' stroke-dasharray="6 4"' if dashed else '') + '/>')
        if label:
            width = len(label)*8.7+12
            self.parts.append(f'<rect x="{x-width/2}" y="{y-16}" width="{width}" height="22" fill="white"/>')
            self.text(x, y, [label], 16)

    def save(self, name):
        (ROOT/name).write_text('\n'.join(self.parts+['</svg>'])+'\n', encoding='utf-8')


def architecture():
    d=Drawing(1200,755)
    d.box(475,5,250,65,'Browser',['Projetos, pipeline e media'])
    d.box(475,125,250,75,'nginx :8080',['Entrada pública nominal'])
    d.box(20,275,220,75,'frontend',['Next.js / React'])
    d.box(300,275,260,75,'api_gateway',['JWT e encaminhamento'])
    d.box(650,275,240,75,'ws_gateway',['Socket.IO / progresso'])
    d.box(960,275,220,75,'SeaweedFS / S3',['Originais e resultados'])
    d.box(20,445,220,90,'users',['Perfis, presets e quota','MongoDB user'])
    d.box(300,445,260,90,'projects',['Projetos e orquestração','MongoDB project'])
    d.box(650,445,240,90,'subscriptions',['Planos / pagamentos','MongoDB subscription'])
    d.box(960,445,220,90,'img_storage',['Fachada de objetos S3'])
    d.box(20,645,220,80,'Ferramentas de imagem',['Uma etapa por mensagem'])
    d.box(300,645,260,80,'RabbitMQ',['Exchange direct picturas'])
    d.box(650,645,240,80,'video_tool',['Pipeline completo por vídeo'],video=True)
    d.box(960,645,220,80,'image_data',['Volume partilhado','projects + workers'],volume=True)
    d.arrow('M600 70 V125','HTTPS / WSS',600,103,both=True)
    d.arrow('M475 160 H130 V275','/',130,234)
    d.arrow('M545 200 V230 H430 V275','/api-gateway/',430,260)
    d.arrow('M725 160 H770 V275','/socket.io',770,234,both=True)
    d.arrow('M725 140 H1070 V275','/s3/ (leitura assinada)',1030,200)
    d.arrow('M300 315 H270 V490 H240')
    d.arrow('M430 350 V445','REST',430,405)
    d.arrow('M560 315 H610 V490 H650')
    d.arrow('M560 505 H590 V575 H1070 V535','Objetos por REST',820,568)
    d.arrow('M1070 445 V350','S3',1090,404)
    d.arrow('M430 535 V645','Pedidos / resultados',430,604,both=True)
    d.arrow('M300 680 H240','Etapas',270,665,both=True)
    d.arrow('M560 680 H650','Vídeo',605,665,both=True,video=True)
    d.arrow('M560 705 H615 V390 H770 V350','ws_queue',720,390)
    d.text(610,750,['Laranja: vídeo. Violeta: volume local. A base publica ainda portas internas no host.'],17)
    d.save('arquitetura-base-legivel.svg')


def sequence(name, messages, note):
    names=[('Browser',''),('nginx / API','entrada agrupada'),('projects',''),('users',''),('Storage / S3','agrupados'),('RabbitMQ',''),('video_tool',''),('wsGateway','')]
    xs=[72+150*i for i in range(8)]
    height=110+43*len(messages)+60
    d=Drawing(1200,height)
    for x,(title,sub) in zip(xs,names):
        d.box(x-68,8,136,67,title,[sub] if sub else [],video=title=='video_tool')
        d.parts.append(f'<path d="M{x} 75 V{height-53}" stroke="#b9c0c9" stroke-dasharray="5 5" fill="none"/>')
    for i,(source,target,label,video) in enumerate(messages):
        y=112+43*i
        path = (f'M{xs[source]} {y} H{xs[source]+75} V{y+12} H{xs[source]}' if source == target
                else f'M{xs[source]} {y} H{xs[target]}')
        d.arrow(path,label,(xs[source]+xs[target])/2,y-8,video=video)
    d.text(600,height-18,[note],16)
    d.save(name)


if __name__=='__main__':
    architecture()
    sequence('sequencia-base-a.svg',[
        (0,1,'1. POST vídeo (multipart)',False),
        (1,2,'2. Encaminhar corpo completo',False),
        (2,4,'3. Validar, calcular hash e guardar original',False),
        (0,1,'4. Definir efeitos do projeto',False),
        (1,2,'5. Validar e guardar pipeline / versão',False),
        (0,1,'6. Apply',False),
        (1,2,'7. POST process',False),
        (2,3,'8. Reservar operações',False),
        (2,4,'9. Obter originais para image_data',False),
        (2,2,'10. Registar todos os Process (local)',False),
        (2,5,'11. video_queue: pipeline completo / vídeo',True),
        (5,6,'12. Consumir um trabalho',True),
    ],'Base 0523102; interações agrupadas. No passo 10, o registo é local em projects, antes da publicação.')
    sequence('sequencia-base-b.svg',[
        (6,5,'13. ws_queue: video-progress',True),
        (5,7,'14. Progresso',True),
        (7,0,'15. Evento Socket.IO pelo nginx',True),
        (6,5,'16. project_queue: resposta final',True),
        (5,2,'17. Entregar resposta correlacionada',False),
        (2,4,'18. Persistir resultado(s)',False),
        (2,5,'19. Commit e notificação de conclusão',False),
        (5,7,'20. ws_queue',False),
        (7,0,'21. Resultado disponível (pelo nginx)',False),
        (0,1,'22. Pedir URL / ZIP',False),
        (1,2,'23. Consultar resultados confirmados',False),
        (2,0,'24. Resposta pela entrada pública',False),
    ],'Workers leem/escrevem image_data. Nas imagens, os passos por ferramenta regressam a projects entre etapas.')
