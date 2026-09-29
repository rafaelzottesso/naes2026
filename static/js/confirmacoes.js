(function ($) {
  function tokenCsrf() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) return meta.content;
    var input = document.querySelector('[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
  }

  $(document).on('click', 'a.js-excluir', function (evento) {
    evento.preventDefault();
    var link = this;
    var destino = link.getAttribute('href');

    bootbox.confirm({
      title: link.dataset.titulo || 'Excluir',
      message: link.dataset.mensagem || 'Excluir este registro?',
      buttons: {
        confirm: { label: 'Sim, excluir', className: 'btn-danger' },
        cancel: { label: 'Cancelar', className: 'btn-outline-secondary' }
      },
      callback: function (confirmado) {
        if (!confirmado) return;
        if (window.AnotAI && window.AnotAI.carregando) window.AnotAI.carregando.iniciar(link, 'Excluindo...');
        var form = document.createElement('form');
        form.method = 'post';
        form.action = destino;
        var token = document.createElement('input');
        token.type = 'hidden';
        token.name = 'csrfmiddlewaretoken';
        token.value = tokenCsrf();
        form.appendChild(token);
        document.body.appendChild(form);
        form.submit();
      }
    });
  });
})(window.jQuery);
