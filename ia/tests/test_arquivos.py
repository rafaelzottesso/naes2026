import hashlib
import io

from django.test import TestCase
from PIL import Image
from pypdf import PdfWriter

from ia.arquivos import ArquivoInvalido, hash_arquivo, preparar_arquivo
from ia.models import ConfiguracaoIA


def _png(largura, altura):
    buffer = io.BytesIO()
    Image.new('RGB', (largura, altura), 'red').save(buffer, format='PNG')
    return buffer.getvalue()


def _pdf(paginas):
    escritor = PdfWriter()
    for _ in range(paginas):
        escritor.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    escritor.write(buffer)
    return buffer.getvalue()


class PrepararArquivoTests(TestCase):
    def test_imagem_vira_jpeg_reduzida_ao_lado_maximo(self):
        conteudo, mime = preparar_arquivo(_png(4000, 3000), 'image/png')

        self.assertEqual(mime, 'image/jpeg')
        with Image.open(io.BytesIO(conteudo)) as imagem:
            self.assertLessEqual(max(imagem.size), 2048)

    def test_pdf_acima_do_limite_de_paginas_e_recusado(self):
        config = ConfiguracaoIA.obter()
        config.pdf_max_paginas = 2
        config.save()

        with self.assertRaises(ArquivoInvalido):
            preparar_arquivo(_pdf(3), 'application/pdf')

    def test_arquivo_acima_do_tamanho_e_recusado(self):
        config = ConfiguracaoIA.obter()
        config.tamanho_maximo_mb = 1
        config.save()

        with self.assertRaises(ArquivoInvalido):
            preparar_arquivo(b'x' * (1024 * 1024 + 1), 'image/png')

    def test_tipo_nao_aceito_e_recusado(self):
        with self.assertRaises(ArquivoInvalido):
            preparar_arquivo(b'texto puro', 'text/plain')

    def test_hash_arquivo_e_sha256_em_hexadecimal(self):
        self.assertEqual(hash_arquivo(b'abc'), hashlib.sha256(b'abc').hexdigest())
