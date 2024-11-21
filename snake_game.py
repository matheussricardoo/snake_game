import pygame
import random
import sys
import json
import math
from pygame import mixer

# Inicialização do Pygame
pygame.init()
mixer.init()

# Cores
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
VERDE_CLARO = (50, 205, 50)
VERDE_ESCURO = (34, 139, 34)
VERMELHO = (220, 20, 60)
AZUL = (30, 144, 255)
CINZA = (169, 169, 169)
DOURADO = (255, 215, 0)
ROXO = (147, 112, 219)
LARANJA = (255, 140, 0)
ROSA = (255, 20, 147)
CIANO = (0, 255, 255)

# Configurações da tela
LARGURA_TOTAL = 1100
LARGURA_JOGO = 800
ALTURA = 600
AREA_LATERAL = LARGURA_TOTAL - LARGURA_JOGO
TAMANHO_BLOCO = 20

# Configurações do jogo
VELOCIDADE_INICIAL = 3
AUMENTO_VELOCIDADE = 0.05

class SnakeGame:
    def __init__(self):
        self.tela = pygame.display.set_mode((LARGURA_TOTAL, ALTURA))
        pygame.display.set_caption('Snake Game 🐍')
        self.clock = pygame.time.Clock()
        
        # Configuração de idioma
        self.idioma = 'pt-br'
        self.todos_textos = self.carregar_todos_textos()
        self.textos = self.todos_textos[self.idioma]
        
        # Configurações de jogo
        self.modo_sem_paredes = False
        self.modo_noturno = False
        
        # Inicialização dos sons
        self.inicializar_sons()
        
        # Configurações visuais
        self.cores = self.definir_cores()
        
        # Power-ups
        self.power_ups = {
            'invencibilidade': {'cor': DOURADO, 'duracao': 150, 'chance': 5},
            'velocidade_reduzida': {'cor': CIANO, 'duracao': 200, 'chance': 5},
            'atravessar_corpo': {'cor': ROXO, 'duracao': 100, 'chance': 5},
            'pontos_dobrados': {'cor': LARANJA, 'duracao': 150, 'chance': 5}
        }
        self.power_up_ativo = None
        self.tempo_power_up = 0
        
        # Sistema de conquistas
        self.inicializar_conquistas()
        
        # Estatísticas
        self.estatisticas = self.carregar_estatisticas()
        
        # Botões e interface
        self.inicializar_interface()
        
        # Estado do jogo
        self.carregar_recorde()
        self.tela_inicial = True
        self.reset_game()
        self.efeito_morte = 0  # Contador para efeito de morte

    def inicializar_sons(self):
        try:
            self.sons = {
                'comida': pygame.mixer.Sound('assets/eat.wav'),
                'colisao': pygame.mixer.Sound('assets/collision.wav'),
                'power_up': pygame.mixer.Sound('assets/powerup.wav'),
                'conquista': pygame.mixer.Sound('assets/achievement.wav')
            }
            pygame.mixer.music.load('assets/background.mp3')
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
            self.musica_ativa = True
            self.som_ativo = True
        except:
            print("Aviso: Arquivos de som não encontrados")
            self.musica_ativa = False
            self.som_ativo = False

    def definir_cores(self):
        return {
            'dia': {
                'fundo': PRETO,
                'grade': (20, 20, 20),
                'lateral': (30, 30, 30)
            },
            'noite': {
                'fundo': (10, 10, 30),
                'grade': (30, 30, 50),
                'lateral': (20, 20, 40)
            }
        }

    def inicializar_conquistas(self):
        self.conquistas = {
            'velocista': {'obtida': False, 'desc': 'Atingiu velocidade máxima'},
            'guloso': {'obtida': False, 'desc': 'Comeu 50 frutas'},
            'imortal': {'obtida': False, 'desc': 'Alcançou 1000 pontos'},
            'arco_iris': {'obtida': False, 'desc': 'Coletou todos os power-ups'},
            'sem_paredes': {'obtida': False, 'desc': 'Sobreviveu 2 minutos sem paredes'},
            'pro': {'obtida': False, 'desc': 'Alcançou nível 10'}
        }
        self.carregar_conquistas()

    def carregar_estatisticas(self):
        try:
            with open('stats.json', 'r') as arquivo:
                return json.load(arquivo)
        except:
            return {
                'partidas_jogadas': 0,
                'total_pontos': 0,
                'maior_combo': 0,
                'power_ups_coletados': 0,
                'tempo_total': 0
            }

    def salvar_estatisticas(self):
        with open('stats.json', 'w') as arquivo:
            json.dump(self.estatisticas, arquivo)

    def reset_game(self):
        self.cobra = [(LARGURA_JOGO//2, ALTURA//2)]
        self.direcao = 'DIREITA'
        self.gerar_nova_comida()
        self.pontuacao = 0
        self.velocidade = VELOCIDADE_INICIAL
        self.game_over = False
        self.pause = False
        self.combo = 0
        self.tempo_jogo = 0
        self.power_up_ativo = None
        self.tempo_power_up = 0
        self.nivel = 1

    def gerar_nova_comida(self):
        # Chance de gerar power-up
        if random.randint(1, 100) <= 10:  # 10% de chance de power-up
            tipo = random.choice(list(self.power_ups.keys()))
            eh_power_up = True
        else:
            tipo = 'normal'
            eh_power_up = False

        while True:
            x = random.randrange(0, LARGURA_JOGO - TAMANHO_BLOCO, TAMANHO_BLOCO)
            y = random.randrange(0, ALTURA - TAMANHO_BLOCO, TAMANHO_BLOCO)
            if (x, y) not in self.cobra:
                self.comida = (x, y, tipo, eh_power_up)
                break

    def aplicar_power_up(self, tipo):
        self.power_up_ativo = tipo
        self.tempo_power_up = self.power_ups[tipo]['duracao']
        self.tocar_som('power_up')
        self.estatisticas['power_ups_coletados'] += 1

    def atualizar_power_up(self):
        if self.power_up_ativo:
            self.tempo_power_up -= 1
            if self.tempo_power_up <= 0:
                self.power_up_ativo = None

    def verificar_conquistas(self):
        conquistas_antigas = {k: v['obtida'] for k, v in self.conquistas.items()}
        
        if self.velocidade >= 25:
            self.conquistas['velocista']['obtida'] = True
        if self.estatisticas['power_ups_coletados'] >= 10:
            self.conquistas['arco_iris']['obtida'] = True
        if self.pontuacao >= 1000:
            self.conquistas['imortal']['obtida'] = True
        if self.nivel >= 10:
            self.conquistas['pro']['obtida'] = True
        
        for k, v in self.conquistas.items():
            if v['obtida'] and not conquistas_antigas[k]:
                self.tocar_som('conquista')
                self.mostrar_conquista(k)
                self.salvar_conquistas()

    def desenhar_efeitos_visuais(self):
        if self.power_up_ativo:
            # Efeito de brilho ao redor da cobra
            for x, y in self.cobra:
                pygame.draw.circle(self.tela, 
                                 self.power_ups[self.power_up_ativo]['cor'],
                                 (x + TAMANHO_BLOCO//2, y + TAMANHO_BLOCO//2),
                                 TAMANHO_BLOCO * 0.8,
                                 2)

    def desenhar_interface(self):
        cores = self.cores['noite'] if self.modo_noturno else self.cores['dia']
        
        # Fundo da área lateral com gradiente suave
        for i in range(AREA_LATERAL):
            alpha = i / AREA_LATERAL
            cor = tuple(max(0, min(255, c - (c * alpha * 0.3))) for c in cores['lateral'])
            pygame.draw.line(self.tela, cor,
                            (LARGURA_JOGO + i, 0),
                            (LARGURA_JOGO + i, ALTURA))
        
        # Título "SNAKE"
        fonte_titulo = pygame.font.Font(None, 48)
        titulo = fonte_titulo.render("SNAKE", True, VERDE_CLARO)
        titulo_rect = titulo.get_rect(center=(LARGURA_JOGO + AREA_LATERAL//2, 40))
        self.tela.blit(titulo, titulo_rect)
        
        # Container para status
        status_container = pygame.Surface((AREA_LATERAL - 40, 180))
        status_container.fill((20, 20, 20))
        status_container.set_alpha(200)
        self.tela.blit(status_container, (LARGURA_JOGO + 20, 80))
        
        # Informações de status
        fonte_status = pygame.font.Font(None, 32)
        y_status = 100
        spacing = 40
        
        status_info = [
            (self.textos['pontuacao_label'], str(self.pontuacao), BRANCO),
            (self.textos['recorde_label'], str(self.recorde), DOURADO),
            (self.textos['nivel_label'], str(self.nivel), VERDE_CLARO),
            (self.textos['velocidade_label'], str(int(self.velocidade)), LARANJA)
        ]
        
        for label, valor, cor in status_info:
            # Label
            texto_label = fonte_status.render(label + ":", True, CINZA)
            self.tela.blit(texto_label, (LARGURA_JOGO + 40, y_status))
            
            # Valor
            texto_valor = fonte_status.render(valor, True, cor)
            valor_x = LARGURA_JOGO + AREA_LATERAL - texto_valor.get_width() - 40
            self.tela.blit(texto_valor, (valor_x, y_status))
            
            y_status += spacing
        
        # Linha separadora
        pygame.draw.line(self.tela, CINZA,
                        (LARGURA_JOGO + 30, y_status + 10),
                        (LARGURA_JOGO + AREA_LATERAL - 30, y_status + 10), 1)
        
        # Container para configurações
        config_container = pygame.Surface((AREA_LATERAL - 40, 140))
        config_container.fill((20, 20, 20))
        config_container.set_alpha(200)
        self.tela.blit(config_container, (LARGURA_JOGO + 20, y_status + 30))
        
        # PAREDES
        y_paredes = y_status + 50
        fonte_config = pygame.font.Font(None, 32)
        texto_paredes = fonte_config.render(self.textos['modo_paredes'], True, CINZA)
        self.tela.blit(texto_paredes, (LARGURA_JOGO + 40, y_paredes))
        
        estado_paredes = "ON" if not self.modo_sem_paredes else "OFF"
        cor_estado = VERDE_CLARO if not self.modo_sem_paredes else VERMELHO
        texto_estado = fonte_config.render(estado_paredes, True, cor_estado)
        estado_x = LARGURA_JOGO + AREA_LATERAL - texto_estado.get_width() - 40
        self.tela.blit(texto_estado, (estado_x, y_paredes))
        
        # Tecla M
        fonte_tecla = pygame.font.Font(None, 24)
        texto_tecla = fonte_tecla.render(self.textos['tecla_m'], True, CINZA)
        tecla_x = LARGURA_JOGO + (AREA_LATERAL - texto_tecla.get_width()) // 2
        self.tela.blit(texto_tecla, (tecla_x, y_paredes + 30))
        
        # MODO
        y_modo = y_paredes + 70
        texto_modo = fonte_config.render(self.textos['modo'], True, CINZA)
        self.tela.blit(texto_modo, (LARGURA_JOGO + 40, y_modo))
        
        estado_modo = self.textos['modo_noturno'] if self.modo_noturno else self.textos['modo_claro']
        cor_modo = ROXO if self.modo_noturno else AZUL
        texto_estado_modo = fonte_config.render(estado_modo, True, cor_modo)
        estado_modo_x = LARGURA_JOGO + AREA_LATERAL - texto_estado_modo.get_width() - 40
        self.tela.blit(texto_estado_modo, (estado_modo_x, y_modo))
        
        # Tecla N
        texto_tecla_n = fonte_tecla.render(self.textos['tecla_n'], True, CINZA)
        tecla_n_x = LARGURA_JOGO + (AREA_LATERAL - texto_tecla_n.get_width()) // 2
        self.tela.blit(texto_tecla_n, (tecla_x, y_modo + 30))

    def desenhar_cobra(self):
        if self.game_over:
            # Efeito de morte da cobra
            self.efeito_morte += 1
            alpha = max(0, 255 - self.efeito_morte * 5)  # Fade out
            
            for i, (x, y) in enumerate(self.cobra):
                # Efeito pulsante vermelho
                intensidade = abs(math.sin(self.efeito_morte * 0.1)) * 255
                cor_morte = (255, max(0, intensidade - 100), 0)
                
                if i == 0:  # Cabeça
                    # Cabeça vermelha pulsante
                    pygame.draw.rect(self.tela, cor_morte, 
                                   (x, y, TAMANHO_BLOCO-2, TAMANHO_BLOCO-2),
                                   border_radius=8)
                    # Olhos vermelhos
                    pygame.draw.circle(self.tela, (255, 0, 0), 
                                     (x + 15, y + 5), 3)
                    pygame.draw.circle(self.tela, (255, 0, 0), 
                                     (x + 15, y + 15), 3)
                else:
                    # Corpo com efeito de fade out
                    cor_segmento = (max(0, intensidade - 150), 0, 0)
                    pygame.draw.rect(self.tela, cor_segmento, 
                                   (x, y, TAMANHO_BLOCO-2, TAMANHO_BLOCO-2),
                                   border_radius=5)
        else:
            # Design normal da cobra (mais elaborado)
            for i, (x, y) in enumerate(self.cobra):
                if i == 0:  # Cabeça
                    # Corpo da cabeça
                    pygame.draw.rect(self.tela, VERDE_CLARO, 
                                   (x, y, TAMANHO_BLOCO-2, TAMANHO_BLOCO-2),
                                   border_radius=8)
                    
                    # Olhos
                    if self.direcao in ['DIREITA', 'ESQUERDA']:
                        olho1_pos = (x + 15, y + 5)
                        olho2_pos = (x + 15, y + 15)
                    elif self.direcao == 'CIMA':
                        olho1_pos = (x + 5, y + 5)
                        olho2_pos = (x + 15, y + 5)
                    else:  # BAIXO
                        olho1_pos = (x + 5, y + 15)
                        olho2_pos = (x + 15, y + 15)
                    
                    # Olhos brancos com pupila preta
                    for olho_pos in [olho1_pos, olho2_pos]:
                        pygame.draw.circle(self.tela, BRANCO, olho_pos, 3)
                        pygame.draw.circle(self.tela, PRETO, olho_pos, 1)
                    
                else:  # Corpo
                    # Gradiente de cor para o corpo
                    intensidade = max(50, 255 - (i * 8))
                    cor_corpo = (0, intensidade, 0)
                    
                    # Efeito de escamas
                    pygame.draw.rect(self.tela, cor_corpo,
                                   (x, y, TAMANHO_BLOCO-2, TAMANHO_BLOCO-2),
                                   border_radius=5)
                    
                    # Detalhe interno para parecer escamas
                    if i % 2 == 0:
                        pygame.draw.rect(self.tela, (0, min(255, intensidade + 20), 0),
                                       (x+2, y+2, TAMANHO_BLOCO-6, TAMANHO_BLOCO-6),
                                       border_radius=3)

    def mover(self):
        if self.game_over:
            pygame.mixer.music.stop()
            return

        x, y = self.cobra[0]
        
        # Movimento normal
        if self.direcao == 'CIMA':
            y -= TAMANHO_BLOCO
        elif self.direcao == 'BAIXO':
            y += TAMANHO_BLOCO
        elif self.direcao == 'ESQUERDA':
            x -= TAMANHO_BLOCO
        elif self.direcao == 'DIREITA':
            x += TAMANHO_BLOCO

        # Verificação de colisão com paredes
        if x < 0 or x >= LARGURA_JOGO or y < 0 or y >= ALTURA:
            if self.power_up_ativo == 'invencibilidade':
                # Com invencibilidade, atravessa as paredes
                x = (x + LARGURA_JOGO) % LARGURA_JOGO
                y = (y + ALTURA) % ALTURA
            elif not self.modo_sem_paredes:
                self.game_over = True
                self.tocar_som('colisao')
                return
            else:
                # Modo sem paredes normal
                x = (x + LARGURA_JOGO) % LARGURA_JOGO
                y = (y + ALTURA) % ALTURA

        # Verificação de colisão com o próprio corpo
        if (x, y) in self.cobra[1:] and self.power_up_ativo != 'atravessar_corpo':
            self.game_over = True
            self.tocar_som('colisao')
            return

        self.cobra.insert(0, (x, y))

        # Verificação de comida com velocidade mais controlada
        if (x, y) == (self.comida[0], self.comida[1]):
            self.tocar_som('comida')
            
            if self.comida[3]:  # É power-up
                self.aplicar_power_up(self.comida[2])
            
            pontos = 20 if self.power_up_ativo == 'pontos_dobrados' else 10
            self.pontuacao += pontos * (self.combo + 1)
            self.combo += 1
            
            # Ajuste mais suave da velocidade
            novo_nivel = self.pontuacao // 100 + 1
            if novo_nivel != self.nivel:
                self.nivel = novo_nivel
                self.velocidade = VELOCIDADE_INICIAL + (self.nivel - 1) * AUMENTO_VELOCIDADE
                self.velocidade = min(self.velocidade, 10)  # Limita a velocidade máxima
            
            if self.combo > self.estatisticas['maior_combo']:
                self.estatisticas['maior_combo'] = self.combo
            
            self.gerar_nova_comida()
        else:
            self.cobra.pop()
            self.combo = 0

        self.verificar_conquistas()
        self.atualizar_power_up()
        self.tempo_jogo += 1

    def desenhar_tela_inicial(self):
        cores = self.cores['noite'] if self.modo_noturno else self.cores['dia']
        self.tela.fill(cores['fundo'])
        
        # Desenha grade de fundo
        for x in range(0, LARGURA_TOTAL, TAMANHO_BLOCO):
            for y in range(0, ALTURA, TAMANHO_BLOCO):
                pygame.draw.rect(self.tela, cores['grade'], 
                               (x, y, TAMANHO_BLOCO, TAMANHO_BLOCO), 1)
        
        # Container principal
        container = pygame.Surface((LARGURA_TOTAL - 200, ALTURA - 100))
        container.fill((20, 20, 20))
        container.set_alpha(230)
        container_rect = container.get_rect(center=(LARGURA_TOTAL//2, ALTURA//2))
        self.tela.blit(container, container_rect)
        
        # Título com efeito de brilho
        tempo = pygame.time.get_ticks() / 1000
        brilho = abs(math.sin(tempo * 2)) * 50
        cor_titulo = tuple(min(255, c + brilho) for c in VERDE_CLARO)
        
        fonte_titulo = pygame.font.Font(None, 100)
        titulo = fonte_titulo.render("SNAKE", True, cor_titulo)
        titulo_rect = titulo.get_rect(center=(LARGURA_TOTAL//2, 100))
        self.tela.blit(titulo, titulo_rect)
        
        # Botão de música (atualizado para usar texto em vez de emoji)
        self.botao_musica = Botao(
            LARGURA_TOTAL - 100, 20, 80, 40,
            "SOM: ON" if self.musica_ativa else "SOM: OFF",
            VERDE_CLARO if self.musica_ativa else VERMELHO
        )
        self.botao_musica.desenhar(self.tela)
        
        # Subtítulo
        fonte_subtitulo = pygame.font.Font(None, 36)
        subtitulo = fonte_subtitulo.render(self.textos['subtitulo'], True, BRANCO)
        subtitulo_rect = subtitulo.get_rect(center=(LARGURA_TOTAL//2, 160))
        self.tela.blit(subtitulo, subtitulo_rect)
        
        # Recorde
        texto_recorde = fonte_subtitulo.render(
            self.textos['recorde'].format(self.recorde), True, DOURADO)
        recorde_rect = texto_recorde.get_rect(center=(LARGURA_TOTAL//2, 200))
        self.tela.blit(texto_recorde, recorde_rect)
        
        # Botões centralizados
        self.botao_comecar.rect.center = (LARGURA_TOTAL//2, 260)
        self.botao_comecar.desenhar(self.tela)
        
        self.botao_idioma.rect.center = (LARGURA_TOTAL//2, 320)
        self.botao_idioma.desenhar(self.tela)
        
        # Seção de Power-ups
        fonte_power = pygame.font.Font(None, 40)
        titulo_power = fonte_power.render(self.textos['power_ups_titulo'], 
                                        True, DOURADO)
        titulo_rect = titulo_power.get_rect(center=(LARGURA_TOTAL//2, 380))
        self.tela.blit(titulo_power, titulo_rect)
        
        # Power-ups com ícones e descrições
        fonte_desc = pygame.font.Font(None, 28)
        y_start = 420
        x_start = LARGURA_TOTAL//2 - 300
        
        for i, (power, info) in enumerate(self.power_ups.items()):
            # Ícone com brilho
            pygame.draw.rect(self.tela, info['cor'],
                            (x_start, y_start + i*35, 25, 25),
                            border_radius=5)
            pygame.draw.rect(self.tela, BRANCO,
                            (x_start, y_start + i*35, 25, 25),
                            border_radius=5, width=1)
            
            # Descrição
            desc = self.textos['power_up_desc'][power]
            texto = fonte_desc.render(desc, True, BRANCO)
            self.tela.blit(texto, (x_start + 35, y_start + i*35 + 5))

    def executar(self):
        while True:
            self.clock.tick(30)
            pos_mouse = pygame.mouse.get_pos()
            
            if self.tela_inicial:
                # Atualiza hover apenas na tela inicial
                if hasattr(self, 'botao_musica'):
                    self.botao_musica.verifica_hover(pos_mouse)
                self.botao_comecar.verifica_hover(pos_mouse)
                self.botao_idioma.verifica_hover(pos_mouse)
                
                for evento in pygame.event.get():
                    if evento.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    
                    if evento.type == pygame.MOUSEBUTTONDOWN:
                        if self.botao_comecar.ativo:
                            self.tela_inicial = False
                            self.reset_game()
                        elif self.botao_idioma.ativo:
                            self.trocar_idioma()
                        elif hasattr(self, 'botao_musica') and self.botao_musica.rect.collidepoint(pos_mouse):
                            self.musica_ativa = not self.musica_ativa
                            if self.musica_ativa:
                                pygame.mixer.music.play(-1)
                                pygame.mixer.music.set_volume(0.5)
                            else:
                                pygame.mixer.music.stop()
                    
                    if evento.type == pygame.KEYDOWN:
                        if evento.key == pygame.K_n:
                            self.modo_noturno = not self.modo_noturno
                
                self.desenhar_tela_inicial()
            else:
                # Loop principal do jogo
                for evento in pygame.event.get():
                    if evento.type == pygame.QUIT:
                        self.salvar_estatisticas()
                        self.salvar_conquistas()
                        pygame.quit()
                        sys.exit()
                    
                    self.processar_eventos(evento)
                
                if not self.pause and not self.game_over:
                    self.mover()
                
                self.desenhar()
            
            pygame.display.flip()

    def trocar_idioma(self):
        self.idioma = 'en' if self.idioma == 'pt-br' else 'pt-br'
        self.textos = self.todos_textos[self.idioma]
        
        # Atualiza textos dos botões
        self.botao_comecar.texto = self.textos['comecar']
        self.botao_idioma.texto = self.textos['idioma']
        self.botao_reiniciar.texto = self.textos['reiniciar']
        
        # Se existir o botão de menu (game over)
        if hasattr(self, 'botao_menu'):
            self.botao_menu.texto = self.textos['menu_principal']

    def carregar_todos_textos(self):
        return {
            'pt-br': {
                'pontuacao': 'Pontuação: {}',
                'pausado': 'PAUSADO',
                'game_over': 'Fim de Jogo!',
                'reiniciar': 'Reiniciar',
                'idioma': 'EN/PT',
                'recorde': 'Recorde: {}',
                'comecar': 'COMEÇAR',
                'titulo_inicial': 'SNAKE GAME',
                'subtitulo': 'Use as setas ou WASD para mover',
                'nivel': 'Nível: {}',
                'modo_paredes': 'PAREDES',
                'com_paredes': 'ON',
                'sem_paredes': 'OFF',
                'menu_principal': 'Menu Principal',
                'modo_noturno': 'NOTURNO',
                'modo_claro': 'CLARO',
                'velocidade': 'Velocidade: {}',
                'power_up': 'Power-up: {}',
                'power_ups_titulo': 'Power-Ups:',
                'power_up_desc': {
                    'invencibilidade': 'Invencível contra paredes',
                    'velocidade_reduzida': 'Reduz a velocidade',
                    'atravessar_corpo': 'Atravessa o próprio corpo',
                    'pontos_dobrados': 'Pontos em dobro'
                },
                'modo': 'MODO',
                'tecla_m': '(Tecla M)',
                'tecla_n': '(Tecla N)',
                'pontuacao_label': 'Pontuação',
                'recorde_label': 'Recorde',
                'nivel_label': 'Nível',
                'velocidade_label': 'Velocidade'
            },
            'en': {
                'pontuacao': 'Score: {}',
                'pausado': 'PAUSED',
                'game_over': 'Game Over!',
                'reiniciar': 'Restart',
                'idioma': 'EN/PT',
                'recorde': 'High Score: {}',
                'comecar': 'START',
                'titulo_inicial': 'SNAKE GAME',
                'subtitulo': 'Use arrows or WASD to move',
                'nivel': 'Level: {}',
                'modo_paredes': 'WALLS',
                'com_paredes': 'ON',
                'sem_paredes': 'OFF',
                'menu_principal': 'Main Menu',
                'modo_noturno': 'NIGHT',
                'modo_claro': 'LIGHT',
                'velocidade': 'Speed: {}',
                'power_up': 'Power-up: {}',
                'power_ups_titulo': 'Power-Ups:',
                'power_up_desc': {
                    'invencibilidade': 'Invincible against walls',
                    'velocidade_reduzida': 'Reduces speed',
                    'atravessar_corpo': 'Pass through body',
                    'pontos_dobrados': 'Double points'
                },
                'modo': 'MODE',
                'tecla_m': '(Key M)',
                'tecla_n': '(Key N)',
                'pontuacao_label': 'Score',
                'recorde_label': 'High Score',
                'nivel_label': 'Level',
                'velocidade_label': 'Speed'
            }
        }

    def inicializar_interface(self):
        self.botao_reiniciar = Botao(LARGURA_JOGO + 35, 100, 130, 40, 
                                    self.textos['reiniciar'], VERDE_ESCURO)
        self.botao_idioma = Botao(LARGURA_JOGO + 35, 160, 130, 40, 
                                 self.textos['idioma'], AZUL)
        self.botao_comecar = Botao(LARGURA_TOTAL//2 - 100, ALTURA//2, 200, 50,
                                  self.textos['comecar'], VERDE_ESCURO)
        self.botao_paredes = Botao(
            LARGURA_JOGO + 35, 280, 130, 40,
            self.textos['modo_paredes'], VERDE_ESCURO)
        
        self.botao_modo_noturno = Botao(
            LARGURA_JOGO + 35, 340, 130, 40,
            self.textos['modo_noturno'], AZUL)

    def carregar_recorde(self):
        try:
            with open('recorde.json', 'r') as arquivo:
                dados = json.load(arquivo)
                self.recorde = dados.get('recorde', 0)
        except:
            self.recorde = 0

    def carregar_conquistas(self):
        try:
            with open('conquistas.json', 'r') as arquivo:
                self.conquistas.update(json.load(arquivo))
        except:
            pass

    def salvar_conquistas(self):
        with open('conquistas.json', 'w') as arquivo:
            json.dump(self.conquistas, arquivo)

    def mostrar_conquista(self, conquista):
        self.conquista_atual = {
            'texto': f"Conquista: {self.conquistas[conquista]['desc']}",
            'tempo': 180
        }

    def tocar_som(self, som):
        if self.som_ativo and som in self.sons:
            self.sons[som].play()

    def processar_eventos(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN:
            pos_mouse = pygame.mouse.get_pos()
            
            if self.tela_inicial:  # Verificar clique apenas na tela inicial
                if hasattr(self, 'botao_musica') and self.botao_musica.rect.collidepoint(pos_mouse):
                    self.musica_ativa = not self.musica_ativa
                    if self.musica_ativa:
                        pygame.mixer.music.play(-1)
                        pygame.mixer.music.set_volume(0.5)
                    else:
                        pygame.mixer.music.stop()
                    # Atualiza o texto do botão
                    self.botao_musica.texto = "SOM: ON" if self.musica_ativa else "SOM: OFF"
                    self.botao_musica.cor = VERDE_CLARO if self.musica_ativa else VERMELHO
                    return
            
            if not self.game_over and not self.pause:
                if self.botao_paredes.rect.collidepoint(pos_mouse):
                    self.modo_sem_paredes = not self.modo_sem_paredes
                elif self.botao_modo_noturno.rect.collidepoint(pos_mouse):
                    self.modo_noturno = not self.modo_noturno
            
            if self.game_over:
                if self.botao_reiniciar.rect.collidepoint(pos_mouse):
                    self.reset_game()
                elif hasattr(self, 'botao_menu') and self.botao_menu.rect.collidepoint(pos_mouse):
                    self.tela_inicial = True
                    self.game_over = False
        
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_SPACE:
                if self.game_over:
                    self.reset_game()
                else:
                    self.pause = not self.pause
            
            elif evento.key == pygame.K_m:
                self.modo_sem_paredes = not self.modo_sem_paredes
            
            elif evento.key == pygame.K_n:
                self.modo_noturno = not self.modo_noturno
            
            if not self.pause and not self.game_over:
                if evento.key in [pygame.K_UP, pygame.K_w] and self.direcao != 'BAIXO':
                    self.direcao = 'CIMA'
                elif evento.key in [pygame.K_DOWN, pygame.K_s] and self.direcao != 'CIMA':
                    self.direcao = 'BAIXO'
                elif evento.key in [pygame.K_LEFT, pygame.K_a] and self.direcao != 'DIREITA':
                    self.direcao = 'ESQUERDA'
                elif evento.key in [pygame.K_RIGHT, pygame.K_d] and self.direcao != 'ESQUERDA':
                    self.direcao = 'DIREITA'

    def desenhar(self):
        cores = self.cores['noite'] if self.modo_noturno else self.cores['dia']
        self.tela.fill(cores['fundo'])
        
        # Grade de fundo
        for x in range(0, LARGURA_JOGO, TAMANHO_BLOCO):
            for y in range(0, ALTURA, TAMANHO_BLOCO):
                pygame.draw.rect(self.tela, cores['grade'], 
                               (x, y, TAMANHO_BLOCO, TAMANHO_BLOCO), 1)
        
        # Desenha cobra
        self.desenhar_cobra()
        
        # Desenha comida/power-up
        cor = self.power_ups[self.comida[2]]['cor'] if self.comida[3] else VERMELHO
        pygame.draw.rect(self.tela, cor,
                        (self.comida[0], self.comida[1], 
                         TAMANHO_BLOCO-2, TAMANHO_BLOCO-2),
                        border_radius=5)
        
        # Efeitos visuais
        self.desenhar_efeitos_visuais()
        
        # Interface
        self.desenhar_interface()
        
        if self.pause:
            fonte = pygame.font.Font(None, 74)
            texto = fonte.render(self.textos['pausado'], True, BRANCO)
            pos = texto.get_rect(center=(LARGURA_JOGO//2, ALTURA//2))
            self.tela.blit(texto, pos)
        
        if self.game_over:
            # Overlay semi-transparente
            s = pygame.Surface((LARGURA_JOGO, ALTURA))
            s.set_alpha(128)
            s.fill((0, 0, 0))
            self.tela.blit(s, (0, 0))
            
            # Texto Game Over
            fonte = pygame.font.Font(None, 74)
            texto = fonte.render(self.textos['game_over'], True, VERMELHO)
            pos = texto.get_rect(center=(LARGURA_JOGO//2, ALTURA//2 - 50))
            self.tela.blit(texto, pos)
            
            # Pontuação final
            fonte_pontos = pygame.font.Font(None, 48)
            texto_pontos = fonte_pontos.render(
                self.textos['pontuacao'].format(self.pontuacao), True, BRANCO)
            pos_pontos = texto_pontos.get_rect(
                center=(LARGURA_JOGO//2, ALTURA//2 + 20))
            self.tela.blit(texto_pontos, pos_pontos)
            
            # Botão Reiniciar
            self.botao_reiniciar.rect.center = (LARGURA_JOGO//2, ALTURA//2 + 80)
            self.botao_reiniciar.desenhar(self.tela)
            
            # Botão Menu Principal
            self.botao_menu = Botao(
                LARGURA_JOGO//2 - 100, ALTURA//2 + 140, 200, 50,
                self.textos['menu_principal'], AZUL)
            self.botao_menu.desenhar(self.tela)

class Botao:
    def __init__(self, x, y, largura, altura, texto, cor):
        self.rect = pygame.Rect(x, y, largura, altura)
        self.texto = texto
        self.cor = cor
        self.cor_hover = tuple(min(255, c + 30) for c in cor)
        self.ativo = False

    def desenhar(self, tela):
        cor = self.cor_hover if self.ativo else self.cor
        pygame.draw.rect(tela, cor, self.rect, border_radius=12)
        pygame.draw.rect(tela, BRANCO, self.rect, 2, border_radius=12)
        
        fonte = pygame.font.Font(None, 36)
        texto = fonte.render(self.texto, True, BRANCO)
        texto_rect = texto.get_rect(center=self.rect.center)
        tela.blit(texto, texto_rect)

    def verifica_hover(self, pos):
        self.ativo = self.rect.collidepoint(pos)
        return self.ativo

# Inicialização do jogo
if __name__ == "__main__":
    jogo = SnakeGame()
    jogo.executar()