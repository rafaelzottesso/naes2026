from hashlib import sha256
from io import BytesIO

from PIL import Image, ImageOps
from pypdf import PdfReader

from ia.models import ConfiguracaoIA

Image.MAX_IMAGE_PIXELS = 40_000_000
MB = 1024 * 1024


class ArquivoInvalido(Exception):
    pass


def preparar_arquivo(conteudo, mime, lado_maximo=2048):
    config = ConfiguracaoIA.obter()
    if len(conteudo) > config.tamanho_maximo_mb * MB:
        raise ArquivoInvalido(f'O arquivo passa de {config.tamanho_maximo_mb} MB. Envie um menor.')
    if mime == 'application/pdf' or conteudo.startswith(b'%PDF-'):
        return _preparar_pdf(conteudo, config.pdf_max_paginas), 'application/pdf'
    if not mime.lower().startswith('image/'):
        raise ArquivoInvalido('Tipo de arquivo não aceito. Envie um PDF ou uma imagem.')
    return _preparar_imagem(conteudo, lado_maximo), 'image/jpeg'


def hash_arquivo(conteudo):
    return sha256(conteudo).hexdigest()


def _preparar_pdf(conteudo, max_paginas):
    try:
        paginas = len(PdfReader(BytesIO(conteudo)).pages)
    except Exception as erro:
        raise ArquivoInvalido('Não consegui ler este PDF.') from erro
    if paginas > max_paginas:
        raise ArquivoInvalido(f'O PDF tem {paginas} páginas. O limite é {max_paginas}.')
    return conteudo


def _preparar_imagem(conteudo, lado_maximo):
    try:
        with Image.open(BytesIO(conteudo)) as original:
            imagem = ImageOps.exif_transpose(original).convert('RGB')
    except (Image.DecompressionBombError, OSError) as erro:
        raise ArquivoInvalido('Não consegui abrir esta imagem.') from erro
    imagem.thumbnail((lado_maximo, lado_maximo))
    saida = BytesIO()
    imagem.save(saida, format='JPEG', quality=85)
    return saida.getvalue()
