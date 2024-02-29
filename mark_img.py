import cv2
import numpy as np

def marcar_caixa(imagem, canto_superior_esquerdo, canto_inferior_direito, cor=(0, 255, 0), espessura=2):
    # Faz uma cópia da imagem para evitar modificar a original
    imagem_marcada = np.copy(imagem)
    
    # Converte as coordenadas para inteiros
    x1, y1 = map(int, canto_superior_esquerdo)
    x2, y2 = map(int, canto_inferior_direito)
    
    # Desenha a caixa na imagem copiada
    cv2.rectangle(imagem_marcada, (x1, y1), (x2, y2), cor, espessura)
    
    return imagem_marcada

# Exemplo de uso:
imagem_original = cv2.imread(".pdf_files/ARQ-00470127000174-2023-1-2.jpg")  # Substitua pelo caminho da sua imagem
canto_superior_esquerdo = (124,601)
canto_inferior_direito = (1505,1165)

imagem_marcada = marcar_caixa(imagem_original, canto_superior_esquerdo, canto_inferior_direito)
cv2.imwrite("marcada.jpg", imagem_marcada)
