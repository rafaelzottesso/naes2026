(function ($) {
  if (!$ || !$.fn.mask) return;

  function somenteDigitos(valor) {
    return (valor || '').replace(/\D/g, '');
  }

  function mascaraDocumento(valor) {
    return somenteDigitos(valor).length > 11
      ? '00.000.000/0000-00'
      : '000.000.000-009';
  }

  function mascaraTelefone(valor) {
    return somenteDigitos(valor).length > 10
      ? '(00) 00000-0000'
      : '(00) 0000-00009';
  }

  var opcoesDocumento = {
    onKeyPress: function (valor, evento, campo, opcoes) {
      $(campo).mask(mascaraDocumento(valor), opcoes);
    }
  };

  var opcoesTelefone = {
    onKeyPress: function (valor, evento, campo, opcoes) {
      $(campo).mask(mascaraTelefone(valor), opcoes);
    }
  };

  $(function () {
    $('input[name]').each(function () {
      var campo = $(this);
      var identificador = [campo.attr('name'), campo.attr('id')]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

      if (identificador.includes('documento') || (identificador.includes('cpf') && identificador.includes('cnpj'))) {
        campo.mask(mascaraDocumento(campo.val()), opcoesDocumento);
      } else if (identificador.includes('cnpj')) {
        campo.mask('00.000.000/0000-00');
      } else if (identificador.includes('cpf')) {
        campo.mask('000.000.000-00');
      } else if (identificador.includes('cep')) {
        campo.mask('00000-000');
      } else if (['telefone', 'celular', 'whatsapp'].some(function (termo) {
        return identificador.includes(termo);
      })) {
        campo.mask(mascaraTelefone(campo.val()), opcoesTelefone);
      }
    });
  });
})(window.jQuery);