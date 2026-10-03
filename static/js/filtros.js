(function ($) {
  'use strict';

  $(document).on('click', '.fin-filtro-botao', function () {
    var acionador = this;
    var template = document.getElementById(acionador.dataset.templateFiltros);
    var formularioModelo = template && template.content.querySelector('form');
    if (!formularioModelo) return;

    var formulario = formularioModelo.cloneNode(true);
    var caixa;
    caixa = bootbox.dialog({
      title: 'Filtros da lista',
      message: $('<div class="fin-filtros-modal"></div>').append(formulario),
      buttons: {
        limpar: {
          label: 'Limpar filtros',
          className: 'btn-outline-secondary',
          callback: function () {
            window.location.assign(acionador.dataset.urlLimpar);
            return false;
          }
        },
        cancelar: { label: 'Cancelar', className: 'btn-outline-secondary' },
        aplicar: {
          label: 'Filtrar',
          className: 'btn-primary',
          callback: function () {
            var botao = caixa.find('[data-bb-handler="aplicar"]')[0];
            if (!botao) return false;
            if (window.AnotAI && window.AnotAI.carregando) {
              window.AnotAI.carregando.iniciar(botao, 'Filtrando...');
            }
            formulario.submit();
            return false;
          }
        }
      }
    });
  });
})(window.jQuery);