import httpx
from google import genai
from google.auth import exceptions as erros_auth
from google.genai import errors, types
from pydantic import ValidationError

from ia.provedores.base import (
    BloqueioSeguranca,
    ErroConfiguracao,
    ErroPermanente,
    ErroTemporario,
    ProvedorIA,
    RespostaIA,
    RespostaInvalida,
    TempoEsgotado,
    UsoTokens,
)

MOTIVOS_BLOQUEIO = ('SAFETY', 'PROHIBITED_CONTENT')


class ProvedorGemini(ProvedorIA):
    def __init__(self, config, acesso):
        super().__init__(config, acesso)
        opcoes_http = types.HttpOptions(
            timeout=config.timeout_s * 1000,
            retry_options=types.HttpRetryOptions(attempts=config.tentativas),
        )
        try:
            if acesso.modo == 'enterprise':
                self.cliente = genai.Client(
                    enterprise=True,
                    project=acesso.projeto,
                    location=acesso.regiao,
                    http_options=opcoes_http,
                )
            else:
                self.cliente = genai.Client(api_key=acesso.chave, http_options=opcoes_http)
        except erros_auth.DefaultCredentialsError as erro:
            raise ErroConfiguracao(
                'Credenciais do Google Cloud não encontradas. No App Engine use a conta de serviço; '
                'localmente rode gcloud auth application-default login.'
            ) from erro

    def gerar(self, pedido):
        modelo = self.config.modelo
        try:
            resposta = self.cliente.models.generate_content(
                model=modelo,
                contents=_conteudos(pedido),
                config=self._configuracao(pedido),
            )
        except errors.APIError as erro:
            raise _erro_da_api(erro, modelo) from erro
        except httpx.TimeoutException as erro:
            raise TempoEsgotado('O Vertex AI não respondeu no tempo limite.', modelo=modelo) from erro
        except httpx.TransportError as erro:
            raise ErroTemporario('Falha de rede ao falar com o Vertex AI.', modelo=modelo) from erro
        return self._resposta(resposta, pedido)

    def _configuracao(self, pedido):
        opcoes = {
            'system_instruction': pedido.instrucoes or None,
            'temperature': float(self.config.temperatura),
            'max_output_tokens': self.config.max_tokens_saida,
        }
        if self.config.nivel_raciocinio:
            nivel = types.ThinkingLevel(self.config.nivel_raciocinio.upper())
            opcoes['thinking_config'] = types.ThinkingConfig(thinking_level=nivel)
        if pedido.esquema is not None:
            opcoes['response_mime_type'] = 'application/json'
            opcoes['response_json_schema'] = _esquema_plano(pedido.esquema)
        return types.GenerateContentConfig(**opcoes)

    def _resposta(self, resposta, pedido):
        uso = _uso(resposta.usage_metadata)
        modelo = getattr(resposta, 'model_version', None) or self.config.modelo
        id_resposta = getattr(resposta, 'response_id', None) or ''
        texto = resposta.text or ''
        candidato = resposta.candidates[0] if resposta.candidates else None
        motivo = _nome(candidato.finish_reason) if candidato else ''
        prompt_bloqueado = resposta.prompt_feedback is not None and resposta.prompt_feedback.block_reason is not None

        if prompt_bloqueado or motivo in MOTIVOS_BLOQUEIO:
            raise BloqueioSeguranca(
                'O Vertex AI bloqueou o conteúdo por segurança.',
                uso=uso, texto_bruto=texto, modelo=modelo,
            )
        if motivo == 'MAX_TOKENS':
            raise RespostaInvalida(
                'A resposta foi cortada no limite de tokens de saída.',
                motivo_fim=motivo, uso=uso, texto_bruto=texto, modelo=modelo,
            )

        dados = None
        if pedido.esquema is not None:
            try:
                dados = pedido.esquema.model_validate_json(texto)
            except ValidationError as erro:
                raise RespostaInvalida(
                    'A resposta não segue o esquema pedido.',
                    motivo_fim=motivo, uso=uso, texto_bruto=texto, modelo=modelo,
                ) from erro
        return RespostaIA(
            texto=texto, dados=dados, uso=uso, modelo=modelo,
            motivo_fim=motivo, id_resposta=id_resposta,
        )


def _conteudos(pedido):
    conteudos = [
        types.Content(role=mensagem.papel, parts=[types.Part(text=mensagem.texto)])
        for mensagem in pedido.historico
    ]
    partes = [
        types.Part.from_bytes(data=arquivo.conteudo, mime_type=arquivo.mime)
        for arquivo in pedido.arquivos
    ]
    partes.append(types.Part(text=pedido.texto))
    conteudos.append(types.Content(role='user', parts=partes))
    return conteudos


def _esquema_plano(modelo):
    esquema = modelo.model_json_schema()
    definicoes = esquema.pop('$defs', {})

    def resolver(no, em_uso=()):
        if isinstance(no, list):
            return [resolver(item, em_uso) for item in no]
        if not isinstance(no, dict):
            return no
        if '$ref' in no:
            nome = no['$ref'].rsplit('/', 1)[-1]
            if nome in em_uso:
                raise ValueError(f'Esquema recursivo não é suportado: {nome}')
            return resolver(definicoes[nome], em_uso + (nome,))
        return {chave: resolver(valor, em_uso) for chave, valor in no.items()}

    return resolver(esquema)


def _uso(metadados):
    if metadados is None:
        return UsoTokens()
    raciocinio = metadados.thoughts_token_count or 0
    return UsoTokens(
        entrada=metadados.prompt_token_count or 0,
        saida=(metadados.candidates_token_count or 0) + raciocinio,
        raciocinio=raciocinio,
    )


def _nome(motivo):
    return motivo.name if hasattr(motivo, 'name') else str(motivo or '')


def _erro_da_api(erro, modelo):
    codigo = erro.code
    mensagem = erro.message or str(erro)
    if codigo in (401, 403):
        return ErroConfiguracao(f'O Vertex AI recusou as credenciais ou a permissão: {mensagem}', modelo=modelo)
    if codigo == 404 or (codigo == 400 and _parece_erro_de_modelo(mensagem)):
        return ErroConfiguracao(f'Modelo ou parâmetro inválido no Vertex AI: {mensagem}', modelo=modelo)
    if codigo == 429 or codigo >= 500:
        return ErroTemporario(f'Vertex AI indisponível no momento: {mensagem}', modelo=modelo)
    return ErroPermanente(f'Vertex AI recusou o pedido: {mensagem}', modelo=modelo)


def _parece_erro_de_modelo(mensagem):
    texto = mensagem.lower()
    return 'model' in texto or 'thinking' in texto
